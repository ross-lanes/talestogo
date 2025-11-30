import React, { useState, useRef } from 'react';
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
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Collapse,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid2 as Grid,
} from '@mui/material';
import {
  Description as DescriptionIcon,
  CloudUpload as UploadIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  OpenInNew as OpenInNewIcon,
  CalendarToday as CalendarIcon,
  School as SchoolIcon,
  Tune as TuneIcon,
  AutoFixHigh as AutoFixIcon,
} from '@mui/icons-material';
import api from '../../services/api';
import { formatMarkdown } from './utils/formatMarkdown';

interface DocumentIssue {
  category: string;
  severity: string;
  text_excerpt: string;
  issue_description: string;
  fda_reference: string;
}

interface DocumentCheckResponse {
  drug_name: string;
  fda_label_date: string | null;
  fda_set_id: string | null;
  dailymed_url: string | null;
  document_text_preview: string;
  document_full_text: string;
  issues: DocumentIssue[];
  summary: string;
  reading_level: string;
  reading_level_description: string;
  disclaimer: string;
}

interface AdjustDocumentResponse {
  adjusted_text: string;
  reading_level: string;
  tone: string;
  changes_summary: string;
}

const READING_LEVELS = [
  { value: '5th Grade', label: '5th Grade', description: 'Very simple language, short sentences' },
  { value: '8th Grade', label: '8th Grade', description: 'Moderate complexity, general public' },
  { value: 'High School', label: 'High School', description: 'Some technical terms explained' },
  { value: 'College', label: 'College', description: 'Academic language, technical terms' },
  { value: 'Professional', label: 'Professional', description: 'Medical/scientific terminology' },
];

const TONES = [
  { value: 'Professional', label: 'Professional', description: 'Formal, objective, clinical' },
  { value: 'Friendly', label: 'Friendly', description: 'Warm, approachable, conversational' },
  { value: 'Empathetic', label: 'Empathetic', description: 'Understanding, supportive' },
  { value: 'Direct', label: 'Direct', description: 'Clear, concise, to the point' },
  { value: 'Educational', label: 'Educational', description: 'Informative, explanatory' },
  { value: 'Reassuring', label: 'Reassuring', description: 'Calming, addresses concerns' },
];

