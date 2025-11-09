import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Alert,
  CircularProgress,
  Button,
} from '@mui/material';
import { GoogleLogin } from '@react-oauth/google';
import type { CredentialResponse } from '@react-oauth/google';
import { PublicClientApplication, InteractionRequiredAuthError } from '@azure/msal-browser';
import { useAuth } from '../../contexts/AuthContext';
import talesLogo from './tales_black.png';

const MICROSOFT_CLIENT_ID = import.meta.env.VITE_MICROSOFT_CLIENT_ID || '';

const msalConfig = {
  auth: {
    clientId: MICROSOFT_CLIENT_ID,
    authority: 'https://login.microsoftonline.com/common',
    redirectUri: window.location.origin,
  },
  cache: {
    cacheLocation: 'localStorage' as const,
    storeAuthStateInCookie: false,
  },
};

const msalInstance = new PublicClientApplication(msalConfig);

const Login: React.FC = () => {
  const navigate = useNavigate();
  const { googleLogin, microsoftLogin } = useAuth();

  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [msalInitialized, setMsalInitialized] = useState(false);

  useEffect(() => {
    msalInstance.initialize().then(() => {
      setMsalInitialized(true);
    });
  }, []);

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

  const handleMicrosoftLogin = async () => {
    if (!msalInitialized) {
      setError('Microsoft login is initializing. Please wait...');
      return;
    }

    setError('');
    setLoading(true);

    try {
      const loginRequest = {
        scopes: ['openid', 'profile', 'email'],
      };

      const loginResponse = await msalInstance.loginPopup(loginRequest);

      if (loginResponse.idToken) {
        await microsoftLogin(loginResponse.idToken);
        navigate('/');
      } else {
        throw new Error('No ID token received from Microsoft');
      }
    } catch (err: any) {
      console.error('Microsoft login error:', err);
      setError(err.response?.data?.detail || 'Microsoft login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        backgroundColor: '#ffffff',
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
            Welcome to Tales!
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

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, alignItems: 'center' }}>
          <Box sx={{ width: '100%', display: 'flex', justifyContent: 'center' }}>
            <GoogleLogin
              onSuccess={handleGoogleSuccess}
              onError={handleGoogleError}
              theme="outline"
              size="large"
              text="signin_with"
              shape="rectangular"
            />
          </Box>

          <Button
            variant="outlined"
            onClick={handleMicrosoftLogin}
            disabled={loading || !msalInitialized}
            fullWidth
            sx={{
              borderColor: '#665775',
              color: '#665775',
              '&:hover': {
                borderColor: '#54475f',
                backgroundColor: 'rgba(102, 87, 117, 0.04)',
              },
              textTransform: 'none',
              fontSize: '14px',
              padding: '10px 16px',
              fontWeight: 500,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 1,
            }}
          >
            <svg width="21" height="21" viewBox="0 0 21 21" xmlns="http://www.w3.org/2000/svg">
              <rect x="1" y="1" width="9" height="9" fill="#f25022"/>
              <rect x="1" y="11" width="9" height="9" fill="#00a4ef"/>
              <rect x="11" y="1" width="9" height="9" fill="#7fba00"/>
              <rect x="11" y="11" width="9" height="9" fill="#ffb900"/>
            </svg>
            Sign in with Microsoft
          </Button>
        </Box>

        <Typography
          variant="body2"
          sx={{ mt: 3, color: '#7f8c8d' }}
        >
          Sign in with your Google or Microsoft account to access TALES
        </Typography>
      </Paper>
    </Box>
  );
};

export default Login;
