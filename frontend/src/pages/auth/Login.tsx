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
import talesLogo from './tales_black.png';

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
    <Box
      sx={{
        backgroundColor: '#665775',
        minHeight: '100vh',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        fontFamily: 'Roboto, sans-serif',
      }}
    >
      <Paper
        elevation={6}
        sx={{
          p: 4,
          width: 400,
          textAlign: 'center',
          borderRadius: 4,
          backgroundColor: '#fff',
        }}
      >
        <Box sx={{ mb: 3 }}>
          <img
            src={talesLogo}
            alt="Tales Logo"
            style={{ width: '120px', marginBottom: '16px' }}
          />
          <Typography
            variant="h4"
            component="h1"
            gutterBottom
            sx={{ color: '#665775', fontWeight: 700 }}
          >
            TALES Login
          </Typography>
          <Typography
            variant="body2"
            sx={{ color: '#80a1d4', mb: 3 }}
          >
            AI Reputation Insights & Optimization
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
            <CircularProgress sx={{ color: '#75c9c8' }} />
          </Box>
        )}

        <GoogleLogin
          onSuccess={handleGoogleSuccess}
          onError={handleGoogleError}
          useOneTap
          theme="outline"
          size="large"
          text="signin_with"
          shape="rectangular"
        />

        <Typography
          variant="body2"
          sx={{ mt: 3, color: '#7f8c8d' }}
        >
          Sign in with your Google account to access TALES
        </Typography>
      </Paper>
    </Box>
  );
};

export default Login;
