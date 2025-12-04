import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  IconButton,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Divider,
} from '@mui/material';
import {
  Delete as DeleteIcon,
  Chat as ChatIcon,
  Forum as ForumIcon,
} from '@mui/icons-material';
import { api } from '../../services/api';

interface ConversationSummary {
  id: number;
  title: string;
  summary: string | null;
  message_count: number;
  created_at: string;
  updated_at: string;
}

interface ConversationUsage {
  saved_count: number;
  max_allowed: number;
}

const NSTXViewConversations: React.FC = () => {
  const navigate = useNavigate();
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [usage, setUsage] = useState<ConversationUsage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [conversationToDelete, setConversationToDelete] = useState<ConversationSummary | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [conversationsRes, usageRes] = await Promise.all([
        api.get<ConversationSummary[]>('/nstxview/conversations'),
        api.get<ConversationUsage>('/nstxview/conversations/usage'),
      ]);
      setConversations(conversationsRes.data);
      setUsage(usageRes.data);
    } catch (err) {
      setError('Failed to load saved conversations');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadConversation = (conversationId: number) => {
    // Navigate to dashboard with conversation ID as query param
    navigate(`/nstxview?conversation=${conversationId}`);
  };

  const handleDeleteClick = (e: React.MouseEvent, conversation: ConversationSummary) => {
    e.stopPropagation();
    setConversationToDelete(conversation);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!conversationToDelete) return;

    setDeleting(true);
    try {
      await api.delete(`/nstxview/conversations/${conversationToDelete.id}`);
      setConversations((prev) => prev.filter((c) => c.id !== conversationToDelete.id));
      if (usage) {
        setUsage({ ...usage, saved_count: usage.saved_count - 1 });
      }
    } catch (err) {
      setError('Failed to delete conversation');
    } finally {
      setDeleting(false);
      setDeleteDialogOpen(false);
      setConversationToDelete(null);
    }
  };

  return (
    <Box>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            Saved Conversations
          </Typography>
          {usage && (
            <Typography variant="body2" color="text.secondary">
              {usage.saved_count} of {usage.max_allowed} conversations saved
            </Typography>
          )}
        </Box>
        <Typography variant="body2" color="text.secondary">
          Your saved research conversations with Ask NSTXView. Click on a conversation to continue where you left off.
        </Typography>
      </Paper>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      ) : conversations.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <ChatIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No saved conversations yet
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Start a chat with Ask NSTXView on the Dashboard and click the Save button to keep your research conversations.
          </Typography>
          <Button variant="contained" onClick={() => navigate('/nstxview')}>
            Go to Dashboard
          </Button>
        </Paper>
      ) : (
        <Paper>
          <List disablePadding>
            {conversations.map((conv, index) => (
              <React.Fragment key={conv.id}>
                {index > 0 && <Divider />}
                <ListItem disablePadding>
                  <ListItemButton
                    onClick={() => handleLoadConversation(conv.id)}
                    sx={{ py: 2 }}
                  >
                    <ForumIcon
                      sx={{
                        mr: 2,
                        color: 'primary.main',
                        fontSize: 28,
                      }}
                    />
                    <ListItemText
                      primary={conv.title}
                      secondary={
                        <Box component="span">
                          {conv.summary && (
                            <Typography
                              variant="body2"
                              color="text.secondary"
                              component="span"
                              sx={{ display: 'block', mb: 0.5 }}
                            >
                              {conv.summary}
                            </Typography>
                          )}
                          <Typography variant="caption" color="text.secondary" component="span">
                            {conv.message_count} messages &bull; Created{' '}
                            {new Date(conv.created_at).toLocaleDateString()} &bull; Updated{' '}
                            {new Date(conv.updated_at).toLocaleDateString()}
                          </Typography>
                        </Box>
                      }
                      slotProps={{
                        primary: { sx: { fontWeight: 500, fontSize: '1rem' } },
                      }}
                    />
                    <IconButton
                      edge="end"
                      onClick={(e) => handleDeleteClick(e, conv)}
                      sx={{ color: 'error.main', ml: 2 }}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </ListItemButton>
                </ListItem>
              </React.Fragment>
            ))}
          </List>
        </Paper>
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Conversation?</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete "{conversationToDelete?.title}"? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)} disabled={deleting}>
            Cancel
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            color="error"
            variant="contained"
            disabled={deleting}
          >
            {deleting ? <CircularProgress size={20} /> : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default NSTXViewConversations;
