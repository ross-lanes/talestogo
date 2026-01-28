import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Button,
  TextField,
  Alert,
  CircularProgress,
  Divider,
} from '@mui/material';
import {
  Save as SaveIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { siteConfigAPI } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';

interface SiteConfig {
  site_url: string | null;
  admin_email: string | null;
  site_name: string | null;
}

const SiteSettings: React.FC = () => {
  const { isAdmin } = useAuth();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [config, setConfig] = useState<SiteConfig>({
    site_url: '',
    admin_email: '',
    site_name: '',
  });

  const loadConfig = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await siteConfigAPI.getConfig();
      setConfig({
        site_url: data.site_url || '',
        admin_email: data.admin_email || '',
        site_name: data.site_name || '',
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load site configuration');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConfig();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      // Only send non-empty values
      const updateData: any = {};
      if (config.site_url) updateData.site_url = config.site_url;
      if (config.admin_email) updateData.admin_email = config.admin_email;
      if (config.site_name) updateData.site_name = config.site_name;

      await siteConfigAPI.updateConfig(updateData);
      setSuccess('Site configuration saved successfully');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save site configuration');
    } finally {
      setSaving(false);
    }
  };

  if (!isAdmin) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Alert severity="error">You must be an admin to access this page.</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Paper sx={{ p: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h5" component="h1">
            Site Settings
          </Typography>
          <Button
            startIcon={<RefreshIcon />}
            onClick={loadConfig}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Configure site-wide settings for email notifications and branding.
          These settings will be used in all system-generated emails.
          If left empty, the system will fall back to environment variables.
        </Typography>

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

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Box component="form" sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <TextField
              label="Site URL"
              value={config.site_url}
              onChange={(e) => setConfig({ ...config, site_url: e.target.value })}
              fullWidth
              placeholder="https://mycompany.com/tales"
              helperText="Base URL for links in emails. Leave empty to use FRONTEND_URL environment variable."
            />

            <TextField
              label="Admin Email"
              value={config.admin_email}
              onChange={(e) => setConfig({ ...config, admin_email: e.target.value })}
              fullWidth
              type="email"
              placeholder="support@mycompany.com"
              helperText="Contact email shown in notification emails. Leave empty to use FROM_EMAIL environment variable."
            />

            <TextField
              label="Site Name"
              value={config.site_name}
              onChange={(e) => setConfig({ ...config, site_name: e.target.value })}
              fullWidth
              placeholder="TALES"
              helperText="Application name used in email subjects and headers. Defaults to 'TALES' if not set."
            />

            <Divider sx={{ my: 1 }} />

            <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="contained"
                color="primary"
                startIcon={saving ? <CircularProgress size={20} color="inherit" /> : <SaveIcon />}
                onClick={handleSave}
                disabled={saving}
              >
                {saving ? 'Saving...' : 'Save Settings'}
              </Button>
            </Box>
          </Box>
        )}
      </Paper>
    </Container>
  );
};

export default SiteSettings;
