import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Card,
  CardContent,
  Grid,
  LinearProgress,
  Chip,
  CircularProgress,
  Alert,
  Button,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  CloudSync as SyncIcon,
  PlayArrow as StartIcon,
  Description as PaperIcon,
  CheckCircle as CompletedIcon,
  Error as ErrorIcon,
  HourglassEmpty as PendingIcon,
  Loop as ProcessingIcon,
} from '@mui/icons-material';

const API_BASE = import.meta.env.VITE_API_URL || '';

interface ProcessingStatusData {
  total_papers: number;
  pending: number;
  processing: number;
  completed: number;
  error: number;
  active_task: {
    id: number;
    type: string;
    total_items: number;
    processed_items: number;
    message: string;
    started_at: string;
  } | null;
}

const ProcessingStatus: React.FC = () => {
  const [status, setStatus] = useState<ProcessingStatusData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('tales_access_token');
      const response = await fetch(`${API_BASE}/nstxview/processing/status`, {
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch processing status');
      }

      const data = await response.json();
      setStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    // Auto-refresh every 10 seconds if there's an active task
    const interval = setInterval(() => {
      if (status?.active_task) {
        fetchStatus();
      }
    }, 10000);

    return () => clearInterval(interval);
  }, [status?.active_task]);

  const handleSync = async () => {
    try {
      setActionLoading(true);
      setActionMessage(null);
      setError(null);

      const token = localStorage.getItem('tales_access_token');
      const response = await fetch(`${API_BASE}/nstxview/processing/sync`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to start sync');
      }

      const data = await response.json();
      setActionMessage(data.message);
      fetchStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start sync');
    } finally {
      setActionLoading(false);
    }
  };

  const handleStartExtraction = async () => {
    try {
      setActionLoading(true);
      setActionMessage(null);
      setError(null);

      const token = localStorage.getItem('tales_access_token');
      const response = await fetch(`${API_BASE}/nstxview/processing/extract`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to start extraction');
      }

      const data = await response.json();
      setActionMessage(data.message);
      fetchStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start extraction');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading && !status) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  const completionPercentage = status
    ? Math.round((status.completed / status.total_papers) * 100) || 0
    : 0;

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
            Processing Status
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Monitor and control paper processing pipeline
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchStatus}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Action Message */}
      {actionMessage && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setActionMessage(null)}>
          {actionMessage}
        </Alert>
      )}

      {status && (
        <>
          {/* Active Task Banner */}
          {status.active_task && (
            <Paper sx={{ p: 2, mb: 3, bgcolor: 'primary.light', color: 'primary.contrastText' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                <ProcessingIcon />
                <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                  Task in Progress: {status.active_task.type}
                </Typography>
              </Box>
              <Typography variant="body2" sx={{ mb: 1 }}>
                {status.active_task.message}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <LinearProgress
                  variant="determinate"
                  value={
                    (status.active_task.processed_items / status.active_task.total_items) * 100
                  }
                  sx={{ flex: 1, height: 8, borderRadius: 4 }}
                />
                <Typography variant="body2">
                  {status.active_task.processed_items} / {status.active_task.total_items}
                </Typography>
              </Box>
            </Paper>
          )}

          {/* Overall Progress */}
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Overall Progress
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <LinearProgress
                variant="determinate"
                value={completionPercentage}
                sx={{ flex: 1, height: 16, borderRadius: 8 }}
              />
              <Typography variant="h6" sx={{ minWidth: 60 }}>
                {completionPercentage}%
              </Typography>
            </Box>
            <Typography variant="body2" color="textSecondary">
              {status.completed} of {status.total_papers} papers fully processed
            </Typography>
          </Paper>

          {/* Status Cards */}
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={6} sm={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <PaperIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                  <Typography variant="h4">{status.total_papers}</Typography>
                  <Typography variant="body2" color="textSecondary">
                    Total Papers
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <PendingIcon sx={{ fontSize: 40, color: 'grey.500', mb: 1 }} />
                  <Typography variant="h4">{status.pending}</Typography>
                  <Typography variant="body2" color="textSecondary">
                    Pending
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <CompletedIcon sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
                  <Typography variant="h4">{status.completed}</Typography>
                  <Typography variant="body2" color="textSecondary">
                    Completed
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <ErrorIcon sx={{ fontSize: 40, color: 'error.main', mb: 1 }} />
                  <Typography variant="h4">{status.error}</Typography>
                  <Typography variant="body2" color="textSecondary">
                    Errors
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Actions */}
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Actions
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <List>
              <ListItem
                secondaryAction={
                  <Button
                    variant="contained"
                    startIcon={<SyncIcon />}
                    onClick={handleSync}
                    disabled={actionLoading || !!status.active_task}
                  >
                    Sync
                  </Button>
                }
              >
                <ListItemIcon>
                  <SyncIcon />
                </ListItemIcon>
                <ListItemText
                  primary="Sync with Google Drive"
                  secondary="Check for new papers and add them to the processing queue"
                />
              </ListItem>
              <ListItem
                secondaryAction={
                  <Button
                    variant="contained"
                    color="secondary"
                    startIcon={<StartIcon />}
                    onClick={handleStartExtraction}
                    disabled={actionLoading || !!status.active_task || status.pending === 0}
                  >
                    Start
                  </Button>
                }
              >
                <ListItemIcon>
                  <StartIcon />
                </ListItemIcon>
                <ListItemText
                  primary="Start Extraction"
                  secondary={`Process ${status.pending} pending papers - extract text, metadata, and structured data`}
                />
              </ListItem>
            </List>
          </Paper>

          {/* Processing Details */}
          <Paper sx={{ p: 3, mt: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Processing Pipeline
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                  Pipeline Stages
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemIcon>
                      <Chip label="1" size="small" />
                    </ListItemIcon>
                    <ListItemText primary="Download PDF from Google Drive" />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <Chip label="2" size="small" />
                    </ListItemIcon>
                    <ListItemText primary="Extract text using PyMuPDF" />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <Chip label="3" size="small" />
                    </ListItemIcon>
                    <ListItemText primary="Extract metadata (title, authors, DOI)" />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <Chip label="4" size="small" />
                    </ListItemIcon>
                    <ListItemText primary="Extract shots, parameters, phenomena using Claude" />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <Chip label="5" size="small" />
                    </ListItemIcon>
                    <ListItemText primary="Generate embeddings for semantic search" />
                  </ListItem>
                </List>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                  Status Legend
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip label="pending" size="small" />
                    <Typography variant="body2">Waiting to be processed</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip label="downloading" size="small" color="primary" />
                    <Typography variant="body2">Downloading from Drive</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip label="extracting_text" size="small" color="primary" />
                    <Typography variant="body2">Extracting text from PDF</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip label="extracting_data" size="small" color="primary" />
                    <Typography variant="body2">Extracting structured data</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip label="completed" size="small" color="success" />
                    <Typography variant="body2">Fully processed</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip label="error" size="small" color="error" />
                    <Typography variant="body2">Processing failed</Typography>
                  </Box>
                </Box>
              </Grid>
            </Grid>
          </Paper>
        </>
      )}
    </Box>
  );
};

export default ProcessingStatus;
