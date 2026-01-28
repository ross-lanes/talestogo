import { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Grid,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  CircularProgress,
  Paper,
  Typography,
} from '@mui/material';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import type { BigIdeaFormData } from '../../../types/bigidea';
import {
  IdeaScale,
  CampaignGoal,
  BudgetIndicator,
  IDEA_SCALE_OPTIONS,
  CAMPAIGN_GOAL_OPTIONS,
  BUDGET_INDICATOR_OPTIONS,
  NUMBER_OF_IDEAS_OPTIONS,
} from '../../../types/bigidea';

interface BigIdeaInputFormProps {
  formData: BigIdeaFormData;
  setFormData: (data: BigIdeaFormData) => void;
  onSubmit: () => void;
  isLoading: boolean;
}

export default function BigIdeaInputForm({
  formData,
  setFormData,
  onSubmit,
  isLoading,
}: BigIdeaInputFormProps) {
  const [errors, setErrors] = useState<{ [key: string]: string }>({});

  const handleChange = (field: keyof BigIdeaFormData, value: string | number) => {
    setFormData({ ...formData, [field]: value });
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors({ ...errors, [field]: '' });
    }
  };

  const validateForm = (): boolean => {
    const newErrors: { [key: string]: string } = {};

    if (!formData.clientName.trim()) {
      newErrors.clientName = 'Client name is required';
    }
    if (!formData.clientDescription.trim()) {
      newErrors.clientDescription = 'Client description is required';
    }
    if (!formData.ideaAreas.trim()) {
      newErrors.ideaAreas = 'Areas for ideas are required';
    }
    if (!formData.targetAudience.trim()) {
      newErrors.targetAudience = 'Target audience is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      onSubmit();
    }
  };

  return (
    <Paper elevation={0} sx={{ p: 4, border: '1px solid', borderColor: 'divider', borderRadius: 2 }}>
      <form onSubmit={handleSubmit}>
        <Grid container spacing={3}>
          {/* Client Name */}
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Client Name"
              required
              value={formData.clientName}
              onChange={(e) => handleChange('clientName', e.target.value)}
              error={!!errors.clientName}
              helperText={errors.clientName || "e.g., 'EcoCharge Electric Vehicles'"}
              placeholder="Enter client name"
            />
          </Grid>

          {/* Account Name */}
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Account Name (Optional)"
              value={formData.accountName || ''}
              onChange={(e) => handleChange('accountName', e.target.value)}
              helperText="e.g., 'Q4 Launch Campaign'"
              placeholder="Enter account name"
            />
          </Grid>

          {/* Client Description */}
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Client / Account Description"
              required
              multiline
              rows={3}
              value={formData.clientDescription}
              onChange={(e) => handleChange('clientDescription', e.target.value)}
              error={!!errors.clientDescription}
              helperText={errors.clientDescription || "Describe the client, their business, and campaign context"}
              placeholder="e.g., 'A rapidly growing startup selling sustainable electric vehicles...'"
            />
          </Grid>

          {/* Strategic Imperatives */}
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Strategic Imperatives (Optional)"
              multiline
              rows={2}
              value={formData.strategicImperatives || ''}
              onChange={(e) => handleChange('strategicImperatives', e.target.value)}
              helperText="Key strategic goals or priorities (numerically label if multiple)"
              placeholder="e.g., '1. Increase market share by 10%...'"
            />
          </Grid>

          {/* Competitors */}
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Known Competitors (Optional)"
              value={formData.competitors || ''}
              onChange={(e) => handleChange('competitors', e.target.value)}
              helperText="Separate with commas"
              placeholder="e.g., 'Tesla, Lucid Motors, Rivian'"
            />
          </Grid>

          {/* Country/Region */}
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Country / Region (Optional)"
              value={formData.countryRegion || ''}
              onChange={(e) => handleChange('countryRegion', e.target.value)}
              helperText="Target geographic area"
              placeholder="e.g., 'United States', 'Europe'"
            />
          </Grid>

          {/* Number of Ideas */}
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Number of Ideas</InputLabel>
              <Select
                value={formData.numberOfIdeas}
                label="Number of Ideas"
                onChange={(e) => handleChange('numberOfIdeas', e.target.value as number)}
              >
                {NUMBER_OF_IDEAS_OPTIONS.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Areas for Ideas */}
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Areas for Ideas"
              required
              value={formData.ideaAreas}
              onChange={(e) => handleChange('ideaAreas', e.target.value)}
              error={!!errors.ideaAreas}
              helperText={errors.ideaAreas || "e.g., 'TV, Digital, Social Media, Experiential'"}
              placeholder="Separate areas with commas"
            />
          </Grid>

          {/* Target Audience */}
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Target Audience Demographics"
              required
              multiline
              rows={2}
              value={formData.targetAudience}
              onChange={(e) => handleChange('targetAudience', e.target.value)}
              error={!!errors.targetAudience}
              helperText={errors.targetAudience || "Describe your target audience"}
              placeholder="e.g., 'Young professionals, 25-40, environmentally conscious'"
            />
          </Grid>

          {/* Campaign Goal */}
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Campaign Goal</InputLabel>
              <Select
                value={formData.campaignGoal}
                label="Campaign Goal"
                onChange={(e) => handleChange('campaignGoal', e.target.value as CampaignGoal)}
              >
                {CAMPAIGN_GOAL_OPTIONS.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Budget */}
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Budget</InputLabel>
              <Select
                value={formData.budget}
                label="Budget"
                onChange={(e) => handleChange('budget', e.target.value as BudgetIndicator)}
              >
                {BUDGET_INDICATOR_OPTIONS.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Idea Scale */}
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Scale of Ideas</InputLabel>
              <Select
                value={formData.ideaScale}
                label="Scale of Ideas"
                onChange={(e) => handleChange('ideaScale', e.target.value as IdeaScale)}
              >
                {IDEA_SCALE_OPTIONS.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Submit Button */}
          <Grid item xs={12}>
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
              <Button
                type="submit"
                variant="contained"
                size="large"
                disabled={isLoading}
                startIcon={isLoading ? <CircularProgress size={20} color="inherit" /> : <AutoAwesomeIcon />}
                sx={{ minWidth: 250, py: 1.5 }}
              >
                {isLoading ? 'Generating Ideas...' : 'Generate Big Ideas'}
              </Button>
            </Box>
          </Grid>
        </Grid>
      </form>
    </Paper>
  );
}
