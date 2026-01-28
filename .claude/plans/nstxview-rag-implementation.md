# NSTXView RAG Implementation Plan

## Executive Summary

This plan implements a hybrid RAG (Retrieval Augmented Generation) approach for NSTXView that combines semantic search for conceptual questions with structured database queries for quantitative data. The system will scale to handle ~1500 papers with efficient chunking, embedding, and retrieval.

## Current Status

### ✅ Already Implemented
- **Vector Store Infrastructure** (`app/services/nstxview/vector_store.py`): ChromaDB wrapper with persistent storage
- **Database Models** (`app/models.py`): `NSTXPaperChunk` table for chunk metadata
- **Chat Service** (`app/services/nstxview/chat_service.py`): Claude-powered chat with 8 structured query tools
- **PDF Processing** (`app/services/nstxview/pdf_processor.py`): Text extraction with `chunk_text()` and `chunk_by_sections()` methods
- **MCP Server** (`nstxview-mcp/server.py`): Model Context Protocol server for structured queries

### ❌ Gaps to Address
1. ChromaDB not installed (missing from requirements.txt)
2. Chunking not integrated into processing pipeline
3. Embeddings not being generated
4. RAG not integrated into chat responses
5. No hybrid routing between structured queries and RAG

## Architecture: Hybrid Approach

### Query Routing Strategy

**Use MCP/Structured Queries for:**
- Specific shot lookups ("What happened in shot 141234?")
- Parameter statistics ("What's the average ion temperature?")
- Quantitative queries ("Papers with beta > 0.3")
- Precise data extraction (shots, parameters, phenomena)

**Use RAG/Semantic Search for:**
- Conceptual questions ("Explain H-mode transitions")
- Finding relevant passages ("How does lithium coating affect performance?")
- Cross-paper synthesis ("What are common ELM mitigation techniques?")
- Open-ended exploration ("What do we know about disruption prediction?")
- Method comparisons ("Different approaches to plasma heating")

**Hybrid (Use Both) for:**
- Complex questions combining concepts and data
- Follow-up questions referencing previous context
- Validation queries ("Show me evidence for X")

## Implementation Plan

### Phase 1: Dependencies & Infrastructure (30 min)

**Files to modify:**
- `requirements.txt`
- `app/config.py`

**Tasks:**
1. Add ChromaDB to requirements.txt:
   - `chromadb>=0.4.24` - Vector database
   - `sentence-transformers>=2.2.2` - For embedding generation
   - `pymupdf>=1.23.0` - For PDF processing (may already exist)

2. Add embedding configuration to `app/config.py`:
   ```python
   # Embedding Configuration
   EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
   """Sentence transformer model for embeddings. Options:
   - all-MiniLM-L6-v2: Fast, good quality (384 dims)
   - all-mpnet-base-v2: Higher quality (768 dims, slower)
   - multi-qa-mpnet-base-dot-v1: Optimized for Q&A
   """

   CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
   """Target chunk size in words (default 500 = ~2-3 paragraphs)"""

   CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
   """Word overlap between chunks for context preservation"""

   RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
   """Number of relevant chunks to retrieve for RAG"""
   ```

### Phase 2: Embedding Service (45 min)

**New file:** `app/services/nstxview/embedding_service.py`

**Purpose:** Centralized service for generating embeddings using sentence-transformers

**Key features:**
- Lazy loading of embedding model (only when needed)
- Batch processing for efficiency
- Caching to avoid re-embedding
- Fallback to ChromaDB's default embeddings if model fails

**Core methods:**
- `generate_embeddings(texts: List[str]) -> List[List[float]]`
- `generate_embedding(text: str) -> List[float]`
- `get_model_info() -> Dict` (dimensions, name)

**Why sentence-transformers:**
- Free, no API costs
- Runs locally or on Railway
- Good quality for scientific text
- Fast enough for 1500 papers
- 384-768 dimensions (compact)

### Phase 3: Processing Pipeline Integration (1 hour)

**Files to modify:**
- `app/services/nstxview/processing_service.py`
- `scripts/process_nstxview_papers.py`

**New function in processing_service.py:** `perform_embedding_generation(task_id: int, paper_ids: List[int])`

