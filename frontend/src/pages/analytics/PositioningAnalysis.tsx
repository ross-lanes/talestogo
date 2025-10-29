import { Box, Typography, Paper, CircularProgress, Alert } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { api } from '../../services/api';

const COLORS = {
  'Leader': '#4caf50',
  'Top 3': '#8bc34a',
  'Featured': '#2196f3',
  'Listed': '#9c27b0',  // Purple instead of orange/yellow for readability
  'Not Mentioned': '#f44336'
};

export default function PositioningAnalysis() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['positioning-analysis'],
    queryFn: async () => {
      const response = await api.get('/analytics/positioning/breakdown');
      return response.data;
    },
  });

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
        Failed to load positioning analysis. Please try again later.
      </Alert>
    );
  }

  // Transform data for bar chart
  // API returns: { leader: 3, top_3: 10, featured: 9, listed: 10, not_mentioned: 43, total: 88, ... }
  const positionMap: { [key: string]: string } = {
    'leader': 'Leader',
    'top_3': 'Top 3',
    'featured': 'Featured',
    'listed': 'Listed',
    'not_mentioned': 'Not Mentioned'
  };

  const chartData = data
    ? Object.entries(positionMap).map(([key, label]) => ({
        position: label,
        count: (data[key] as number) || 0,
        percentage: data.total > 0 ? (((data[key] as number || 0) / data.total) * 100).toFixed(1) : '0'
      })).filter(item => item.count > 0)  // Only show positions with data
    : [];

  return (
    <Box>
      <Typography variant="h2" component="h1" gutterBottom>
        Positioning Analysis
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Analyze how your brand is positioned when mentioned in AI responses.
      </Typography>

      <Paper sx={{ p: 4, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Brand Positioning Distribution
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Total responses analyzed: {data?.total || 0} | Average positioning score: {data?.average_score?.toFixed(2) || 'N/A'}
        </Typography>

        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="position" />
              <YAxis />
              <Tooltip
                formatter={(value: number, name: string, props: any) => [
                  `${value} mentions (${props.payload.percentage}%)`,
                  'Count'
                ]}
              />
              <Legend />
              <Bar dataKey="count" name="Number of Mentions">
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[entry.position as keyof typeof COLORS] || '#999'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <Alert severity="info">
            No positioning data available yet. Run analysis to generate positioning insights.
          </Alert>
        )}
      </Paper>

      {/* Position Definitions */}
      <Paper sx={{ p: 4, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Position Definitions
        </Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 2, mt: 2 }}>
          <Box>
            <Typography variant="subtitle2" color="success.main">Leader (Score: 5)</Typography>
            <Typography variant="body2" color="text.secondary">
              Your brand is presented as the top choice or industry leader
            </Typography>
          </Box>
          <Box>
            <Typography variant="subtitle2" color="success.light">Top 3 (Score: 4)</Typography>
            <Typography variant="body2" color="text.secondary">
              Your brand is among the top 3 recommendations
            </Typography>
          </Box>
          <Box>
            <Typography variant="subtitle2" color="primary.main">Featured (Score: 3)</Typography>
            <Typography variant="body2" color="text.secondary">
              Your brand is featured prominently in the response
            </Typography>
          </Box>
          <Box>
            <Typography variant="subtitle2" sx={{ color: '#9c27b0' }}>Listed (Score: 2)</Typography>
            <Typography variant="body2" color="text.secondary">
              Your brand is mentioned in a list with competitors
            </Typography>
          </Box>
          <Box>
            <Typography variant="subtitle2" color="error.main">Not Mentioned (Score: 1)</Typography>
            <Typography variant="body2" color="text.secondary">
              Your brand was not mentioned in the response
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Key Metrics */}
      <Paper sx={{ p: 4 }}>
        <Typography variant="h6" gutterBottom>
          Key Metrics
        </Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 3, mt: 2 }}>
          {chartData
            .sort((a, b) => b.count - a.count)
            .map((item, index) => (
              <Box key={index}>
                <Typography variant="h4" color={COLORS[item.position as keyof typeof COLORS]}>
                  {item.percentage}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {item.position}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  ({item.count} mentions)
                </Typography>
              </Box>
            ))}
        </Box>
      </Paper>
    </Box>
  );
}
