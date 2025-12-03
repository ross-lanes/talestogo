import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  CircularProgress,
  Chip,
  Collapse,
  Alert,
  Button,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Divider,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar,
} from '@mui/material';
import {
  Send as SendIcon,
  Person as PersonIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  ContentCopy as CopyIcon,
  Check as CheckIcon,
  Save as SaveIcon,
  Add as AddIcon,
  History as HistoryIcon,
  Delete as DeleteIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import { api } from '../../services/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  toolCalls?: Array<{ name: string; input: Record<string, unknown> }>;
}

interface ChatResponse {
  response: string;
  tool_calls: Array<{ name: string; input: Record<string, unknown> }>;
  error?: string;
}

interface ConversationSummary {
  id: number;
  title: string;
  summary: string | null;
  message_count: number;
  created_at: string;
  updated_at: string;
}

interface ConversationDetail {
  id: number;
  title: string;
  summary: string | null;
  messages: Array<{
    role: string;
    content: string;
    sequence: number;
    created_at: string;
  }>;
  created_at: string;
  updated_at: string;
}

interface ConversationUsage {
  saved_count: number;
  max_allowed: number;
}

const EXAMPLE_QUESTIONS = [
  'What papers discuss H-mode transitions?',
  'What are the typical ion temperatures in NSTX experiments?',
  'What phenomena are most commonly studied?',
  'Find papers about lithium wall conditioning',
];

