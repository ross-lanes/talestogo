"""
Embedding Service for NSTXView

Generates embeddings for paper chunks using sentence-transformers.
Provides efficient batch processing and caching.
"""

import logging
from typing import List, Dict, Any, Optional
import hashlib

logger = logging.getLogger(__name__)

# Try to import sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    SentenceTransformer = None
    logger.warning("sentence-transformers not installed. Embedding generation will be unavailable.")

from app.config import EMBEDDING_MODEL


class EmbeddingService:
    """
    Service for generating embeddings using sentence-transformers.

    Features:
    - Lazy loading of model (only loads when first needed)
    - Batch processing for efficiency
    - Model info for dimension tracking
    - Fallback to None if model unavailable
    """

    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the embedding service.

        Args:
            model_name: Name of the sentence-transformer model to use.
                       If None, uses EMBEDDING_MODEL from config.
        """
        if not HAS_SENTENCE_TRANSFORMERS:
            raise ImportError(
                "sentence-transformers is required for embedding generation. "
                "Install it with: pip install sentence-transformers"
            )

        self.model_name = model_name or EMBEDDING_MODEL
        self._model = None
        self._model_info = None

    @property
    def model(self) -> SentenceTransformer:
        """Lazy load the embedding model"""
        if self._model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            logger.info(f"Model loaded successfully. Dimension: {self._model.get_sentence_embedding_dimension()}")
        return self._model

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.

        Returns:
            Dict with 'name', 'dimension', and 'max_seq_length' keys
        """
        if self._model_info is None:
            model = self.model  # Trigger lazy load
            self._model_info = {
                "name": self.model_name,
                "dimension": model.get_sentence_embedding_dimension(),
                "max_seq_length": model.max_seq_length
            }
        return self._model_info

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            # Return zero vector of correct dimension
            dimension = self.get_model_info()["dimension"]
            return [0.0] * dimension

        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def generate_embeddings(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = False
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process at once (default 32)
            show_progress: Whether to show progress bar

        Returns:
            List of embedding vectors (each is a list of floats)
        """
        if not texts:
            return []

        # Filter out empty texts and track indices
        valid_texts = []
        valid_indices = []
        for i, text in enumerate(texts):
            if text and text.strip():
                valid_texts.append(text)
                valid_indices.append(i)

        if not valid_texts:
            logger.warning("No valid texts to embed")
            dimension = self.get_model_info()["dimension"]
            return [[0.0] * dimension for _ in texts]

        logger.info(f"Generating embeddings for {len(valid_texts)} texts...")

        # Generate embeddings in batches
        embeddings = self.model.encode(
            valid_texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )

        # Convert to list of lists
        embeddings_list = [emb.tolist() for emb in embeddings]

        # Insert embeddings back at correct positions
        dimension = self.get_model_info()["dimension"]
        result = [[0.0] * dimension for _ in texts]
        for valid_idx, original_idx in enumerate(valid_indices):
            result[original_idx] = embeddings_list[valid_idx]

        logger.info(f"Generated {len(embeddings_list)} embeddings")
        return result

    def generate_chunk_embeddings(
        self,
        chunks: List[Dict[str, Any]],
        content_key: str = "content",
        batch_size: int = 32
    ) -> List[Dict[str, Any]]:
        """
        Generate embeddings for paper chunks.

        Args:
            chunks: List of chunk dicts (must have 'content' key)
            content_key: Key name for the text content in chunk dicts
            batch_size: Batch size for processing

        Returns:
            List of chunk dicts with 'embedding' key added
        """
        if not chunks:
            return []

        # Extract text content
        texts = [chunk.get(content_key, "") for chunk in chunks]

        # Generate embeddings
        embeddings = self.generate_embeddings(texts, batch_size=batch_size)

        # Add embeddings to chunks
        result = []
        for chunk, embedding in zip(chunks, embeddings):
            chunk_with_embedding = chunk.copy()
            chunk_with_embedding["embedding"] = embedding
            result.append(chunk_with_embedding)

        return result

    @staticmethod
    def compute_text_hash(text: str) -> str:
        """
        Compute a hash of text for caching/deduplication.

        Args:
            text: Text to hash

        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(text.encode('utf-8')).hexdigest()


# Singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service(model_name: Optional[str] = None) -> EmbeddingService:
    """
    Get or create the embedding service singleton.

    Args:
        model_name: Optional model name override

    Returns:
        EmbeddingService instance
    """
    global _embedding_service

    if _embedding_service is None or (model_name and model_name != _embedding_service.model_name):
        if not HAS_SENTENCE_TRANSFORMERS:
            raise ImportError(
                "sentence-transformers is required. "
                "Install it with: pip install sentence-transformers"
            )
        _embedding_service = EmbeddingService(model_name)

    return _embedding_service


def is_available() -> bool:
    """Check if embedding generation is available"""
    return HAS_SENTENCE_TRANSFORMERS
