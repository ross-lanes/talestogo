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
import { PieChart, Pie, Cell, Tooltip, Legend, BarChart, Bar, XAxis, YAxis, CartesianGrid, LabelList } from 'recharts';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { useBrand } from '../contexts/BrandContext';
import { useTaskStatus } from '../contexts/TaskStatusContext';
import BatchSelector from '../components/BatchSelector';
import { captureAndUploadCharts } from '../utils/chartCapture';
import ChartContainer from '../components/ChartContainer';

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

export default function Dashboard() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { activeBrand } = useBrand();
  const { tasks } = useTaskStatus();
  const dashboardRef = useRef<HTMLDivElement>(null);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' | 'info' }>({
    open: false,
    message: '',
    severity: 'info',
  });
  const [collectionStatus, setCollectionStatus] = useState<'idle' | 'running'>('idle');
  const [selectedBatchId, setSelectedBatchId] = useState<number | null>(null);
  const [dismissedTaskId, setDismissedTaskId] = useState<number | null>(null);

  const brandName = activeBrand?.brand_name || 'Your Brand';

  // Reset selectedBatchId when brand changes
  useEffect(() => {
    setSelectedBatchId(null);
  }, [activeBrand?.id]);

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
        link.download = `KeyMetrics_${brandNameFormatted}_${dateStr}.png`;
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


  // REMOVED: Redundant task status polling - now handled by TaskStatusContext
  // This was causing database connection pool exhaustion by polling every 3-30 seconds
  // TaskStatusContext already provides global task status with optimized polling

  // Fetch dashboard metrics
  const { data: metrics, isLoading, error } = useQuery<DashboardMetrics>({
    queryKey: ['dashboard-metrics', selectedBatchId],
    queryFn: async () => {
      const params = selectedBatchId ? { batch_id: selectedBatchId } : {};
      const response = await api.get('/analytics/dashboard', { params });
      return response.data;
    },
    // REMOVED refetchInterval - was causing unnecessary polling
  });

  // Fetch sentiment breakdown
  const { data: sentimentData } = useQuery({
    queryKey: ['sentiment-breakdown', selectedBatchId],
    queryFn: async () => {
      const params = selectedBatchId ? { batch_id: selectedBatchId } : {};
      const response = await api.get('/analytics/sentiment/breakdown', { params });
      return response.data;
    },
  });

  // Fetch share of voice
  const { data: shareOfVoice } = useQuery({
    queryKey: ['share-of-voice-dashboard', selectedBatchId],
    queryFn: async () => {
      const params = selectedBatchId ? { batch_id: selectedBatchId } : {};
      const response = await api.get('/analytics/share-of-voice', { params });
      return response.data;
    },
  });

  // Fetch positioning data
  const { data: positioningData } = useQuery({
    queryKey: ['positioning-dashboard', selectedBatchId],
    queryFn: async () => {
      const params = selectedBatchId ? { batch_id: selectedBatchId } : {};
      const response = await api.get('/analytics/positioning/breakdown', { params });
      return response.data;
    },
  });

  // Fetch competitor threats (calculated server-side)
  const { data: competitorThreats } = useQuery({
    queryKey: ['competitor-threats-dashboard', selectedBatchId],
    queryFn: async () => {
      const params = selectedBatchId ? { batch_id: selectedBatchId } : {};
      const response = await api.get('/analytics/competitor-threats', { params });
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
    onSuccess: async (data) => {
      setSnackbar({
        open: true,
        message: data.message + ' ' + (data.note || ''),
        severity: 'info',
      });

      // Wait for charts to render
      setTimeout(async () => {
        queryClient.invalidateQueries({ queryKey: ['dashboard-metrics'] });
        queryClient.invalidateQueries({ queryKey: ['responses'] });

        // Automatically capture and upload charts for report generation
        try {
          console.log('📸 Auto-capturing charts after analysis...');
          const result = await captureAndUploadCharts(
            {
              dashboard: 'dashboard-main',
              sentiment: 'dashboard-sentiment-chart',
              positioning: 'dashboard-positioning-chart',
            },
            api
          );

          if (result.success) {
            console.log('✅ Charts captured and uploaded for reports');
          } else {
            console.warn('⚠️ Chart capture incomplete:', result.message);
          }
        } catch (error) {
          console.error('❌ Error auto-capturing charts:', error);
          // Don't show error to user - this is a background process
        }
      }, 3000); // Wait 3 seconds for charts to fully render
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
        {sign} {value > 0 ? '+' : ''}{Math.round(value)}% vs last period
      </Typography>
    );
  };

  // Use competitor threats from API (already calculated server-side)
  const threats = competitorThreats || [];
  const highThreatCount = threats.filter((c: any) => c.threat_level === 'High').length;
  const mediumThreatCount = threats.filter((c: any) => c.threat_level === 'Medium').length;

  // Get the first running task from global task status
  const runningTask = tasks.find(task => task.status === 'running');

  return (
    <Box>
      {/* Task Progress Indicator */}
      {runningTask && dismissedTaskId !== runningTask.id && (
        <Alert
          severity="info"
          sx={{ mb: 3 }}
          onClose={() => setDismissedTaskId(runningTask.id)}
        >
          <Box display="flex" alignItems="center" gap={2}>
            <CircularProgress size={20} />
            <Box flex={1}>
              <Typography variant="body2" fontWeight="bold">
                {runningTask.task_type === 'analysis' ? 'Analysis & Report Generation' : runningTask.task_type}
              </Typography>
              <Typography variant="caption">
                {runningTask.message || `Processing ${runningTask.processed_items} of ${runningTask.total_items} items...`}
              </Typography>
            </Box>
          </Box>
        </Alert>
      )}

      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
        <Typography variant="h2" component="h1">
          Key Metrics Dashboard
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Box sx={{ minWidth: 300 }}>
            <BatchSelector
              selectedBatchId={selectedBatchId}
              onBatchChange={setSelectedBatchId}
              showAllOption={true}
              label="Filter by Collection"
            />
          </Box>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleDownloadDashboard}
            size="small"
          >
            Download Dashboard as Image
          </Button>
        </Box>
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
      <Box ref={dashboardRef} id="dashboard-main" sx={{ p: 2 }}>
        {/* Show message if no data */}
        {metrics.total_responses === 0 && (
          <Paper sx={{ p: 3, mb: 4, backgroundColor: 'info.light' }}>
            <Typography variant="h6" gutterBottom>
              New to TALES?
            </Typography>
            <Typography>
              Click on <strong>Customize</strong> on the left and start adding information about your brands!
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
                    {Math.round(metrics.mention_rate ?? 0)}%
                  </Typography>
                  {formatChange(metrics.change_mention_rate)}
                </Box>
                <TrendingUpIcon sx={{
                  fontSize: 48,
                  color: metrics.change_mention_rate > 0 ? '#58A13B' : metrics.change_mention_rate < 0 ? '#EA4A4A' : '#003e60'
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
                    {highThreatCount ?? 0}
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
                    {Math.round(metrics.descriptor_match ?? 0)}%
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
                    {Math.round(metrics.share_of_voice ?? 0)}%
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    {metrics.leading_position}
                  </Typography>
                  <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mt: 0.5 }}>
                    {(() => {
                      const brandData = Array.isArray(shareOfVoice)
                        ? shareOfVoice.find((item: any) => item.is_brand)
                        : null;
                      return `${Math.round(brandData?.leadership_visibility ?? 0)}% Leadership Visibility`;
                    })()}
                  </Typography>
                </Box>
                <VisibilityIcon sx={{ fontSize: 48, color: '#003e60' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts Section */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper id="dashboard-sentiment-chart" sx={{ p: 3, height: 300, border: '1px solid #e0e0e0', boxShadow: 'none' }}>
            <Typography variant="h6" gutterBottom>
              Sentiment Breakdown
            </Typography>
            {sentimentData && sentimentData.total > 0 ? (
              <Box sx={{ display: 'flex', alignItems: 'center', height: 240 }}>
                {/* Legend on the left */}
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mr: 2 }}>
                  {[
                    { name: 'Very Positive', value: sentimentData.very_positive_pct || 0, color: '#116C29' },
                    { name: 'Positive', value: sentimentData.positive_pct || 0, color: '#58A13B' },
                    { name: 'Neutral', value: sentimentData.neutral_pct || 0, color: '#9FA8DA' },
                    { name: 'Mixed', value: sentimentData.mixed_pct || 0, color: '#75C9C8' },
                    { name: 'Negative', value: sentimentData.negative_pct || 0, color: '#E04320' },
                  ].filter(item => item.value > 0).map((item) => (
                    <Box key={item.name} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box sx={{ width: 16, height: 16, backgroundColor: item.color, borderRadius: '2px' }} />
                      <Typography variant="body2" sx={{ fontSize: '13px' }}>
                        {item.name}: {Math.round(item.value)}%
                      </Typography>
                    </Box>
                  ))}
                </Box>
                {/* Pie chart on the right */}
                <ChartContainer width="100%" height={240} showLogo={false}>
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Very Positive', value: sentimentData.very_positive_pct || 0, fill: '#116C29' },
                        { name: 'Positive', value: sentimentData.positive_pct || 0, fill: '#58A13B' },
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
                    <Tooltip formatter={(value) => `${Math.round(Number(value))}%`} />
                  </PieChart>
                </ChartContainer>
              </Box>
            ) : (
              <Box sx={{ height: 240, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Typography color="textSecondary">No sentiment data available</Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper id="dashboard-positioning-chart" sx={{ p: 3, height: 300, border: '1px solid #e0e0e0', boxShadow: 'none' }}>
            <Typography variant="h6" gutterBottom>
              Positioning Distribution
            </Typography>
            {positioningData && positioningData.total > 0 ? (
              (() => {
                const maxValue = Math.max(
                  positioningData.leader || 0,
                  positioningData.featured || 0,
                  positioningData.listed || 0,
                  positioningData.not_mentioned || 0
                );
                const minYAxis = maxValue + 2;
                // Round up to next 5 or 10
                let roundedMax;
                if (minYAxis <= 5) {
                  roundedMax = 5;
                } else if (minYAxis <= 10) {
                  roundedMax = 10;
                } else {
                  // Round up to next multiple of 5 or 10
                  const remainder = minYAxis % 10;
                  if (remainder === 0) {
                    roundedMax = minYAxis;
                  } else if (remainder <= 5) {
                    roundedMax = minYAxis - remainder + 5;
                  } else {
                    roundedMax = minYAxis - remainder + 10;
                  }
                }
                return (
              <ChartContainer width="100%" height={240}>
                <BarChart
                  data={[
                    { position: 'Leader', fullName: 'Leader', count: positioningData.leader || 0, fill: '#116C29' },
                    { position: 'Featured', fullName: 'Featured', count: positioningData.featured || 0, fill: '#75C9C8' },
                    { position: 'Listed', fullName: 'Listed', count: positioningData.listed || 0, fill: '#80A1D4' },
                    { position: 'Not Mentioned', fullName: 'Not Mentioned', count: positioningData.not_mentioned || 0, fill: '#003e60' },
                  ]}
                  margin={{ top: 5, right: 30, left: 20, bottom: 40 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="position" angle={-45} textAnchor="end" height={50} />
                  <YAxis domain={[0, roundedMax]} allowDecimals={false} />
                  <Tooltip
                    formatter={(value: number, name: string, props: any) => [
                      value,
                      props.payload.fullName || name
                    ]}
                  />
                  <Bar dataKey="count">
                    {[
                      { position: 'Leader', count: positioningData.leader || 0, fill: '#116C29' },
                      { position: 'Featured', count: positioningData.featured || 0, fill: '#75C9C8' },
                      { position: 'Listed', count: positioningData.listed || 0, fill: '#80A1D4' },
                      { position: 'Not Mentioned', count: positioningData.not_mentioned || 0, fill: '#003e60' },
                    ].map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                    <LabelList dataKey="count" position="top" />
                  </Bar>
                </BarChart>
              </ChartContainer>
                );
              })()
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
