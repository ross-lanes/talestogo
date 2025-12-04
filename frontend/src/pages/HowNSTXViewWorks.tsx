import React from 'react';
import {
  Box,
  Typography,
  Paper,
} from '@mui/material';

export default function HowNSTXViewWorks() {
  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, color: 'primary.main' }}>
          How NSTXView Works
        </Typography>
      </Box>

      {/* Overview */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, color: 'secondary.main' }}>
          Overview
        </Typography>
        <Typography variant="body1" paragraph>
          NSTXView is a research analysis platform for scholarly papers about plasma physics experiments conducted on National Spherical Torus Experiment (NSTX) and National Spherical Torus Experiment-Upgrade (NSTX-U) at Princeton Plasma Physics Laboratory (PPPL). It extracts structured information from hundreds of research papers to help scientists understand what characteristics make plasma "shots" scientifically interesting.
        </Typography>
        <Typography variant="body1" paragraph>
          The core hypothesis: If researchers wrote a paper about a particular shot or set of shots, those shots must have been interesting in some way. By analyzing what papers say about these shots, NSTXView identifies patterns that define "interestingness" and can potentially apply these criteria to future NSTX-U experiments.
        </Typography>
      </Paper>

      {/* Key Concepts */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, color: 'secondary.main' }}>
          Key Concepts
        </Typography>

        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mt: 2 }}>
          Shots
        </Typography>
        <Typography variant="body1" paragraph>
          Individual plasma experiments are identified by 6-digit shot numbers starting with 1 (e.g., 141234, 138576). Each shot represents a specific plasma discharge with unique parameters and observed phenomena. The same shot may be discussed in multiple papers, each providing different insights.
        </Typography>

        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mt: 2 }}>
          Parameters
        </Typography>
        <Typography variant="body1" paragraph>
          Quantitative plasma measurements extracted from papers include:
        </Typography>
        <Box component="ul" sx={{ pl: 3, mb: 2 }}>
          <Typography component="li" variant="body1">
            <strong>Plasma Parameters:</strong> Ion temperature (Ti), electron temperature (Te), density (ne), pressure, beta values
          </Typography>
          <Typography component="li" variant="body1">
            <strong>Operational Parameters:</strong> Plasma current (Ip), magnetic field (Bt), heating power (NBI, RF)
          </Typography>
          <Typography component="li" variant="body1">
            <strong>Performance Metrics:</strong> H-factor, confinement time (τE), stored energy
          </Typography>
        </Box>

        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mt: 2 }}>
          Phenomena
        </Typography>
        <Typography variant="body1" paragraph>
          Observed physics categorized into types:
        </Typography>
        <Box component="ul" sx={{ pl: 3, mb: 2 }}>
          <Typography component="li" variant="body1">
            <strong>Instabilities:</strong> Edge-localized modes (ELMs), kink modes, tearing modes, Alfvén eigenmodes
          </Typography>
          <Typography component="li" variant="body1">
            <strong>Confinement:</strong> High-confinement mode (H-mode), low-confinement mode (L-mode), transport barriers
          </Typography>
          <Typography component="li" variant="body1">
            <strong>Disruptions:</strong> Vertical displacement events (VDEs), runaway electrons, thermal quench
          </Typography>
          <Typography component="li" variant="body1">
            <strong>Divertor:</strong> Detachment, snowflake configurations, lithium conditioning
          </Typography>
        </Box>
      </Paper>

      {/* Data Processing Pipeline */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, color: 'secondary.main' }}>
          Data Processing Pipeline
        </Typography>
        <Typography variant="body1" paragraph>
          NSTXView processes papers through a multi-stage pipeline:
        </Typography>
        <Box component="ol" sx={{ pl: 3, mb: 2 }}>
          <Typography component="li" variant="body1" paragraph>
            <strong>PDF Ingestion:</strong> Papers are ingested from the source folder, and text is extracted preserving structure (sections, tables, figure captions).
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Metadata Extraction:</strong> Artificial intelligence (AI) extracts paper metadata including title, authors, journal, digital object identifier (DOI), publication year, and abstract.
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Shot Extraction:</strong> Shot numbers are identified with their role in the paper (primary focus, comparison, or reference) and associated context.
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Parameter Extraction:</strong> Quantitative values are extracted with units, uncertainties, and associated shot numbers where available.
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Phenomenon Extraction:</strong> Physics phenomena are identified and categorized, with flags for primary focus topics.
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Embedding Generation:</strong> Paper text is chunked and embedded for semantic search capabilities.
          </Typography>
        </Box>
      </Paper>

      {/* Text Chunking for RAG */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, color: 'secondary.main' }}>
          Text Chunking for Semantic Search
        </Typography>

        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mt: 2 }}>
          The Chunking Strategy
        </Typography>
        <Typography variant="body1" paragraph>
          Papers in NSTXView are broken into chunks (smaller text segments) to enable precise semantic search. Each paper is divided into approximately 500-word segments with 50-word overlap between consecutive chunks. This approach allows the system to retrieve specific relevant passages rather than entire papers when answering conceptual questions.
        </Typography>

        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mt: 2 }}>
          Two Chunking Methods
        </Typography>
        <Typography variant="body1" paragraph>
          <strong>Section-Aware Chunking (Preferred):</strong> When the PDF processor can identify section boundaries (Introduction, Methods, Results, Discussion, etc.), chunks respect these boundaries and are labeled with their section names. This preserves document structure and provides valuable context about where each passage originated.
        </Typography>
        <Typography variant="body1" paragraph>
          <strong>Simple Sliding Window (Fallback):</strong> When sections cannot be identified, the system uses a sliding window approach that moves through the text in 500-word increments with 50-word overlap. This ensures complete coverage while maintaining context across chunk boundaries.
        </Typography>
        <Typography variant="body1" paragraph>
          The 50-word overlap is crucial for preventing important context from being split awkwardly. For example, a sentence like "investigated disruption mitigation using lithium wall conditioning" won't be broken across chunks, ensuring coherent search results.
        </Typography>

        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mt: 2 }}>
          What Happens After Chunking
        </Typography>
        <Box component="ol" sx={{ pl: 3, mb: 2 }}>
          <Typography component="li" variant="body1" paragraph>
            <strong>Embedding Generation:</strong> Each chunk is converted to a 384-dimensional vector using the sentence-transformers model (all-MiniLM-L6-v2).
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Storage:</strong> Vectors are stored in ChromaDB for fast semantic search, while metadata (paper ID, chunk index, section name) is stored in PostgreSQL.
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Semantic Search:</strong> When you ask a conceptual question, the system converts your question to a vector, finds the 5 most similar chunk vectors in ChromaDB, and returns the actual text passages with proper citations.
          </Typography>
        </Box>

        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mt: 2 }}>
          Impact of This Approach
        </Typography>
        <Box component="ul" sx={{ pl: 3, mb: 2 }}>
          <Typography component="li" variant="body1">
            <strong>Precise retrieval:</strong> Returns specific relevant passages rather than entire papers, making answers more focused and useful.
          </Typography>
          <Typography component="li" variant="body1">
            <strong>Better relevance:</strong> 500-word chunks provide enough context to understand the passage without including irrelevant information.
          </Typography>
          <Typography component="li" variant="body1">
            <strong>Section context:</strong> Knowing whether a passage comes from Results, Methods, or Discussion helps interpret its significance.
          </Typography>
          <Typography component="li" variant="body1">
            <strong>Scalability:</strong> For 1,500 papers at approximately 20 chunks per paper, the system manages about 30,000 searchable chunks (approximately 150 MB of embeddings) with sub-second query performance.
          </Typography>
        </Box>

        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mt: 2 }}>
          Why 500 Words?
        </Typography>
        <Typography variant="body1" paragraph>
          The 500-word chunk size (approximately 2-3 paragraphs) represents an optimal balance based on research best practices. Smaller chunks (100-200 words) tend to lose important context and contain incomplete thoughts, while larger chunks (1,000+ words) include too much irrelevant information and reduce search precision. At 500 words, chunks typically contain complete ideas while remaining focused enough to provide relevant, targeted search results.
        </Typography>
      </Paper>

      {/* Features */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, color: 'secondary.main' }}>
          Features
        </Typography>

        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mt: 2 }}>
          Browse Papers
        </Typography>
        <Typography variant="body1" paragraph>
          Search and filter the paper collection by title, author, or keywords. View extracted metadata, processing status, and jump to detailed paper views showing all extracted shots, parameters, and phenomena.
        </Typography>

        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mt: 2 }}>
          Explore Shots
        </Typography>
        <Typography variant="body1" paragraph>
          Search for specific shot numbers and see all papers that discuss them. Filter by role (primary, comparison, reference) to find shots that were the main focus of analysis. View all parameters and phenomena associated with each shot across all papers.
        </Typography>

        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mt: 2 }}>
          Analyze Parameters
        </Typography>
        <Typography variant="body1" paragraph>
          Browse all extracted parameter types and see aggregate statistics (min, max, average, count). Click on any parameter to see values across all papers and shots, enabling comparison of reported values and identification of high-performing shots.
        </Typography>

        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mt: 2 }}>
          Phenomena Explorer
        </Typography>
        <Typography variant="body1" paragraph>
          Browse all observed phenomena by category. See which phenomena are most commonly studied and which papers focus on each type. Identify shots associated with specific phenomena.
        </Typography>

        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mt: 2 }}>
          Processing Status
        </Typography>
        <Typography variant="body1" paragraph>
          Monitor the data processing pipeline, view progress of paper extraction, and trigger sync/extraction operations. Track errors and processing logs.
        </Typography>
      </Paper>

      {/* AI Query System */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, color: 'secondary.main' }}>
          AI Query System: Hybrid MCP + RAG Architecture
        </Typography>
        <Typography variant="body1" paragraph>
          NSTXView's "Ask NSTXView" chat feature uses a hybrid approach that intelligently combines two complementary technologies to answer different types of research questions:
        </Typography>

        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mt: 3 }}>
          Model Context Protocol (MCP) for Structured Queries
        </Typography>
        <Typography variant="body1" paragraph>
          MCP provides structured database tools for quantitative and precise queries:
        </Typography>
        <Box component="ul" sx={{ pl: 3, mb: 2 }}>
          <Typography component="li" variant="body1">
            <strong>Specific shot lookups:</strong> "What happened in shot 141234?"
          </Typography>
          <Typography component="li" variant="body1">
            <strong>Parameter statistics:</strong> "What's the average ion temperature in H-mode?"
          </Typography>
          <Typography component="li" variant="body1">
            <strong>Quantitative queries:</strong> "Find papers with beta greater than 0.3"
          </Typography>
          <Typography component="li" variant="body1">
            <strong>Data extraction:</strong> Get exact values for shots, parameters, and phenomena
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary" paragraph>
          <strong>Available MCP tools:</strong> search_papers, query_shots, get_shot_details, get_parameter_statistics, list_parameters, list_phenomena, search_by_phenomenon, get_database_stats
        </Typography>

        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mt: 3 }}>
          Retrieval Augmented Generation (RAG) for Semantic Search
        </Typography>
        <Typography variant="body1" paragraph>
          RAG uses semantic search to find relevant passages for conceptual questions:
        </Typography>
        <Box component="ul" sx={{ pl: 3, mb: 2 }}>
          <Typography component="li" variant="body1">
            <strong>Conceptual explanations:</strong> "Explain how high-confinement mode (H-mode) transitions occur"
          </Typography>
          <Typography component="li" variant="body1">
            <strong>Finding relevant passages:</strong> "What do papers say about lithium coating effects?"
          </Typography>
          <Typography component="li" variant="body1">
            <strong>Cross-paper synthesis:</strong> "What are common edge-localized mode (ELM) mitigation techniques?"
          </Typography>
          <Typography component="li" variant="body1">
            <strong>Method comparisons:</strong> "Different approaches to disruption prediction"
          </Typography>
          <Typography component="li" variant="body1">
            <strong>Open-ended exploration:</strong> "What factors affect plasma confinement time?"
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary" paragraph>
          <strong>Technical details:</strong> Uses ChromaDB vector store with sentence-transformers embeddings (all-MiniLM-L6-v2 model, 384 dimensions). Papers are chunked into ~500-word segments with 50-word overlap, preserving section context when possible.
        </Typography>

        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mt: 3 }}>
          Intelligent Query Routing
        </Typography>
        <Typography variant="body1" paragraph>
          Claude Sonnet 3.5 intelligently routes your questions to the appropriate system based on query type. For complex questions that combine concepts and quantitative data, Claude uses both systems together to provide comprehensive answers with proper citations.
        </Typography>
        <Typography variant="body1" paragraph>
          The MCP server can also be used alongside CollisionDB MCP to cross-reference paper findings with atomic collision data, enabling comprehensive plasma physics research queries.
        </Typography>
      </Paper>
    </Box>
  );
}
