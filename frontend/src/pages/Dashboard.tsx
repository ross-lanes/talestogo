import { useState, useEffect, useRef } from 'react';
import { Box, Typography, Grid, Card, CardContent, Paper, CircularProgress, Button, Alert, Snackbar, Table, TableBody, TableCell, TableRow, IconButton } from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  SentimentSatisfied as SentimentIcon,
  Visibility as VisibilityIcon,
  Label as LabelIcon,
  CloudDownload as CollectionIcon,
  Analytics as AnalysisIcon,
  Warning as WarningIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';
import html2canvas from 'html2canvas';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { useNavigate } from 'react-router-dom';
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
  leadership_visibility?: number;
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
  const navigate = useNavigate();
  const { activeBrand } = useBrand();
  const dashboardRef = useRef<HTMLDivElement>(null);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' | 'info' }>({
    open: false,
    message: '',
    severity: 'info',
  });
  const [collectionStatus, setCollectionStatus] = useState<'idle' | 'running'>('idle');

  const brandName = activeBrand?.brand_name || 'Your Brand';

  // Function to download dashboard as PNG
  const handleDownloadDashboard = async () => {
    if (dashboardRef.current) {
      try {
        // Add a small delay to ensure all content is rendered
        await new Promise(resolve => setTimeout(resolve, 100));

        const canvas = await html2canvas(dashboardRef.current, {
          backgroundColor: '#ffffff',
          scale: 2, // Higher quality
          allowTaint: true,
          useCORS: true,
          scrollY: -window.scrollY,
          scrollX: -window.scrollX,
        });

        // Format date as MM_DD_YYYY
        const now = new Date();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const year = now.getFullYear();
        const dateStr = `${month}_${day}_${year}`;

        // Format brand name (replace spaces with underscores, remove special chars)
        const brandNameFormatted = brandName.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_]/g, '');

        const link = document.createElement('a');
        link.download = `${brandNameFormatted}_TalesDashboard_${dateStr}.png`;
        link.href = canvas.toDataURL('image/png');
        link.click();
      } catch (error) {
        console.error('Error generating dashboard screenshot:', error);
        setSnackbar({
          open: true,
          message: 'Failed to download dashboard',
          severity: 'error',
        });
      }
    }
  };

  // Query to check if user has any brand info at all
  const { data: brandList } = useQuery({
    queryKey: ['brand-list'],
    queryFn: async () => {
      const response = await api.get('/brand-info/');
      return response.data;
    },
  });


  // Fetch task status
  const { data: taskStatus } = useQuery<TaskStatus>({
    queryKey: ['task-status'],
    queryFn: async () => {
      const response = await api.get('/tasks/status/');
      return response.data;
    },
    refetchInterval: (data: any) => {
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

  // Fetch sentiment breakdown
  const { data: sentimentData } = useQuery({
    queryKey: ['sentiment-breakdown'],
    queryFn: async () => {
      const response = await api.get('/analytics/sentiment/breakdown');
      return response.data;
    },
  });

  // Fetch share of voice
  const { data: shareOfVoice } = useQuery({
    queryKey: ['share-of-voice-dashboard'],
    queryFn: async () => {
      const response = await api.get('/analytics/share-of-voice');
      return response.data;
    },
  });

  // Fetch positioning data
  const { data: positioningData } = useQuery({
    queryKey: ['positioning-dashboard'],
    queryFn: async () => {
      const response = await api.get('/analytics/positioning/breakdown');
      return response.data;
    },
  });

  // Fetch responses for threat calculation
  const { data: responses } = useQuery({
    queryKey: ['responses-dashboard'],
    queryFn: async () => {
      const response = await api.get('/responses/');
      return response.data;
    },
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

  // Calculate competitor threats
  const competitors = Array.isArray(shareOfVoice) ? shareOfVoice.filter((item: any) => !item.is_brand) : [];
  const competitorThreats = competitors.map((comp: any) => {
    const competitiveResponses = Array.isArray(responses) ? responses.filter((r: any) =>
      r.competitors && r.competitors.includes(comp.organization)
    ) : [];

    const negativeWhenCompetitorPresent = competitiveResponses.filter((r: any) =>
      r.sentiment === 'Negative' || r.sentiment === 'Very Negative'
    ).length;

    const positiveCompetitor = competitiveResponses.filter((r: any) =>
      r.sentiment === 'Positive' || r.sentiment === 'Very Positive'
    ).length;

    const threatScore = (comp.total_mentions || 0) * 0.7 +
                        negativeWhenCompetitorPresent * 2 +
                        positiveCompetitor * 1.5;

    return {
      name: comp.organization,
      threatScore: Math.round(threatScore),
      threatLevel: threatScore > 50 ? 'High' : threatScore > 20 ? 'Medium' : 'Low'
    };
  });

  const highThreatCount = competitorThreats.filter(c => c.threatLevel === 'High').length;
  const mediumThreatCount = competitorThreats.filter(c => c.threatLevel === 'Medium').length;

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

      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h2" component="h1">
          Key Metrics Dashboard
        </Typography>
        <Button
          variant="outlined"
          startIcon={<DownloadIcon />}
          onClick={handleDownloadDashboard}
          size="small"
        >
          Download Dashboard as Image
        </Button>
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

      {/* Dashboard Content Wrapper for Screenshot */}
      <Box ref={dashboardRef} sx={{ p: 2 }}>
        {/* Show message if no data */}
        {metrics.total_responses === 0 && (
          <Paper sx={{ p: 3, mb: 4, backgroundColor: 'info.light' }}>
            <Typography variant="h6" gutterBottom>
              New to TALES?
            </Typography>
            <Typography>
              Click on the <strong>Add Brand</strong> button to begin!
            </Typography>
          </Paper>
        )}

        {/* KPI Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%', border: '1px solid #e0e0e0', boxShadow: 'none' }}>
            <CardContent sx={{ height: '100%' }}>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Brand Mentions
                  </Typography>
                  <Typography variant="h4" component="div" color="primary">
                    {metrics.mention_rate}%
                  </Typography>
                  {formatChange(metrics.change_mention_rate)}
                </Box>
                <TrendingUpIcon sx={{
                  fontSize: 48,
                  color: metrics.change_mention_rate > 0 ? '#58A13B' : metrics.change_mention_rate < 0 ? '#EA4A4A' : '#665775'
                }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%', border: '1px solid #e0e0e0', boxShadow: 'none' }}>
            <CardContent sx={{ height: '100%' }}>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Threats Summary
                  </Typography>
                  <Typography variant="h4" component="div" color="primary">
                    {highThreatCount}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    High threat competitors
                  </Typography>
                </Box>
                <WarningIcon sx={{ fontSize: 48, color: '#EA4A4A' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%', border: '1px solid #e0e0e0', boxShadow: 'none' }}>
            <CardContent sx={{ height: '100%' }}>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Target Descriptor Adoption
                  </Typography>
                  <Typography variant="h4" component="div" color="primary">
                    {metrics.descriptor_match}%
                  </Typography>
                  {formatChange(metrics.change_descriptor)}
                </Box>
                <LabelIcon sx={{ fontSize: 48, color: '#80A1D4' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%', border: '1px solid #e0e0e0', boxShadow: 'none' }}>
            <CardContent sx={{ height: '100%' }}>
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
                  <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mt: 0.5 }}>
                    {metrics.leadership_visibility}% Leadership Visibility
                  </Typography>
                </Box>
                <VisibilityIcon sx={{ fontSize: 48, color: '#665775' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts Section */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: 300, border: '1px solid #e0e0e0', boxShadow: 'none' }}>
            <Typography variant="h6" gutterBottom>
              Sentiment Breakdown
            </Typography>
            {sentimentData && sentimentData.total > 0 ? (
              <Box sx={{ display: 'flex', alignItems: 'center', height: 240 }}>
                {/* Legend on the left */}
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mr: 2 }}>
                  {[
                    { name: 'Very Positive', value: sentimentData.very_positive_pct || 0, color: '#58A13B' },
                    { name: 'Positive', value: sentimentData.positive_pct || 0, color: '#B2C9AB' },
                    { name: 'Neutral', value: sentimentData.neutral_pct || 0, color: '#9FA8DA' },
                    { name: 'Mixed', value: sentimentData.mixed_pct || 0, color: '#75C9C8' },
                    { name: 'Negative', value: sentimentData.negative_pct || 0, color: '#E04320' },
                  ].filter(item => item.value > 0).map((item) => (
                    <Box key={item.name} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box sx={{ width: 16, height: 16, backgroundColor: item.color, borderRadius: '2px' }} />
                      <Typography variant="body2" sx={{ fontSize: '13px' }}>
                        {item.name}: {item.value}%
                      </Typography>
                    </Box>
                  ))}
                </Box>
                {/* Pie chart on the right */}
                <ResponsiveContainer width="100%" height={240}>
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Very Positive', value: sentimentData.very_positive_pct || 0, fill: '#58A13B' },
                        { name: 'Positive', value: sentimentData.positive_pct || 0, fill: '#B2C9AB' },
                        { name: 'Neutral', value: sentimentData.neutral_pct || 0, fill: '#9FA8DA' },
                        { name: 'Mixed', value: sentimentData.mixed_pct || 0, fill: '#75C9C8' },
                        { name: 'Negative', value: sentimentData.negative_pct || 0, fill: '#E04320' },
                      ].filter(item => item.value > 0)}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      dataKey="value"
                    >
                    </Pie>
                    <Tooltip formatter={(value) => `${value}%`} />
                  </PieChart>
                </ResponsiveContainer>
              </Box>
            ) : (
              <Box sx={{ height: 240, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Typography color="textSecondary">No sentiment data available</Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: 300, border: '1px solid #e0e0e0', boxShadow: 'none' }}>
            <Typography variant="h6" gutterBottom>
              Positioning Distribution
            </Typography>
            {positioningData && positioningData.total > 0 ? (
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={[
                  { position: 'Leader', count: positioningData.leader || 0, fill: '#B2C9AB' },
                  { position: 'Top 3', count: positioningData.top_3 || 0, fill: '#44809C' },
                  { position: 'Featured', count: positioningData.featured || 0, fill: '#75C9C8' },
                  { position: 'Listed', count: positioningData.listed || 0, fill: '#80A1D4' },
                  { position: 'Not Mentioned', count: positioningData.not_mentioned || 0, fill: '#665775' },
                ].filter(item => item.count > 0)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="position" angle={-45} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count">
                    {[
                      { position: 'Leader', count: positioningData.leader || 0, fill: '#B2C9AB' },
                      { position: 'Top 3', count: positioningData.top_3 || 0, fill: '#44809C' },
                      { position: 'Featured', count: positioningData.featured || 0, fill: '#75C9C8' },
                      { position: 'Listed', count: positioningData.listed || 0, fill: '#80A1D4' },
                      { position: 'Not Mentioned', count: positioningData.not_mentioned || 0, fill: '#665775' },
                    ].filter(item => item.count > 0).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <Box sx={{ height: 240, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Typography color="textSecondary">No positioning data available</Typography>
              </Box>
            )}
          </Paper>
        </Grid>

      </Grid>
      </Box>

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
