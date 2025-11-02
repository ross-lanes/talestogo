import { Box, Typography, Paper, CircularProgress, Alert, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Button } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend, BarChart, Bar, XAxis, YAxis, CartesianGrid, LabelList } from 'recharts';
import { TrendingUp, TrendingDown, TrendingFlat, Download } from '@mui/icons-material';
import { api } from '../../services/api';
import html2canvas from 'html2canvas';
import { useRef } from 'react';

const BRAND_COLOR = '#665775';
const COMPETITOR_COLORS = [
  '#80a1d4', '#75c9c8', '#44809C',  // TALES colors (removed #c0b9dd and #ded9e2)
  '#9FA8DA', '#4A55EA', '#58A13B', '#EA4A4A'   // Extended palette
];

export default function ShareOfVoice() {
  const chartRef = useRef<HTMLDivElement>(null);

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
  // API returns: { organization, total_mentions, share_of_voice, leadership_visibility, is_brand, ... }
  const shareData = Array.isArray(data)
    ? data.map((item: any) => ({
        name: item.organization,
        mention_count: item.total_mentions,
        share_of_voice: item.share_of_voice,
        leadership_visibility: item.leadership_visibility,
        leader_count: item.leader_count,
        top3_count: item.top3_count,
        is_brand: item.is_brand || false
      }))
    : [];

  const brandData = shareData.find(item => item.is_brand) || null;
  const competitorData = shareData.filter(item => !item.is_brand);

  // Calculate total mentions for percentage
  const totalMentions = shareData.reduce((sum, item) => sum + (item.mention_count || 0), 0);

  // Calculate brand rank (position in sorted list by mentions)
  const sortedByMentions = [...shareData].sort((a, b) => b.mention_count - a.mention_count);
  const brandRank = brandData ? sortedByMentions.findIndex(item => item.is_brand) + 1 : null;
  const totalOrganizations = shareData.length;

  // Prepare data for pie chart - use mention_count for both slice size AND percentage calculation
  const pieData = shareData.map((item, index) => ({
    name: item.name,
    value: item.mention_count || 0,
    percentage: totalMentions > 0 ? ((item.mention_count || 0) / totalMentions * 100).toFixed(1) : '0',
    is_brand: item.is_brand
  }));


  // Helper function to create acronym from organization name
  const createAcronym = (name: string): string => {
    // Split by spaces and common separators
    const words = name.split(/[\s\-_&]+/).filter(word => word.length > 0);

    // If single word, check if it's already an acronym or abbreviation
    if (words.length === 1) {
      // If already short (<=6 chars) or all caps, return as-is
      if (name.length <= 6 || name === name.toUpperCase()) {
        return name;
      }
      // Otherwise take first 6 chars
      return name.substring(0, 6).toUpperCase();
    }

    // Create acronym from first letters of each word
    const acronym = words.map(word => word[0].toUpperCase()).join('');

    // If acronym is too long (more than 8 letters), use first 8
    return acronym.length > 8 ? acronym.substring(0, 8) : acronym;
  };

  // Prepare data for bar chart - top 10 + brand if not in top 10
  const sortedForChart = [...shareData].sort((a, b) => b.share_of_voice - a.share_of_voice);
  const top10 = sortedForChart.slice(0, 10);
  const brandInTop10 = top10.some(item => item.is_brand);

  let barChartData = top10.map(item => ({
    name: createAcronym(item.name),
    fullName: item.name,
    shareOfVoice: item.share_of_voice,
    is_brand: item.is_brand
  }));

  // Add brand as 11th column if not in top 10
  if (!brandInTop10 && brandData) {
    barChartData.push({
      name: createAcronym(brandData.name),
      fullName: brandData.name,
      shareOfVoice: brandData.share_of_voice,
      is_brand: true
    });
  }

  // Download bar chart as PNG
  const handleDownloadChart = async () => {
    if (!chartRef.current) return;

    try {
      const canvas = await html2canvas(chartRef.current, {
        backgroundColor: '#ffffff',
        scale: 2,
      });

      const link = document.createElement('a');
      const today = new Date();
      const month = String(today.getMonth() + 1).padStart(2, '0');
      const day = String(today.getDate()).padStart(2, '0');
      const year = today.getFullYear();
      const dateStr = `${month}_${day}_${year}`;

      const brandName = brandData?.name || 'Brand';
      const brandNameFormatted = brandName.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_]/g, '');

      link.download = `${brandNameFormatted}_ShareOfVoice_${dateStr}.png`;
      link.href = canvas.toDataURL();
      link.click();
    } catch (error) {
      console.error('Error downloading chart:', error);
    }
  };


  return (
    <Box>
      <Typography variant="h2" component="h1" gutterBottom>
        Share of Voice
      </Typography>

      {/* Explanatory Text */}
      <Paper sx={{ p: 3, mb: 4, backgroundColor: '#f9f9f9' }}>
        <Typography variant="body1" paragraph>
          <strong>Share of Voice</strong> measures the percentage of all brand mentions that reference your brand. This is a simple count showing how often your brand appears compared to all competitors.
        </Typography>
        <Typography variant="body1">
          <strong>Leadership Visibility</strong> measures how often your brand appears in premium positions (Leader or Top 3) within AI responses. This quality-weighted metric shows your brand's strength in competitive positioning, not just presence.
        </Typography>
      </Paper>

      {/* Brand Performance Metrics */}
      {brandData && brandRank && (
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 3, mb: 4 }}>
          <Paper sx={{ p: 3, backgroundColor: '#75C9C8', color: 'white' }}>
            <Typography variant="h3" sx={{ fontWeight: 700 }}>
              {brandData.share_of_voice?.toFixed(1) || 0}%
            </Typography>
            <Typography variant="h6" sx={{ mt: 1, mb: 0.5 }}>
              Share of Voice
            </Typography>
            <Typography variant="body2">
              {brandData.mention_count} out of {totalMentions} total mentions
            </Typography>
            <Typography variant="caption" sx={{ display: 'block', mt: 1, opacity: 0.9 }}>
              Ranking #{brandRank} out of {totalOrganizations} organizations
            </Typography>
          </Paper>

          <Paper sx={{ p: 3, backgroundColor: '#80a1d4', color: 'white' }}>
            <Typography variant="h3" sx={{ fontWeight: 700 }}>
              {brandData.leadership_visibility !== undefined ? brandData.leadership_visibility.toFixed(1) : '0.0'}%
            </Typography>
            <Typography variant="h6" sx={{ mt: 1, mb: 0.5 }}>
              Leadership Visibility
            </Typography>
            <Typography variant="body2">
              Leader or Top 3 positioning
            </Typography>
            <Typography variant="caption" sx={{ display: 'block', mt: 1, opacity: 0.9 }}>
              {brandData.leader_count} Leader + {brandData.top3_count} Top 3
            </Typography>
          </Paper>
        </Box>
      )}

      {/* Bar Chart - Top 10 Organizations */}
      {barChartData.length > 0 && (
        <Paper sx={{ p: 4, mb: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Share of Voice - Top Organizations
            </Typography>
            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={handleDownloadChart}
              size="small"
            >
              Download Chart As Image
            </Button>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Comparison of share of voice for the top 10 organizations{!brandInTop10 && brandData ? ' (including your brand)' : ''}.
          </Typography>
          <Box ref={chartRef} sx={{ backgroundColor: 'white', p: 2, border: '1px solid #e0e0e0' }}>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={barChartData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="name"
                  angle={0}
                  textAnchor="middle"
                  height={60}
                  interval={0}
                  tick={{ fontSize: 11 }}
                />
                <YAxis
                  label={{ value: 'Share of Voice (%)', angle: -90, position: 'insideLeft' }}
                  domain={[0, 'auto']}
                  allowDecimals={false}
                />
                <Tooltip
                  formatter={(value: number, name: string, props: any) => [
                    `${value.toFixed(1)}%`,
                    props.payload.fullName || name
                  ]}
                  labelFormatter={(label, payload) => {
                    if (payload && payload.length > 0) {
                      return payload[0].payload.fullName || label;
                    }
                    return label;
                  }}
                  labelStyle={{ fontWeight: 'bold' }}
                />
                <Bar dataKey="shareOfVoice" radius={[8, 8, 0, 0]}>
                  {barChartData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.is_brand ? BRAND_COLOR : COMPETITOR_COLORS[index % COMPETITOR_COLORS.length]}
                    />
                  ))}
                  <LabelList
                    dataKey="shareOfVoice"
                    position="top"
                    formatter={(value: any) => typeof value === 'number' ? `${value.toFixed(1)}%` : ''}
                    style={{ fontSize: '12px', fontWeight: 'bold' }}
                  />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Box>
        </Paper>
      )}

      {/* Share of Voice Distribution - Table or Pie Chart */}
      <Paper sx={{ p: 4 }}>
        <Typography variant="h6" gutterBottom>
          Share of Voice Distribution
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          This shows what percentage of the total "conversation" each organization owns. Higher percentages indicate greater visibility and mind share in AI-generated content.
        </Typography>

        {pieData.length > 0 ? (
          <>
            {/* Show pie chart only if 5 or fewer total entities (brand + competitors) */}
            {pieData.length <= 5 ? (
              <ResponsiveContainer width="100%" height={500}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    labelLine={true}
                    label={({ name, percentage }: any) => `${name}: ${percentage}%`}
                    outerRadius={150}
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
                    formatter={(value: any, name: any, props: any) => {
                      const percentage = props?.payload?.percentage || '0';
                      const displayName = props?.payload?.name || name;
                      return [`${value} mentions (${percentage}%)`, displayName];
                    }}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              /* Show table when more than 5 entities */
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>Rank</strong></TableCell>
                      <TableCell><strong>Organization</strong></TableCell>
                      <TableCell align="right"><strong>Mentions</strong></TableCell>
                      <TableCell align="right"><strong>Share of Voice (%)</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {pieData.map((item, index) => (
                      <TableRow
                        key={index}
                        sx={{
                          backgroundColor: item.is_brand ? 'rgba(102, 87, 117, 0.1)' : 'transparent',
                          '&:hover': {
                            backgroundColor: item.is_brand ? 'rgba(102, 87, 117, 0.15)' : 'rgba(0, 0, 0, 0.04)'
                          }
                        }}
                      >
                        <TableCell>{index + 1}</TableCell>
                        <TableCell>
                          <Typography variant="body2" fontWeight={item.is_brand ? 'bold' : 'normal'}>
                            {item.name} {item.is_brand && '(Your Brand)'}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" fontWeight={item.is_brand ? 'bold' : 'normal'}>
                            {item.value}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" fontWeight={item.is_brand ? 'bold' : 'normal'}>
                            {item.percentage}%
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </>
        ) : (
          <Alert severity="info">
            No share of voice data available yet. Run analysis to generate insights.
          </Alert>
        )}
      </Paper>
    </Box>
  );
}
