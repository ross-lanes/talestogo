import React, { useState } from 'react';
import {
  Box,
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
  Grid,
  Divider,
  InputAdornment,
  IconButton,
} from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { authAPI } from '../services/api';

const Settings: React.FC = () => {
  const { user, refreshUser } = useAuth();

  // Profile state
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [organization, setOrganization] = useState(user?.organization || '');

  // API Keys state
  const [openaiKey, setOpenaiKey] = useState('');
  const [anthropicKey, setAnthropicKey] = useState('');
  const [geminiKey, setGeminiKey] = useState('');
  const [perplexityKey, setPerplexityKey] = useState('');

  // UI state
  const [showKeys, setShowKeys] = useState({
    openai: false,
    anthropic: false,
    gemini: false,
    perplexity: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSaveProfile = async () => {
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      await authAPI.updateProfile({
        full_name: fullName,
        organization: organization,
      });

      await refreshUser();
      setSuccess('Profile updated successfully!');
    } catch (err: any) {
      console.error('Profile update error:', err);
      setError(err.response?.data?.detail || 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveApiKeys = async () => {
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const updates: any = {};

      if (openaiKey) updates.openai_api_key = openaiKey;
      if (anthropicKey) updates.anthropic_api_key = anthropicKey;
      if (geminiKey) updates.gemini_api_key = geminiKey;
      if (perplexityKey) updates.perplexity_api_key = perplexityKey;

      if (Object.keys(updates).length === 0) {
        setError('No API keys to update');
        setLoading(false);
        return;
      }

      await authAPI.updateProfile(updates);

      // Clear the form fields after successful save
      setOpenaiKey('');
      setAnthropicKey('');
      setGeminiKey('');
      setPerplexityKey('');

      setSuccess('API keys updated successfully! Keys are encrypted and stored securely.');
    } catch (err: any) {
      console.error('API keys update error:', err);
      setError(err.response?.data?.detail || 'Failed to update API keys');
    } finally {
      setLoading(false);
    }
  };

  const toggleShowKey = (key: keyof typeof showKeys) => {
    setShowKeys((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom>
        Settings
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

      {/* Profile Section */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Profile Information
        </Typography>
        <Divider sx={{ mb: 3 }} />

        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Email"
              value={user?.email || ''}
              disabled
              helperText="Email cannot be changed"
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Full Name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Organization"
              value={organization}
              onChange={(e) => setOrganization(e.target.value)}
              placeholder="Brand you're tracking"
            />
          </Grid>

          <Grid item xs={12}>
            <Typography variant="caption" color="text.secondary">
              Account Status: {user?.is_active ? 'Active' : 'Pending Approval'}
              {user?.is_admin && ' • Admin'}
            </Typography>
          </Grid>

          <Grid item xs={12}>
            <Button
              variant="contained"
              onClick={handleSaveProfile}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Save Profile'}
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* API Keys Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          API Keys
        </Typography>
        <Divider sx={{ mb: 3 }} />

        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Your API keys are encrypted and stored securely. They are never visible to admins or other users.
          Only enter keys if you want to update them.
        </Typography>

        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="OpenAI API Key"
              type={showKeys.openai ? 'text' : 'password'}
              value={openaiKey}
              onChange={(e) => setOpenaiKey(e.target.value)}
              placeholder="sk-..."
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton onClick={() => toggleShowKey('openai')} edge="end">
                      {showKeys.openai ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Anthropic (Claude) API Key"
              type={showKeys.anthropic ? 'text' : 'password'}
              value={anthropicKey}
              onChange={(e) => setAnthropicKey(e.target.value)}
              placeholder="sk-ant-..."
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton onClick={() => toggleShowKey('anthropic')} edge="end">
                      {showKeys.anthropic ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Google Gemini API Key"
              type={showKeys.gemini ? 'text' : 'password'}
              value={geminiKey}
              onChange={(e) => setGeminiKey(e.target.value)}
              placeholder="AIza..."
              helperText="Required for analysis and reports"
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton onClick={() => toggleShowKey('gemini')} edge="end">
                      {showKeys.gemini ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Perplexity API Key"
              type={showKeys.perplexity ? 'text' : 'password'}
              value={perplexityKey}
              onChange={(e) => setPerplexityKey(e.target.value)}
              placeholder="pplx-..."
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton onClick={() => toggleShowKey('perplexity')} edge="end">
                      {showKeys.perplexity ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
          </Grid>

          <Grid item xs={12}>
            <Button
              variant="contained"
              color="primary"
              onClick={handleSaveApiKeys}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Save API Keys'}
            </Button>
          </Grid>
        </Grid>
      </Paper>
    </Container>
  );
};

export default Settings;
