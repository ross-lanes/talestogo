import { Box, Typography, Paper, CircularProgress, Alert, Button, Card, CardContent } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Download, TrendingUp as TrendingUpIcon } from '@mui/icons-material';
import { api } from '../../services/api';
import html2canvas from 'html2canvas';
import { useRef } from 'react';


const BRAND_COLOR = '#665775';

export default function BrandMentions() {
  const trendChartRef = useRef<HTMLDivElement>(null);

  // Fetch dashboard metrics - this is the single source of truth for current metrics
  const { data: metrics, isLoading: metricsLoading, error: metricsError } = useQuery({
    queryKey: ['dashboard-metrics'],
    queryFn: async () => {
      const response = await api.get('/analytics/dashboard');
      return response.data;
    },
  });

  // Fetch trend data for the chart and table
  const { data: trendData, isLoading: trendLoading, error: trendError } = useQuery({
    queryKey: ['brand-mentions-trend'],
    queryFn: async () => {
      const response = await api.get('/analytics/trends/brand-mentions');
      return response.data;
    },
  });

  const isLoading = metricsLoading || trendLoading;
  const error = metricsError || trendError;

  // Format change percentage for display
  const formatChange = (change: number | undefined) => {
    if (change === undefined || change === null || change === 0) return null;
    const sign = change > 0 ? '+' : '';
    const color = change > 0 ? '#58A13B' : '#EA4A4A';
    return (
      <Typography variant="body2" sx={{ color, fontWeight: 600 }}>
        {sign}{change}% vs. previous
      </Typography>
    );
  };

  // Download trend chart as PNG
  const handleDownloadTrendChart = async () => {
    if (!trendChartRef.current) return;

    try {
      const canvas = await html2canvas(trendChartRef.current, {
        backgroundColor: '#ffffff',
        scale: 2,
      });

      const link = document.createElement('a');
      const today = new Date();
      const month = String(today.getMonth() + 1).padStart(2, '0');
      const day = String(today.getDate()).padStart(2, '0');
      const year = today.getFullYear();
      const dateStr = `${month}_${day}_${year}`;

      link.download = `BrandMentionsTrend_${dateStr}.png`;
      link.href = canvas.toDataURL();
      link.click();
    } catch (error) {
      console.error('Error downloading chart:', error);
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        Failed to load brand mentions analysis. Please try again later.
      </Alert>
    );
  }

  // Show the current metric even if there's no trend data yet
  const hasCurrentMetrics = metrics && metrics.mention_rate !== undefined;

  // Format dates for display
  const formattedData = trendData?.map((item: any) => ({
    ...item,
    displayDate: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  })) || [];

  return (
    <Box>
      <Typography variant="h2" component="h1" sx={{ mb: 3 }}>
        Brand Mentions
      </Typography>

      {/* Explanatory Text */}
      <Paper sx={{ p: 3, mb: 4, backgroundColor: '#f9f9f9' }}>
        <Typography variant="body1">
          <strong>Brand Mentions</strong> tracks how often your brand appears in AI-generated responses over time. This metric shows the percentage of responses that mention your brand (either directly or indirectly) when answering queries in your domain. An increasing trend indicates growing brand visibility in AI systems.
        </Typography>
      </Paper>

      {/* Brand Mentions Summary Card - Dashboard Style */}
      {hasCurrentMetrics ? (
        <Box sx={{ mb: 4 }}>
          <Card sx={{ border: '1px solid #e0e0e0', boxShadow: 'none' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Brand Mentions
                  </Typography>
                  <Typography variant="h4" component="div" color="primary">
                    {Math.round(metrics.mention_rate)}%
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
        </Box>
      ) : (
        <Alert severity="info" sx={{ mb: 4 }}>
          No brand mention data available yet. Data will appear after running data collection.
        </Alert>
      )}

      {/* Trend Chart */}
      <Paper sx={{ p: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box>
            <Typography variant="h6">
              Brand Mention Rate Over Time
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Percentage of AI responses that mention your brand across all collection periods
            </Typography>
          </Box>
          {formattedData.length > 0 && (
            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={handleDownloadTrendChart}
              size="small"
            >
              Image
            </Button>
          )}
        </Box>

        {formattedData.length > 0 ? (
          <Box ref={trendChartRef} sx={{ backgroundColor: 'white', p: 2, border: '1px solid #e0e0e0', mt: 2 }}>
            <ResponsiveContainer width="100%" height={400}>
            <LineChart data={formattedData} margin={{ top: 20, right: 30, left: 20, bottom: 80 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="displayDate"
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis
                label={{ value: 'Mention Rate (%)', angle: -90, position: 'insideLeft' }}
                domain={[0, 100]}
              />
              <Tooltip
                formatter={(value: number) => [`${value}%`, 'Mention Rate']}
                labelFormatter={(label) => `Date: ${label}`}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="mention_rate"
                stroke={BRAND_COLOR}
                strokeWidth={formattedData.length === 1 ? 0 : 3}
                name="Mention Rate"
                dot={{ fill: BRAND_COLOR, r: 4, stroke: BRAND_COLOR, strokeWidth: 2 }}
                activeDot={{ r: 6 }}
                connectNulls={true}
              />
            </LineChart>
          </ResponsiveContainer>
          </Box>
        ) : (
          <Alert severity="info">
            No brand mention data available yet. Data will appear after running data collection.
          </Alert>
        )}
      </Paper>

      {/* Data Table */}
      {formattedData.length > 0 && (
        <Paper sx={{ p: 4, mt: 4 }}>
          <Typography variant="h6" gutterBottom>
            Collection History
          </Typography>
          <Box sx={{ overflowX: 'auto', mt: 2 }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #e0e0e0' }}>
                  <th style={{ textAlign: 'left', padding: '12px', fontWeight: 'bold' }}>Date</th>
                  <th style={{ textAlign: 'right', padding: '12px', fontWeight: 'bold' }}>Mention Rate</th>
                  <th style={{ textAlign: 'right', padding: '12px', fontWeight: 'bold' }}>Mentions</th>
                  <th style={{ textAlign: 'right', padding: '12px', fontWeight: 'bold' }}>Total Responses</th>
                </tr>
              </thead>
              <tbody>
                {formattedData.slice().reverse().map((item: any, index: number) => (
                  <tr key={index} style={{ borderBottom: '1px solid #f0f0f0' }}>
                    <td style={{ padding: '12px' }}>{item.displayDate}</td>
                    <td style={{ padding: '12px', textAlign: 'right', fontWeight: 'bold' }}>
                      {item.mention_rate}%
                    </td>
                    <td style={{ padding: '12px', textAlign: 'right' }}>{item.mention_count}</td>
                    <td style={{ padding: '12px', textAlign: 'right' }}>{item.total}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Box>
        </Paper>
      )}
    </Box>
  );
}
