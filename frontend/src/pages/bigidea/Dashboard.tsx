import { useState, useEffect, useCallback } from 'react';
import {
  Container,
  Typography,
  Box,
  Alert,
  Button,
  CircularProgress,
  Grid,
} from '@mui/material';
import HistoryIcon from '@mui/icons-material/History';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import DownloadIcon from '@mui/icons-material/Download';
import type {
  BigIdeaFormData,
  GeneratedResponse,
  Idea,
  ClientProject,
  SavedIdea,
} from '../../types/bigidea';
import { DEFAULT_FORM_DATA } from '../../types/bigidea';
import {
  generateBigIdeas,
  expandIdea,
  checkApiStatus,
  saveGenerationToStorage,
  loadGenerationFromStorage,
  hasStoredGeneration,
  getProjects,
  saveProjects,
} from '../../services/bigideaService';
import BigIdeaInputForm from './components/BigIdeaInputForm';
import IdeaCard from './components/IdeaCard';
import CompetitorAnalysisCard from './components/CompetitorAnalysisCard';
import SaveIdeaDialog from './components/SaveIdeaDialog';
import axios from 'axios';

export default function BigIdeaDashboard() {
  const [formData, setFormData] = useState<BigIdeaFormData>(DEFAULT_FORM_DATA);
  const [currentView, setCurrentView] = useState<'input' | 'results'>('input');
  const [response, setResponse] = useState<GeneratedResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [hasSavedData, setHasSavedData] = useState(false);
  const [expandingIdeaId, setExpandingIdeaId] = useState<string | null>(null);
  const [apiConfigured, setApiConfigured] = useState<boolean | null>(null);
  const [projects, setProjects] = useState<ClientProject[]>([]);

  // Save dialog state
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [ideaToSave, setIdeaToSave] = useState<Idea | null>(null);

  useEffect(() => {
    setHasSavedData(hasStoredGeneration());
    setProjects(getProjects());

    // Check if Gemini API is configured on the server
    checkApiStatus()
      .then((status) => {
        setApiConfigured(status.gemini_configured);
      })
      .catch(() => {
        setApiConfigured(true);
      });
  }, []);

  const handleGenerate = useCallback(async () => {
    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const result = await generateBigIdeas(formData);
      setResponse(result);
      setCurrentView('results');
      saveGenerationToStorage(result, formData);
      setHasSavedData(true);
    } catch (err: unknown) {
      let errorMessage = 'An unexpected error occurred.';
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err instanceof Error) {
        errorMessage = err.message;
      }
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [formData]);

  const handleLoadRecent = () => {
    const saved = loadGenerationFromStorage();
    if (saved) {
      setResponse(saved.response);
      setFormData(saved.formData);
      setCurrentView('results');
    }
  };

  const handleUpdateIdea = (updatedIdea: Idea) => {
    if (!response) return;
    const updatedIdeas = response.ideas.map((idea) =>
      idea.id === updatedIdea.id ? updatedIdea : idea
    );
    const updatedResponse = { ...response, ideas: updatedIdeas };
    setResponse(updatedResponse);
    saveGenerationToStorage(updatedResponse, formData);
  };

  const handleExpandIdea = async (ideaId: string) => {
    if (!response) return;
    const ideaToExpand = response.ideas.find((i) => i.id === ideaId);
    if (!ideaToExpand) return;

    setExpandingIdeaId(ideaId);
    setError(null);

    try {
      const result = await expandIdea(formData, ideaToExpand);
      if (result.ideas.length > 0) {
        const expandedIdea = result.ideas[0];
        handleUpdateIdea(expandedIdea);
        setSuccessMessage(`"${expandedIdea.title}" expanded successfully!`);
        setTimeout(() => setSuccessMessage(null), 3000);
      }
    } catch (err: unknown) {
      let errorMessage = 'Failed to expand idea.';
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err instanceof Error) {
        errorMessage = err.message;
      }
      setError(errorMessage);
    } finally {
      setExpandingIdeaId(null);
    }
  };

  const handleOpenSaveDialog = (idea: Idea) => {
    setIdeaToSave(idea);
    setSaveDialogOpen(true);
  };

  const handleSaveIdea = (idea: Idea, projectName: string, notes: string, tags: string[]) => {
    const savedIdea: SavedIdea = {
      ...idea,
      savedAt: Date.now(),
      notes,
      tags,
      projectId: '',
    };

    const existingProjectIndex = projects.findIndex(
      (p) => p.name.toLowerCase() === projectName.toLowerCase()
    );

    let updatedProjects: ClientProject[];

    if (existingProjectIndex > -1) {
      const updatedProject = { ...projects[existingProjectIndex] };
      savedIdea.projectId = updatedProject.id;

      const existingIdeaIndex = updatedProject.ideas.findIndex((i) => i.id === idea.id);
      if (existingIdeaIndex > -1) {
        updatedProject.ideas[existingIdeaIndex] = savedIdea;
      } else {
        updatedProject.ideas.push(savedIdea);
      }
      updatedProjects = [...projects];
      updatedProjects[existingProjectIndex] = updatedProject;
    } else {
      const newProjectId = `project-${Date.now()}`;
      savedIdea.projectId = newProjectId;
      const newProject: ClientProject = {
        id: newProjectId,
        name: projectName,
        ideas: [savedIdea],
      };
      updatedProjects = [...projects, newProject];
    }

    setProjects(updatedProjects);
    saveProjects(updatedProjects);
    setSuccessMessage(`Idea saved to project "${projectName}"!`);
    setTimeout(() => setSuccessMessage(null), 3000);
  };

  const handleExportJson = () => {
    if (!response) return;
    const dataStr = JSON.stringify(response, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${formData.clientName.replace(/\s+/g, '_')}_big_ideas.json`;
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
              Big Idea Generator
            </Typography>
            <Typography
              variant="body1"
              color="text.secondary"
              sx={{ maxWidth: 600, mx: 'auto', mb: 3 }}
            >
              Input your client's details and let AI spark groundbreaking marketing ideas,
              tailored to your ambition and goals.
            </Typography>

            {apiConfigured === false && (
              <Alert severity="warning" sx={{ maxWidth: 600, mx: 'auto', mb: 3 }}>
                The Gemini API is not configured on the server. Please contact the administrator.
              </Alert>
            )}

            {hasSavedData && (
              <Button
                variant="outlined"
                startIcon={<HistoryIcon />}
                onClick={handleLoadRecent}
                sx={{ mb: 2 }}
              >
                View Most Recent Ideas
              </Button>
            )}
          </Box>

          {/* Input Form */}
          <Box sx={{ maxWidth: 900, mx: 'auto' }}>
            <BigIdeaInputForm
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
          {response && (
            <Box sx={{ textAlign: 'center', mt: 3 }}>
              <Button variant="text" onClick={() => setCurrentView('results')}>
                Return to current results
              </Button>
            </Box>
          )}
        </Box>
      )}

      {/* Results View */}
      {currentView === 'results' && response && (
        <Box>
          {/* Toolbar */}
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              mb: 3,
              pb: 2,
              borderBottom: '1px solid',
              borderColor: 'divider',
            }}
          >
            <Button
              startIcon={<ArrowBackIcon />}
              onClick={() => setCurrentView('input')}
            >
              Back to Form
            </Button>
            <Typography variant="h6" fontWeight={600}>
              Generated Ideas for {formData.clientName}
            </Typography>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={handleExportJson}
            >
              Export JSON
            </Button>
          </Box>

          {/* Messages */}
          {error && (
            <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
          {successMessage && (
            <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccessMessage(null)}>
              {successMessage}
            </Alert>
          )}

          {/* Loading */}
          {loading ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 10 }}>
              <CircularProgress size={48} sx={{ mb: 2 }} />
              <Typography color="text.secondary">Generating ideas...</Typography>
            </Box>
          ) : (
            <Grid container spacing={3}>
              {/* Ideas Column */}
              <Grid item xs={12} md={8}>
                <Typography variant="h6" fontWeight={600} sx={{ mb: 2 }}>
                  Ideas ({response.ideas.length})
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                  {response.ideas.map((idea) => (
                    <IdeaCard
                      key={idea.id}
                      idea={idea}
                      onUpdate={handleUpdateIdea}
                      onExpand={() => handleExpandIdea(idea.id)}
                      onSave={() => handleOpenSaveDialog(idea)}
                      isExpanding={expandingIdeaId === idea.id}
                    />
                  ))}
                </Box>
              </Grid>

              {/* Competitor Analysis Column */}
              <Grid item xs={12} md={4}>
                <CompetitorAnalysisCard analysis={response.competitorAnalysis} />

                {/* Grounding Sources */}
                {response.groundingUrls && response.groundingUrls.length > 0 && (
                  <Box
                    sx={{
                      mt: 3,
                      p: 2,
                      bgcolor: 'background.paper',
                      border: '1px solid',
                      borderColor: 'divider',
                      borderRadius: 2,
                    }}
                  >
                    <Typography variant="subtitle2" fontWeight={600} sx={{ mb: 1 }}>
                      Sources
                    </Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      {response.groundingUrls.map((source, idx) => (
                        <Button
                          key={idx}
                          variant="text"
                          size="small"
                          href={source.uri}
                          target="_blank"
                          rel="noopener noreferrer"
                          sx={{ textTransform: 'none', justifyContent: 'flex-start' }}
                        >
                          {source.title || source.uri}
                        </Button>
                      ))}
                    </Box>
                  </Box>
                )}
              </Grid>
            </Grid>
          )}

          {/* Back to input */}
          <Box sx={{ textAlign: 'center', mt: 4 }}>
            <Button variant="text" onClick={() => setCurrentView('input')}>
              Generate New Ideas
            </Button>
          </Box>
        </Box>
      )}

      {/* Save Idea Dialog */}
      <SaveIdeaDialog
        open={saveDialogOpen}
        idea={ideaToSave}
        onClose={() => setSaveDialogOpen(false)}
        onSave={handleSaveIdea}
        defaultProjectName={formData.clientName}
      />
    </Container>
  );
}