**Pipeline flow:**
```
1. Download PDF from Drive
2. Extract text (existing)
3. Extract structured data - shots/parameters/phenomena (existing)
4. **NEW: Generate chunks**
   - Use pdf_processor.chunk_by_sections() if sections identified
   - Fall back to chunk_text() for generic chunking
   - Target: ~500 words per chunk with 50 word overlap
5. **NEW: Generate embeddings**
   - Batch process chunks (10-50 at a time)
   - Store in ChromaDB with metadata
   - Save chunk metadata to NSTXPaperChunk table
6. Update paper status to COMPLETED
```

**Database updates:**
- Add `embedding_date` field to track when embeddings generated
- Update `NSTXProcessingStatus` enum to include `GENERATING_EMBEDDINGS`

**Error handling:**
- If embedding fails, mark paper as COMPLETED but log warning
- Allow re-running embedding generation separately
- Skip papers that already have embeddings

### Phase 4: RAG-Enhanced Chat Service (1.5 hours)

**Files to modify:**
- `app/services/nstxview/chat_service.py`

**New tool:** `semantic_search`
```python
{
    "name": "semantic_search",
    "description": "Semantic search across paper content for conceptual questions, finding relevant passages, or exploring topics. Returns relevant text excerpts with citations.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language query to search for"
            },
            "top_k": {
                "type": "integer",
                "description": "Number of relevant chunks to return (default 5)",
                "default": 5
            },
            "paper_ids": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Optional: Limit search to specific papers"
            }
        },
        "required": ["query"]
    }
}
```

**Implementation approach:**
1. Add VectorStore instance to NSTXViewChatService
2. Implement `_semantic_search()` method:
   - Query ChromaDB with user's question
   - Retrieve top_k chunks with metadata
   - Format results with paper title, section, and DOI
   - Return as structured JSON for Claude

3. Update system prompt to include guidance on when to use semantic search:
   ```
   Use semantic_search for:
   - Conceptual explanations
   - Finding relevant passages across papers
   - Open-ended exploration
   - Method comparisons

   Use structured tools (search_papers, query_shots, etc.) for:
   - Specific shot/parameter data
   - Quantitative analysis
   - Statistics and aggregations
   ```

