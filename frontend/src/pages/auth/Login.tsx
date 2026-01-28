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

// PPPL Entra ID Client ID (public, not a secret)
const MICROSOFT_CLIENT_ID = import.meta.env.VITE_ENTRA_CLIENT_ID || import.meta.env.VITE_MICROSOFT_CLIENT_ID || '2bee91ee-b116-4939-a84c-21ffbf5a7eed';

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
        backgroundColor: '#000000',
        minHeight: '100vh',
        width: '100vw',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        fontFamily: '"Roboto Condensed", "Roboto", "Arial", sans-serif',
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        padding: 3,
      }}
    >
      {/* Login Card */}
      <Paper
        elevation={0}
        sx={{
          p: 5,
          width: 500,
          maxWidth: '90vw',
          textAlign: 'center',
          borderRadius: 2,
          backgroundColor: '#ffffff',
          border: '1px solid rgba(0, 0, 0, 0.12)',
        }}
      >
        <Box sx={{ mb: 4 }}>
          <Typography
            variant="h4"
            component="h1"
            gutterBottom
            sx={{
              color: '#000000',
              fontWeight: 700,
              lineHeight: 1.3,
              fontFamily: '"Montserrat", "Arial", sans-serif',
              mb: 2,
            }}
          >
            Welcome to Tales!
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3, textAlign: 'left' }}>
            {error}
          </Alert>
        )}

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
            <CircularProgress sx={{ color: '#75c9c8' }} />
          </Box>
        )}

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, alignItems: 'center', mb: 3 }}>
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
              borderColor: '#003e60',
              color: '#003e60',
              borderWidth: '1.5px',
              '&:hover': {
                borderColor: '#003e60',
                borderWidth: '1.5px',
                backgroundColor: 'rgba(0, 62, 96, 0.04)',
              },
              textTransform: 'none',
              fontSize: '15px',
              padding: '11px 24px',
              fontWeight: 600,
              fontFamily: '"Roboto Condensed", sans-serif',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 1.5,
              borderRadius: 1,
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
          sx={{
            color: 'rgba(0, 0, 0, 0.6)',
            fontSize: '0.875rem',
            fontFamily: '"Roboto Condensed", sans-serif',
          }}
        >
          Sign in with your Google or Microsoft account
        </Typography>

        <Typography
          variant="caption"
          sx={{
            mt: 2,
            display: 'block',
            color: 'rgba(0, 0, 0, 0.5)',
            fontSize: '0.75rem',
            fontStyle: 'italic',
            fontFamily: '"Roboto Condensed", sans-serif',
          }}
        >
          New users will be reviewed by an administrator for approval
        </Typography>
      </Paper>

      {/* Footer */}
      <Box sx={{ mt: 4, textAlign: 'center' }}>
        <Typography
          variant="caption"
          sx={{
            color: 'rgba(255, 255, 255, 0.7)',
            fontSize: '0.75rem',
            fontFamily: '"Roboto Condensed", sans-serif',
          }}
        >
          © 2025 RobotRachel • AI Reputation Intelligence
        </Typography>
      </Box>
    </Box>
  );
};

export default Login;
