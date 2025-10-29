import { Box, Typography, Paper, CircularProgress, Alert } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { api } from '../../services/api';

const BRAND_COLOR = '#665775';
const COMPETITOR_COLORS = [
  '#80a1d4', '#75c9c8', '#44809C',  // TALES colors (removed #c0b9dd and #ded9e2)
  '#A13C84', '#4A55EA', '#58A13B', '#EA4A4A'   // Extended palette
];

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

      {/* Explanatory Text */}
      <Paper sx={{ p: 3, mb: 4, backgroundColor: '#f9f9f9' }}>
        <Typography variant="body1">
          <strong>Share of Voice</strong> measures your brand's visibility relative to competitors across all AI responses. TALES calculates this by analyzing how frequently your brand appears in leadership positions (Leader, Top 3) compared to the total number of responses, expressing it as a percentage. A higher share of voice indicates stronger competitive positioning and greater mindshare in AI-generated content.
        </Typography>
      </Paper>

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

      {/* Pie Chart - Share of Voice Distribution */}
      <Paper sx={{ p: 4 }}>
        <Typography variant="h6" gutterBottom>
          Share of Voice Distribution
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          This chart shows what percentage of the total "conversation" each organization owns. A larger slice means greater visibility and mind share in AI-generated content.
        </Typography>
        {shareData.length > 0 ? (
          <ResponsiveContainer width="100%" height={500}>
            <PieChart>
              <Pie
                data={shareData}
                cx="50%"
                cy="50%"
                labelLine={true}
                label={({ name, share_of_voice }: any) => `${name}: ${share_of_voice?.toFixed(1)}%`}
                outerRadius={150}
                fill="#8884d8"
                dataKey="mention_count"
              >
                {shareData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.is_brand ? BRAND_COLOR : COMPETITOR_COLORS[index % COMPETITOR_COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip
                formatter={(value: number, name: string, props: any) => [
                  `${value} mentions (${props.payload.share_of_voice?.toFixed(1)}%)`,
                  props.payload.name
                ]}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <Alert severity="info">
            No share of voice data available yet. Run analysis to generate insights.
          </Alert>
        )}
      </Paper>
    </Box>
  );
}