4. Enhance citation formatting:
   - When RAG returns chunks, include both paper citation AND section
   - Format: [Paper Title - Section](DOI)
   - Example: [H-mode studies in NSTX - Results](https://doi.org/10.1088/...)

### Phase 5: API Endpoint Updates (30 min)

**Files to modify:**
- `app/routers/nstxview.py`

**Updates to `/search` endpoint:**
- Replace TODO with actual ChromaDB semantic search
- Keep SQL fallback for when ChromaDB unavailable
- Add response field indicating search method used

**New endpoint:** `POST /nstxview/papers/{paper_id}/embeddings/regenerate`
- Allow re-generating embeddings for a specific paper
- Useful if embedding model is upgraded
- Admin-only endpoint

**Updated endpoint:** `GET /nstxview/stats`
- Add embedding statistics:
  - Papers with embeddings
  - Total chunks
  - Average chunks per paper

### Phase 6: MCP Server Enhancement (30 min)

**Files to modify:**
- `nstxview-mcp/server.py`

**Add semantic search tool to MCP:**
```python
@mcp.tool()
def semantic_search(
    query: str,
    top_k: int = 5,
    paper_ids: Optional[List[int]] = None
) -> str:
    """
    Semantic search across paper content.

    Use this for conceptual questions, finding relevant passages,
    or exploring topics across papers.
    """
    collection = get_chromadb_collection()
    if not collection:
        return json.dumps({"error": "Vector search not available"})

    # Query ChromaDB
    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        where={"paper_id": {"$in": paper_ids}} if paper_ids else None,
        include=["documents", "metadatas", "distances"]
    )

    # Format results with paper info
    # ...
```

**Update MCP instructions:**
- Clarify when to use semantic search vs structured queries
- Provide examples of each query type

### Phase 7: Batch Processing & Migration (1 hour)

**New script:** `scripts/admin/generate_embeddings.py`

**Purpose:** Batch generate embeddings for existing papers

**Features:**
- Process papers in batches (10-20 at a time)
- Progress tracking
- Resume capability (skip papers that already have embeddings)
- Parallel processing option for faster completion
- Estimated time remaining

**Usage:**
```bash
# Generate embeddings for all papers without embeddings
python scripts/admin/generate_embeddings.py --all

# Generate for specific papers
python scripts/admin/generate_embeddings.py --paper-ids 1 2 3

# Regenerate embeddings (force re-generation)
python scripts/admin/generate_embeddings.py --all --force

# Parallel processing (4 workers)
python scripts/admin/generate_embeddings.py --all --workers 4
```

**Estimated time for 1500 papers:**
- Text extraction: Already done
- Chunking: ~0.1 sec/paper = 2.5 minutes
- Embedding generation: ~1 sec/paper = 25 minutes
- ChromaDB insertion: ~0.2 sec/paper = 5 minutes
- **Total: ~35 minutes for full corpus**

## Scalability Considerations

### For 1500 Papers

**Storage estimates:**
- Average paper: 20 pages, ~10k words
- Chunks per paper: ~20 chunks (500 words each)
- Total chunks: 1500 × 20 = 30,000 chunks
- Embedding size: 384 dims × 4 bytes = 1.5 KB per chunk
- Total embedding storage: 30,000 × 1.5 KB = ~45 MB
- ChromaDB index: ~100 MB
- **Total: ~150 MB** (very manageable)

**Query performance:**
- ChromaDB can handle millions of vectors
- 30k vectors: sub-second queries
- No need for approximation (ANN) at this scale
- Exact search is fast enough

**Processing time:**
- Initial embedding generation: ~35 minutes
- Incremental updates: ~1 minute per new paper
- Re-embedding all (if model upgraded): ~35 minutes

### Optimization Strategies

1. **Chunking strategy:**
   - Use section-aware chunking when possible
   - Preserve important context (figure captions, equations)
   - Balance chunk size: too small = fragmented, too large = irrelevant

2. **Embedding efficiency:**
   - Batch embeddings (10-50 texts at once)
   - Cache embeddings to avoid re-computation
   - Use smaller model (384 dims) for speed

3. **Query optimization:**
   - Limit top_k to 5-10 chunks (more = slower, less relevant)
   - Use metadata filtering (paper_id, section) to narrow search
   - Cache frequently asked questions

4. **Storage optimization:**
   - Store only content hash in PostgreSQL
   - Full content in ChromaDB only
   - Implement TTL for old embeddings if needed

## Testing Strategy

### Unit Tests
- Embedding service: test batch processing, error handling
- Chunking: test overlap, section boundaries
- Vector store: test CRUD operations

### Integration Tests
- End-to-end pipeline: PDF → chunks → embeddings → search
- Chat service: test RAG tool integration
- API endpoints: test search functionality

### Manual Testing
- Ask conceptual questions (RAG should be used)
- Ask quantitative questions (structured tools should be used)
- Ask hybrid questions (both should be used)
- Verify citation quality

### Performance Tests
- Measure embedding generation time for 10/100/1000 papers
- Measure search latency (should be < 200ms)
- Test concurrent queries

## Rollout Plan

### Development (Local)
1. Install dependencies
2. Implement embedding service
3. Test with 5-10 papers
4. Verify chat integration

### Staging (Railway Dev)
1. Deploy updated code
2. Run embedding generation script on ~90 existing papers
3. Test API endpoints
4. Verify MCP server

### Production
1. Deploy to production Railway
2. Run batch embedding generation (monitor progress)
3. Update frontend to show embedding status
4. Monitor query performance

## Configuration Variables

### Environment Variables to Add

```bash
# Embedding Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2  # or all-mpnet-base-v2 for better quality
CHUNK_SIZE=500                     # words per chunk
CHUNK_OVERLAP=50                   # word overlap between chunks
RAG_TOP_K=5                        # chunks returned per search

# ChromaDB Configuration (already exist)
CHROMADB_HOST=                     # empty = use persistent local storage
CHROMADB_PORT=8000
CHROMADB_PERSIST_DIR=./data/chromadb  # local storage path
```

### Railway Configuration
- Add `CHROMADB_PERSIST_DIR=/app/data/chromadb`
- Ensure Railway volume mounted at `/app/data` for persistence
- Or use Railway's built-in disk for ChromaDB storage

## Success Metrics

### Quality Metrics
- **Citation accuracy**: 95%+ of responses include proper citations
- **Relevance**: Top-3 retrieved chunks are relevant for 90%+ of queries
- **Response quality**: Users rate responses 4+/5 stars

### Performance Metrics
- **Search latency**: < 200ms for semantic search
- **Embedding generation**: < 1 minute per paper
- **Chat response time**: < 5 seconds including RAG

### Adoption Metrics
- **RAG usage**: 30%+ of queries use semantic search
- **User satisfaction**: 4+/5 rating for conceptual answers
- **Error rate**: < 1% of queries fail

## Risk Mitigation

### Risk 1: Embedding quality is poor
**Mitigation:**
- Start with proven model (all-MiniLM-L6-v2)
- Test on sample queries before full rollout
- Plan for easy model swapping

### Risk 2: ChromaDB storage issues on Railway
**Mitigation:**
- Use persistent volumes
- Implement export/backup scripts
- Fallback to SQL text search

### Risk 3: Slow embedding generation
**Mitigation:**
- Batch processing
- Parallel workers
- Process incrementally (not all at once)

### Risk 4: Poor query routing (RAG vs structured)
**Mitigation:**
- Let Claude decide with clear tool descriptions
- Monitor which tools are used
- Refine system prompt based on usage patterns

## Future Enhancements

### Phase 8+ (Post-MVP)
1. **Hybrid ranking**: Combine semantic + keyword + citation signals
2. **Re-ranking**: Use cross-encoder for better relevance
3. **Query expansion**: Expand user query with domain terms
4. **Multi-modal**: Include figures, tables, equations in search
5. **Citation graph**: Use paper citations to improve relevance
6. **User feedback**: Learn from which results users click
7. **Summarization**: Auto-summarize retrieved chunks
8. **Question decomposition**: Break complex questions into sub-queries

## Appendix: Alternative Approaches Considered

### Approach 1: Use OpenAI Embeddings API
**Pros:** Higher quality, maintained by OpenAI
**Cons:** API costs ($0.0001/1k tokens), latency, external dependency
**Decision:** Use sentence-transformers for cost and control

### Approach 2: Use Pinecone/Weaviate instead of ChromaDB
**Pros:** Managed service, better scaling
**Cons:** Additional costs, vendor lock-in, setup complexity
**Decision:** ChromaDB sufficient for 1500 papers

### Approach 3: Store embeddings in PostgreSQL (pgvector)
**Pros:** Single database, simpler architecture
**Cons:** Slower for vector search, more complex setup
**Decision:** ChromaDB better for vector operations

### Approach 4: No RAG, only structured queries
**Pros:** Simpler, more predictable
**Cons:** Can't answer conceptual questions, no passage retrieval
**Decision:** Hybrid approach provides best user experience

---

## Implementation Checklist

- [ ] Phase 1: Add dependencies to requirements.txt
- [ ] Phase 1: Add configuration to app/config.py
- [ ] Phase 2: Create embedding_service.py
- [ ] Phase 2: Test embedding generation locally
- [ ] Phase 3: Integrate chunking into processing pipeline
- [ ] Phase 3: Add embedding generation to pipeline
- [ ] Phase 3: Update database models
- [ ] Phase 4: Add semantic_search tool to chat service
- [ ] Phase 4: Update system prompt
- [ ] Phase 4: Test RAG in chat
- [ ] Phase 5: Update /search endpoint
- [ ] Phase 5: Add regenerate embeddings endpoint
- [ ] Phase 5: Update stats endpoint
- [ ] Phase 6: Add semantic search to MCP server
- [ ] Phase 6: Update MCP instructions
- [ ] Phase 7: Create batch embedding script
- [ ] Phase 7: Test on small subset (10 papers)
- [ ] Phase 7: Run on full corpus (~90 papers)
- [ ] Testing: Unit tests for embedding service
- [ ] Testing: Integration tests for pipeline
- [ ] Testing: Manual testing of chat queries
- [ ] Deploy to Railway dev
- [ ] Deploy to Railway production
- [ ] Monitor performance and quality

**Estimated total implementation time: 6-8 hours**
