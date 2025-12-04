import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
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
          NSTXView is a research analysis platform for scholarly papers about plasma physics experiments conducted on NSTX (National Spherical Torus Experiment) and NSTX-U (Upgrade) at Princeton Plasma Physics Laboratory. It extracts structured information from hundreds of research papers to help scientists understand what characteristics make plasma "shots" scientifically interesting.
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
            <strong>Instabilities:</strong> ELMs, kink modes, tearing modes, Alfvén eigenmodes
          </Typography>
          <Typography component="li" variant="body1">
            <strong>Confinement:</strong> H-mode, L-mode, transport barriers
          </Typography>
          <Typography component="li" variant="body1">
            <strong>Disruptions:</strong> VDEs, runaway electrons, thermal quench
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
            <strong>Metadata Extraction:</strong> AI extracts paper metadata including title, authors, journal, DOI, publication year, and abstract.
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

      {/* Typical Parameter Ranges */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, color: 'secondary.main' }}>
          Typical NSTX-U Parameter Ranges
        </Typography>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 600 }}>Parameter</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Symbol</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Typical Range</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Unit</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow>
                <TableCell>Ion Temperature</TableCell>
                <TableCell>Ti</TableCell>
                <TableCell>0.5 - 5</TableCell>
                <TableCell>keV</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Electron Temperature</TableCell>
                <TableCell>Te</TableCell>
                <TableCell>0.5 - 3</TableCell>
                <TableCell>keV</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Electron Density</TableCell>
                <TableCell>ne</TableCell>
                <TableCell>1 - 10 × 10¹⁹</TableCell>
                <TableCell>m⁻³</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Plasma Current</TableCell>
                <TableCell>Ip</TableCell>
                <TableCell>0.3 - 1.5</TableCell>
                <TableCell>MA</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Toroidal Field</TableCell>
                <TableCell>Bt</TableCell>
                <TableCell>0.3 - 0.55</TableCell>
                <TableCell>T</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>NBI Power</TableCell>
                <TableCell>PNBI</TableCell>
                <TableCell>2 - 7</TableCell>
                <TableCell>MW</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Normalized Beta</TableCell>
                <TableCell>βN</TableCell>
                <TableCell>3 - 6</TableCell>
                <TableCell>-</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Energy Confinement Time</TableCell>
                <TableCell>τE</TableCell>
                <TableCell>20 - 100</TableCell>
                <TableCell>ms</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
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
          MCP (Model Context Protocol) for Structured Queries
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
          RAG (Retrieval Augmented Generation) for Semantic Search
        </Typography>
        <Typography variant="body1" paragraph>
          RAG uses semantic search to find relevant passages for conceptual questions:
        </Typography>
        <Box component="ul" sx={{ pl: 3, mb: 2 }}>
          <Typography component="li" variant="body1">
            <strong>Conceptual explanations:</strong> "Explain how H-mode transitions occur"
          </Typography>
          <Typography component="li" variant="body1">
            <strong>Finding relevant passages:</strong> "What do papers say about lithium coating effects?"
          </Typography>
          <Typography component="li" variant="body1">
            <strong>Cross-paper synthesis:</strong> "What are common ELM mitigation techniques?"
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

      {/* About NSTX-U */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, color: 'secondary.main' }}>
          About NSTX-U
        </Typography>
        <Typography variant="body1" paragraph>
          NSTX and NSTX-U are spherical tokamaks—fusion devices with a compact, spherical shape (aspect ratio ~1.3) compared to conventional tokamaks. This geometry offers potential advantages for future fusion power plants including higher plasma pressure (beta) limits, better confinement at high beta, more compact design, and natural divertor solutions.
        </Typography>
        <Typography variant="body1" paragraph>
          Key NSTX-U specifications:
        </Typography>
        <Box component="ul" sx={{ pl: 3, mb: 2 }}>
          <Typography component="li" variant="body1">Major radius: 0.93 m</Typography>
          <Typography component="li" variant="body1">Minor radius: 0.6 m</Typography>
          <Typography component="li" variant="body1">Aspect ratio: 1.55</Typography>
          <Typography component="li" variant="body1">Toroidal field: up to 1 T</Typography>
          <Typography component="li" variant="body1">Plasma current: up to 2 MA</Typography>
          <Typography component="li" variant="body1">NBI power: up to 10 MW</Typography>
          <Typography component="li" variant="body1">RF power: up to 6 MW</Typography>
        </Box>
      </Paper>
    </Box>
  );
}
