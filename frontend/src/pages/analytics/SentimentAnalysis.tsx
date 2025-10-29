import { Box, Typography, Paper, CircularProgress, Alert } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { api } from '../../services/api';

const COLORS = {
  'Very Positive': '#58A13B',  // Extended green
  'Positive': '#4A55EA',       // Extended bright blue
  'Neutral': '#A13C84',        // Extended purple
  'Negative': '#EA4A4A',       // Extended red
  'Very Negative': '#EA4A4A',  // Extended red (same as Negative)
  'Mixed': '#75c9c8'           // TALES teal
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
  // API returns: { very_positive, positive, neutral, negative, mixed, total, ... }
  const sentimentMap: { [key: string]: string } = {
    'very_positive': 'Very Positive',
    'positive': 'Positive',
    'neutral': 'Neutral',
    'negative': 'Negative',
    'very_negative': 'Very Negative',
    'mixed': 'Mixed'
  };

  const chartData = data
    ? Object.entries(sentimentMap)
        .map(([key, label]) => ({
          name: label,
          value: (data[key] as number) || 0,
          percentage: data.total > 0 ? (((data[key] as number || 0) / data.total) * 100).toFixed(1) : '0'
        }))
        .filter(item => item.value > 0)  // Only show sentiments with data
    : [];

  return (
    <Box>
      <Typography variant="h2" component="h1" gutterBottom>
        Sentiment Analysis
      </Typography>

      {/* Explanatory Text */}
      <Paper sx={{ p: 3, mb: 4, backgroundColor: '#f9f9f9' }}>
        <Typography variant="body1">
          <strong>Sentiment analysis</strong> assesses the tone and attitude expressed toward your brand in AI responses. TALES evaluates each mention on a five-point scale: Very Positive, Positive, Neutral, Negative, or Very Negative, with an additional Mixed category for responses containing both positive and negative elements. This analysis reveals how AI systems characterize your brand's reputation and helps identify opportunities to improve perception.
        </Typography>
      </Paper>

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
      <Paper sx={{ p: 4, mb: 4 }}>
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

      {/* Negative Statements */}
      <Paper sx={{ p: 4, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Negative Statements
        </Typography>
        {data?.negative_statements && data.negative_statements.length > 0 ? (
          <Box>
            {data.negative_statements.map((statement: any, index: number) => (
              <Box key={index} sx={{ mb: 3, pb: 3, borderBottom: index < data.negative_statements.length - 1 ? '1px solid #e0e0e0' : 'none' }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  <strong>Query:</strong> {statement.query}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  <strong>Platform:</strong> {statement.platform}
                </Typography>
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                  {statement.text}
                </Typography>
              </Box>
            ))}
          </Box>
        ) : (
          <Typography variant="body2" color="text.secondary">
            None
          </Typography>
        )}
      </Paper>

      {/* Mixed Statements */}
      <Paper sx={{ p: 4 }}>
        <Typography variant="h6" gutterBottom>
          Mixed Statements
        </Typography>
        {data?.mixed_statements && data.mixed_statements.length > 0 ? (
          <Box>
            {data.mixed_statements.map((statement: any, index: number) => (
              <Box key={index} sx={{ mb: 3, pb: 3, borderBottom: index < data.mixed_statements.length - 1 ? '1px solid #e0e0e0' : 'none' }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  <strong>Query:</strong> {statement.query}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  <strong>Platform:</strong> {statement.platform}
                </Typography>
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                  {statement.text}
                </Typography>
              </Box>
            ))}
          </Box>
        ) : (
          <Typography variant="body2" color="text.secondary">
            None
          </Typography>
        )}
      </Paper>
    </Box>
  );
}
