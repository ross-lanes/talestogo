import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  TextField,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
  Grid2 as Grid,
  InputAdornment,
  ToggleButton,
  ToggleButtonGroup,
} from '@mui/material';
import {
  Search as SearchIcon,
  ExpandMore as ExpandMoreIcon,
  Warning as WarningIcon,
  LocalHospital as DrugIcon,
  Info as InfoIcon,
  OpenInNew as OpenInNewIcon,
} from '@mui/icons-material';
import { formatMarkdown } from './utils/formatMarkdown';

// OpenFDA API base URL
const OPENFDA_BASE_URL = 'https://api.fda.gov';

// Types
interface DrugLabel {
  brand_name: string | null;
  generic_name: string | null;
  manufacturer: string | null;
  effective_time: string | null;
  version: string | null;
  set_id: string | null;
  spl_id: string | null;
  indications_and_usage?: string[];
  warnings?: string[];
  adverse_reactions?: string[];
  dosage_and_administration?: string[];
  boxed_warning?: string[];
  contraindications?: string[];
  drug_interactions?: string[];
}

// Helper to format FDA date (YYYYMMDD) to readable format
const formatFDADate = (dateStr: string | null): string | null => {
  if (!dateStr || dateStr.length !== 8) return dateStr;
  const year = dateStr.substring(0, 4);
  const month = dateStr.substring(4, 6);
  const day = dateStr.substring(6, 8);
  const date = new Date(`${year}-${month}-${day}`);
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
};

interface AdverseEventCount {
  term: string;
  count: number;
}

interface SearchResult {
  type: 'label' | 'adverse_events';
  label?: DrugLabel;
  adverseEvents?: {
    total: number;
    topReactions: AdverseEventCount[];
  };
}

