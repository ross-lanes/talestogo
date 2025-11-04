import { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  Alert,
  Snackbar,
  CircularProgress,
} from '@mui/material';
import { HelpOutline as HelpIcon, Send as SendIcon } from '@mui/icons-material';
import { useMutation } from '@tanstack/react-query';
import { api } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

export default function Help() {
  const { user } = useAuth();
  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'info' as 'success' | 'error' | 'info',
  });

  const sendHelpMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post('/help/contact', {
        subject,
        message,
      });
      return response.data;
    },
    onSuccess: () => {
      setSnackbar({
        open: true,
        message: 'Your message has been sent successfully! We\'ll get back to you soon.',
        severity: 'success',
      });
      setSubject('');
      setMessage('');
    },
    onError: (error: any) => {
      setSnackbar({
        open: true,
        message: error.response?.data?.detail || 'Failed to send message. Please try again.',
        severity: 'error',
      });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!subject.trim() || !message.trim()) {
      setSnackbar({
        open: true,
        message: 'Please fill in both subject and message fields.',
        severity: 'error',
      });
      return;
    }
    sendHelpMutation.mutate();
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 4 }}>
        <HelpIcon sx={{ fontSize: 40, mr: 2, color: 'primary.main' }} />
        <Box>
          <Typography variant="h2" component="h1">
            Help & Support
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mt: 1 }}>
            Have a question or need assistance? Send us a message and we'll get back to you shortly.
          </Typography>
        </Box>
      </Box>

      <Paper sx={{ p: 4, maxWidth: 800 }}>
        <form onSubmit={handleSubmit}>
          <Box sx={{ mb: 3 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Signed in as: <strong>{user?.email}</strong>
            </Typography>
          </Box>

          <TextField
            fullWidth
            label="Subject"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="Brief description of your question or issue"
            sx={{ mb: 3 }}
            required
          />

          <TextField
            fullWidth
            label="Message"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Please provide details about your question or issue..."
            multiline
            rows={8}
            sx={{ mb: 3 }}
            required
          />

          <Button
            type="submit"
            variant="contained"
            size="large"
            startIcon={sendHelpMutation.isPending ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
            disabled={sendHelpMutation.isPending}
            sx={{
              backgroundColor: '#80A1D4',
              '&:hover': {
                backgroundColor: '#6B8BC0',
              },
            }}
          >
            {sendHelpMutation.isPending ? 'Sending...' : 'Send Message'}
          </Button>
        </form>

        <Box sx={{ mt: 4, pt: 3, borderTop: '1px solid #e0e0e0' }}>
          <Typography variant="h6" gutterBottom>
            Common Questions
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            • How do I set up automated monthly reports?
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            • What AI platforms does TALES collect data from?
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            • How can I add more competitors to track?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            For detailed documentation, visit the{' '}
            <a href="/how-tales-works" style={{ color: '#80A1D4', textDecoration: 'none' }}>
              How TALES Works
            </a>{' '}
            page.
          </Typography>
        </Box>
      </Paper>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert severity={snackbar.severity}>{snackbar.message}</Alert>
      </Snackbar>
    </Box>
  );
}
