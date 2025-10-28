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
        width: '100vw',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        fontFamily: 'Roboto, sans-serif',
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
      }}
    >
      <Paper
        elevation={6}
        sx={{
          p: 4,
          width: 500,
          maxWidth: '90vw',
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
            variant="h5"
            component="h1"
            gutterBottom
            sx={{ color: '#665775', fontWeight: 700, lineHeight: 1.4 }}
          >
            Welcome to Tales where you can shape your AI story.
          </Typography>
          <Typography
            variant="body2"
            sx={{ color: '#80a1d4', mt: 2, mb: 2, lineHeight: 1.6 }}
          >
            If you are a new user, an administrator will be alerted when you log in for the first time to consider your account for approval.
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
