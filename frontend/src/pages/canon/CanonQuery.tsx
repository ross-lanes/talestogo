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
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  InputAdornment,
} from '@mui/material';
import {
  QuestionAnswer as QuestionIcon,
  Send as SendIcon,
  Source as SourceIcon,
  Info as InfoIcon,
  Lightbulb as LightbulbIcon,
} from '@mui/icons-material';
import api from '../../services/api';
import { formatMarkdown } from './utils/formatMarkdown';

interface QuestionResponse {
  answer: string;
  sources: string[];
  disclaimer: string;
}

const CanonQuery: React.FC = () => {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<QuestionResponse | null>(null);

  const handleAsk = async () => {
    if (!question.trim()) {
      setError('Please enter a question');
      return;
    }

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const result = await api.post<QuestionResponse>('/canon/ask', {
        question: question.trim(),
      });
      setResponse(result.data);
    } catch (err: any) {
      console.error('Ask error:', err);
      if (err.response?.status === 503) {
        setError('The AI service is temporarily unavailable. Please try again later.');
      } else if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('An error occurred while processing your question. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleAsk();
    }
  };

  const exampleQuestions = [
    'What are the most common side effects of Galafold?',
    'Compare the warnings for Posluma and Pylarify',
    'Does Salonpas have any contraindications?',
    'What drugs interact with Ozempic?',
  ];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Ask a Question
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Ask questions about FDA drug data in natural language. Our AI will search official FDA databases and provide answers.
        </Typography>
      </Box>

      {/* Question Input */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
          <TextField
            fullWidth
            multiline
            rows={2}
            placeholder="Ask anything about FDA drug data... (e.g., What are the most common side effects of Ozempic?)"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={loading}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start" sx={{ alignSelf: 'flex-start', mt: 1.5 }}>
                  <QuestionIcon color="action" />
                </InputAdornment>
              ),
            }}
          />
          <Button
            variant="contained"
            onClick={handleAsk}
            disabled={loading || !question.trim()}
            sx={{ minWidth: 120, height: 56 }}
            startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
          >
            {loading ? 'Asking...' : 'Ask'}
          </Button>
        </Box>

        {/* Example Questions */}
        <Box sx={{ mt: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <LightbulbIcon sx={{ fontSize: 16, color: 'text.secondary', mr: 0.5 }} />
            <Typography variant="caption" color="text.secondary">
              Try asking:
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
            {exampleQuestions.map((example, index) => (
              <Chip
                key={index}
                label={example}
                size="small"
                onClick={() => setQuestion(example)}
                sx={{ cursor: 'pointer' }}
                variant="outlined"
              />
            ))}
          </Box>
        </Box>
      </Paper>

      {/* Error Message */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Response */}
      {response && (
        <Card>
          <CardContent>
            {/* Answer */}
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <QuestionIcon sx={{ mr: 1, color: 'primary.main' }} />
              Answer
            </Typography>
            <Box
              sx={{
                whiteSpace: 'pre-wrap',
                mb: 3,
                pl: 2,
                borderLeft: '3px solid',
                borderColor: 'primary.main',
                '& strong': { fontWeight: 600 },
                '& em': { fontStyle: 'italic' },
              }}
            >
              <Typography variant="body1" component="div">
                {formatMarkdown(response.answer)}
              </Typography>
            </Box>

            <Divider sx={{ my: 2 }} />

            {/* Sources */}
            <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <SourceIcon sx={{ mr: 1, fontSize: 18 }} />
              Data Sources
            </Typography>
            <List dense>
              {response.sources.map((source, index) => (
                <ListItem key={index} sx={{ py: 0 }}>
                  <ListItemIcon sx={{ minWidth: 24 }}>
                    <Box
                      sx={{
                        width: 6,
                        height: 6,
                        borderRadius: '50%',
                        bgcolor: 'primary.main',
                      }}
                    />
                  </ListItemIcon>
                  <ListItemText
                    primary={source}
                    primaryTypographyProps={{ variant: 'body2' }}
                  />
                </ListItem>
              ))}
            </List>

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
            Canon uses AI to answer your questions about FDA drug data:
          </Typography>
          <Box component="ol" sx={{ pl: 2, '& li': { mb: 1 } }}>
            <Typography component="li" variant="body2" color="text.secondary">
              <strong>You ask a question</strong> about any drug or medication
            </Typography>
            <Typography component="li" variant="body2" color="text.secondary">
              <strong>We search FDA databases</strong> including drug labels and adverse event reports
            </Typography>
            <Typography component="li" variant="body2" color="text.secondary">
              <strong>AI synthesizes an answer</strong> based on official FDA data
            </Typography>
            <Typography component="li" variant="body2" color="text.secondary">
              <strong>Sources are cited</strong> so you know where the information comes from
            </Typography>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            <strong>Best for:</strong> Comparing drugs, understanding side effects, checking warnings, and researching drug interactions.
          </Typography>
        </Paper>
      )}
    </Container>
  );
};

export default CanonQuery;
