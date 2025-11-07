import { Box, Typography, Paper, CircularProgress, Alert, Button } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip, AreaChart, Area, XAxis, YAxis, CartesianGrid } from 'recharts';
import { Download } from '@mui/icons-material';
import { api } from '../../services/api';
import html2canvas from 'html2canvas';
import { useRef, useState } from 'react';
import BatchSelector from '../../components/BatchSelector';
import { formatDateEST, formatDateForFilename } from '../../utils/dateUtils';

const COLORS = {
  'Very Positive': '#116C29',  // Bright highlighter green
  'Positive': '#58A13B',       // Extended green (formerly Very Positive)
  'Neutral': '#9FA8DA',        // Periwinkle
  'Negative': '#E04320',       // Burnt orange/red
  'Very Negative': '#EA4A4A'   // Extended red
};

export default function SentimentAnalysis() {
  const sentimentChartRef = useRef<HTMLDivElement>(null);
  const sentimentTrendChartRef = useRef<HTMLDivElement>(null);
  const [selectedBatchId, setSelectedBatchId] = useState<number | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ['sentiment-analysis', selectedBatchId],
    queryFn: async () => {
      const params = selectedBatchId ? { batch_id: selectedBatchId } : {};
      const response = await api.get('/analytics/sentiment/breakdown', { params });
      return response.data;
    },
  });

  const { data: sentimentTrends, isLoading: loadingTrends } = useQuery({
    queryKey: ['sentiment-trends'],
    queryFn: async () => {
      const response = await api.get('/analytics/trends/sentiment');
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
      const dateStr = formatDateForFilename();

      link.download = `SentimentAnalysis_${dateStr}.png`;
      link.href = canvas.toDataURL();
      link.click();
    } catch (error) {
      console.error('Error downloading chart:', error);
    }
  };

  // Download sentiment trend chart as PNG
  const handleDownloadSentimentTrendChart = async () => {
    if (!sentimentTrendChartRef.current) return;

    try {
      const canvas = await html2canvas(sentimentTrendChartRef.current, {
        backgroundColor: '#ffffff',
        scale: 2,
      });

      const link = document.createElement('a');
      const dateStr = formatDateForFilename();

      link.download = `SentimentTrend_${dateStr}.png`;
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
    const dateStr = formatDateForFilename();

    link.download = `NegativeStatements_${dateStr}.csv`;
    link.href = URL.createObjectURL(blob);
    link.click();
    URL.revokeObjectURL(link.href);
  };

  // Download sentiment distribution as CSV
  const handleDownloadSentimentCSV = () => {
    if (!chartData || chartData.length === 0) return;

    const csvHeaders = ['Sentiment', 'Count', 'Percentage'];
    const csvRows = chartData.map((item: any) => [
      `"${item.name}"`,
      String(item.value),
      `${item.percentage}%`
    ]);

    const csvContent = [
      csvHeaders.join(','),
      ...csvRows.map((row: string[]) => row.join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const dateStr = formatDateForFilename();

    link.download = `SentimentDistribution_${dateStr}.csv`;
    link.href = URL.createObjectURL(blob);
    link.click();
    URL.revokeObjectURL(link.href);
  };

  // Download sentiment trend as CSV
  const handleDownloadSentimentTrendCSV = () => {
    if (!sentimentTrends || sentimentTrends.length === 0) return;

    const csvHeaders = ['Date', 'Very Positive (%)', 'Positive (%)', 'Neutral (%)', 'Negative (%)', 'Very Negative (%)'];
    const csvRows = sentimentTrends.map((item: any) => [
      formatDateEST(item.date, 'short'),
      String(item.very_positive),
      String(item.positive),
      String(item.neutral),
      String(item.negative),
      String(item.very_negative)
    ]);

    const csvContent = [
      csvHeaders.join(','),
      ...csvRows.map((row: string[]) => row.join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const dateStr = formatDateForFilename();

    link.download = `SentimentTrend_${dateStr}.csv`;
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
          percentage: data.total > 0 ? Math.round(((data[key] as number || 0) / data.total) * 100) : 0
        }))
        .filter(item => item.value > 0)  // Only show sentiments with data in chart
    : [];

  // Prepare all sentiment data for insights (including 0%)
  const allSentimentData = data
    ? Object.entries(sentimentMap).map(([key, label]) => ({
        name: label,
        key: key,
        value: (data[key] as number) || 0,
        percentage: data.total > 0 ? Math.round(((data[key] as number || 0) / data.total) * 100) : 0,
        insight: data.sentiment_insights?.[key] || 'No insight available.'
      }))
    : [];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h2" component="h1">
          Sentiment Analysis
        </Typography>
        <Box sx={{ minWidth: 300 }}>
          <BatchSelector
            selectedBatchId={selectedBatchId}
            onBatchChange={setSelectedBatchId}
            showAllOption={true}
            label="Filter by Collection"
          />
        </Box>
      </Box>

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
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={handleDownloadSentimentCSV}
              size="small"
            >
              Spreadsheet
            </Button>
            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={handleDownloadSentimentChart}
              size="small"
            >
              Image
            </Button>
          </Box>
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
              Spreadsheet
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

      {/* Sentiment Over Time */}
      <Paper sx={{ p: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box>
            <Typography variant="h6">
              Sentiment Distribution Over Time
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Track how sentiment toward your brand has evolved across collection periods
            </Typography>
          </Box>
          {sentimentTrends && sentimentTrends.length > 0 && (
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="outlined"
                startIcon={<Download />}
                onClick={handleDownloadSentimentTrendCSV}
                size="small"
              >
                Spreadsheet
              </Button>
              <Button
                variant="outlined"
                startIcon={<Download />}
                onClick={handleDownloadSentimentTrendChart}
                size="small"
              >
                Image
              </Button>
            </Box>
          )}
        </Box>

        {loadingTrends ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
            <CircularProgress />
          </Box>
        ) : sentimentTrends && sentimentTrends.length > 0 ? (
          <>
            {/* Format dates for display */}
            {(() => {
              const formattedData = sentimentTrends.map((item: any) => ({
                ...item,
                displayDate: formatDateEST(item.date, 'short')
              }));

              return (
                <Box ref={sentimentTrendChartRef} sx={{ backgroundColor: 'white', p: 2, border: '1px solid #e0e0e0', mt: 2 }}>
                  <ResponsiveContainer width="100%" height={400}>
                  <AreaChart data={formattedData} margin={{ top: 20, right: 30, left: 20, bottom: 80 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="displayDate"
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis
                      label={{ value: 'Percentage (%)', angle: -90, position: 'insideLeft' }}
                      domain={[0, 100]}
                    />
                    <Tooltip
                      formatter={(value: number, name: string) => [`${value}%`, name]}
                      labelFormatter={(label) => `Date: ${label}`}
                    />
                    <Legend />
                    <Area
                      type="monotone"
                      dataKey="very_positive"
                      stackId="1"
                      stroke={COLORS['Very Positive']}
                      fill={COLORS['Very Positive']}
                      name="Very Positive"
                    />
                    <Area
                      type="monotone"
                      dataKey="positive"
                      stackId="1"
                      stroke={COLORS['Positive']}
                      fill={COLORS['Positive']}
                      name="Positive"
                    />
                    <Area
                      type="monotone"
                      dataKey="neutral"
                      stackId="1"
                      stroke={COLORS['Neutral']}
                      fill={COLORS['Neutral']}
                      name="Neutral"
                    />
                    <Area
                      type="monotone"
                      dataKey="negative"
                      stackId="1"
                      stroke={COLORS['Negative']}
                      fill={COLORS['Negative']}
                      name="Negative"
                    />
                    <Area
                      type="monotone"
                      dataKey="very_negative"
                      stackId="1"
                      stroke={COLORS['Very Negative']}
                      fill={COLORS['Very Negative']}
                      name="Very Negative"
                    />
                  </AreaChart>
                </ResponsiveContainer>
                </Box>
              );
            })()}
          </>
        ) : (
          <Alert severity="info">
            No sentiment trend data available yet. Data will appear after running data collection.
          </Alert>
        )}
      </Paper>
    </Box>
  );
}
