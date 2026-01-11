import { Box, Typography, Paper, CircularProgress, Alert, Button } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, LabelList, LineChart, Line, Legend, AreaChart, Area } from 'recharts';
import { Download } from '@mui/icons-material';
import { api } from '../../services/api';
import html2canvas from 'html2canvas';
import { useRef, useState } from 'react';
import BatchSelector from '../../components/BatchSelector';
import { formatDateEST, formatDateForFilename } from '../../utils/dateUtils';
import ChartContainer from '../../components/ChartContainer';

// TALES brand colors + extended palette (removed #c0b9dd and #ded9e2 - too light)
const BRAND_COLORS = [
  '#003e60', '#80a1d4', '#75c9c8', '#44809C',  // TALES colors
  '#9FA8DA', '#4A55EA', '#58A13B', '#EA4A4A'   // Extended palette
];

// Platform colors for consistency
const PLATFORM_COLORS: Record<string, string> = {
  'ChatGPT': '#10A37F',
  'Claude': '#CC785C',
  'Gemini': '#4285F4',
  'Perplexity': '#1FB8CD'
};

export default function PositioningAnalysis() {
  const positioningChartRef = useRef<HTMLDivElement>(null);
  const positioningTrendChartRef = useRef<HTMLDivElement>(null);
  const llmChartRef = useRef<HTMLDivElement>(null);
  const [selectedBatchId, setSelectedBatchId] = useState<number | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ['positioning-analysis', selectedBatchId],
    queryFn: async () => {
      const params = selectedBatchId ? { batch_id: selectedBatchId } : {};
      const response = await api.get('/analytics/positioning/breakdown', { params });
      return response.data;
    },
  });

  const { data: positioningTrends, isLoading: loadingPositioningTrends } = useQuery({
    queryKey: ['positioning-trends'],
    queryFn: async () => {
      const response = await api.get('/analytics/trends/positioning');
      return response.data;
    },
  });

  // Fetch LLM breakdown data
  const { data: llmData, isLoading: llmLoading, error: llmError } = useQuery({
    queryKey: ['positioning-by-llm'],
    queryFn: async () => {
      const response = await api.get('/analytics/positioning-by-llm');
      return response.data;
    },
  });

  // Download positioning chart as PNG
  const handleDownloadPositioningChart = async () => {
    if (!positioningChartRef.current) return;

    try {
      const canvas = await html2canvas(positioningChartRef.current, {
        backgroundColor: '#ffffff',
        scale: 2,
      });

      const link = document.createElement('a');
      const dateStr = formatDateForFilename();

      link.download = `BrandPositioning_${dateStr}.png`;
      link.href = canvas.toDataURL();
      link.click();
    } catch (error) {
      console.error('Error downloading chart:', error);
    }
  };

  // Download positioning trend chart as PNG
  const handleDownloadPositioningTrendChart = async () => {
    if (!positioningTrendChartRef.current) return;

    try {
      const canvas = await html2canvas(positioningTrendChartRef.current, {
        backgroundColor: '#ffffff',
        scale: 2,
      });

      const link = document.createElement('a');
      const dateStr = formatDateForFilename();

      link.download = `PositioningTrend_${dateStr}.png`;
      link.href = canvas.toDataURL();
      link.click();
    } catch (error) {
      console.error('Error downloading chart:', error);
    }
  };

  // Download positioning distribution as CSV
  const handleDownloadPositioningCSV = () => {
    if (!chartData || chartData.length === 0) return;

    const csvHeaders = ['Position', 'Count', 'Percentage'];
    const csvRows = chartData.map((item: any) => [
      `"${item.position}"`,
      String(item.count),
      `${item.percentage}%`
    ]);

    const csvContent = [
      csvHeaders.join(','),
      ...csvRows.map((row: string[]) => row.join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const dateStr = formatDateForFilename();

    link.download = `BrandPositioning_${dateStr}.csv`;
    link.href = URL.createObjectURL(blob);
    link.click();
    URL.revokeObjectURL(link.href);
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

      link.download = `PositioningByLLM_${dateStr}.png`;
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
        Failed to load positioning analysis. Please try again later.
      </Alert>
    );
  }

  // Transform data for horizontal bar chart
  // API returns: { leader: 3, top_3: 10, featured: 9, listed: 10, not_mentioned: 43, total: 88, ... }
  const positionOrder = [
    { key: 'not_mentioned', label: 'Not mentioned', color: '#003e60' },
    { key: 'listed', label: 'Listed', color: '#80a1d4' },
    { key: 'featured', label: 'Featured', color: '#75c9c8' },
    { key: 'leader', label: 'Leader', color: '#116C29' }  // Bright highlighter green
  ];

  const chartData = data
    ? positionOrder.map(({ key, label, color }) => ({
        position: label,
        count: (data[key] as number) || 0,
        percentage: data.total > 0 ? Math.round(((data[key] as number || 0) / data.total) * 100) : 0,
        fill: color
      }))  // Show all positions, even if count is 0
    : [];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h2" component="h1">
          Positioning Analysis
        </Typography>
        <Box sx={{ minWidth: 300 }}>
          <BatchSelector
            selectedBatchId={selectedBatchId}
            onBatchChange={setSelectedBatchId}
            showAllOption={true}
            label="Filter by Collection"
            defaultToLatest={true}
          />
        </Box>
      </Box>

      {/* Explanatory Text */}
      <Paper sx={{ p: 3, mb: 4, backgroundColor: '#f9f9f9' }}>
        <Typography variant="body1">
          <strong>Brand positioning</strong> evaluates where your brand appears within AI-generated responses. TALES categorizes each mention into four tiers: Leader (primary recommendation), Featured (prominent attention or top recommendation), Listed (included but not emphasized), or Not Mentioned. This hierarchy reveals how AI systems prioritize your brand relative to alternatives when answering user queries.
        </Typography>
      </Paper>

      <Paper sx={{ p: 4, mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box>
            <Typography variant="h6">
              Brand Positioning Distribution
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              How your brand is positioned across all AI responses
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={handleDownloadPositioningCSV}
              size="small"
            >
              Spreadsheet
            </Button>
            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={handleDownloadPositioningChart}
              size="small"
            >
              Image
            </Button>
          </Box>
        </Box>

        {chartData.length > 0 ? (
          <Box ref={positioningChartRef} sx={{ backgroundColor: 'white', p: 2, border: '1px solid #e0e0e0', mt: 2 }}>
            <ChartContainer width="100%" height={500}>
            <BarChart data={chartData} layout="vertical" margin={{ top: 20, right: 100, left: 120, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis type="category" dataKey="position" width={100} />
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
                  position="right"
                  content={(props: any) => {
                    const { x, y, width, height, value, index } = props;
                    const entry = chartData[index];
                    return (
                      <text
                        x={Number(x) + Number(width) + 10}
                        y={Number(y) + Number(height) / 2}
                        fill="#666"
                        fontSize={14}
                        fontWeight="bold"
                        dominantBaseline="middle"
                      >
                        {value} ({entry?.percentage}%)
                      </text>
                    );
                  }}
                />
              </Bar>
            </BarChart>
          </ChartContainer>
          </Box>
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
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 3, mt: 2 }}>
          <Box>
            <Typography variant="h6" sx={{ color: '#003e60', mb: 1 }}>Not mentioned (Score: 1)</Typography>
            <Typography variant="body1" color="text.secondary">
              Your brand was not mentioned in the response
            </Typography>
          </Box>
          <Box>
            <Typography variant="h6" sx={{ color: '#80a1d4', mb: 1 }}>Listed (Score: 2)</Typography>
            <Typography variant="body1" color="text.secondary">
              Your brand is mentioned in a list with competitors
            </Typography>
          </Box>
          <Box>
            <Typography variant="h6" sx={{ color: '#75c9c8', mb: 1 }}>Featured (Score: 3)</Typography>
            <Typography variant="body1" color="text.secondary">
              Your brand receives prominent attention in the response, either through detailed discussion or being highlighted as a top recommendation
            </Typography>
          </Box>
          <Box>
            <Typography variant="h6" sx={{ color: '#116C29', mb: 1 }}>Leader (Score: 4)</Typography>
            <Typography variant="body1" color="text.secondary">
              Your brand is presented as the top choice or industry leader
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* LLM Breakdown Chart */}
      {llmData && llmData.length > 0 && (
        <Paper sx={{ p: 4, mb: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box>
              <Typography variant="h6">
                Brand Positioning by LLM Platform
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Positioning breakdown across different AI platforms
              </Typography>
            </Box>
            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={handleDownloadLLMChart}
              size="small"
            >
              Image
            </Button>
          </Box>

          <Box ref={llmChartRef} sx={{ backgroundColor: 'white', p: 2, border: '1px solid #e0e0e0', mt: 2 }}>
            <ChartContainer width="100%" height={400}>
              <BarChart data={llmData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="platform" />
                <YAxis label={{ value: 'Number of Responses', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="Leader" fill="#116C29" stackId="a" />
                <Bar dataKey="Featured" fill="#75c9c8" stackId="a" />
                <Bar dataKey="Listed" fill="#80a1d4" stackId="a" />
                <Bar dataKey="Not Mentioned" fill="#003e60" stackId="a" />
              </BarChart>
            </ChartContainer>
          </Box>

          {/* LLM Data Table */}
          <Box sx={{ overflowX: 'auto', mt: 3 }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #e0e0e0' }}>
                  <th style={{ textAlign: 'left', padding: '12px', fontWeight: 'bold' }}>Platform</th>
                  <th style={{ textAlign: 'right', padding: '12px', fontWeight: 'bold' }}>Leader</th>
                  <th style={{ textAlign: 'right', padding: '12px', fontWeight: 'bold' }}>Featured</th>
                  <th style={{ textAlign: 'right', padding: '12px', fontWeight: 'bold' }}>Listed</th>
                  <th style={{ textAlign: 'right', padding: '12px', fontWeight: 'bold' }}>Not Mentioned</th>
                  <th style={{ textAlign: 'right', padding: '12px', fontWeight: 'bold' }}>Total</th>
                </tr>
              </thead>
              <tbody>
                {llmData.map((item: any, index: number) => (
                  <tr key={index} style={{ borderBottom: '1px solid #f0f0f0' }}>
                    <td style={{ padding: '12px' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box
                          sx={{
                            width: 12,
                            height: 12,
                            borderRadius: '50%',
                            backgroundColor: PLATFORM_COLORS[item.platform] || '#003e60'
                          }}
                        />
                        {item.platform}
                      </Box>
                    </td>
                    <td style={{ padding: '12px', textAlign: 'right' }}>{item.Leader || 0}</td>
                    <td style={{ padding: '12px', textAlign: 'right' }}>{item.Featured || 0}</td>
                    <td style={{ padding: '12px', textAlign: 'right' }}>{item.Listed || 0}</td>
                    <td style={{ padding: '12px', textAlign: 'right' }}>{item['Not Mentioned'] || 0}</td>
                    <td style={{ padding: '12px', textAlign: 'right', fontWeight: 'bold' }}>{item.total}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Box>
        </Paper>
      )}

      {/* Positioning Distribution Over Time */}
      <Paper sx={{ p: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box>
            <Typography variant="h6">
              Positioning Distribution Over Time
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              How your brand's positioning has evolved across collection periods
            </Typography>
          </Box>
          {positioningTrends && positioningTrends.length > 0 && (
            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={handleDownloadPositioningTrendChart}
              size="small"
            >
              Image
            </Button>
          )}
        </Box>

        {loadingPositioningTrends ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
            <CircularProgress />
          </Box>
        ) : positioningTrends && positioningTrends.length > 0 ? (
          <>
            {/* Format dates for display */}
            {(() => {
              const formattedData = positioningTrends.map((item: any) => ({
                ...item,
                displayDate: formatDateEST(item.date, 'short')
              }));

              return (
                <Box ref={positioningTrendChartRef} sx={{ backgroundColor: 'white', p: 2, border: '1px solid #e0e0e0', mt: 2 }}>
                  <ChartContainer width="100%" height={400}>
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
                      dataKey="leader"
                      stackId="1"
                      stroke="#116C29"
                      fill="#116C29"
                      name="Leader"
                    />
                    <Area
                      type="monotone"
                      dataKey="featured"
                      stackId="1"
                      stroke="#75c9c8"
                      fill="#75c9c8"
                      name="Featured"
                    />
                    <Area
                      type="monotone"
                      dataKey="listed"
                      stackId="1"
                      stroke="#80a1d4"
                      fill="#80a1d4"
                      name="Listed"
                    />
                    <Area
                      type="monotone"
                      dataKey="not_mentioned"
                      stackId="1"
                      stroke="#003e60"
                      fill="#003e60"
                      name="Not Mentioned"
                    />
                  </AreaChart>
                </ChartContainer>
                </Box>
              );
            })()}
          </>
        ) : (
          <Alert severity="info">
            No positioning trend data available yet. Data will appear after running data collection.
          </Alert>
        )}
      </Paper>
    </Box>
  );
}
