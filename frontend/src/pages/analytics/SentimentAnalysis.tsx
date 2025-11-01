import { Box, Typography, Paper, CircularProgress, Alert, Button } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { Download } from '@mui/icons-material';
import { api } from '../../services/api';
import html2canvas from 'html2canvas';
import { useRef } from 'react';

const COLORS = {
  'Very Positive': '#76FF03',  // Bright highlighter green
  'Positive': '#58A13B',       // Extended green (formerly Very Positive)
  'Neutral': '#9FA8DA',        // Periwinkle
  'Negative': '#E04320',       // Burnt orange/red
  'Very Negative': '#EA4A4A'   // Extended red
};

export default function SentimentAnalysis() {
  const sentimentChartRef = useRef<HTMLDivElement>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ['sentiment-analysis'],
    queryFn: async () => {
      const response = await api.get('/analytics/sentiment/breakdown');
      return response.data;
    },
  });

  // Download sentiment chart as PNG
  const handleDownloadSentimentChart = async () => {
    if (!sentimentChartRef.current) return;

    try {
      const canvas = await html2canvas(sentimentChartRef.current, {
        backgroundColor: '#ffffff',
        scale: 2,
      });

      const link = document.createElement('a');
      const today = new Date();
      const month = String(today.getMonth() + 1).padStart(2, '0');
      const day = String(today.getDate()).padStart(2, '0');
      const year = today.getFullYear();
      const dateStr = `${month}_${day}_${year}`;

      link.download = `SentimentAnalysis_${dateStr}.png`;
      link.href = canvas.toDataURL();
      link.click();
    } catch (error) {
      console.error('Error downloading chart:', error);
    }
  };

  // Download negative statements as CSV
  const handleDownloadNegativeStatementsCSV = () => {
    if (!data?.negative_statements || data.negative_statements.length === 0) return;

    const csvHeaders = ['Query', 'Platform', 'Statement'];
    const csvRows = data.negative_statements.map((statement: any) => [
      `"${statement.query.replace(/"/g, '""')}"`,
      `"${statement.platform}"`,
      `"${statement.text.replace(/"/g, '""')}"`
    ]);

    const csvContent = [
      csvHeaders.join(','),
      ...csvRows.map((row: string[]) => row.join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const today = new Date();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    const year = today.getFullYear();
    const dateStr = `${month}_${day}_${year}`;

    link.download = `NegativeStatements_${dateStr}.csv`;
    link.href = URL.createObjectURL(blob);
    link.click();
    URL.revokeObjectURL(link.href);
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
        Failed to load sentiment analysis. Please try again later.
      </Alert>
    );
  }

  // Transform data for pie chart
  // API returns: { very_positive, positive, neutral, negative, very_negative, total, ... }
  const sentimentMap: { [key: string]: string } = {
    'very_positive': 'Very Positive',
    'positive': 'Positive',
    'neutral': 'Neutral',
    'negative': 'Negative',
    'very_negative': 'Very Negative'
  };

  const chartData = data
    ? Object.entries(sentimentMap)
        .map(([key, label]) => ({
          name: label,
          value: (data[key] as number) || 0,
          percentage: data.total > 0 ? (((data[key] as number || 0) / data.total) * 100).toFixed(1) : '0'
        }))
        .filter(item => item.value > 0)  // Only show sentiments with data in chart
    : [];

  // Prepare all sentiment data for insights (including 0%)
  const allSentimentData = data
    ? Object.entries(sentimentMap).map(([key, label]) => ({
        name: label,
        key: key,
        value: (data[key] as number) || 0,
        percentage: data.total > 0 ? (((data[key] as number || 0) / data.total) * 100).toFixed(1) : '0',
        insight: data.sentiment_insights?.[key] || 'No insight available.'
      }))
    : [];

  return (
    <Box>
      <Typography variant="h2" component="h1" gutterBottom>
        Sentiment Analysis
      </Typography>

      {/* Explanatory Text */}
      <Paper sx={{ p: 3, mb: 4, backgroundColor: '#f9f9f9' }}>
        <Typography variant="body1">
          <strong>Sentiment analysis</strong> assesses the tone and attitude expressed toward your brand in AI responses. TALES evaluates each mention on a five-point scale: Very Positive, Positive, Neutral, Negative, or Very Negative. This analysis reveals how AI systems characterize your brand's reputation and helps identify opportunities to improve perception.
        </Typography>
      </Paper>

      <Paper sx={{ p: 4, mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box>
            <Typography variant="h6">
              Sentiment Distribution
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Total brand mentions analyzed: {data?.total || 0}
            </Typography>
          </Box>
          <Button
            variant="outlined"
            startIcon={<Download />}
            onClick={handleDownloadSentimentChart}
            size="small"
          >
            Download Chart As Image
          </Button>
        </Box>

        {chartData.length > 0 ? (
          <Box ref={sentimentChartRef} sx={{ backgroundColor: 'white', p: 2, border: '1px solid #e0e0e0', mt: 2 }}>
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
          </Box>
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
        {allSentimentData.length > 0 ? (
          <Box>
            {allSentimentData.map((item, index) => (
              <Box key={index} sx={{ mb: 4, pb: 3, borderBottom: index < allSentimentData.length - 1 ? '1px solid #e0e0e0' : 'none' }}>
                <Typography variant="body1" sx={{ mb: 1, fontWeight: 'bold', color: COLORS[item.name as keyof typeof COLORS] || '#000' }}>
                  {item.name}: {item.value} mentions ({item.percentage}%)
                </Typography>
                <Typography variant="body2" sx={{ color: 'text.secondary', whiteSpace: 'pre-wrap' }}>
                  {item.insight}
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
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">
            Negative Statements
          </Typography>
          {data?.negative_statements && data.negative_statements.length > 0 && (
            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={handleDownloadNegativeStatementsCSV}
              size="small"
            >
              Download as CSV
            </Button>
          )}
        </Box>
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
    </Box>
  );
}
