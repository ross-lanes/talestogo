import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Box,
  Alert,
  Button,
  CircularProgress,
} from '@mui/material';
import HistoryIcon from '@mui/icons-material/History';
import { useAuth } from '../../contexts/AuthContext';
import type { Persona, HeadsFormData, Source } from '../../types/heads';
import { DEFAULT_FORM_DATA, ExportFormat } from '../../types/heads';
import {
  generatePersonas,
  generatePersonaImage,
  saveGenerationToStorage,
  loadGenerationFromStorage,
  hasStoredGeneration,
} from '../../services/headsService';
import HeadsInputForm from './components/HeadsInputForm';
import PersonaCard from './components/PersonaCard';
import HeadsExportToolbar from './components/HeadsExportToolbar';

export default function HeadsDashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [formData, setFormData] = useState<HeadsFormData>(DEFAULT_FORM_DATA);
  const [currentView, setCurrentView] = useState<'input' | 'results'>('input');
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSavedData, setHasSavedData] = useState(false);
  const [generatingImageFor, setGeneratingImageFor] = useState<string | null>(null);

  const geminiApiKey = user?.gemini_api_key || '';

  useEffect(() => {
    setHasSavedData(hasStoredGeneration());
  }, []);

  const handleGenerate = useCallback(async () => {
    if (!geminiApiKey) {
      setError('Please add your Gemini API key in Settings to generate personas.');
      return;
    }

    setLoading(true);
    setError(null);
    setPersonas([]);
    setSources([]);

    try {
      const result = await generatePersonas(formData, geminiApiKey);
      setPersonas(result.personas);
      setSources(result.sources);
      setCurrentView('results');
      saveGenerationToStorage(result.personas, result.sources, formData);
      setHasSavedData(true);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'An unexpected error occurred.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [formData, geminiApiKey]);

  const handleLoadRecent = () => {
    const saved = loadGenerationFromStorage();
    if (saved) {
      setPersonas(saved.personas);
      setSources(saved.sources);
      setFormData(saved.formData);
      setCurrentView('results');
    }
  };

  const handleUpdatePersona = (updatedPersona: Persona) => {
    setPersonas((prevPersonas) => {
      const newPersonas = prevPersonas.map((p) =>
        p.id === updatedPersona.id ? updatedPersona : p
      );
      saveGenerationToStorage(newPersonas, sources, formData);
      return newPersonas;
    });
  };

  const handleGenerateImage = async (persona: Persona, styleKeywords?: string) => {
    if (!geminiApiKey) {
      setError('Please add your Gemini API key in Settings to generate images.');
      return;
    }

    setGeneratingImageFor(persona.id);
    try {
      const imageBase64 = await generatePersonaImage(persona, geminiApiKey, styleKeywords);
      handleUpdatePersona({ ...persona, avatarBase64: imageBase64 });
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate image.';
      setError(errorMessage);
    } finally {
      setGeneratingImageFor(null);
    }
  };

  const exportData = (data: Persona | Persona[], format: ExportFormat) => {
    let content = '';
    let filename = 'personas';
    let mimeType = 'text/plain';

    if (Array.isArray(data)) {
      filename = `${formData.brand.replace(/\s+/g, '_')}_personas`;
    } else {
      filename = `${data.name.replace(/\s+/g, '_')}_persona`;
    }

    if (format === ExportFormat.JSON) {
      content = JSON.stringify(data, null, 2);
      mimeType = 'application/json';
      filename += '.json';
    } else if (format === ExportFormat.TXT) {
      mimeType = 'text/plain';
      filename += '.txt';
      const list = Array.isArray(data) ? data : [data];
      content = list
        .map(
          (p) => `
----------------------------------------
TITLE: ${p.generalizationTitle}
NAME: ${p.name}
AGE: ${p.age}
OCCUPATION: ${p.occupation}
LOCATION: ${p.location}
WORKPLACE: ${p.workplace}
TECH ABILITY: ${p.technologyAbility || 'N/A'}
TECH COMFORT: ${p.technologyComfortability || 'N/A'}
PROFILE: ${p.profile}

GOALS:
${p.goals.map((g) => `- ${g}`).join('\n')}

FRUSTRATIONS:
${p.frustrations.map((f) => `- ${f}`).join('\n')}

BRAND VIEW: ${p.brandView}
MARKETING STRATEGY: ${p.marketingStrategy}
----------------------------------------
        `
        )
        .join('\n');
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Input View */}
      {currentView === 'input' && (
        <Box sx={{ animation: 'fadeIn 0.3s ease-in-out' }}>
          {/* Header */}
          <Box sx={{ mb: 4, textAlign: 'center' }}>
            <Typography variant="h4" fontWeight={700} gutterBottom>
              Construct Your Ideal Personas
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 600, mx: 'auto', mb: 3 }}>
              Input your brand details and target demographics. We'll generate detailed,
              actionable user personas to guide your marketing strategy.
            </Typography>

            {!geminiApiKey && (
              <Alert severity="warning" sx={{ maxWidth: 600, mx: 'auto', mb: 3 }}>
                Please add your Gemini API key in{' '}
                <Button
                  size="small"
                  onClick={() => navigate('/settings')}
                  sx={{ textTransform: 'none', p: 0, minWidth: 'auto' }}
                >
                  Settings
                </Button>{' '}
                to generate personas.
              </Alert>
            )}

            {hasSavedData && (
              <Button
                variant="outlined"
                startIcon={<HistoryIcon />}
                onClick={handleLoadRecent}
                sx={{ mb: 2 }}
              >
                View Most Recent Personas
              </Button>
            )}
          </Box>

          {/* Input Form */}
          <Box sx={{ maxWidth: 900, mx: 'auto' }}>
            <HeadsInputForm
              formData={formData}
              setFormData={setFormData}
              onSubmit={handleGenerate}
              isLoading={loading}
            />
          </Box>

          {/* Error */}
          {error && (
            <Alert severity="error" sx={{ maxWidth: 900, mx: 'auto', mt: 3 }}>
              {error}
            </Alert>
          )}

          {/* Link to results if available */}
          {personas.length > 0 && (
            <Box sx={{ textAlign: 'center', mt: 3 }}>
              <Button variant="text" onClick={() => setCurrentView('results')}>
                Return to current results
              </Button>
            </Box>
          )}
        </Box>
      )}

      {/* Results View */}
      {currentView === 'results' && (
        <Box>
          {/* Toolbar */}
          <HeadsExportToolbar
            personas={personas}
            formData={formData}
            onBack={() => setCurrentView('input')}
            onExportJson={() => exportData(personas, ExportFormat.JSON)}
            onExportText={() => exportData(personas, ExportFormat.TXT)}
            onPrint={() => window.print()}
          />

          {/* Error */}
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          {/* Loading */}
          {loading ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 10 }}>
              <CircularProgress size={48} sx={{ mb: 2 }} />
              <Typography color="text.secondary">Updating Personas...</Typography>
            </Box>
          ) : (
            <>
              {/* Persona Cards */}
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {personas.map((persona) => (
                  <PersonaCard
                    key={persona.id}
                    persona={persona}
                    onExport={exportData}
                    onUpdate={handleUpdatePersona}
                    onGenerateImage={handleGenerateImage}
                    isGeneratingImage={generatingImageFor === persona.id}
                  />
                ))}
              </Box>

              {/* Sources */}
              {sources.length > 0 && (
                <Box
                  sx={{
                    mt: 4,
                    p: 3,
                    bgcolor: 'background.paper',
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 2,
                  }}
                  className="no-print"
                >
                  <Typography variant="subtitle2" fontWeight={600} sx={{ mb: 2 }}>
                    Sources & Citations
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {sources.map((source, idx) => (
                      <Button
                        key={idx}
                        variant="outlined"
                        size="small"
                        href={source.uri}
                        target="_blank"
                        rel="noopener noreferrer"
                        sx={{ textTransform: 'none' }}
                      >
                        {source.title}
                      </Button>
                    ))}
                  </Box>
                </Box>
              )}

              {/* Back to input */}
              <Box sx={{ textAlign: 'center', mt: 4 }} className="no-print">
                <Button variant="text" onClick={() => setCurrentView('input')}>
                  Create New Personas
                </Button>
              </Box>
            </>
          )}
        </Box>
      )}
    </Container>
  );
}
