import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Alert,
  CircularProgress,
} from '@mui/material';
import { GoogleLogin } from '@react-oauth/google';
import type { CredentialResponse } from '@react-oauth/google';
import { useAuth } from '../../contexts/AuthContext';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const { googleLogin } = useAuth();

  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleGoogleSuccess = async (credentialResponse: CredentialResponse) => {
    setError('');
    setLoading(true);

    try {
      if (!credentialResponse.credential) {
        throw new Error('No credential received from Google');
      }

      // Send the Google ID token to our backend
      await googleLogin(credentialResponse.credential);
      navigate('/');
    } catch (err: any) {
      console.error('Google login error:', err);
      setError(err.response?.data?.detail || 'Google login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleError = () => {
    setError('Google login failed. Please try again.');
  };

  return (
    <div style={{
      minHeight: '100vh',
      paddingTop: '32px',
      paddingBottom: '32px',
      paddingLeft: '50px'
    }}>
      <Paper elevation={3} sx={{ p: 4, width: 400 }}>
          <Typography variant="h4" component="h1" gutterBottom align="center">
            AIRO Login
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom align="center" sx={{ mb: 3 }}>
            AI Reputation Insights & Optimization
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          {loading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
              <CircularProgress />
            </Box>
          )}

          <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
            <GoogleLogin
              onSuccess={handleGoogleSuccess}
              onError={handleGoogleError}
              useOneTap
              theme="outline"
              size="large"
            />
          </Box>

          <Typography variant="body2" color="text.secondary" align="center">
            Sign in with your Google account to access AIRO
          </Typography>
      </Paper>
    </div>
  );
};

export default Login;