const CanonLookup: React.FC = () => {
  const [query, setQuery] = useState('');
  const [searchType, setSearchType] = useState<'label' | 'adverse_events'>('label');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SearchResult | null>(null);

  const handleSearch = async () => {
    if (!query.trim()) {
      setError('Please enter a drug name to search');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      if (searchType === 'label') {
        await searchDrugLabel(query.trim());
      } else {
        await searchAdverseEvents(query.trim());
      }
    } catch (err: any) {
      console.error('Search error:', err);
      setError(err.message || 'An error occurred while searching. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const searchDrugLabel = async (drugName: string) => {
    const searchQuery = encodeURIComponent(`openfda.brand_name:"${drugName}" OR openfda.generic_name:"${drugName}"`);
    const url = `${OPENFDA_BASE_URL}/drug/label.json?search=${searchQuery}&limit=1`;

    const response = await fetch(url);

    if (response.status === 404) {
      setError(`No FDA label found for "${drugName}". Try a different spelling or drug name.`);
      return;
    }

    if (!response.ok) {
      throw new Error('Failed to fetch drug label');
    }

    const data = await response.json();

    if (!data.results || data.results.length === 0) {
      setError(`No FDA label found for "${drugName}". Try a different spelling or drug name.`);
      return;
    }

    const labelData = data.results[0];
    const openfda = labelData.openfda || {};

    const label: DrugLabel = {
      brand_name: openfda.brand_name?.[0] || null,
      generic_name: openfda.generic_name?.[0] || null,
      manufacturer: openfda.manufacturer_name?.[0] || null,
      effective_time: labelData.effective_time || null,
      version: labelData.version || null,
      set_id: labelData.set_id || null,
      spl_id: openfda.spl_id?.[0] || labelData.id || null,
      indications_and_usage: labelData.indications_and_usage,
      warnings: labelData.warnings,
      adverse_reactions: labelData.adverse_reactions,
      dosage_and_administration: labelData.dosage_and_administration,
      boxed_warning: labelData.boxed_warning,
      contraindications: labelData.contraindications,
      drug_interactions: labelData.drug_interactions,
    };

    setResult({ type: 'label', label });
  };

  const searchAdverseEvents = async (drugName: string) => {
    const searchQuery = encodeURIComponent(`patient.drug.medicinalproduct:"${drugName}"`);
    const url = `${OPENFDA_BASE_URL}/drug/event.json?search=${searchQuery}&count=patient.reaction.reactionmeddrapt.exact&limit=20`;

    const response = await fetch(url);

    if (response.status === 404) {
      setError(`No adverse events found for "${drugName}". Try a different spelling or drug name.`);
      return;
    }

    if (!response.ok) {
      throw new Error('Failed to fetch adverse events');
    }

    const data = await response.json();

    if (!data.results || data.results.length === 0) {
      setError(`No adverse events found for "${drugName}".`);
      return;
    }

    const topReactions: AdverseEventCount[] = data.results.map((r: any) => ({
      term: r.term,
      count: r.count,
    }));

    const total = topReactions.reduce((sum, r) => sum + r.count, 0);

    setResult({
      type: 'adverse_events',
      adverseEvents: { total, topReactions },
    });
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const exampleQueries = [
    'Galafold',
    'Posluma',
    'Salonpas',
    'Ozempic',
  ];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Look Up
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Search FDA drug labels and adverse event reports
        </Typography>
      </Box>

      {/* Search Box */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Box sx={{ mb: 2 }}>
          <ToggleButtonGroup
            value={searchType}
            exclusive
            onChange={(_, value) => value && setSearchType(value)}
            size="small"
          >
            <ToggleButton value="label">
              <DrugIcon sx={{ mr: 1 }} />
              Drug Label
            </ToggleButton>
            <ToggleButton value="adverse_events">
              <WarningIcon sx={{ mr: 1 }} />
              Adverse Events
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>

        <Box sx={{ display: 'flex', gap: 2 }}>
          <TextField
            fullWidth
            placeholder={searchType === 'label'
              ? "Enter a drug name (e.g., Lipitor, Ozempic, Humira)"
              : "Enter a drug name to see reported adverse events"
            }
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon color="action" />
                </InputAdornment>
              ),
            }}
          />
          <Button
            variant="contained"
            onClick={handleSearch}
            disabled={loading}
            sx={{ minWidth: 120 }}
          >
            {loading ? <CircularProgress size={24} color="inherit" /> : 'Search'}
          </Button>
        </Box>

        {/* Example Queries */}
        <Box sx={{ mt: 2 }}>
          <Typography variant="caption" color="text.secondary" sx={{ mr: 1 }}>
            Try:
          </Typography>
          {exampleQueries.map((example) => (
            <Chip
              key={example}
              label={example}
              size="small"
              onClick={() => setQuery(example)}
              sx={{ mr: 0.5, mb: 0.5, cursor: 'pointer' }}
              variant="outlined"
            />
          ))}
        </Box>
      </Paper>

      {/* Error Message */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Results */}
      {result && result.type === 'label' && result.label && (
        <LabelResults label={result.label} />
      )}

      {result && result.type === 'adverse_events' && result.adverseEvents && (
        <AdverseEventsResults
          drugName={query}
          data={result.adverseEvents}
        />
      )}

      {/* Disclaimer */}
      <Paper sx={{ p: 2, mt: 4, bgcolor: 'grey.50' }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start' }}>
          <InfoIcon sx={{ mr: 1, color: 'info.main', fontSize: 20 }} />
          <Typography variant="caption" color="text.secondary">
            <strong>Disclaimer:</strong> This data is sourced from the FDA's openFDA API.
            It is intended for informational purposes only and should not be used as a substitute
            for professional medical advice, diagnosis, or treatment. The information may not be
            complete or up-to-date. Always consult with a qualified healthcare provider.
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
};

// Label Results Component
const LabelResults: React.FC<{ label: DrugLabel }> = ({ label }) => {
  // Build DailyMed URL using set_id if available
  const dailyMedUrl = label.set_id
    ? `https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=${label.set_id}`
    : null;

  return (
    <Card>
      <CardContent>
        {/* Drug Header */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h5" gutterBottom>
            {label.brand_name || label.generic_name || 'Unknown Drug'}
          </Typography>
          {label.generic_name && label.brand_name && (
            <Typography variant="subtitle1" color="text.secondary">
              Generic: {label.generic_name}
            </Typography>
          )}
          {label.manufacturer && (
            <Typography variant="body2" color="text.secondary">
              Manufacturer: {label.manufacturer}
            </Typography>
          )}

          {/* Document Metadata */}
          <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
            <Grid container spacing={2}>
              {label.effective_time && (
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Typography variant="caption" color="text.secondary" display="block">
                    Label Effective Date
                  </Typography>
                  <Typography variant="body2" fontWeight={500}>
                    {formatFDADate(label.effective_time)}
                  </Typography>
                </Grid>
              )}
              {label.version && (
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Typography variant="caption" color="text.secondary" display="block">
                    Version
                  </Typography>
                  <Typography variant="body2" fontWeight={500}>
                    {label.version}
                  </Typography>
                </Grid>
              )}
              {label.set_id && (
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Typography variant="caption" color="text.secondary" display="block">
                    Set ID
                  </Typography>
                  <Typography variant="body2" fontWeight={500} sx={{
                    fontFamily: 'monospace',
                    fontSize: '0.75rem',
                    wordBreak: 'break-all'
                  }}>
                    {label.set_id}
                  </Typography>
                </Grid>
              )}
              {dailyMedUrl && (
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Typography variant="caption" color="text.secondary" display="block">
                    Full Document
                  </Typography>
                  <Button
                    variant="outlined"
                    size="small"
                    href={dailyMedUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    endIcon={<OpenInNewIcon />}
                    sx={{ mt: 0.5 }}
                  >
                    View on DailyMed
                  </Button>
                </Grid>
              )}
            </Grid>
          </Box>
        </Box>

        <Divider sx={{ mb: 2 }} />

        {/* Boxed Warning */}
        {label.boxed_warning && label.boxed_warning.length > 0 && (
          <Alert severity="error" sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              <strong>BOXED WARNING</strong>
            </Typography>
            <Box sx={{ whiteSpace: 'pre-wrap', '& strong': { fontWeight: 600 }, '& em': { fontStyle: 'italic' } }}>
              <Typography variant="body2" component="div">
                {formatMarkdown(truncateText(label.boxed_warning.join('\n\n'), 1000))}
              </Typography>
            </Box>
          </Alert>
        )}

        {/* Label Sections */}
        <LabelSection
          title="Indications and Usage"
          content={label.indications_and_usage}
          defaultExpanded
        />
        <LabelSection
          title="Warnings"
          content={label.warnings}
        />
        <LabelSection
          title="Adverse Reactions"
          content={label.adverse_reactions}
        />
        <LabelSection
          title="Dosage and Administration"
          content={label.dosage_and_administration}
        />
        <LabelSection
          title="Contraindications"
          content={label.contraindications}
        />
        <LabelSection
          title="Drug Interactions"
          content={label.drug_interactions}
        />
      </CardContent>
    </Card>
  );
};

// Label Section Accordion
const LabelSection: React.FC<{
  title: string;
  content?: string[];
  defaultExpanded?: boolean;
}> = ({ title, content, defaultExpanded = false }) => {
  if (!content || content.length === 0) {
    return null;
  }

  return (
    <Accordion defaultExpanded={defaultExpanded}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Typography variant="subtitle1" fontWeight={500}>
          {title}
        </Typography>
      </AccordionSummary>
      <AccordionDetails>
        <Box sx={{ whiteSpace: 'pre-wrap', '& strong': { fontWeight: 600 }, '& em': { fontStyle: 'italic' } }}>
          <Typography variant="body2" component="div">
            {formatMarkdown(truncateText(content.join('\n\n'), 3000))}
          </Typography>
        </Box>
      </AccordionDetails>
    </Accordion>
  );
};

// Adverse Events Results Component
const AdverseEventsResults: React.FC<{
  drugName: string;
  data: { total: number; topReactions: AdverseEventCount[] };
}> = ({ drugName, data }) => {
  const maxCount = data.topReactions[0]?.count || 1;

  return (
    <Card>
      <CardContent>
        <Box sx={{ mb: 3 }}>
          <Typography variant="h5" gutterBottom>
            Adverse Events for {drugName}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Top 20 reported adverse reactions from FDA adverse event reports
          </Typography>
        </Box>

        <Divider sx={{ mb: 3 }} />

        <Grid container spacing={2}>
          {data.topReactions.map((reaction, index) => (
            <Grid size={{ xs: 12, sm: 6 }} key={reaction.term}>
              <Box sx={{ mb: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                  <Typography variant="body2" fontWeight={500}>
                    {index + 1}. {reaction.term}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {reaction.count.toLocaleString()} reports
                  </Typography>
                </Box>
                <Box
                  sx={{
                    height: 8,
                    bgcolor: 'grey.200',
                    borderRadius: 1,
                    overflow: 'hidden',
                  }}
                >
                  <Box
                    sx={{
                      height: '100%',
                      width: `${(reaction.count / maxCount) * 100}%`,
                      bgcolor: index < 5 ? 'error.main' : 'warning.main',
                      borderRadius: 1,
                    }}
                  />
                </Box>
              </Box>
            </Grid>
          ))}
        </Grid>

        <Alert severity="info" sx={{ mt: 3 }}>
          <Typography variant="body2">
            These counts represent the number of adverse event reports submitted to the FDA
            where this reaction was mentioned. A report does not prove the drug caused the reaction.
          </Typography>
        </Alert>
      </CardContent>
    </Card>
  );
};

// Helper function to truncate long text
const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '... [truncated]';
};

export default CanonLookup;
