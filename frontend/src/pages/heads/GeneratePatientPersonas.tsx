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
  IconButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  AutoAwesome as AIIcon,
  ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';
import { useBrand } from '../../contexts/BrandContext';
import { headsAPI } from '../../services/api';

interface PatientPersonaForm {
  id: string;
  occupation: string;
  clinical_scenario: string;
  gender: string;
  symptoms: string;
  age_range: string;
}

export default function GeneratePatientPersonas() {
  const navigate = useNavigate();
  const { activeBrand } = useBrand();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [aiLoading, setAiLoading] = useState(false);

  // AI Generation state
  const [aiPersonaCount, setAiPersonaCount] = useState(3);

  // Manual form state - start with 1 persona form
  const [personaForms, setPersonaForms] = useState<PatientPersonaForm[]>([
    {
      id: '1',
      occupation: '',
      clinical_scenario: '',
      gender: '',
      symptoms: '',
      age_range: '',
    },
  ]);

  const handleAIGenerate = async () => {
    setError('');
    setAiLoading(true);

    try {
      await headsAPI.generatePersonas({
        persona_type: 'patient',
        ai_generation: true,
        count: aiPersonaCount,
      });
      navigate('/heads/generations');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate AI personas. Please try again.');
    } finally {
      setAiLoading(false);
    }
  };

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await headsAPI.generatePersonas({
        persona_type: 'patient',
        ai_generation: false,
        personas: personaForms.map((form) => ({
          patient_occupation: form.occupation,
          patient_clinical_scenario: form.clinical_scenario,
          patient_gender: form.gender,
          patient_symptoms: form.symptoms,
          patient_age_range: form.age_range,
        })),
      });
      navigate('/heads/generations');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate personas. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const addPersonaForm = () => {
    const newId = (Math.max(...personaForms.map((f) => parseInt(f.id))) + 1).toString();
    setPersonaForms([
      ...personaForms,
      {
        id: newId,
        occupation: '',
        clinical_scenario: '',
        gender: '',
        symptoms: '',
        age_range: '',
      },
    ]);
  };

  const removePersonaForm = (id: string) => {
    if (personaForms.length > 1) {
      setPersonaForms(personaForms.filter((form) => form.id !== id));
    }
  };

  const updatePersonaForm = (id: string, field: keyof PatientPersonaForm, value: string) => {
    setPersonaForms(
      personaForms.map((form) => (form.id === id ? { ...form, [field]: value } : form))
    );
  };

  if (!activeBrand) {
    return (
      <Container maxWidth="lg">
        <Alert severity="warning">
          Please select an active brand before generating personas.
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="md">
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Generate Patient Personas
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Create patient personas for <strong>{activeBrand.brand_name}</strong>
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* AI Generation Section */}
      <Paper sx={{ p: 3, mb: 3, backgroundColor: '#f8f9fa' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <AIIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h6">Generate Personas Based on Brand Info Using AI</Typography>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Let AI analyze your brand's disease state and automatically create realistic patient
          personas with appropriate demographics, symptoms, occupation, and clinical scenarios.
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>Number of Personas</InputLabel>
            <Select
              value={aiPersonaCount}
              label="Number of Personas"
              onChange={(e) => setAiPersonaCount(Number(e.target.value))}
              disabled={aiLoading}
            >
              {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((num) => (
                <MenuItem key={num} value={num}>
                  {num} {num === 1 ? 'Persona' : 'Personas'}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Button
            variant="contained"
            startIcon={aiLoading ? <CircularProgress size={20} /> : <AIIcon />}
            onClick={handleAIGenerate}
            disabled={aiLoading}
            size="large"
          >
            {aiLoading ? 'Generating with AI...' : 'Generate with AI'}
          </Button>
        </Box>

        {aiLoading && (
          <Alert severity="info" sx={{ mt: 2 }}>
            AI is generating personas... This may take 1-2 minutes. You will be redirected when
            complete.
          </Alert>
        )}
      </Paper>

      <Divider sx={{ my: 4 }}>
        <Typography variant="body2" color="text.secondary">
          OR
        </Typography>
      </Divider>

      {/* Manual Form Section */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Create Personas Manually
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Fill in details for each patient persona you want to create
        </Typography>

        <Box component="form" onSubmit={handleManualSubmit}>
          {personaForms.map((form, index) => (
            <Accordion key={form.id} defaultExpanded={index === 0} sx={{ mb: 2 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                  <Typography sx={{ flexGrow: 1 }}>
                    Patient Persona #{parseInt(form.id)}
                  </Typography>
                  {personaForms.length > 1 && (
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        removePersonaForm(form.id);
                      }}
                      sx={{ mr: 1 }}
                    >
                      <DeleteIcon />
                    </IconButton>
                  )}
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Occupation"
                      value={form.occupation}
                      onChange={(e) => updatePersonaForm(form.id, 'occupation', e.target.value)}
                      helperText="e.g., Retired engineer, Teacher, Former accountant, Unemployed"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Gender"
                      value={form.gender}
                      onChange={(e) => updatePersonaForm(form.id, 'gender', e.target.value)}
                      helperText="e.g., Male, Female, Non-binary"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Age Range"
                      value={form.age_range}
                      onChange={(e) => updatePersonaForm(form.id, 'age_range', e.target.value)}
                      helperText="e.g., 50-65, 40-70"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Clinical Scenario / Diagnosis"
                      value={form.clinical_scenario}
                      onChange={(e) =>
                        updatePersonaForm(form.id, 'clinical_scenario', e.target.value)
                      }
                      multiline
                      rows={2}
                      helperText="Describe the clinical scenario or diagnosis"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Symptoms"
                      value={form.symptoms}
                      onChange={(e) => updatePersonaForm(form.id, 'symptoms', e.target.value)}
                      multiline
                      rows={2}
                      helperText="Describe key symptoms the patient experiences"
                    />
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          ))}

          <Button
            startIcon={<AddIcon />}
            onClick={addPersonaForm}
            sx={{ mt: 2, mb: 3 }}
            variant="outlined"
          >
            Add Another Patient Persona
          </Button>

          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mt: 3 }}>
            <Button type="button" onClick={() => navigate('/heads')} disabled={loading}>
              Cancel
            </Button>
            <Button type="submit" variant="contained" disabled={loading}>
              {loading ? 'Generating...' : `Generate ${personaForms.length} Patient${personaForms.length > 1 ? 's' : ''}`}
            </Button>
          </Box>

          {loading && (
            <Alert severity="info" sx={{ mt: 2 }}>
              Generating personas... This may take 1-2 minutes. You will be redirected when
              complete.
            </Alert>
          )}
        </Box>
      </Paper>
    </Container>
  );
}
