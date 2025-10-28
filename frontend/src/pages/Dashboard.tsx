import { useState } from 'react';
import { Box, Typography, Grid, Card, CardContent, Paper, CircularProgress, Button, Alert, Snackbar } from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  SentimentSatisfied as SentimentIcon,
  Visibility as VisibilityIcon,
  Label as LabelIcon,
  CloudDownload as CollectionIcon,
  Analytics as AnalysisIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { useBrand } from '../contexts/BrandContext';

interface DashboardMetrics {
  mention_rate: number;
  mention_count: number;
  total_responses: number;
  positive_sentiment: number;
  descriptor_match: number;
  share_of_voice: number;
  change_mention_rate: number;
  change_sentiment: number;
  change_descriptor: number;
  leading_position: string;
}

interface TaskStatus {
  status: string;
  task_type: string;
  progress: number;
  total_items: number;
  processed_items: number;
  message: string;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
}

export default function Dashboard() {
  const queryClient = useQueryClient();
  const { activeBrand } = useBrand();
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' | 'info' }>({
    open: false,
    message: '',
    severity: 'info',
  });
  const [collectionStatus, setCollectionStatus] = useState<'idle' | 'running'>('idle');

  const brandName = activeBrand?.brand_name || 'Your Brand';

  // Fetch task status
  const { data: taskStatus } = useQuery<TaskStatus>({
    queryKey: ['task-status'],
    queryFn: async () => {
      const response = await api.get('/tasks/status/');
      return response.data;
    },
    refetchInterval: (data) => {
      // Poll every 3 seconds if a task is running, otherwise every 30 seconds
      return data?.status === 'running' ? 3000 : 30000;
    },
  });

  // Fetch dashboard metrics
  const { data: metrics, isLoading, error } = useQuery<DashboardMetrics>({
    queryKey: ['dashboard-metrics'],
    queryFn: async () => {
      const response = await api.get('/analytics/dashboard');
      return response.data;
    },
    refetchInterval: 30000, // Auto-refresh every 30 seconds
  });

  // Collection mutation
  const collectionMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post('/tasks/run-collection/');
      return response.data;
    },
    onSuccess: (data) => {
      setCollectionStatus('running');
      setSnackbar({
        open: true,
        message: data.message + ' ' + (data.note || ''),
        severity: 'success',
      });
      // Refresh metrics and check status periodically
      const checkInterval = setInterval(() => {
        queryClient.invalidateQueries({ queryKey: ['dashboard-metrics'] });
        queryClient.invalidateQueries({ queryKey: ['responses'] });
      }, 5000);

      // Assume collection completes after 60 seconds and stop checking
      setTimeout(() => {
        clearInterval(checkInterval);
        setCollectionStatus('idle');
        queryClient.invalidateQueries({ queryKey: ['dashboard-metrics'] });
        queryClient.invalidateQueries({ queryKey: ['responses'] });
        setSnackbar({
          open: true,
          message: 'Collection completed! Dashboard has been updated.',
          severity: 'success',
        });
      }, 60000);
    },
    onError: (error: any) => {
      setSnackbar({
        open: true,
        message: error.response?.data?.detail || 'Failed to start collection',
        severity: 'error',
      });
    },
  });

  // Analysis mutation
  const analysisMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post('/tasks/run-analysis/');
      return response.data;
    },
    onSuccess: (data) => {
      setSnackbar({
        open: true,
        message: data.message + ' ' + (data.note || ''),
        severity: 'info',
      });
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['dashboard-metrics'] });
        queryClient.invalidateQueries({ queryKey: ['responses'] });
      }, 2000);
    },
    onError: (error: any) => {
      setSnackbar({
        open: true,
        message: error.response?.data?.detail || 'Failed to start analysis',
        severity: 'error',
      });
    },
  });

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <Typography variant="h2" gutterBottom color="error">
          Error Loading Dashboard
        </Typography>
        <Typography>
          Unable to load dashboard metrics. Please make sure the backend server is running.
        </Typography>
      </Box>
    );
  }

  if (!metrics) {
    return null;
  }

  // Format change indicators
  const formatChange = (value: number) => {
    if (value === 0) return null;
    const sign = value > 0 ? '↑' : '↓';
    const color = value > 0 ? 'success.main' : 'error.main';
    return (
      <Typography variant="body2" color={color}>
        {sign} {value > 0 ? '+' : ''}{value.toFixed(1)}% vs last period
      </Typography>
    );
  };

  return (
    <Box>
      {/* Task Progress Indicator */}
      {taskStatus && taskStatus.status === 'running' && (
        <Alert severity="info" sx={{ mb: 3 }}>
          <Box display="flex" alignItems="center" gap={2}>
            <CircularProgress size={20} />
            <Box flex={1}>
              <Typography variant="body2" fontWeight="bold">
                {taskStatus.task_type === 'analysis_and_report' ? 'Analysis & Report Generation' : taskStatus.task_type}
              </Typography>
              <Typography variant="caption">
                {taskStatus.message || `Processing ${taskStatus.processed_items} of ${taskStatus.total_items} items...`}
              </Typography>
            </Box>
          </Box>
        </Alert>
      )}

      <Box sx={{ mb: 4 }}>
        <Typography variant="h2" component="h1">
          Key Metrics Dashboard
        </Typography>
      </Box>

      {/* Collection Status Banner */}
      {collectionStatus === 'running' && (
        <Alert severity="info" sx={{ mb: 3 }} icon={<CircularProgress size={20} />}>
          <Typography variant="body1" fontWeight={600}>
            Collection in Progress
          </Typography>
          <Typography variant="body2">
            The system is collecting responses from LLM platforms. This may take a few minutes.
            The dashboard will automatically refresh with new data.
          </Typography>
        </Alert>
      )}

      {/* Show message if no data */}
      {metrics.total_responses === 0 && (
        <Paper sx={{ p: 3, mb: 4, backgroundColor: 'info.light' }}>
          <Typography variant="h6" gutterBottom>
            New to TALES?
          </Typography>
          <Typography>
            Click on <strong>Customize → Brand Info</strong> to begin!
          </Typography>
        </Paper>
      )}

      {/* KPI Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    {brandName} Mentions
                  </Typography>
                  <Typography variant="h4" component="div" color="primary">
                    {metrics.mention_rate}%
                  </Typography>
                  {formatChange(metrics.change_mention_rate)}
                  <Typography variant="caption" color="textSecondary">
                    {metrics.mention_count} of {metrics.total_responses} responses
                  </Typography>
                </Box>
                <TrendingUpIcon sx={{ fontSize: 48, color: 'primary.main', opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Positive Sentiment
                  </Typography>
                  <Typography variant="h4" component="div" color="primary">
                    {metrics.positive_sentiment}%
                  </Typography>
                  {formatChange(metrics.change_sentiment)}
                  <Typography variant="caption" color="textSecondary">
                    Of {brandName} mentions
                  </Typography>
                </Box>
                <SentimentIcon sx={{ fontSize: 48, color: 'success.main', opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Descriptor Match
                  </Typography>
                  <Typography variant="h4" component="div" color="primary">
                    {metrics.descriptor_match}%
                  </Typography>
                  {formatChange(metrics.change_descriptor)}
                  <Typography variant="caption" color="textSecondary">
                    Target descriptors used
                  </Typography>
                </Box>
                <LabelIcon sx={{ fontSize: 48, color: 'info.main', opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Share of Voice
                  </Typography>
                  <Typography variant="h4" component="div" color="primary">
                    {metrics.share_of_voice}%
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    {metrics.leading_position}
                  </Typography>
                </Box>
                <VisibilityIcon sx={{ fontSize: 48, color: 'secondary.main', opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts Section Placeholder */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: 300 }}>
            <Typography variant="h6" gutterBottom>
              Mention Rate Trend
            </Typography>
            <Box
              sx={{
                height: 240,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: 'background.default',
                borderRadius: 1,
              }}
            >
              <Typography color="textSecondary">
                Chart will be added in next phase
              </Typography>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: 300 }}>
            <Typography variant="h6" gutterBottom>
              Sentiment Breakdown
            </Typography>
            <Box
              sx={{
                height: 240,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: 'background.default',
                borderRadius: 1,
              }}
            >
              <Typography color="textSecondary">
                Chart will be added in next phase
              </Typography>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: 300 }}>
            <Typography variant="h6" gutterBottom>
              Share of Voice
            </Typography>
            <Box
              sx={{
                height: 240,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: 'background.default',
                borderRadius: 1,
              }}
            >
              <Typography color="textSecondary">
                Chart will be added in next phase
              </Typography>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: 300 }}>
            <Typography variant="h6" gutterBottom>
              Positioning Distribution
            </Typography>
            <Box
              sx={{
                height: 240,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: 'background.default',
                borderRadius: 1,
              }}
            >
              <Typography color="textSecondary">
                Chart will be added in next phase
              </Typography>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}