const CanonDocuments: React.FC = () => {
  const [drugName, setDrugName] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [adjusting, setAdjusting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<DocumentCheckResponse | null>(null);
  const [adjustedResponse, setAdjustedResponse] = useState<AdjustDocumentResponse | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [showAdjusted, setShowAdjusted] = useState(false);
  const [targetReadingLevel, setTargetReadingLevel] = useState('');
  const [targetTone, setTargetTone] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      if (!selectedFile.name.toLowerCase().endsWith('.docx')) {
        setError('Please select a Word document (.docx file)');
        return;
      }
      setFile(selectedFile);
      setError(null);
      setResponse(null);
      setAdjustedResponse(null);
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const droppedFile = event.dataTransfer.files[0];
    if (droppedFile) {
      if (!droppedFile.name.toLowerCase().endsWith('.docx')) {
        setError('Please select a Word document (.docx file)');
        return;
      }
      setFile(droppedFile);
      setError(null);
      setResponse(null);
      setAdjustedResponse(null);
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  };

  const handleCheck = async () => {
    if (!file) {
      setError('Please select a document to check');
      return;
    }
    if (!drugName.trim()) {
      setError('Please enter the drug name');
      return;
    }

    setLoading(true);
    setError(null);
    setResponse(null);
    setAdjustedResponse(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('drug_name', drugName.trim());

      const result = await api.post<DocumentCheckResponse>('/canon/check-document', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setResponse(result.data);
    } catch (err: any) {
      console.error('Document check error:', err);
      if (err.response?.status === 404) {
        setError(`No FDA label found for "${drugName}". Please check the drug name spelling.`);
      } else if (err.response?.status === 503) {
        setError('The AI service is temporarily unavailable. Please try again later.');
      } else if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('An error occurred while checking the document. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleAdjust = async () => {
    if (!response) return;
    if (!targetReadingLevel && !targetTone) {
      setError('Please select a reading level or tone to adjust to');
      return;
    }

    setAdjusting(true);
    setError(null);

    try {
      const result = await api.post<AdjustDocumentResponse>('/canon/adjust-document', {
        document_text: response.document_full_text,
        drug_name: response.drug_name,
        target_reading_level: targetReadingLevel || null,
        target_tone: targetTone || null,
      });
      setAdjustedResponse(result.data);
      setShowAdjusted(true);
    } catch (err: any) {
      console.error('Document adjust error:', err);
      if (err.response?.status === 503) {
        setError('The AI service is temporarily unavailable. Please try again later.');
      } else if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('An error occurred while adjusting the document. Please try again.');
      }
    } finally {
      setAdjusting(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      case 'low':
        return 'info';
      default:
        return 'default';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'high':
        return <ErrorIcon color="error" />;
      case 'medium':
        return <WarningIcon color="warning" />;
      case 'low':
        return <InfoIcon color="info" />;
      default:
        return <InfoIcon />;
    }
  };

  const getCategoryLabel = (category: string) => {
    switch (category) {
      case 'accuracy':
        return 'Accuracy Issue';
      case 'outdated':
        return 'Potentially Outdated';
      case 'missing':
        return 'Missing Information';
      case 'warning':
        return 'Safety Warning';
      default:
        return category;
    }
  };

  const getReadingLevelColor = (level: string) => {
    switch (level) {
      case '5th Grade':
        return 'success';
      case '8th Grade':
        return 'info';
      case 'High School':
        return 'primary';
      case 'College':
        return 'warning';
      case 'Professional':
        return 'error';
      default:
        return 'default';
    }
  };

  const exampleDrugs = ['Ozempic', 'Humira', 'Lipitor', 'Galafold'];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Check a Document
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Upload a Word document and verify its claims against official FDA drug label data.
        </Typography>
      </Box>

      {/* Upload Section */}
      <Paper sx={{ p: 3, mb: 4 }}>
        {/* Drug Name Input */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Drug Name
          </Typography>
          <TextField
            fullWidth
            placeholder="Enter the drug name (e.g., Ozempic, Humira)"
            value={drugName}
            onChange={(e) => setDrugName(e.target.value)}
            disabled={loading}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <DescriptionIcon color="action" />
                </InputAdornment>
              ),
            }}
          />
          <Box sx={{ mt: 1 }}>
            <Typography variant="caption" color="text.secondary" sx={{ mr: 1 }}>
              Examples:
            </Typography>
            {exampleDrugs.map((drug) => (
              <Chip
                key={drug}
                label={drug}
                size="small"
                onClick={() => setDrugName(drug)}
                sx={{ mr: 0.5, cursor: 'pointer' }}
                variant="outlined"
              />
            ))}
          </Box>
        </Box>

        {/* File Upload Area */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Document
          </Typography>
          <Box
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onClick={() => fileInputRef.current?.click()}
            sx={{
              border: '2px dashed',
              borderColor: file ? 'success.main' : 'grey.300',
              borderRadius: 2,
              p: 4,
              textAlign: 'center',
              cursor: 'pointer',
              bgcolor: file ? 'success.50' : 'grey.50',
              transition: 'all 0.2s',
              '&:hover': {
                borderColor: 'primary.main',
                bgcolor: 'primary.50',
              },
            }}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".docx"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
            {file ? (
              <Box>
                <CheckIcon sx={{ fontSize: 48, color: 'success.main', mb: 1 }} />
                <Typography variant="body1" fontWeight={500}>
                  {file.name}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {(file.size / 1024).toFixed(1)} KB - Click to change
                </Typography>
              </Box>
            ) : (
              <Box>
                <UploadIcon sx={{ fontSize: 48, color: 'grey.400', mb: 1 }} />
                <Typography variant="body1" color="text.secondary">
                  Drag and drop a Word document here, or click to select
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Supports .docx files up to 10 MB
                </Typography>
              </Box>
            )}
          </Box>
        </Box>

        {/* Check Button */}
        <Button
          variant="contained"
          size="large"
          onClick={handleCheck}
          disabled={loading || !file || !drugName.trim()}
          startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <CheckIcon />}
          fullWidth
        >
          {loading ? 'Checking Document...' : 'Check Document'}
        </Button>
      </Paper>

      {/* Error Message */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Results */}
      {response && (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            {/* FDA Label Info Header */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="h5" gutterBottom>
                Results for {response.drug_name}
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center' }}>
                {response.fda_label_date && (
                  <Chip
                    icon={<CalendarIcon />}
                    label={`FDA Label Date: ${response.fda_label_date}`}
                    variant="outlined"
                    color="primary"
                  />
                )}
                {response.dailymed_url && (
                  <Button
                    variant="outlined"
                    size="small"
                    href={response.dailymed_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    endIcon={<OpenInNewIcon />}
                  >
                    View FDA Label on DailyMed
                  </Button>
                )}
              </Box>
            </Box>

            <Divider sx={{ my: 2 }} />

            {/* Reading Level Section */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <SchoolIcon sx={{ mr: 1 }} />
                Reading Comprehension Level
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                <Chip
                  label={response.reading_level}
                  color={getReadingLevelColor(response.reading_level) as any}
                  sx={{ fontWeight: 600 }}
                />
              </Box>
              <Typography variant="body2" color="text.secondary">
                {response.reading_level_description}
              </Typography>
            </Box>

            <Divider sx={{ my: 2 }} />

            {/* Adjust Reading Level & Tone Section */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <TuneIcon sx={{ mr: 1 }} />
                Adjust Document
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Adjust the reading level or tone while preserving FDA-accurate information.
              </Typography>
              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Target Reading Level</InputLabel>
                    <Select
                      value={targetReadingLevel}
                      label="Target Reading Level"
                      onChange={(e) => setTargetReadingLevel(e.target.value)}
                    >
                      <MenuItem value="">
                        <em>No change</em>
                      </MenuItem>
                      {READING_LEVELS.map((level) => (
                        <MenuItem key={level.value} value={level.value}>
                          <Box>
                            <Typography variant="body2">{level.label}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {level.description}
                            </Typography>
                          </Box>
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Target Tone</InputLabel>
                    <Select
                      value={targetTone}
                      label="Target Tone"
                      onChange={(e) => setTargetTone(e.target.value)}
                    >
                      <MenuItem value="">
                        <em>No change</em>
                      </MenuItem>
                      {TONES.map((tone) => (
                        <MenuItem key={tone.value} value={tone.value}>
                          <Box>
                            <Typography variant="body2">{tone.label}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {tone.description}
                            </Typography>
                          </Box>
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>
              <Button
                variant="outlined"
                onClick={handleAdjust}
                disabled={adjusting || (!targetReadingLevel && !targetTone)}
                startIcon={adjusting ? <CircularProgress size={20} /> : <AutoFixIcon />}
              >
                {adjusting ? 'Adjusting...' : 'Adjust Document'}
              </Button>
            </Box>

            {/* Adjusted Document Result */}
            {adjustedResponse && (
              <>
                <Divider sx={{ my: 2 }} />
                <Box sx={{ mb: 3 }}>
                  <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                    <AutoFixIcon sx={{ mr: 1, color: 'success.main' }} />
                    Adjusted Document
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                    {adjustedResponse.reading_level !== 'unchanged' && (
                      <Chip
                        label={`Reading Level: ${adjustedResponse.reading_level}`}
                        color="success"
                        size="small"
                      />
                    )}
                    {adjustedResponse.tone !== 'unchanged' && (
                      <Chip
                        label={`Tone: ${adjustedResponse.tone}`}
                        color="success"
                        size="small"
                      />
                    )}
                  </Box>
                  <Alert severity="info" sx={{ mb: 2 }}>
                    <Typography variant="body2">
                      {adjustedResponse.changes_summary}
                    </Typography>
                  </Alert>
                  <Button
                    variant="text"
                    onClick={() => setShowAdjusted(!showAdjusted)}
                    endIcon={showAdjusted ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                  >
                    {showAdjusted ? 'Hide' : 'Show'} Adjusted Text
                  </Button>
                  <Collapse in={showAdjusted}>
                    <Paper sx={{ p: 2, mt: 1, bgcolor: 'success.50', maxHeight: 400, overflow: 'auto' }}>
                      <Typography
                        variant="body2"
                        sx={{ whiteSpace: 'pre-wrap' }}
                      >
                        {adjustedResponse.adjusted_text}
                      </Typography>
                    </Paper>
                  </Collapse>
                </Box>
              </>
            )}

            <Divider sx={{ my: 2 }} />

            {/* Summary */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Summary
              </Typography>
              <Box
                sx={{
                  p: 2,
                  bgcolor: response.issues.length === 0 ? 'success.50' : 'warning.50',
                  borderRadius: 1,
                  borderLeft: '4px solid',
                  borderColor: response.issues.length === 0 ? 'success.main' : 'warning.main',
                }}
              >
                <Typography variant="body1">
                  {formatMarkdown(response.summary)}
                </Typography>
              </Box>
            </Box>

            {/* Issues */}
            {response.issues.length > 0 && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Issues Found ({response.issues.length})
                </Typography>
                <List>
                  {response.issues.map((issue, index) => (
                    <Paper key={index} sx={{ mb: 2, overflow: 'hidden' }}>
                      <ListItem
                        sx={{
                          bgcolor: issue.severity === 'high' ? 'error.50' :
                                   issue.severity === 'medium' ? 'warning.50' : 'info.50',
                        }}
                      >
                        <ListItemIcon>
                          {getSeverityIcon(issue.severity)}
                        </ListItemIcon>
                        <ListItemText
                          primary={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Typography variant="subtitle1" fontWeight={500}>
                                {getCategoryLabel(issue.category)}
                              </Typography>
                              <Chip
                                label={issue.severity.toUpperCase()}
                                size="small"
                                color={getSeverityColor(issue.severity) as any}
                              />
                            </Box>
                          }
                          secondary={
                            <Typography
                              variant="body2"
                              sx={{ mt: 0.5, fontStyle: 'italic', color: 'text.secondary' }}
                            >
                              "{issue.text_excerpt}"
                            </Typography>
                          }
                        />
                      </ListItem>
                      <Box sx={{ p: 2 }}>
                        <Typography variant="body2" sx={{ mb: 1 }}>
                          <strong>Issue:</strong> {issue.issue_description}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          <strong>FDA Reference:</strong> {issue.fda_reference}
                        </Typography>
                      </Box>
                    </Paper>
                  ))}
                </List>
              </Box>
            )}

            {response.issues.length === 0 && (
              <Alert severity="success" sx={{ mb: 3 }}>
                <Typography variant="body1">
                  No significant issues were found in the document.
                </Typography>
              </Alert>
            )}

            {/* Document Preview Toggle */}
            <Box sx={{ mb: 2 }}>
              <Button
                variant="text"
                onClick={() => setShowPreview(!showPreview)}
                endIcon={showPreview ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              >
                {showPreview ? 'Hide' : 'Show'} Original Document Preview
              </Button>
              <Collapse in={showPreview}>
                <Paper sx={{ p: 2, mt: 1, bgcolor: 'grey.50', maxHeight: 300, overflow: 'auto' }}>
                  <Typography
                    variant="body2"
                    sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}
                  >
                    {response.document_text_preview}
                  </Typography>
                </Paper>
              </Collapse>
            </Box>

            <Divider sx={{ my: 2 }} />

            {/* Disclaimer */}
            <Alert severity="info" icon={<InfoIcon />}>
              <Typography variant="caption">
                {response.disclaimer}
              </Typography>
            </Alert>
          </CardContent>
        </Card>
      )}

      {/* How It Works */}
      {!response && !loading && (
        <Paper sx={{ p: 3, bgcolor: 'grey.50' }}>
          <Typography variant="h6" gutterBottom>
            How It Works
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Canon's document checker helps verify pharmaceutical content against FDA data:
          </Typography>
          <Box component="ol" sx={{ pl: 2, '& li': { mb: 1 } }}>
            <Typography component="li" variant="body2" color="text.secondary">
              <strong>Upload a document</strong> containing claims about a drug
            </Typography>
            <Typography component="li" variant="body2" color="text.secondary">
              <strong>Enter the drug name</strong> to check against
            </Typography>
            <Typography component="li" variant="body2" color="text.secondary">
              <strong>AI analyzes</strong> the document against official FDA label data
            </Typography>
            <Typography component="li" variant="body2" color="text.secondary">
              <strong>Review issues</strong> with FDA references and severity levels
            </Typography>
            <Typography component="li" variant="body2" color="text.secondary">
              <strong>Adjust reading level and tone</strong> while preserving accuracy
            </Typography>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            <strong>Best for:</strong> Marketing copy, patient materials, training documents, and manuscripts that reference drug information.
          </Typography>
        </Paper>
      )}
    </Container>
  );
};

export default CanonDocuments;
