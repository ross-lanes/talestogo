import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Container,
} from '@mui/material';
import { api, authAPI } from '../../services/api';

interface InvitationInfo {
  email: string;
  full_name: string;
  expires_at: string;
}

export default function InviteAccept() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');

  const [loading, setLoading] = useState(true);
  const [validating, setValidating] = useState(false);
  const [invitationInfo, setInvitationInfo] = useState<InvitationInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState<string | null>(null);

  // Validate token on mount
  useEffect(() => {
    if (!token) {
      setError('Invalid invitation link. No token provided.');
      setLoading(false);
      return;
    }

    validateToken();
  }, [token]);

  const validateToken = async () => {
    try {
      const response = await api.get<InvitationInfo>(`/invite/validate?token=${token}`);
      setInvitationInfo(response.data);
      setError(null);
    } catch (err: any) {
      console.error('Validation error:', err);
      setError(
        err.response?.data?.detail ||
        'This invitation link is invalid or has expired. Please contact your administrator.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptInvitation = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError(null);

    // Validate password
    if (password.length < 8) {
      setPasswordError('Password must be at least 8 characters long');
      return;
    }

    if (password !== confirmPassword) {
      setPasswordError('Passwords do not match');
      return;
    }

    setValidating(true);
    try {
      // Accept invitation - this sets password and activates account
      const response = await api.post<{ access_token: string; token_type: string }>(
        '/invite/accept',
        { token, password }
      );

      // Store token
      localStorage.setItem('tales_access_token', response.data.access_token);

      // Fetch and store user data
      const userResponse = await api.get('/auth/me');
      localStorage.setItem('tales_user', JSON.stringify(userResponse.data));

      // Redirect to Brand Info page to set up their brand
      navigate('/manage/brand-info');
    } catch (err: any) {
      console.error('Accept invitation error:', err);
      setError(
        err.response?.data?.detail ||
        'Failed to accept invitation. Please try again.'
      );
    } finally {
      setValidating(false);
    }
  };

  if (loading) {
    return (
      <Box
        sx={{
          backgroundColor: '#003e60',
          minHeight: '100vh',
          width: '100vw',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
        }}
      >
        <CircularProgress sx={{ color: '#75c9c8' }} />
      </Box>
    );
  }

  if (error && !invitationInfo) {
    return (
      <Box
        sx={{
          backgroundColor: '#003e60',
          minHeight: '100vh',
          width: '100vw',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
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
          <Typography variant="h4" gutterBottom sx={{ color: '#003e60', fontWeight: 700 }}>
            Invalid Invitation
          </Typography>
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
          <Button
            variant="contained"
            fullWidth
            sx={{ mt: 3, backgroundColor: '#003e60', '&:hover': { backgroundColor: '#54475f' } }}
            onClick={() => navigate('/login')}
          >
            Go to Login
          </Button>
        </Paper>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        backgroundColor: '#003e60',
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
        <Typography
          variant="h4"
          gutterBottom
          sx={{ color: '#003e60', fontWeight: 700, lineHeight: 1.4 }}
        >
          Welcome to TALES!
        </Typography>

        {invitationInfo && (
          <>
            <Typography variant="body1" sx={{ color: '#80a1d4', mb: 3, lineHeight: 1.6 }}>
              Hi <strong>{invitationInfo.full_name}</strong>! You've been invited to join TALES.
            </Typography>

            <Alert severity="info" sx={{ mb: 3 }}>
              Email: <strong>{invitationInfo.email}</strong>
            </Alert>

            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Set your password to create your account and get started.
            </Typography>

            <form onSubmit={handleAcceptInvitation}>
              <TextField
                label="Password"
                type="password"
                fullWidth
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                margin="normal"
                helperText="At least 8 characters"
                error={!!passwordError && passwordError.includes('8 characters')}
              />

              <TextField
                label="Confirm Password"
                type="password"
                fullWidth
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                margin="normal"
                error={!!passwordError && passwordError.includes('do not match')}
              />

              {passwordError && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {passwordError}
                </Alert>
              )}

              {error && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {error}
                </Alert>
              )}

              <Button
                type="submit"
                variant="contained"
                fullWidth
                size="large"
                disabled={validating}
                sx={{
                  mt: 3,
                  backgroundColor: '#003e60',
                  '&:hover': { backgroundColor: '#54475f' },
                }}
              >
                {validating ? <CircularProgress size={24} sx={{ color: '#fff' }} /> : 'Create Account & Get Started'}
              </Button>
            </form>
          </>
        )}
      </Paper>
    </Box>
  );
}
