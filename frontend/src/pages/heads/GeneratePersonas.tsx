import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Box,
  Paper,
  TextField,
  Button,
  Grid,
  Alert,
  Divider,
  CircularProgress,
} from '@mui/material';
import { Create as CreateIcon } from '@mui/icons-material';
import { useBrand } from '../../contexts/BrandContext';
import { headsAPI } from '../../services/api';

export default function GeneratePersonas() {
  const navigate = useNavigate();
  const { activeBrand } = useBrand();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [formData, setFormData] = useState({
    // Patient inputs
    patient_occupation: '',
    patient_clinical_scenario: '',
    patient_gender: '',
    patient_symptoms: '',
    patient_age_range: '',
    // HCP inputs
    hcp_doctor_type: '',
    hcp_disease: '',
    hcp_location: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await headsAPI.generatePersonas(formData);
      navigate('/heads/generations');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate personas. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (!activeBrand) {
    return (
      <Container maxWidth="lg">
        <Alert severity="warning">
          Please select an active brand before generating personas.
          Go to <a href="/brands">Brand Management</a> to create or activate a brand.
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="md">
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Generate Personas
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Create patient and HCP personas for <strong>{activeBrand.brand_name}</strong>
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 3 }}>
        <Box component="form" onSubmit={handleSubmit}>
          {/* Patient Persona Inputs */}
          <Typography variant="h6" gutterBottom>
            Patient Persona Inputs
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Provide characteristics for patient personas
          </Typography>

          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Occupation"
                value={formData.patient_occupation}
                onChange={(e) => setFormData({ ...formData, patient_occupation: e.target.value })}
                helperText="e.g., Retired engineer, Teacher, Business owner"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Gender"
                value={formData.patient_gender}
                onChange={(e) => setFormData({ ...formData, patient_gender: e.target.value })}
                helperText="e.g., Male, Female, Mixed"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Age Range"
                value={formData.patient_age_range}
                onChange={(e) => setFormData({ ...formData, patient_age_range: e.target.value })}
                helperText="e.g., 50-65, 40-70"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Clinical Scenario / Diagnosis"
                value={formData.patient_clinical_scenario}
                onChange={(e) => setFormData({ ...formData, patient_clinical_scenario: e.target.value })}
                multiline
                rows={2}
                helperText="Describe the clinical scenario or diagnosis"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Symptoms"
                value={formData.patient_symptoms}
                onChange={(e) => setFormData({ ...formData, patient_symptoms: e.target.value })}
                multiline
                rows={2}
                helperText="Describe key symptoms patients experience"
              />
            </Grid>
          </Grid>

          <Divider sx={{ my: 4 }} />

          {/* HCP Persona Inputs */}
          <Typography variant="h6" gutterBottom>
            Healthcare Professional Persona Inputs
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Provide characteristics for HCP personas
          </Typography>

          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Type of Doctor"
                value={formData.hcp_doctor_type}
                onChange={(e) => setFormData({ ...formData, hcp_doctor_type: e.target.value })}
                helperText="e.g., Urologist, Oncologist, Primary Care"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Location"
                value={formData.hcp_location}
                onChange={(e) => setFormData({ ...formData, hcp_location: e.target.value })}
                helperText="e.g., Northeast US, Major academic centers"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Disease / Disease Area"
                value={formData.hcp_disease}
                onChange={(e) => setFormData({ ...formData, hcp_disease: e.target.value })}
                helperText="The disease or therapeutic area they specialize in"
              />
            </Grid>
          </Grid>

          <Box sx={{ mt: 4, display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
            <Button
              type="button"
              onClick={() => navigate('/')}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="contained"
              startIcon={loading ? <CircularProgress size={20} /> : <CreateIcon />}
              disabled={loading}
            >
              {loading ? 'Generating...' : 'Generate Personas'}
            </Button>
          </Box>

          {loading && (
            <Alert severity="info" sx={{ mt: 2 }}>
              Generating personas... This may take 1-2 minutes. You will be redirected when complete.
            </Alert>
          )}
        </Box>
      </Paper>
    </Container>
  );
}
