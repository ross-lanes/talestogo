import { Box, Typography, Paper, CircularProgress, Alert } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, LabelList } from 'recharts';
import { api } from '../../services/api';

// TALES brand colors
const BRAND_COLORS = ['#665775', '#80a1d4', '#75c9c8', '#c0b9dd', '#ded9e2'];

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

  // Transform data for horizontal bar chart
  // API returns: { leader: 3, top_3: 10, featured: 9, listed: 10, not_mentioned: 43, total: 88, ... }
  const positionOrder = [
    { key: 'not_mentioned', label: 'Not mentioned' },
    { key: 'listed', label: 'Listed' },
    { key: 'featured', label: 'Featured' },
    { key: 'top_3', label: 'Top 3' },
    { key: 'leader', label: 'Leader' }
  ];

  const chartData = data
    ? positionOrder.map(({ key, label }, index) => ({
        position: label,
        count: (data[key] as number) || 0,
        percentage: data.total > 0 ? (((data[key] as number || 0) / data.total) * 100).toFixed(1) : '0',
        fill: BRAND_COLORS[index % BRAND_COLORS.length]
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
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="position" />
              <YAxis />
              <Tooltip
                formatter={(value: number, name: string, props: any) => [
                  `${value} mentions (${props.payload.percentage}%)`,
                  'Count'
                ]}
              />
              <Bar dataKey="count" name="Number of Mentions">
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
                <LabelList
                  dataKey="count"
                  position="top"
                  content={(props: any) => {
                    const { x, y, width, value, index } = props;
                    const entry = chartData[index];
                    return (
                      <text
                        x={Number(x) + Number(width) / 2}
                        y={Number(y) - 5}
                        fill="#666"
                        fontSize={14}
                        fontWeight="bold"
                        textAnchor="middle"
                      >
                        {value} ({entry?.percentage}%)
                      </text>
                    );
                  }}
                />
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
      <Paper sx={{ p: 4 }}>
        <Typography variant="h6" gutterBottom>
          Position Definitions
        </Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 2, mt: 2 }}>
          <Box>
            <Typography variant="subtitle2" sx={{ color: '#665775' }}>Not mentioned (Score: 1)</Typography>
            <Typography variant="body2" color="text.secondary">
              Your brand was not mentioned in the response
            </Typography>
          </Box>
          <Box>
            <Typography variant="subtitle2" sx={{ color: '#80a1d4' }}>Listed (Score: 2)</Typography>
            <Typography variant="body2" color="text.secondary">
              Your brand is mentioned in a list with competitors
            </Typography>
          </Box>
          <Box>
            <Typography variant="subtitle2" sx={{ color: '#75c9c8' }}>Featured (Score: 3)</Typography>
            <Typography variant="body2" color="text.secondary">
              Your brand is featured prominently in the response
            </Typography>
          </Box>
          <Box>
            <Typography variant="subtitle2" sx={{ color: '#c0b9dd' }}>Top 3 (Score: 4)</Typography>
            <Typography variant="body2" color="text.secondary">
              Your brand is among the top 3 recommendations
            </Typography>
          </Box>
          <Box>
            <Typography variant="subtitle2" sx={{ color: '#ded9e2' }}>Leader (Score: 5)</Typography>
            <Typography variant="body2" color="text.secondary">
              Your brand is presented as the top choice or industry leader
            </Typography>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
}
