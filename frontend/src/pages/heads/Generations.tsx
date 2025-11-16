import { useEffect, useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Grid,
  Chip,
  Button,
  CircularProgress,
} from '@mui/material';
import { Download as DownloadIcon, Refresh as RefreshIcon } from '@mui/icons-material';
import { headsAPI } from '../../services/api';
import type { PersonaGeneration } from '../../types';

export default function Generations() {
  const [generations, setGenerations] = useState<PersonaGeneration[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadGenerations();
  }, []);

  const loadGenerations = async () => {
    setLoading(true);
    try {
      const data = await headsAPI.getGenerations();
      setGenerations(data);
    } catch (error) {
      console.error('Failed to load generations:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'generating':
        return 'info';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  const handleDownload = (deckUrl: string) => {
    window.open(`${import.meta.env.VITE_API_URL}${deckUrl}`, '_blank');
  };

  if (loading) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">Persona Generations</Typography>
        <Button startIcon={<RefreshIcon />} onClick={loadGenerations}>
          Refresh
        </Button>
      </Box>

      {generations.length === 0 ? (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="h6" color="text.secondary">
              No persona generations yet
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Generate your first set of personas to see them here
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {generations.map((generation) => (
            <Grid item xs={12} key={generation.id}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                    <Box>
                      <Typography variant="h6" gutterBottom>
                        Generation #{generation.id}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Created: {new Date(generation.created_at).toLocaleString()}
                      </Typography>
                      {generation.completed_at && (
                        <Typography variant="body2" color="text.secondary">
                          Completed: {new Date(generation.completed_at).toLocaleString()}
                        </Typography>
                      )}
                    </Box>
                    <Chip
                      label={generation.status.toUpperCase()}
                      color={getStatusColor(generation.status) as any}
                    />
                  </Box>

                  <Grid container spacing={2} sx={{ mb: 2 }}>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" gutterBottom>
                        Patient Inputs:
                      </Typography>
                      {generation.patient_occupation && (
                        <Typography variant="body2">
                          • Occupation: {generation.patient_occupation}
                        </Typography>
                      )}
                      {generation.patient_age_range && (
                        <Typography variant="body2">
                          • Age: {generation.patient_age_range}
                        </Typography>
                      )}
                      {generation.patient_gender && (
                        <Typography variant="body2">
                          • Gender: {generation.patient_gender}
                        </Typography>
                      )}
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" gutterBottom>
                        HCP Inputs:
                      </Typography>
                      {generation.hcp_doctor_type && (
                        <Typography variant="body2">
                          • Type: {generation.hcp_doctor_type}
                        </Typography>
                      )}
                      {generation.hcp_disease && (
                        <Typography variant="body2">
                          • Disease: {generation.hcp_disease}
                        </Typography>
                      )}
                      {generation.hcp_location && (
                        <Typography variant="body2">
                          • Location: {generation.hcp_location}
                        </Typography>
                      )}
                    </Grid>
                  </Grid>

                  {generation.error_message && (
                    <Typography variant="body2" color="error" sx={{ mb: 2 }}>
                      Error: {generation.error_message}
                    </Typography>
                  )}

                  {generation.deck_url && generation.status === 'completed' && (
                    <Button
                      variant="contained"
                      startIcon={<DownloadIcon />}
                      onClick={() => handleDownload(generation.deck_url!)}
                    >
                      Download PowerPoint Deck
                    </Button>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Container>
  );
}
