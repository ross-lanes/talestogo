import { Box, Typography, Paper, CircularProgress, Alert } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { api } from '../../services/api';

const COLORS = {
  'Very Positive': '#4caf50',
  'Positive': '#8bc34a',
  'Neutral': '#9e9e9e',
  'Negative': '#e65100',  // Darker orange for better readability
  'Very Negative': '#f44336',
  'Mixed': '#2196f3'
};

export default function SentimentAnalysis() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['sentiment-analysis'],
    queryFn: async () => {
      const response = await api.get('/analytics/sentiment/breakdown');
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
        Failed to load sentiment analysis. Please try again later.
      </Alert>
    );
  }

  // Transform data for pie chart
  const chartData = Object.entries(data?.breakdown || {}).map(([sentiment, count]) => ({
    name: sentiment,
    value: count as number,
    percentage: data?.total > 0 ? ((count as number / data.total) * 100).toFixed(1) : 0
  }));

  return (
    <Box>
      <Typography variant="h2" component="h1" gutterBottom>
        Sentiment Analysis
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Analyze the sentiment distribution across all brand mentions in AI responses.
      </Typography>

      <Paper sx={{ p: 4, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Sentiment Distribution
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Total brand mentions analyzed: {data?.total || 0}
        </Typography>

        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percentage }) => `${name}: ${percentage}%`}
                outerRadius={120}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[entry.name as keyof typeof COLORS] || '#999'} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value: number, name: string, props: any) => [
                  `${value} mentions (${props.payload.percentage}%)`,
                  name
                ]}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <Alert severity="info">
            No sentiment data available yet. Run analysis to generate sentiment insights.
          </Alert>
        )}
      </Paper>

      {/* Key Insights */}
      <Paper sx={{ p: 4 }}>
        <Typography variant="h6" gutterBottom>
          Key Insights
        </Typography>
        {chartData.length > 0 ? (
          <Box>
            {chartData
              .sort((a, b) => b.value - a.value)
              .slice(0, 3)
              .map((item, index) => (
                <Box key={index} sx={{ mb: 2 }}>
                  <Typography variant="body1">
                    <strong>{item.name}:</strong> {item.value} mentions ({item.percentage}%)
                  </Typography>
                </Box>
              ))}
          </Box>
        ) : (
          <Typography variant="body2" color="text.secondary">
            No insights available yet.
          </Typography>
        )}
      </Paper>
    </Box>
  );
}
