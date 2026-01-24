import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Alert,
  CircularProgress,
  Button,
} from '@mui/material';
import { useAuth } from '../../contexts/AuthContext';

// Dev mode: skip MSAL entirely (for HTTP environments without Web Crypto)
// Hardcoded to true for PPPL internal deployment
const DEV_MODE = true;

const MICROSOFT_CLIENT_ID = import.meta.env.VITE_MICROSOFT_CLIENT_ID || '';
const MICROSOFT_TENANT_ID = import.meta.env.VITE_MICROSOFT_TENANT_ID || 'common';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const { microsoftLogin, devLogin } = useAuth();

  const [error, setError] = useState('');
  const [loading, setLoading] = useState(DEV_MODE); // Start loading in dev mode for auto-login
  const [msalInitialized, setMsalInitialized] = useState(false);
  const msalInstanceRef = useRef<any>(null);

  useEffect(() => {
    if (DEV_MODE) {
      // Auto-login in dev mode
      handleDevLogin();
      return;
    }

    // Dynamically import and initialize MSAL only when not in dev mode
    const initMsal = async () => {
      try {
        const { PublicClientApplication } = await import('@azure/msal-browser');
        const msalConfig = {
          auth: {
            clientId: MICROSOFT_CLIENT_ID,
            authority: `https://login.microsoftonline.com/${MICROSOFT_TENANT_ID}`,
            redirectUri: window.location.origin,
          },
          cache: {
            cacheLocation: 'localStorage' as const,
            storeAuthStateInCookie: false,
          },
        };
        msalInstanceRef.current = new PublicClientApplication(msalConfig);
        await msalInstanceRef.current.initialize();
        setMsalInitialized(true);
      } catch (err) {
        console.error('Failed to initialize MSAL:', err);
        setError('Failed to initialize authentication. Try enabling dev mode.');
      }
    };

    initMsal();
  }, []);

  const handleDevLogin = async () => {
    setLoading(true);
    try {
      await devLogin();
      navigate('/');
    } catch (err: any) {
      console.error('Dev login error:', err);
      setError(err.response?.data?.detail || 'Dev login failed');
      setLoading(false);
    }
  };

  const handleMicrosoftLogin = async () => {
    if (DEV_MODE) {
      handleDevLogin();
      return;
    }

    if (!msalInitialized || !msalInstanceRef.current) {
      setError('Microsoft login is initializing. Please wait...');
      return;
    }

    setError('');
    setLoading(true);

    try {
      const loginRequest = {
        scopes: ['openid', 'profile', 'email'],
      };

      const loginResponse = await msalInstanceRef.current.loginPopup(loginRequest);

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
        backgroundColor: '#1a1a2e',
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
              color: '#1a1a2e',
              fontWeight: 700,
              lineHeight: 1.3,
              fontFamily: '"Montserrat", "Arial", sans-serif',
              mb: 2,
            }}
          >
            PPPL Tales
          </Typography>
          <Typography
            variant="body1"
            sx={{
              color: 'rgba(0, 0, 0, 0.6)',
              fontFamily: '"Roboto Condensed", sans-serif',
            }}
          >
            AI Reputation Monitoring Platform
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3, textAlign: 'left' }}>
            {error}
          </Alert>
        )}

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
            <CircularProgress sx={{ color: '#0066b2' }} />
          </Box>
        )}

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, alignItems: 'center', mb: 3 }}>
          <Button
            variant="outlined"
            onClick={handleMicrosoftLogin}
            disabled={loading || (!DEV_MODE && !msalInitialized)}
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
            {DEV_MODE ? (
              'Dev Login'
            ) : (
              <>
                <svg width="21" height="21" viewBox="0 0 21 21" xmlns="http://www.w3.org/2000/svg">
                  <rect x="1" y="1" width="9" height="9" fill="#f25022"/>
                  <rect x="1" y="11" width="9" height="9" fill="#00a4ef"/>
                  <rect x="11" y="1" width="9" height="9" fill="#7fba00"/>
                  <rect x="11" y="11" width="9" height="9" fill="#ffb900"/>
                </svg>
                Sign in with Microsoft
              </>
            )}
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
          {DEV_MODE ? 'Development mode enabled' : 'Sign in with your PPPL Microsoft account'}
        </Typography>

        {!DEV_MODE && (
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
        )}
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
          Princeton Plasma Physics Laboratory
        </Typography>
      </Box>
    </Box>
  );
};

export default Login;
