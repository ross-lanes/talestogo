import React from 'react';
import {
  Box,
  TextField,
  Button,
  Grid,
  Typography,
  Card,
  CardContent,
  Checkbox,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
} from '@mui/material';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import CheckIcon from '@mui/icons-material/Check';
import type { HeadsFormData } from '../../../types/heads';
import { ARCHETYPES } from '../../../types/heads';

interface HeadsInputFormProps {
  formData: HeadsFormData;
  setFormData: React.Dispatch<React.SetStateAction<HeadsFormData>>;
  onSubmit: () => void;
  isLoading: boolean;
  submitLabel?: string;
}

const HeadsInputForm: React.FC<HeadsInputFormProps> = ({
  formData,
  setFormData,
  onSubmit,
  isLoading,
  submitLabel,
}) => {
  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement> | { target: { name: string; value: unknown } }
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === 'numberOfPersonas' ? Number(value) : value,
    }));
  };

  const toggleArchetype = (archetypeId: string) => {
    setFormData((prev) => {
      const current = prev.archetypes || [];
      if (current.includes(archetypeId)) {
        return { ...prev, archetypes: current.filter((id) => id !== archetypeId) };
      } else {
        return { ...prev, archetypes: [...current, archetypeId] };
      }
    });
  };

  const isValid = formData.brand.trim() !== '' && formData.occupations.trim() !== '';

  return (
    <Card elevation={0} sx={{ border: '1px solid', borderColor: 'divider' }}>
      <CardContent sx={{ p: { xs: 2, md: 4 } }}>
        <Grid container spacing={3}>
          {/* Brand Name */}
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Brand Name"
              name="brand"
              value={formData.brand}
              onChange={handleChange}
              placeholder="e.g. Nike, Starbucks, or a startup name"
              required
              InputLabelProps={{ shrink: true }}
            />
          </Grid>

          {/* Brand Account */}
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Brand Account"
              name="brandAccount"
              value={formData.brandAccount}
              onChange={handleChange}
              placeholder="e.g. Footwear Division, Coffee Subscription, Enterprise Software"
              helperText="Optional - specific division or focus area"
              InputLabelProps={{ shrink: true }}
            />
          </Grid>

          {/* Account Details */}
          <Grid item xs={12}>
            <TextField
              fullWidth
              multiline
              rows={3}
              label="Account Details"
              name="accountDetails"
              value={formData.accountDetails}
              onChange={handleChange}
              placeholder="Add context about the account, project goals, or specific focus areas..."
              helperText="Optional - additional context for persona generation"
              InputLabelProps={{ shrink: true }}
            />
          </Grid>

          {/* Target Occupations */}
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Target Occupations"
              name="occupations"
              value={formData.occupations}
              onChange={handleChange}
              placeholder="e.g. Marketing Managers, Students, Freelancers"
              required
              InputLabelProps={{ shrink: true }}
            />
          </Grid>

          {/* Age Ranges & Number of Personas */}
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Age Ranges"
              name="ageRanges"
              value={formData.ageRanges}
              onChange={handleChange}
              placeholder="e.g. 18-24, 30-45"
              helperText="Optional"
              InputLabelProps={{ shrink: true }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Number of Personas</InputLabel>
              <Select
                name="numberOfPersonas"
                value={formData.numberOfPersonas}
                onChange={(e) => handleChange(e as { target: { name: string; value: unknown } })}
                label="Number of Personas"
              >
                {[1, 2, 3, 4, 5, 6].map((num) => (
                  <MenuItem key={num} value={num}>
                    {num} Persona{num > 1 ? 's' : ''}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Website & Target Countries */}
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Brand Website"
              name="website"
              value={formData.website}
              onChange={handleChange}
              placeholder="https://example.com"
              helperText="Optional"
              InputLabelProps={{ shrink: true }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Target Countries"
              name="targetCountries"
              value={formData.targetCountries}
              onChange={handleChange}
              placeholder="e.g. USA, UK, Germany, Brazil"
              helperText="Optional"
              InputLabelProps={{ shrink: true }}
            />
          </Grid>

          {/* Custom Characteristics */}
          <Grid item xs={12}>
            <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 2 }}>
              Specific Persona Characteristics (Optional)
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  size="small"
                  name="customCharacteristic1"
                  value={formData.customCharacteristic1}
                  onChange={handleChange}
                  placeholder="Characteristic 1 (e.g. Eco-conscious)"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  size="small"
                  name="customCharacteristic2"
                  value={formData.customCharacteristic2}
                  onChange={handleChange}
                  placeholder="Characteristic 2 (e.g. Remote worker)"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  size="small"
                  name="customCharacteristic3"
                  value={formData.customCharacteristic3}
                  onChange={handleChange}
                  placeholder="Characteristic 3 (e.g. Urban Dweller)"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  size="small"
                  name="customCharacteristic4"
                  value={formData.customCharacteristic4}
                  onChange={handleChange}
                  placeholder="Characteristic 4 (e.g. Heavy Social Media User)"
                />
              </Grid>
            </Grid>
          </Grid>

          {/* Archetypes */}
          <Grid item xs={12}>
            <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 2 }}>
              Include Archetypes (Optional)
            </Typography>
            <Grid container spacing={2}>
              {ARCHETYPES.map((arch) => {
                const isSelected = formData.archetypes?.includes(arch.id);
                return (
                  <Grid item xs={12} sm={6} lg={4} key={arch.id}>
                    <Card
                      onClick={() => toggleArchetype(arch.id)}
                      sx={{
                        cursor: 'pointer',
                        border: '1px solid',
                        borderColor: isSelected ? 'primary.main' : 'divider',
                        bgcolor: isSelected ? 'primary.50' : 'background.paper',
                        transition: 'all 0.2s',
                        '&:hover': {
                          borderColor: isSelected ? 'primary.main' : 'primary.light',
                          bgcolor: isSelected ? 'primary.50' : 'action.hover',
                        },
                      }}
                    >
                      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5 }}>
                          <Checkbox
                            checked={isSelected}
                            size="small"
                            sx={{ p: 0, mt: 0.25 }}
                            icon={
                              <Box
                                sx={{
                                  width: 18,
                                  height: 18,
                                  border: '2px solid',
                                  borderColor: 'divider',
                                  borderRadius: 0.5,
                                }}
                              />
                            }
                            checkedIcon={
                              <Box
                                sx={{
                                  width: 18,
                                  height: 18,
                                  bgcolor: 'primary.main',
                                  borderRadius: 0.5,
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                }}
                              >
                                <CheckIcon sx={{ fontSize: 14, color: 'white' }} />
                              </Box>
                            }
                          />
                          <Box>
                            <Typography
                              variant="body2"
                              fontWeight={600}
                              color={isSelected ? 'primary.main' : 'text.primary'}
                            >
                              {arch.id}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {arch.description}
                            </Typography>
                          </Box>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                );
              })}
            </Grid>
          </Grid>
        </Grid>

        {/* Submit Button */}
        <Box sx={{ mt: 4, display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            variant="contained"
            size="large"
            onClick={onSubmit}
            disabled={isLoading || !isValid}
            startIcon={
              isLoading ? (
                <CircularProgress size={20} color="inherit" />
              ) : (
                <AutoAwesomeIcon />
              )
            }
            sx={{ minWidth: 200 }}
          >
            {isLoading
              ? submitLabel
                ? 'Updating...'
                : 'Generating...'
              : submitLabel || 'Generate Personas'}
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
};

export default HeadsInputForm;
