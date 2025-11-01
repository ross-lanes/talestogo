import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Typography,
  Alert,
  CircularProgress,
  Box,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Divider,
} from '@mui/material';
import { Delete as DeleteIcon } from '@mui/icons-material';
import { api } from '../services/api';

interface ShareBrandDialogProps {
  open: boolean;
  onClose: () => void;
  brandId: number;
  brandName: string;
}

interface BrandShare {
  id: number;
  user_email: string;
  user_full_name: string | null;
  shared_by_email: string;
  created_at: string;
}

const ShareBrandDialog: React.FC<ShareBrandDialogProps> = ({
  open,
  onClose,
  brandId,
  brandName,
}) => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sharesLoading, setSharesLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [shares, setShares] = useState<BrandShare[]>([]);

  // Fetch existing shares when dialog opens
  React.useEffect(() => {
    if (open) {
      fetchShares();
    } else {
      // Reset state when dialog closes
      setEmail('');
      setError('');
      setSuccess('');
    }
  }, [open]);

  const fetchShares = async () => {
    setSharesLoading(true);
    try {
      const response = await api.get<BrandShare[]>(`/brands/${brandId}/shares`);
      setShares(response.data);
    } catch (err: any) {
      console.error('Error fetching shares:', err);
      // Don't show error for shares fetch - just set empty array
      setShares([]);
    } finally {
      setSharesLoading(false);
    }
  };

  const handleShare = async () => {
    setError('');
    setSuccess('');

    if (!email.trim()) {
      setError('Please enter an email address');
      return;
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError('Please enter a valid email address');
      return;
    }

    setLoading(true);

    try {
      await api.post(`/brands/${brandId}/share`, { email: email.trim() });
      setSuccess(`Brand successfully shared with ${email}`);
      setEmail('');
      // Refresh the shares list
      await fetchShares();
    } catch (err: any) {
      console.error('Share error:', err);
      setError(err.response?.data?.detail || 'Failed to share brand');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveShare = async (shareId: number, userEmail: string) => {
    try {
      await api.delete(`/brands/${brandId}/shares/${shareId}`);
      setSuccess(`Removed share with ${userEmail}`);
      // Refresh the shares list
      await fetchShares();
    } catch (err: any) {
      console.error('Remove share error:', err);
      setError(err.response?.data?.detail || 'Failed to remove share');
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Share Brand: {brandName}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Share this brand with other TALES users. They will be able to view and edit all queries,
          descriptors, and competitors for this brand.
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

        <TextField
          fullWidth
          label="Email Address"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="user@example.com"
          helperText="Enter the email of a TALES user to share with"
          disabled={loading}
          onKeyPress={(e) => {
            if (e.key === 'Enter') {
              handleShare();
            }
          }}
          sx={{ mb: 3 }}
        />

        <Button
          variant="contained"
          onClick={handleShare}
          disabled={loading || !email.trim()}
          fullWidth
          sx={{ mb: 3 }}
        >
          {loading ? <CircularProgress size={24} /> : 'Share Brand'}
        </Button>

        <Divider sx={{ my: 2 }} />

        <Typography variant="h6" gutterBottom>
          Currently Shared With
        </Typography>

        {sharesLoading ? (
          <Box display="flex" justifyContent="center" py={2}>
            <CircularProgress size={24} />
          </Box>
        ) : shares.length === 0 ? (
          <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
            This brand is not currently shared with anyone.
          </Typography>
        ) : (
          <List>
            {shares.map((share) => (
              <ListItem key={share.id}>
                <ListItemText
                  primary={share.user_email}
                  secondary={share.user_full_name || 'No name set'}
                />
                <ListItemSecondaryAction>
                  <IconButton
                    edge="end"
                    aria-label="remove"
                    onClick={() => handleRemoveShare(share.id, share.user_email)}
                  >
                    <DeleteIcon />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        )}
      </DialogContent>
      <DialogActions sx={{ p: 3 }}>
        <Button onClick={onClose} variant="outlined">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ShareBrandDialog;
