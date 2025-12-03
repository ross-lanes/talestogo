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
} from '@mui/material';
import {
  Send as SendIcon,
  Person as PersonIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  ContentCopy as CopyIcon,
  Check as CheckIcon,
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
    // Scroll within the container only, not the whole page
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
    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.post<ChatResponse>('/nstxview/chat', {
        message: messageToSend,
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

  return (
    <Paper sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
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
        {messages.some(m => m.role === 'assistant') && (
          <IconButton
            onClick={handleCopy}
            size="small"
            title={copied ? 'Copied!' : 'Copy last answer'}
            sx={{
              color: copied ? 'success.main' : 'text.secondary',
              '&:hover': { bgcolor: 'grey.100' },
            }}
          >
            {copied ? <CheckIcon fontSize="small" /> : <CopyIcon fontSize="small" />}
          </IconButton>
        )}
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
    </Paper>
  );
};

export default NSTXViewChat;
