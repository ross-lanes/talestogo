import { Box, Typography, Paper, CircularProgress, Alert, Button } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, LabelList, LineChart, Line, Legend } from 'recharts';
import { Download } from '@mui/icons-material';
import { api } from '../../services/api';
import html2canvas from 'html2canvas';
import { useRef, useState } from 'react';
import BatchSelector from '../../components/BatchSelector';

// TALES brand colors + extended palette (removed #c0b9dd and #ded9e2 - too light)
const BRAND_COLORS = [
  '#665775', '#80a1d4', '#75c9c8', '#44809C',  // TALES colors
  '#9FA8DA', '#4A55EA', '#58A13B', '#EA4A4A'   // Extended palette
];

export default function PositioningAnalysis() {
  const positioningChartRef = useRef<HTMLDivElement>(null);
  const [selectedBatchId, setSelectedBatchId] = useState<number | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ['positioning-analysis', selectedBatchId],
    queryFn: async () => {
      const params = selectedBatchId ? { batch_id: selectedBatchId } : {};
      const response = await api.get('/analytics/positioning/breakdown', { params });
      return response.data;
    },
  });

  const { data: mentionTrends, isLoading: loadingTrends } = useQuery({
    queryKey: ['mention-trends'],
    queryFn: async () => {
      const response = await api.get('/analytics/trends/mentions?days=30');
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
      const today = new Date();
      const month = String(today.getMonth() + 1).padStart(2, '0');
      const day = String(today.getDate()).padStart(2, '0');
      const year = today.getFullYear();
      const dateStr = `${month}_${day}_${year}`;

      link.download = `BrandPositioning_${dateStr}.png`;
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
    { key: 'not_mentioned', label: 'Not mentioned', color: '#665775' },
    { key: 'listed', label: 'Listed', color: '#80a1d4' },
    { key: 'featured', label: 'Featured', color: '#75c9c8' },
    { key: 'leader', label: 'Leader', color: '#116C29' }  // Bright highlighter green
  ];

  const chartData = data
    ? positionOrder.map(({ key, label, color }) => ({
        position: label,
        count: (data[key] as number) || 0,
        percentage: data.total > 0 ? (((data[key] as number || 0) / data.total) * 100).toFixed(0) : '0',
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
          <Button
            variant="outlined"
            startIcon={<Download />}
            onClick={handleDownloadPositioningChart}
            size="small"
          >
            Download Chart As Image
          </Button>
        </Box>

        {chartData.length > 0 ? (
          <Box ref={positioningChartRef} sx={{ backgroundColor: 'white', p: 2, border: '1px solid #e0e0e0', mt: 2 }}>
            <ResponsiveContainer width="100%" height={500}>
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
          </ResponsiveContainer>
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
            <Typography variant="h6" sx={{ color: '#665775', mb: 1 }}>Not mentioned (Score: 1)</Typography>
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

      {/* Mentions Over Time */}
      <Paper sx={{ p: 4 }}>
        <Typography variant="h6" gutterBottom>
          Brand Mentions Over Time
        </Typography>

        {loadingTrends ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
            <CircularProgress />
          </Box>
        ) : mentionTrends && mentionTrends.length > 0 ? (
          <>
            {/* Show latest mention count */}
            {(() => {
              const latestData = mentionTrends[mentionTrends.length - 1];
              return (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="body1" color="text.secondary">
                    Latest collection: <strong>{latestData.mentions}</strong> brand mentions out of <strong>{latestData.total_responses}</strong> total responses ({latestData.mention_rate}%)
                  </Typography>
                </Box>
              );
            })()}

            {/* Only show graph if there are multiple data points */}
            {mentionTrends.length > 1 && (
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={mentionTrends} margin={{ top: 20, right: 30, left: 20, bottom: 80 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="date"
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis
                    label={{ value: 'Mention Rate (%)', angle: -90, position: 'insideLeft' }}
                  />
                  <Tooltip
                    formatter={(value: number) => [`${value}%`, 'Mention Rate']}
                    labelFormatter={(label) => `Date: ${label}`}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="mention_rate"
                    stroke="#665775"
                    strokeWidth={2}
                    name="Mention Rate"
                    dot={{ fill: '#665775', r: 4 }}
                    activeDot={{ r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </>
        ) : (
          <Alert severity="info">
            No mention trend data available yet. Data will appear after running data collection.
          </Alert>
        )}
      </Paper>
    </Box>
  );
}
