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
import { GoogleLogin, GoogleOAuthProvider } from '@react-oauth/google';
import type { CredentialResponse } from '@react-oauth/google';
import { PublicClientApplication } from '@azure/msal-browser';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../services/api';

// Auth configuration from backend
interface AuthConfig {
  local_auth_enabled: boolean;
  microsoft_auth_enabled: boolean;
  google_auth_enabled: boolean;
  microsoft_client_id: string | null;
  microsoft_authority: string | null;
  google_client_id: string | null;
}

// Branding configuration from backend
interface BrandingConfig {
  site_name: string;
  site_logo_url: string | null;
  primary_color: string;
  secondary_color: string;
}

const Login: React.FC = () => {
  const navigate = useNavigate();
  const { googleLogin, microsoftLogin } = useAuth();

  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [configLoading, setConfigLoading] = useState(true);
  const [authConfig, setAuthConfig] = useState<AuthConfig | null>(null);
  const [branding, setBranding] = useState<BrandingConfig | null>(null);
  const [msalInitialized, setMsalInitialized] = useState(false);
  const msalInstanceRef = useRef<PublicClientApplication | null>(null);

  // Fetch auth and branding config from backend
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const [authResponse, brandingResponse] = await Promise.all([
          api.get('/auth/config'),
          api.get('/site/branding'),
        ]);
        setAuthConfig(authResponse.data);
        setBranding(brandingResponse.data);
      } catch (err) {
        console.error('Failed to fetch config:', err);
        // Set defaults if config fetch fails
        setAuthConfig({
          local_auth_enabled: true,
          microsoft_auth_enabled: false,
          google_auth_enabled: false,
          microsoft_client_id: null,
          google_client_id: null,
        });
        setBranding({
          site_name: 'Tales',
          site_logo_url: null,
          primary_color: '#003e60',
          secondary_color: '#75c9c8',
        });
      } finally {
        setConfigLoading(false);
      }
    };

    fetchConfig();
  }, []);

  // Initialize MSAL when Microsoft auth is enabled and we have a client ID
  useEffect(() => {
    if (authConfig?.microsoft_auth_enabled && authConfig.microsoft_client_id) {
      const msalConfig = {
        auth: {
          clientId: authConfig.microsoft_client_id,
          authority: authConfig.microsoft_authority || 'https://login.microsoftonline.com/common',
          redirectUri: window.location.origin,
        },
        cache: {
          cacheLocation: 'localStorage' as const,
          storeAuthStateInCookie: false,
        },
      };

      const instance = new PublicClientApplication(msalConfig);
      msalInstanceRef.current = instance;

      instance.initialize().then(() => {
        setMsalInitialized(true);
      });
    }
  }, [authConfig]);

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

  // Show loading while fetching config
  if (configLoading) {
    return (
      <Box
        sx={{
          backgroundColor: '#000000',
          minHeight: '100vh',
          width: '100vw',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        <CircularProgress sx={{ color: '#75c9c8' }} />
      </Box>
    );
  }

  const siteName = branding?.site_name || 'Tales';
  const primaryColor = branding?.primary_color || '#003e60';
  const secondaryColor = branding?.secondary_color || '#75c9c8';

  // Determine which auth methods to show
  const showMicrosoft = authConfig?.microsoft_auth_enabled && authConfig.microsoft_client_id;
  const showGoogle = authConfig?.google_auth_enabled && authConfig.google_client_id;

  // Build the login method description
  let loginMethodText = 'Sign in with your ';
  const methods: string[] = [];
  if (showGoogle) methods.push('Google');
  if (showMicrosoft) methods.push('Microsoft');
  if (methods.length > 0) {
    loginMethodText += methods.join(' or ') + ' account';
  } else {
    loginMethodText = 'No authentication methods configured. Please contact your administrator.';
  }

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
          {branding?.site_logo_url && (
            <Box sx={{ mb: 3 }}>
              <img
                src={branding.site_logo_url}
                alt={siteName}
                style={{ maxWidth: '220px', maxHeight: '80px' }}
              />
            </Box>
          )}
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
            Welcome to {siteName}!
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3, textAlign: 'left' }}>
            {error}
          </Alert>
        )}

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
            <CircularProgress sx={{ color: secondaryColor }} />
          </Box>
        )}

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, alignItems: 'center', mb: 3 }}>
          {/* Google Login Button */}
          {showGoogle && authConfig.google_client_id && (
            <GoogleOAuthProvider clientId={authConfig.google_client_id}>
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
            </GoogleOAuthProvider>
          )}

          {/* Microsoft Login Button */}
          {showMicrosoft && (
            <Button
              variant="outlined"
              onClick={handleMicrosoftLogin}
              disabled={loading || !msalInitialized}
              fullWidth
              sx={{
                borderColor: primaryColor,
                color: primaryColor,
                borderWidth: '1.5px',
                '&:hover': {
                  borderColor: primaryColor,
                  borderWidth: '1.5px',
                  backgroundColor: `${primaryColor}0a`,
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
          )}
        </Box>

        <Typography
          variant="body2"
          sx={{
            color: 'rgba(0, 0, 0, 0.6)',
            fontSize: '0.875rem',
            fontFamily: '"Roboto Condensed", sans-serif',
          }}
        >
          {loginMethodText}
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
          {siteName} - AI Reputation Intelligence
        </Typography>
      </Box>
    </Box>
  );
};

export default Login;