const NSTXViewChat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showTools, setShowTools] = useState<number | null>(null);
  const [copied, setCopied] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // Conversation memory state
  const [isSaving, setIsSaving] = useState(false);
  const [conversationUsage, setConversationUsage] = useState<ConversationUsage | null>(null);
  const [savedConversations, setSavedConversations] = useState<ConversationSummary[]>([]);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [loadingConversations, setLoadingConversations] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [conversationToDelete, setConversationToDelete] = useState<number | null>(null);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });

  // Fetch conversation usage on mount
  useEffect(() => {
    fetchConversationUsage();
  }, []);

  const fetchConversationUsage = async () => {
    try {
      const response = await api.get<ConversationUsage>('/nstxview/conversations/usage');
      setConversationUsage(response.data);
    } catch (err) {
      console.error('Failed to fetch conversation usage:', err);
    }
  };

  const fetchSavedConversations = async () => {
    setLoadingConversations(true);
    try {
      const response = await api.get<ConversationSummary[]>('/nstxview/conversations');
      setSavedConversations(response.data);
    } catch (err) {
      console.error('Failed to fetch conversations:', err);
      setSnackbar({ open: true, message: 'Failed to load saved conversations', severity: 'error' });
    } finally {
      setLoadingConversations(false);
    }
  };

  const getLastAssistantMessage = (): string | null => {
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === 'assistant') {
        return messages[i].content;
      }
    }
    return null;
  };

  const handleCopy = async () => {
    const lastMessage = getLastAssistantMessage();
    if (lastMessage) {
      await navigator.clipboard.writeText(lastMessage);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const scrollToBottom = () => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (message?: string) => {
    const messageToSend = message || inputValue.trim();
    if (!messageToSend || isLoading) return;

    const userMessage: Message = { role: 'user', content: messageToSend };
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInputValue('');
    setIsLoading(true);
    setError(null);

    try {
      // Build conversation history for API (exclude the message we just added since it's in 'message')
      const conversationHistory = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const response = await api.post<ChatResponse>('/nstxview/chat', {
        message: messageToSend,
        conversation_history: conversationHistory.length > 0 ? conversationHistory : undefined,
      });

      const data = response.data;

      const assistantMessage: Message = {
        role: 'assistant',
        content: data.response,
        toolCalls: data.tool_calls,
      };

      setMessages((prev) => [...prev, assistantMessage]);

      if (data.error) {
        setError(data.error);
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setError(errorMessage);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, I encountered an error processing your request. Please try again.',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setError(null);
  };

  const handleSaveConversation = async () => {
    if (messages.length < 2) return;

    setIsSaving(true);
    try {
      const messagesToSave = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      await api.post('/nstxview/conversations', {
        messages: messagesToSave,
      });

      setSnackbar({ open: true, message: 'Conversation saved successfully!', severity: 'success' });
      fetchConversationUsage();
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save conversation';
      setSnackbar({ open: true, message: errorMessage, severity: 'error' });
    } finally {
      setIsSaving(false);
    }
  };

  const handleOpenDrawer = () => {
    setDrawerOpen(true);
    fetchSavedConversations();
  };

  const handleLoadConversation = async (conversationId: number) => {
    try {
      const response = await api.get<ConversationDetail>(`/nstxview/conversations/${conversationId}`);
      const loadedMessages: Message[] = response.data.messages.map((m) => ({
        role: m.role as 'user' | 'assistant',
        content: m.content,
      }));
      setMessages(loadedMessages);
      setDrawerOpen(false);
      setSnackbar({ open: true, message: 'Conversation loaded', severity: 'success' });
    } catch (err) {
      setSnackbar({ open: true, message: 'Failed to load conversation', severity: 'error' });
    }
  };

  const handleDeleteClick = (e: React.MouseEvent, conversationId: number) => {
    e.stopPropagation();
    setConversationToDelete(conversationId);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!conversationToDelete) return;

    try {
      await api.delete(`/nstxview/conversations/${conversationToDelete}`);
      setSnackbar({ open: true, message: 'Conversation deleted', severity: 'success' });
      fetchSavedConversations();
      fetchConversationUsage();
    } catch (err) {
      setSnackbar({ open: true, message: 'Failed to delete conversation', severity: 'error' });
    } finally {
      setDeleteDialogOpen(false);
      setConversationToDelete(null);
    }
  };

  const canSave = messages.length >= 2 && conversationUsage && conversationUsage.saved_count < conversationUsage.max_allowed;

  return (
    <Paper sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Box
            component="img"
            src="/RobotRachel Icon.png"
            alt="NSTXView"
            sx={{ width: 36, height: 36 }}
          />
          <Typography
            variant="h5"
            sx={{
              fontWeight: 700,
              letterSpacing: '-0.5px',
            }}
          >
            Ask NSTXView
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {/* Usage indicator */}
          {conversationUsage && (
            <Typography variant="caption" color="text.secondary" sx={{ mr: 1 }}>
              {conversationUsage.saved_count}/{conversationUsage.max_allowed} saved
            </Typography>
          )}

          {/* Saved Conversations button */}
          <Tooltip title="Saved Conversations">
            <IconButton onClick={handleOpenDrawer} size="small">
              <HistoryIcon fontSize="small" />
            </IconButton>
          </Tooltip>

          {/* New Chat button */}
          <Tooltip title="New Chat">
            <IconButton onClick={handleNewChat} size="small" disabled={messages.length === 0}>
              <AddIcon fontSize="small" />
            </IconButton>
          </Tooltip>

          {/* Save button */}
          <Tooltip title={canSave ? 'Save Conversation' : messages.length < 2 ? 'Need at least one exchange to save' : 'Conversation limit reached'}>
            <span>
              <IconButton
                onClick={handleSaveConversation}
                size="small"
                disabled={!canSave || isSaving}
              >
                {isSaving ? <CircularProgress size={18} /> : <SaveIcon fontSize="small" />}
              </IconButton>
            </span>
          </Tooltip>

          {/* Copy button */}
          {messages.some((m) => m.role === 'assistant') && (
            <Tooltip title={copied ? 'Copied!' : 'Copy last answer'}>
              <IconButton
                onClick={handleCopy}
                size="small"
                sx={{
                  color: copied ? 'success.main' : 'text.secondary',
                }}
              >
                {copied ? <CheckIcon fontSize="small" /> : <CopyIcon fontSize="small" />}
              </IconButton>
            </Tooltip>
          )}
        </Box>
      </Box>

      {/* Messages Container */}
      <Box
        ref={messagesContainerRef}
        sx={{
          flexGrow: 1,
          overflowY: 'auto',
          mb: 2,
          minHeight: 200,
          maxHeight: 400,
          bgcolor: 'grey.50',
          borderRadius: 1,
          p: 1,
        }}
      >
        {messages.length === 0 ? (
          <Box sx={{ p: 2, textAlign: 'center' }}>
            <Typography color="textSecondary" sx={{ mb: 2 }}>
              Ask me anything about NSTX/NSTX-U plasma physics research!
            </Typography>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
              Try these example questions:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, justifyContent: 'center' }}>
              {EXAMPLE_QUESTIONS.map((q, i) => (
                <Chip
                  key={i}
                  label={q}
                  size="small"
                  onClick={() => handleSend(q)}
                  sx={{ cursor: 'pointer' }}
                  variant="outlined"
                />
              ))}
            </Box>
          </Box>
        ) : (
          messages.map((msg, index) => (
            <Box
              key={index}
              sx={{
                display: 'flex',
                gap: 1,
                mb: 2,
                flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
              }}
            >
              <Box
                sx={{
                  width: 32,
                  height: 32,
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  bgcolor: msg.role === 'user' ? 'primary.main' : 'grey.300',
                  color: msg.role === 'user' ? 'white' : 'text.primary',
                  flexShrink: 0,
                }}
              >
                {msg.role === 'user' ? (
                  <PersonIcon fontSize="small" />
                ) : (
                  <Box
                    component="img"
                    src="/RobotRachel Icon.png"
                    alt="NSTXView"
                    sx={{ width: 24, height: 24 }}
                  />
                )}
              </Box>
              <Box
                sx={{
                  maxWidth: '80%',
                  bgcolor: msg.role === 'user' ? 'primary.main' : 'white',
                  color: msg.role === 'user' ? 'white' : 'text.primary',
                  p: 1.5,
                  borderRadius: 2,
                  boxShadow: 1,
                }}
              >
                {msg.role === 'assistant' ? (
                  <Box sx={{ '& p': { m: 0 }, '& ul, & ol': { pl: 2, m: 0 } }}>
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </Box>
                ) : (
                  <Typography variant="body2">{msg.content}</Typography>
                )}

                {/* Tool calls indicator */}
                {msg.toolCalls && msg.toolCalls.length > 0 && (
                  <Box sx={{ mt: 1 }}>
                    <Box
                      onClick={() => setShowTools(showTools === index ? null : index)}
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        cursor: 'pointer',
                        color: 'text.secondary',
                        fontSize: '0.75rem',
                      }}
                    >
                      <Typography variant="caption">
                        Used {msg.toolCalls.length} tool{msg.toolCalls.length > 1 ? 's' : ''}
                      </Typography>
                      {showTools === index ? (
                        <ExpandLessIcon fontSize="small" />
                      ) : (
                        <ExpandMoreIcon fontSize="small" />
                      )}
                    </Box>
                    <Collapse in={showTools === index}>
                      <Box sx={{ mt: 1 }}>
                        {msg.toolCalls.map((tool, i) => (
                          <Chip
                            key={i}
                            label={tool.name}
                            size="small"
                            variant="outlined"
                            sx={{ mr: 0.5, mb: 0.5, fontSize: '0.7rem' }}
                          />
                        ))}
                      </Box>
                    </Collapse>
                  </Box>
                )}
              </Box>
            </Box>
          ))
        )}

        {/* Loading indicator */}
        {isLoading && (
          <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
            <Box
              sx={{
                width: 32,
                height: 32,
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                bgcolor: 'grey.300',
              }}
            >
              <Box
                component="img"
                src="/RobotRachel Icon.png"
                alt="NSTXView"
                sx={{ width: 24, height: 24 }}
              />
            </Box>
            <Box
              sx={{
                bgcolor: 'white',
                p: 1.5,
                borderRadius: 2,
                boxShadow: 1,
                display: 'flex',
                alignItems: 'center',
                gap: 1,
              }}
            >
              <CircularProgress size={16} />
              <Typography variant="body2" color="textSecondary">
                Searching database...
              </Typography>
            </Box>
          </Box>
        )}

        <div ref={messagesEndRef} />
      </Box>

      {/* Error alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 1 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Input */}
      <Box
        sx={{
          display: 'flex',
          gap: 1,
          p: 0.5,
          borderRadius: 2,
          background: '#764ba2',
        }}
      >
        <TextField
          fullWidth
          placeholder="Ask a question about NSTX/NSTX-U research..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isLoading}
          size="small"
          multiline
          maxRows={3}
          sx={{
            bgcolor: 'white',
            borderRadius: 1.5,
            '& .MuiOutlinedInput-root': {
              '& fieldset': {
                border: 'none',
              },
            },
          }}
        />
        <IconButton
          onClick={() => handleSend()}
          disabled={!inputValue.trim() || isLoading}
          sx={{
            bgcolor: 'white',
            borderRadius: 1.5,
            '&:hover': {
              bgcolor: 'grey.100',
            },
            '&.Mui-disabled': {
              bgcolor: 'white',
            },
          }}
        >
          <SendIcon sx={{ color: '#667eea' }} />
        </IconButton>
      </Box>

      {/* Saved Conversations Drawer */}
      <Drawer anchor="right" open={drawerOpen} onClose={() => setDrawerOpen(false)}>
        <Box sx={{ width: 350, p: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6">Saved Conversations</Typography>
            <IconButton onClick={() => setDrawerOpen(false)} size="small">
              <CloseIcon />
            </IconButton>
          </Box>
          <Divider sx={{ mb: 2 }} />

          {loadingConversations ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : savedConversations.length === 0 ? (
            <Typography color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
              No saved conversations yet.
              <br />
              Start a chat and click Save to keep it.
            </Typography>
          ) : (
            <List disablePadding>
              {savedConversations.map((conv) => (
                <ListItem key={conv.id} disablePadding sx={{ mb: 1 }}>
                  <ListItemButton
                    onClick={() => handleLoadConversation(conv.id)}
                    sx={{
                      border: '1px solid',
                      borderColor: 'grey.200',
                      borderRadius: 1,
                      '&:hover': {
                        borderColor: 'primary.main',
                      },
                    }}
                  >
                    <ListItemText
                      primary={conv.title}
                      secondary={
                        <>
                          {conv.summary && (
                            <Typography variant="caption" component="span" display="block" color="text.secondary">
                              {conv.summary}
                            </Typography>
                          )}
                          <Typography variant="caption" color="text.secondary">
                            {conv.message_count} messages • {new Date(conv.created_at).toLocaleDateString()}
                          </Typography>
                        </>
                      }
                      slotProps={{ primary: { fontWeight: 500, fontSize: '0.9rem' } }}
                    />
                    <IconButton
                      edge="end"
                      size="small"
                      onClick={(e) => handleDeleteClick(e, conv.id)}
                      sx={{ color: 'error.main', ml: 1 }}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          )}
        </Box>
      </Drawer>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Conversation?</DialogTitle>
        <DialogContent>
          <Typography>
            This will permanently delete this saved conversation. This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Paper>
  );
};

export default NSTXViewChat;
