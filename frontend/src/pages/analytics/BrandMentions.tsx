import { Box, Typography, Paper, CircularProgress, Alert, Button, Card, CardContent } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Cell } from 'recharts';
import { Download, TrendingUp as TrendingUpIcon } from '@mui/icons-material';
import { api } from '../../services/api';
import html2canvas from 'html2canvas';
import { useRef } from 'react';
import { formatDateEST, formatDateForFilename } from '../../utils/dateUtils';
import ChartContainer from '../../components/ChartContainer';


const BRAND_COLOR = '#003e60';

// Platform colors for consistency
const PLATFORM_COLORS: Record<string, string> = {
  'ChatGPT': '#10A37F',
  'Claude': '#CC785C',
  'Gemini': '#4285F4',
  'Perplexity': '#1FB8CD'
};

export default function BrandMentions() {
  const trendChartRef = useRef<HTMLDivElement>(null);
  const llmChartRef = useRef<HTMLDivElement>(null);

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

  // Fetch LLM breakdown data
  const { data: llmData, isLoading: llmLoading, error: llmError } = useQuery({
    queryKey: ['brand-mentions-by-llm'],
    queryFn: async () => {
      const response = await api.get('/analytics/brand-mentions-by-llm');
      return response.data;
    },
  });

  const isLoading = metricsLoading || trendLoading || llmLoading;
  const error = metricsError || trendError || llmError;

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
      const dateStr = formatDateForFilename();

      link.download = `BrandMentionsTrend_${dateStr}.png`;
      link.href = canvas.toDataURL();
      link.click();
    } catch (error) {
      console.error('Error downloading chart:', error);
    }
  };

  // Download LLM chart as PNG
  const handleDownloadLLMChart = async () => {
    if (!llmChartRef.current) return;

    try {
      const canvas = await html2canvas(llmChartRef.current, {
        backgroundColor: '#ffffff',
        scale: 2,
      });

      const link = document.createElement('a');
      const dateStr = formatDateForFilename();

      link.download = `BrandMentionsByLLM_${dateStr}.png`;
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

  // Show the current metric only if we have actual response data
  // mention_rate will be 0 if there's no data, so we need to check for actual responses
  const hasCurrentMetrics = metrics && metrics.total_responses !== undefined && metrics.total_responses > 0;

  // Format dates for display
  const formattedData = trendData?.map((item: any) => ({
    ...item,
    displayDate: formatDateEST(item.date, 'short')
  })) || [];

  return (
    <Box>
      <Typography variant="h2" component="h1" sx={{ mb: 3 }}>
        Brand Mentions
      </Typography>

      {/* Explanatory Text */}
      <Paper sx={{ p: { xs: 2, sm: 3 }, mb: { xs: 3, sm: 4 }, backgroundColor: '#f9f9f9' }}>
        <Typography variant="body1" sx={{ fontSize: { xs: '0.9rem', sm: '1rem' } }}>
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
                  color: metrics.change_mention_rate > 0 ? '#58A13B' : metrics.change_mention_rate < 0 ? '#EA4A4A' : '#003e60'
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
      <Paper sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' }, mb: 2, gap: { xs: 2, sm: 0 } }}>
          <Box sx={{ flex: 1 }}>
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
              startIcon={<Download sx={{ display: { xs: 'none', sm: 'inline' } }} />}
              onClick={handleDownloadTrendChart}
              size="small"
              sx={{ minWidth: { xs: 44, sm: 'auto' }, px: { xs: 1, sm: 2 } }}
            >
              <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>Image</Box>
              <Download sx={{ display: { xs: 'inline', sm: 'none' } }} />
            </Button>
          )}
        </Box>

        {formattedData.length > 0 ? (
          <Box ref={trendChartRef} sx={{ backgroundColor: 'white', p: { xs: 1, sm: 2 }, border: '1px solid #e0e0e0', mt: 2 }}>
            <ChartContainer width="100%" height={{ xs: 300, sm: 350, md: 400 }}>
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
          </ChartContainer>
          </Box>
        ) : (
          <Alert severity="info">
            No brand mention data available yet. Data will appear after running data collection.
          </Alert>
        )}
      </Paper>

      {/* LLM Breakdown Chart */}
      {llmData && llmData.length > 0 && (
        <Paper sx={{ p: { xs: 2, sm: 3, md: 4 }, mt: { xs: 3, sm: 4 } }}>
          <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' }, mb: 2, gap: { xs: 2, sm: 0 } }}>
            <Box sx={{ flex: 1 }}>
              <Typography variant="h6">
                Brand Mention Rate by LLM Platform
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Comparison of mention rates across different AI platforms
              </Typography>
            </Box>
            <Button
              variant="outlined"
              startIcon={<Download sx={{ display: { xs: 'none', sm: 'inline' } }} />}
              onClick={handleDownloadLLMChart}
              size="small"
              sx={{ minWidth: { xs: 44, sm: 'auto' }, px: { xs: 1, sm: 2 } }}
            >
              <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>Image</Box>
              <Download sx={{ display: { xs: 'inline', sm: 'none' } }} />
            </Button>
          </Box>

          <Box ref={llmChartRef} sx={{ backgroundColor: 'white', p: { xs: 1, sm: 2 }, border: '1px solid #e0e0e0', mt: 2 }}>
            <ChartContainer width="100%" height={{ xs: 300, sm: 350, md: 400 }}>
              <BarChart data={llmData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="platform" />
                <YAxis
                  label={{ value: 'Mention Rate (%)', angle: -90, position: 'insideLeft' }}
                  domain={[0, 100]}
                />
                <Tooltip
                  formatter={(value: number, name: string) => {
                    if (name === 'mention_rate') return [`${value}%`, 'Mention Rate'];
                    return [value, name];
                  }}
                  labelFormatter={(label) => `Platform: ${label}`}
                />
                <Legend />
                <Bar dataKey="mention_rate" name="Mention Rate" radius={[8, 8, 0, 0]}>
                  {llmData.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={PLATFORM_COLORS[entry.platform] || BRAND_COLOR} />
                  ))}
                </Bar>
              </BarChart>
            </ChartContainer>
          </Box>

          {/* LLM Data Table */}
          <Box sx={{ overflowX: 'auto', mt: 3, WebkitOverflowScrolling: 'touch' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '500px' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #e0e0e0' }}>
                  <th style={{ textAlign: 'left', padding: '8px 12px', fontWeight: 'bold', fontSize: '0.875rem' }}>Platform</th>
                  <th style={{ textAlign: 'right', padding: '8px 12px', fontWeight: 'bold', fontSize: '0.875rem' }}>Mention Rate</th>
                  <th style={{ textAlign: 'right', padding: '8px 12px', fontWeight: 'bold', fontSize: '0.875rem' }}>Mentions</th>
                  <th style={{ textAlign: 'right', padding: '8px 12px', fontWeight: 'bold', fontSize: '0.875rem' }}>Total Responses</th>
                </tr>
              </thead>
              <tbody>
                {llmData.map((item: any, index: number) => (
                  <tr key={index} style={{ borderBottom: '1px solid #f0f0f0' }}>
                    <td style={{ padding: '8px 12px' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box
                          sx={{
                            width: 12,
                            height: 12,
                            borderRadius: '50%',
                            backgroundColor: PLATFORM_COLORS[item.platform] || BRAND_COLOR
                          }}
                        />
                        {item.platform}
                      </Box>
                    </td>
                    <td style={{ padding: '8px 12px', textAlign: 'right', fontWeight: 'bold', fontSize: '0.875rem' }}>
                      {item.mention_rate}%
                    </td>
                    <td style={{ padding: '8px 12px', textAlign: 'right', fontSize: '0.875rem' }}>{item.mentions}</td>
                    <td style={{ padding: '8px 12px', textAlign: 'right', fontSize: '0.875rem' }}>{item.total_responses}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Box>
        </Paper>
      )}

      {/* Data Table */}
      {formattedData.length > 0 && (
        <Paper sx={{ p: { xs: 2, sm: 3, md: 4 }, mt: { xs: 3, sm: 4 } }}>
          <Typography variant="h6" gutterBottom>
            Collection History
          </Typography>
          <Box sx={{ overflowX: 'auto', mt: 2, WebkitOverflowScrolling: 'touch' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '500px' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #e0e0e0' }}>
                  <th style={{ textAlign: 'left', padding: '8px 12px', fontWeight: 'bold', fontSize: '0.875rem' }}>Date</th>
                  <th style={{ textAlign: 'right', padding: '8px 12px', fontWeight: 'bold', fontSize: '0.875rem' }}>Mention Rate</th>
                  <th style={{ textAlign: 'right', padding: '8px 12px', fontWeight: 'bold', fontSize: '0.875rem' }}>Mentions</th>
                  <th style={{ textAlign: 'right', padding: '8px 12px', fontWeight: 'bold', fontSize: '0.875rem' }}>Total Responses</th>
                </tr>
              </thead>
              <tbody>
                {formattedData.slice().reverse().map((item: any, index: number) => (
                  <tr key={index} style={{ borderBottom: '1px solid #f0f0f0' }}>
                    <td style={{ padding: '8px 12px', fontSize: '0.875rem' }}>{item.displayDate}</td>
                    <td style={{ padding: '8px 12px', textAlign: 'right', fontWeight: 'bold', fontSize: '0.875rem' }}>
                      {item.mention_rate}%
                    </td>
                    <td style={{ padding: '8px 12px', textAlign: 'right', fontSize: '0.875rem' }}>{item.mention_count}</td>
                    <td style={{ padding: '8px 12px', textAlign: 'right', fontSize: '0.875rem' }}>{item.total}</td>
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
