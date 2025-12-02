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
  Divider,
  Grid2 as Grid,
  IconButton,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  CompareArrows as CompareIcon,
  Add as AddIcon,
  Remove as RemoveIcon,
  Download as DownloadIcon,
  OpenInNew as OpenInNewIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import api from '../../services/api';
import { formatMarkdown } from './utils/formatMarkdown';
import { formatDateEST } from '../../utils/dateUtils';

interface DrugComparisonData {
  drug_name: string;
  brand_name: string | null;
  generic_name: string | null;
  manufacturer: string | null;
  fda_label_date: string | null;
  indications_summary: string | null;
  key_warnings: string | null;
  common_side_effects: string | null;
  dailymed_url: string | null;
}

interface CompareResponse {
  drugs: DrugComparisonData[];
  comparison_table: string;
  comparison_paragraphs: string;
  disclaimer: string;
}

const CanonCompare: React.FC = () => {
  const [drugNames, setDrugNames] = useState<string[]>(['', '']);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CompareResponse | null>(null);

  const handleDrugNameChange = (index: number, value: string) => {
    const newDrugNames = [...drugNames];
    newDrugNames[index] = value;
    setDrugNames(newDrugNames);
  };

  const addDrugField = () => {
    if (drugNames.length < 4) {
      setDrugNames([...drugNames, '']);
    }
  };

  const removeDrugField = (index: number) => {
    if (drugNames.length > 2) {
      const newDrugNames = drugNames.filter((_, i) => i !== index);
      setDrugNames(newDrugNames);
    }
  };

  const handleCompare = async () => {
    const validDrugNames = drugNames.filter(name => name.trim());

    if (validDrugNames.length < 2) {
      setError('Please enter at least 2 drug names to compare');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await api.post<CompareResponse>('/canon/compare', {
        drug_names: validDrugNames,
      });
      setResult(response.data);
    } catch (err: any) {
      console.error('Compare error:', err);
      if (err.response?.status === 503) {
        setError('The AI service is temporarily unavailable. Please try again later.');
      } else if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('An error occurred while comparing drugs. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleCompare();
    }
  };

  const downloadAsWord = () => {
    if (!result) return;

    // Build document content
    let content = `Drug Comparison Report\n${'='.repeat(50)}\n\n`;
    content += `Generated: ${formatDateEST(new Date(), 'long')}\n\n`;
    content += `Drugs Compared: ${result.drugs.map(d => d.brand_name || d.drug_name).join(', ')}\n\n`;

    // Add drug details
    content += `DRUG DETAILS\n${'-'.repeat(30)}\n\n`;
    for (const drug of result.drugs) {
      content += `${drug.brand_name || drug.drug_name}\n`;
      if (drug.generic_name) content += `Generic Name: ${drug.generic_name}\n`;
      if (drug.manufacturer) content += `Manufacturer: ${drug.manufacturer}\n`;
      if (drug.fda_label_date) content += `FDA Label Date: ${drug.fda_label_date}\n`;
      if (drug.dailymed_url) content += `DailyMed: ${drug.dailymed_url}\n`;
      content += '\n';
    }

    // Add comparison analysis
    content += `\nCOMPARISON ANALYSIS\n${'-'.repeat(30)}\n\n`;
    content += result.comparison_paragraphs.replace(/\*\*/g, '').replace(/\*/g, '') + '\n\n';

    // Add disclaimer
    content += `\nDISCLAIMER\n${'-'.repeat(30)}\n`;
    content += result.disclaimer + '\n';

    // Create blob and download
    const blob = new Blob([content], { type: 'application/msword' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Drug_Comparison_${result.drugs.map(d => d.brand_name || d.drug_name).join('_vs_')}.doc`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const exampleComparisons = [
    ['Ozempic', 'Wegovy'],
    ['Lipitor', 'Crestor'],
    ['Humira', 'Enbrel'],
  ];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <CompareIcon sx={{ mr: 2, fontSize: 32, color: 'info.main' }} />
        <Box>
          <Typography variant="h4" component="h1">
            Compare Drugs
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Compare FDA-approved labeling for 2-4 drugs side-by-side
          </Typography>
        </Box>
      </Box>

      {/* Drug Input Form */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="subtitle2" gutterBottom>
          Enter drug names to compare (2-4 drugs)
        </Typography>

        <Grid container spacing={2} sx={{ mb: 2 }}>
          {drugNames.map((name, index) => (
            <Grid size={{ xs: 12, sm: 6, md: 3 }} key={index}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <TextField
                  fullWidth
                  size="small"
                  label={`Drug ${index + 1}`}
                  placeholder="e.g., Ozempic"
                  value={name}
                  onChange={(e) => handleDrugNameChange(index, e.target.value)}
                  onKeyPress={handleKeyPress}
                  disabled={loading}
                />
                {drugNames.length > 2 && (
                  <IconButton
                    size="small"
                    onClick={() => removeDrugField(index)}
                    color="error"
                    disabled={loading}
                  >
                    <RemoveIcon />
                  </IconButton>
                )}
              </Box>
            </Grid>
          ))}
        </Grid>

        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
          {drugNames.length < 4 && (
            <Button
              variant="outlined"
              size="small"
              startIcon={<AddIcon />}
              onClick={addDrugField}
              disabled={loading}
            >
              Add Drug
            </Button>
          )}

          <Button
            variant="contained"
            onClick={handleCompare}
            disabled={loading || drugNames.filter(n => n.trim()).length < 2}
            startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <CompareIcon />}
          >
            {loading ? 'Comparing...' : 'Compare'}
          </Button>
        </Box>

        {/* Example Comparisons */}
        <Box sx={{ mt: 2 }}>
          <Typography variant="caption" color="text.secondary" sx={{ mr: 1 }}>
            Try comparing:
          </Typography>
          {exampleComparisons.map((pair, index) => (
            <Chip
              key={index}
              label={`${pair[0]} vs ${pair[1]}`}
              size="small"
              onClick={() => setDrugNames([pair[0], pair[1]])}
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
      {result && (
        <>
          {/* Download Button */}
          <Box sx={{ mb: 2, display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={downloadAsWord}
            >
              Download as Word
            </Button>
          </Box>

          {/* Drug Overview Cards */}
          <Grid container spacing={2} sx={{ mb: 4 }}>
            {result.drugs.map((drug, index) => (
              <Grid size={{ xs: 12, sm: 6, md: 3 }} key={index}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {drug.brand_name || drug.drug_name}
                    </Typography>
                    {drug.generic_name && (
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        {drug.generic_name}
                      </Typography>
                    )}
                    {drug.manufacturer && (
                      <Typography variant="caption" display="block" color="text.secondary">
                        {drug.manufacturer}
                      </Typography>
                    )}
                    {drug.fda_label_date && (
                      <Typography variant="caption" display="block" color="text.secondary">
                        Label Date: {drug.fda_label_date}
                      </Typography>
                    )}
                    {drug.dailymed_url && (
                      <Button
                        size="small"
                        href={drug.dailymed_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        endIcon={<OpenInNewIcon fontSize="small" />}
                        sx={{ mt: 1, p: 0 }}
                      >
                        View on DailyMed
                      </Button>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>

          {/* Comparison Table */}
          <Card sx={{ mb: 4 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Comparison Table
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>Drug</strong></TableCell>
                      <TableCell><strong>Indications</strong></TableCell>
                      <TableCell><strong>Key Warnings</strong></TableCell>
                      <TableCell><strong>Common Side Effects</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {result.drugs.map((drug, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <strong>{drug.brand_name || drug.drug_name}</strong>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {drug.indications_summary || 'See full label'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {drug.key_warnings || 'See full label'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {drug.common_side_effects || 'See full label'}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>

          {/* Comparison Analysis */}
          <Card sx={{ mb: 4 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Detailed Comparison
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Box sx={{
                whiteSpace: 'pre-wrap',
                '& strong': { fontWeight: 600 },
                '& em': { fontStyle: 'italic' },
              }}>
                <Typography variant="body1" component="div">
                  {formatMarkdown(result.comparison_paragraphs)}
                </Typography>
              </Box>
            </CardContent>
          </Card>

          {/* Disclaimer */}
          <Alert severity="info" icon={<InfoIcon />}>
            <Typography variant="caption">
              {result.disclaimer}
            </Typography>
          </Alert>
        </>
      )}

      {/* How It Works - shown when no results */}
      {!result && !loading && (
        <Paper sx={{ p: 3, bgcolor: 'grey.50' }}>
          <Typography variant="h6" gutterBottom>
            How It Works
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Canon's Compare Drugs feature helps you understand the differences between medications:
          </Typography>
          <Box component="ol" sx={{ pl: 2, '& li': { mb: 1 } }}>
            <Typography component="li" variant="body2" color="text.secondary">
              <strong>Enter 2-4 drug names</strong> you want to compare
            </Typography>
            <Typography component="li" variant="body2" color="text.secondary">
              <strong>We fetch official FDA label data</strong> for each drug
            </Typography>
            <Typography component="li" variant="body2" color="text.secondary">
              <strong>AI analyzes and compares</strong> indications, warnings, and side effects
            </Typography>
            <Typography component="li" variant="body2" color="text.secondary">
              <strong>Download the comparison</strong> as a Word document for reference
            </Typography>
          </Box>
        </Paper>
      )}
    </Container>
  );
};

export default CanonCompare;
