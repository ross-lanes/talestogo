"""
ChromaDB Vector Store for NSTXView

Manages embeddings and semantic search for paper chunks.
"""

import os
import logging
from typing import List, Optional, Dict, Any

from app.config import CHROMADB_HOST, CHROMADB_PORT, CHROMADB_PERSIST_DIR, ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)

# Try to import ChromaDB
try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False
    logger.warning("ChromaDB not installed. Vector search will be unavailable.")


class VectorStore:
    """
    ChromaDB vector store for NSTXView paper embeddings.

    Provides:
    - Embedding storage and retrieval
    - Semantic search across papers
    - Metadata filtering
    """

    COLLECTION_NAME = "nstxview_papers"

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        persist_directory: Optional[str] = None
    ):
        """
        Initialize the vector store.

        Args:
            host: ChromaDB server host (for client mode)
            port: ChromaDB server port
            persist_directory: Directory for local persistence (for embedded mode)
        """
        if not HAS_CHROMADB:
            raise ImportError(
                "ChromaDB is required for vector search. "
                "Install it with: pip install chromadb"
            )

        self.host = host or CHROMADB_HOST
        self.port = port or CHROMADB_PORT
        self.persist_directory = persist_directory
        self._client = None
        self._collection = None

    @property
    def client(self):
        """Get or create ChromaDB client"""
        if self._client is None:
            if self.persist_directory:
                # Use local persistent storage
                self._client = chromadb.PersistentClient(
                    path=self.persist_directory,
                    settings=Settings(anonymized_telemetry=False)
                )
                logger.info(f"Using persistent ChromaDB at {self.persist_directory}")
            elif self.host and self.host != "localhost":
                # Connect to remote ChromaDB server
                self._client = chromadb.HttpClient(
                    host=self.host,
                    port=self.port
                )
                logger.info(f"Connected to ChromaDB at {self.host}:{self.port}")
            else:
                # Use ephemeral in-memory client (for development)
                self._client = chromadb.Client(
                    settings=Settings(anonymized_telemetry=False)
                )
                logger.info("Using ephemeral in-memory ChromaDB")

        return self._client

    @property
    def collection(self):
        """Get or create the papers collection"""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"description": "NSTX/NSTX-U paper chunks for semantic search"}
            )
            logger.info(f"Using collection '{self.COLLECTION_NAME}' with {self._collection.count()} documents")

        return self._collection

    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
        embeddings: Optional[List[List[float]]] = None
    ) -> None:
        """
        Add documents to the collection.

        Args:
            documents: List of text content
            metadatas: List of metadata dicts
            ids: List of unique document IDs
            embeddings: Optional pre-computed embeddings
        """
        if embeddings:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
        else:
            # ChromaDB will generate embeddings using its default function
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

        logger.info(f"Added {len(documents)} documents to collection")

    def add_paper_chunks(
        self,
        paper_id: int,
        chunks: List[Dict[str, Any]],
        embeddings: Optional[List[List[float]]] = None
    ) -> List[str]:
        """
        Add chunks from a paper to the collection.

        Args:
            paper_id: Database ID of the paper
            chunks: List of chunk dicts with 'content', 'index', 'section'
            embeddings: Optional pre-computed embeddings

        Returns:
            List of ChromaDB document IDs
        """
        documents = []
        metadatas = []
        ids = []

        for chunk in chunks:
            chromadb_id = f"paper_{paper_id}_chunk_{chunk['index']}"

            documents.append(chunk['content'])
            metadatas.append({
                "paper_id": paper_id,
                "chunk_index": chunk['index'],
                "section": chunk.get('section') or ""
            })
            ids.append(chromadb_id)

        self.add_documents(documents, metadatas, ids, embeddings)

        return ids

    def search(
        self,
        query: str,
        n_results: int = 10,
        paper_ids: Optional[List[int]] = None,
        sections: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Semantic search across paper chunks.

        Args:
            query: Search query text
            n_results: Maximum number of results
            paper_ids: Optional filter by paper IDs
            sections: Optional filter by section names

        Returns:
            Dict with 'ids', 'documents', 'metadatas', 'distances'
        """
        where_filter = None

        if paper_ids or sections:
            conditions = []

            if paper_ids:
                if len(paper_ids) == 1:
                    conditions.append({"paper_id": paper_ids[0]})
                else:
                    conditions.append({"paper_id": {"$in": paper_ids}})

            if sections:
                if len(sections) == 1:
                    conditions.append({"section": sections[0]})
                else:
                    conditions.append({"section": {"$in": sections}})

            if len(conditions) == 1:
                where_filter = conditions[0]
            else:
                where_filter = {"$and": conditions}

        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        return {
            "ids": results["ids"][0] if results["ids"] else [],
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else []
        }

    def delete_paper(self, paper_id: int) -> int:
        """
        Delete all chunks for a paper.

        Args:
            paper_id: Database ID of the paper

        Returns:
            Number of documents deleted
        """
        # Get all document IDs for this paper
        results = self.collection.get(
            where={"paper_id": paper_id},
            include=[]
        )

        ids_to_delete = results["ids"]

        if ids_to_delete:
            self.collection.delete(ids=ids_to_delete)
            logger.info(f"Deleted {len(ids_to_delete)} chunks for paper {paper_id}")

        return len(ids_to_delete)

    def get_paper_chunks(self, paper_id: int) -> Dict[str, Any]:
        """
        Get all chunks for a paper.

        Args:
            paper_id: Database ID of the paper

        Returns:
            Dict with 'ids', 'documents', 'metadatas'
        """
        results = self.collection.get(
            where={"paper_id": paper_id},
            include=["documents", "metadatas"]
        )

        return {
            "ids": results["ids"],
            "documents": results["documents"],
            "metadatas": results["metadatas"]
        }

    def count(self) -> int:
        """Get total number of documents in collection"""
        return self.collection.count()

    def reset(self) -> None:
        """
        Delete and recreate the collection.

        WARNING: This deletes all data!
        """
        self.client.delete_collection(self.COLLECTION_NAME)
        self._collection = None
        logger.warning(f"Reset collection '{self.COLLECTION_NAME}'")


# Convenience function
def get_vector_store(persist_directory: Optional[str] = None) -> VectorStore:
    """
    Get a configured VectorStore instance.

    Uses local persistent storage by default (no Docker required).
    Set CHROMADB_HOST to use a remote server instead.

    Args:
        persist_directory: Optional local directory for persistence.
                          Defaults to CHROMADB_PERSIST_DIR config.

    Returns:
        VectorStore instance
    """
    # Use persistent directory if no remote host is configured
    if not CHROMADB_HOST and persist_directory is None:
        persist_directory = CHROMADB_PERSIST_DIR

    return VectorStore(persist_directory=persist_directory)


def is_available() -> bool:
    """Check if vector store is available (ChromaDB installed)"""
    return HAS_CHROMADB
