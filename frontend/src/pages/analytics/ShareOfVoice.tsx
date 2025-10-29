import { Box, Typography, Paper, CircularProgress, Alert } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, LabelList } from 'recharts';
import { api } from '../../services/api';

const BRAND_COLOR = '#665775';
const COMPETITOR_COLORS = ['#80a1d4', '#75c9c8', '#c9ada7', '#9a8c98', '#4a4e69', '#22223b', '#f2e9e4'];

export default function ShareOfVoice() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['share-of-voice'],
    queryFn: async () => {
      const response = await api.get('/analytics/share-of-voice');
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
        Failed to load share of voice analysis. Please try again later.
      </Alert>
    );
  }

  // Transform API data to match expected format
  // API returns: { organization, total_mentions, share_of_voice, is_brand, ... }
  const shareData = Array.isArray(data)
    ? data.map((item: any) => ({
        name: item.organization,
        mention_count: item.total_mentions,
        share_of_voice: item.share_of_voice,
        is_brand: item.is_brand || false
      }))
    : [];

  const brandData = shareData.find(item => item.is_brand) || null;
  const competitorData = shareData.filter(item => !item.is_brand);

  // Calculate total mentions for percentage
  const totalMentions = shareData.reduce((sum, item) => sum + (item.mention_count || 0), 0);

  // Prepare data for pie chart
  const pieData = shareData.map((item, index) => ({
    name: item.name,
    value: item.mention_count || 0,
    percentage: totalMentions > 0 ? ((item.mention_count || 0) / totalMentions * 100).toFixed(1) : 0,
    is_brand: item.is_brand
  }));

  return (
    <Box>
      <Typography variant="h2" component="h1" gutterBottom>
        Share of Voice
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Compare your brand's visibility against competitors in AI responses.
      </Typography>

      {/* Key Metrics */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 3, mb: 4 }}>
        {brandData && (
          <Paper sx={{ p: 3, backgroundColor: BRAND_COLOR, color: 'white' }}>
            <Typography variant="h4">{brandData.share_of_voice?.toFixed(1)}%</Typography>
            <Typography variant="body1">{brandData.name} (Your Brand)</Typography>
            <Typography variant="caption">{brandData.mention_count} mentions</Typography>
          </Paper>
        )}
        <Paper sx={{ p: 3 }}>
          <Typography variant="h4">{competitorData.length}</Typography>
          <Typography variant="body1">Active Competitors</Typography>
          <Typography variant="caption">Mentioned in responses</Typography>
        </Paper>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h4">{totalMentions}</Typography>
          <Typography variant="body1">Total Mentions</Typography>
          <Typography variant="caption">Across all entities</Typography>
        </Paper>
      </Box>

      {/* Bar Chart - Comparison */}
      <Paper sx={{ p: 4, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Mention Comparison
        </Typography>
        {shareData.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={shareData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
              <YAxis />
              <Tooltip formatter={(value: number) => [`${value} mentions`, 'Count']} />
              <Legend />
              <Bar dataKey="mention_count" name="Mentions" fill={BRAND_COLOR}>
                {shareData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.is_brand ? BRAND_COLOR : COMPETITOR_COLORS[index % COMPETITOR_COLORS.length]} />
                ))}
                <LabelList
                  dataKey="mention_count"
                  position="top"
                  style={{ fill: '#666', fontWeight: 'bold', fontSize: 12 }}
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <Alert severity="info">
            No share of voice data available yet. Run analysis to generate insights.
          </Alert>
        )}
      </Paper>

      {/* Pie Chart - Market Share */}
      <Paper sx={{ p: 4, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Market Share Distribution
        </Typography>
        {pieData.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percentage }) => `${name}: ${percentage}%`}
                outerRadius={120}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.is_brand ? BRAND_COLOR : COMPETITOR_COLORS[index % COMPETITOR_COLORS.length]}
                  />
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
            No data available for visualization.
          </Alert>
        )}
      </Paper>

      {/* Detailed Breakdown */}
      <Paper sx={{ p: 4 }}>
        <Typography variant="h6" gutterBottom>
          Detailed Breakdown
        </Typography>
        <Box sx={{ mt: 2 }}>
          {shareData
            .sort((a, b) => (b.mention_count || 0) - (a.mention_count || 0))
            .map((item, index) => (
              <Box
                key={index}
                sx={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  p: 2,
                  mb: 1,
                  backgroundColor: item.is_brand ? `${BRAND_COLOR}10` : '#f5f5f5',
                  borderLeft: `4px solid ${item.is_brand ? BRAND_COLOR : COMPETITOR_COLORS[index % COMPETITOR_COLORS.length]}`
                }}
              >
                <Box>
                  <Typography variant="body1" fontWeight={item.is_brand ? 'bold' : 'normal'}>
                    {item.name} {item.is_brand && '(Your Brand)'}
                  </Typography>
                </Box>
                <Box sx={{ textAlign: 'right' }}>
                  <Typography variant="h6">{item.share_of_voice?.toFixed(1)}%</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {item.mention_count} mentions
                  </Typography>
                </Box>
              </Box>
            ))}
        </Box>
      </Paper>
    </Box>
  );
}
