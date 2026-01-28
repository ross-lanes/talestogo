import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Alert,
  Grid,
} from '@mui/material';
import { Save as SaveIcon } from '@mui/icons-material';
import { adminAPI } from '../../services/api';

interface Brand {
  id: number;
  user_id: number;
  brand_name: string;
  website_url?: string;
  industry?: string;
  description?: string;
  strategic_messages?: string;
  is_active: boolean;
}

interface AdminBrandInfoTabProps {
  userId: number;
  brandId: number;
  brand: Brand;
  onUpdate: () => void;
}

const AdminBrandInfoTab: React.FC<AdminBrandInfoTabProps> = ({ userId, brandId, brand, onUpdate }) => {
  const [formData, setFormData] = useState({
    brand_name: brand.brand_name || '',
    website_url: brand.website_url || '',
    industry: brand.industry || '',
    description: brand.description || '',
    strategic_messages: brand.strategic_messages || '',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    setError('');
    setSuccess('');
    setSaving(true);

    try {
      await adminAPI.updateBrand(brandId, formData);
      setSuccess('Brand information updated successfully');
      onUpdate();
    } catch (err: any) {
      console.error('Failed to update brand:', err);
      setError(err.response?.data?.detail || 'Failed to update brand information');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Box sx={{ px: 2 }}>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Brand Name"
            value={formData.brand_name}
            onChange={(e) => handleChange('brand_name', e.target.value)}
            required
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Website URL"
            value={formData.website_url}
            onChange={(e) => handleChange('website_url', e.target.value)}
            placeholder="https://example.com"
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Industry"
            value={formData.industry}
            onChange={(e) => handleChange('industry', e.target.value)}
            placeholder="e.g., Technology, Healthcare"
          />
        </Grid>

        <Grid item xs={12}>
          <TextField
            fullWidth
            multiline
            rows={4}
            label="Description"
            value={formData.description}
            onChange={(e) => handleChange('description', e.target.value)}
            placeholder="Brief description of the brand"
          />
        </Grid>

        <Grid item xs={12}>
          <TextField
            fullWidth
            multiline
            rows={4}
            label="Strategic Messages"
            value={formData.strategic_messages}
            onChange={(e) => handleChange('strategic_messages', e.target.value)}
            placeholder="Key strategic messages for this brand"
          />
        </Grid>

        <Grid item xs={12}>
          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={handleSave}
            disabled={saving || !formData.brand_name}
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
        </Grid>
      </Grid>
    </Box>
  );
};

export default AdminBrandInfoTab;
