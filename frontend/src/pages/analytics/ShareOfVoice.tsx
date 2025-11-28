import { Box, Typography, Paper, CircularProgress, Alert, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Button } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { PieChart, Pie, Cell, Tooltip, Legend, BarChart, Bar, XAxis, YAxis, CartesianGrid, LabelList, LineChart, Line } from 'recharts';
import { TrendingUp, TrendingDown, TrendingFlat, Download } from '@mui/icons-material';
import { api } from '../../services/api';
import html2canvas from 'html2canvas';
import { useRef, useState } from 'react';
import BatchSelector from '../../components/BatchSelector';
import { formatDateEST, formatDateForFilename } from '../../utils/dateUtils';
import ChartContainer from '../../components/ChartContainer';

const BRAND_COLOR = '#003e60';
const COMPETITOR_COLORS = [
  '#80a1d4', '#75c9c8', '#44809C',  // TALES colors (removed #c0b9dd and #ded9e2)
  '#9FA8DA', '#4A55EA', '#58A13B', '#EA4A4A'   // Extended palette
];

// Platform colors for consistency
const PLATFORM_COLORS: Record<string, string> = {
  'ChatGPT': '#10A37F',
  'Claude': '#CC785C',
  'Gemini': '#4285F4',
  'Perplexity': '#1FB8CD'
};

export default function ShareOfVoice() {
  const chartRef = useRef<HTMLDivElement>(null);
  const trendChartRef = useRef<HTMLDivElement>(null);
  const llmChartRef = useRef<HTMLDivElement>(null);
  const [selectedBatchId, setSelectedBatchId] = useState<number | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ['share-of-voice', selectedBatchId],
    queryFn: async () => {
      const params = selectedBatchId ? { batch_id: selectedBatchId } : {};
      const response = await api.get('/analytics/share-of-voice', { params });
      return response.data;
    },
  });

  const { data: sovTrends, isLoading: loadingTrends } = useQuery({
    queryKey: ['sov-trends'],
    queryFn: async () => {
      const response = await api.get('/analytics/trends/share-of-voice');
      return response.data;
    },
  });

  // Fetch LLM breakdown data
  const { data: llmData, isLoading: llmLoading, error: llmError } = useQuery({
    queryKey: ['share-of-voice-by-llm'],
    queryFn: async () => {
      const response = await api.get('/analytics/share-of-voice-by-llm');
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
        featured_count: item.featured_count,
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
    percentage: totalMentions > 0 ? Math.round((item.mention_count || 0) / totalMentions * 100) : 0,
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
      const dateStr = formatDateForFilename();

      const brandName = brandData?.name || 'Brand';
      const brandNameFormatted = brandName.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_]/g, '');

      link.download = `${brandNameFormatted}_ShareOfVoice_${dateStr}.png`;
      link.href = canvas.toDataURL();
      link.click();
    } catch (error) {
      console.error('Error downloading chart:', error);
    }
  };

  // Download trend chart as PNG
  const handleDownloadTrendChart = async () => {
    if (!trendChartRef.current) return;

    try {
      const canvas = await html2canvas(trendChartRef.current, {
        backgroundColor: '#ffffff',
        scale: 2,
      });

      const link = document.createElement('a');
      const dateStr = formatDateForFilename();

      link.download = `ShareOfVoiceTrend_${dateStr}.png`;
      link.href = canvas.toDataURL();
      link.click();
    } catch (error) {
      console.error('Error downloading chart:', error);
    }
  };

  // Download Share of Voice Distribution as CSV
  const handleDownloadDistributionCSV = () => {
    if (!pieData || pieData.length === 0) return;

    const csvHeaders = ['Rank', 'Organization', 'Mentions', 'Share of Voice (%)'];
    const csvRows = pieData.map((item: any, index: number) => [
      String(index + 1),
      `"${item.name.replace(/"/g, '""')}"`,
      String(item.value),
      String(item.percentage)
    ]);

    const csvContent = [
      csvHeaders.join(','),
      ...csvRows.map((row: string[]) => row.join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const dateStr = formatDateForFilename();

    link.download = `ShareOfVoiceDistribution_${dateStr}.csv`;
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

      link.download = `ShareOfVoiceByLLM_${dateStr}.png`;
      link.href = canvas.toDataURL();
      link.click();
    } catch (error) {
      console.error('Error downloading chart:', error);
    }
  };


  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h2" component="h1">
          Share of Voice
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
        <Typography variant="body1" paragraph>
          <strong>Share of Voice</strong> measures the percentage of all brand mentions that reference your brand. This is a simple count showing how often your brand appears compared to all competitors.
        </Typography>
        <Typography variant="body1">
          <strong>Leadership Visibility</strong> measures how often your brand appears in premium positions (Leader or Featured) within AI responses. This quality-weighted metric shows your brand's strength in competitive positioning, not just presence.
        </Typography>
      </Paper>

      {/* Brand Performance Metrics */}
      {brandData && brandRank && (
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 3, mb: 4 }}>
          <Paper sx={{ p: 3, backgroundColor: '#75C9C8', color: 'white' }}>
            <Typography variant="h3" sx={{ fontWeight: 700 }}>
              {Math.round(brandData.share_of_voice || 0)}%
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
              {Math.round(brandData.leadership_visibility || 0)}%
            </Typography>
            <Typography variant="h6" sx={{ mt: 1, mb: 0.5 }}>
              Leadership Visibility
            </Typography>
            <Typography variant="body2">
              Leader or Featured positioning
            </Typography>
            <Typography variant="caption" sx={{ display: 'block', mt: 1, opacity: 0.9 }}>
              {brandData.leader_count} Leader + {brandData.featured_count} Featured
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
              Image
            </Button>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Comparison of share of voice for the top 10 organizations{!brandInTop10 && brandData ? ' (including your brand)' : ''}.
          </Typography>
          <Box ref={chartRef} sx={{ backgroundColor: 'white', p: 2, border: '1px solid #e0e0e0' }}>
            <ChartContainer width="100%" height={400}>
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
                    `${Math.round(value)}%`,
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
                    formatter={(value: any) => typeof value === 'number' ? `${Math.round(value)}%` : ''}
                    style={{ fontSize: '12px', fontWeight: 'bold' }}
                  />
                </Bar>
              </BarChart>
            </ChartContainer>
          </Box>
        </Paper>
      )}

      {/* Share of Voice Distribution - Table or Pie Chart */}
      <Paper sx={{ p: 4, mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box>
            <Typography variant="h6">
              Share of Voice Distribution
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              This shows what percentage of the total "conversation" each organization owns. Higher percentages indicate greater visibility and mind share in AI-generated content.
            </Typography>
          </Box>
          {pieData.length > 0 && (
            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={handleDownloadDistributionCSV}
              size="small"
            >
              Spreadsheet
            </Button>
          )}
        </Box>

        {pieData.length > 0 ? (
          <>
            {/* Show pie chart only if 5 or fewer total entities (brand + competitors) */}
            {pieData.length <= 5 ? (
              <ChartContainer width="100%" height={500}>
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
              </ChartContainer>
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

      {/* LLM Breakdown Chart */}
      {llmData && llmData.length > 0 && (
        <Paper sx={{ p: 4, mb: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box>
              <Typography variant="h6">
                Share of Voice by LLM Platform
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Brand vs. Competitor mentions across different AI platforms
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
                <YAxis label={{ value: 'Number of Mentions', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="brand" name="Your Brand" fill={BRAND_COLOR} />
                <Bar dataKey="competitors" name="Competitors" fill="#80a1d4" />
              </BarChart>
            </ChartContainer>
          </Box>

          {/* LLM Data Table */}
          <Box sx={{ overflowX: 'auto', mt: 3 }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #e0e0e0' }}>
                  <th style={{ textAlign: 'left', padding: '12px', fontWeight: 'bold' }}>Platform</th>
                  <th style={{ textAlign: 'right', padding: '12px', fontWeight: 'bold' }}>Your Brand</th>
                  <th style={{ textAlign: 'right', padding: '12px', fontWeight: 'bold' }}>Competitors</th>
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
                    <td style={{ padding: '12px', textAlign: 'right' }}>{item.brand || 0}</td>
                    <td style={{ padding: '12px', textAlign: 'right' }}>{item.competitors || 0}</td>
                    <td style={{ padding: '12px', textAlign: 'right', fontWeight: 'bold' }}>
                      {(item.brand || 0) + (item.competitors || 0)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Box>
        </Paper>
      )}

      {/* Share of Voice Over Time */}
      <Paper sx={{ p: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box>
            <Typography variant="h6">
              Share of Voice Trends
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Track how your brand's share of voice compares to top competitors over time
            </Typography>
          </Box>
          {sovTrends && sovTrends.length > 0 && (
            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={handleDownloadTrendChart}
              size="small"
            >
              Image
            </Button>
          )}
        </Box>

        {loadingTrends ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 100 }}>
            <CircularProgress />
          </Box>
        ) : sovTrends && sovTrends.length > 0 ? (
          <>
            {/* Format data for chart */}
            {(() => {
              // The API returns data in format: { date: "...", "OrgName1": 30, "OrgName2": 20, ... }
              // We need to format dates and extract organization names
              const formattedData = sovTrends.map((item: any) => {
                const result: any = {
                  date: formatDateEST(item.date, 'short')
                };
                // Copy all organization data (everything except 'date')
                Object.entries(item).forEach(([key, value]) => {
                  if (key !== 'date') {
                    result[key] = value;
                  }
                });
                return result;
              });

              // Get all organization names from the first data point (excluding 'date')
              const allOrgs = sovTrends.length > 0
                ? Object.keys(sovTrends[0]).filter(key => key !== 'date')
                : [];
              const orgNames = Array.from(allOrgs);

              // Identify which organization is the brand (from the share of voice data)
              const brandName = brandData?.name || null;

              return (
                <Box ref={trendChartRef} sx={{ backgroundColor: 'white', p: 2, border: '1px solid #e0e0e0', mt: 2 }}>
                <ChartContainer width="100%" height={800}>
                  <LineChart data={formattedData} margin={{ top: 20, right: 30, left: 20, bottom: 80 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="date"
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis
                      label={{ value: 'Share of Voice (%)', angle: -90, position: 'insideLeft' }}
                      domain={[0, 100]}
                    />
                    <Tooltip
                      formatter={(value: number) => [`${value}%`, '']}
                      labelFormatter={(label) => `Date: ${label}`}
                    />
                    <Legend wrapperStyle={{ paddingTop: '20px' }} />
                    {orgNames.map((org, index) => {
                      const isBrand = org === brandName;
                      // Use acronym for legend, but keep full name in tooltip
                      const legendName = isBrand ? 'Your Brand' : createAcronym(org);
                      return (
                        <Line
                          key={org}
                          type="monotone"
                          dataKey={org}
                          stroke={isBrand ? BRAND_COLOR : COMPETITOR_COLORS[index % COMPETITOR_COLORS.length]}
                          strokeWidth={formattedData.length === 1 ? 0 : (isBrand ? 3 : 2)}
                          name={legendName}
                          dot={{ fill: isBrand ? BRAND_COLOR : COMPETITOR_COLORS[index % COMPETITOR_COLORS.length], r: isBrand ? 8 : 6, stroke: isBrand ? BRAND_COLOR : COMPETITOR_COLORS[index % COMPETITOR_COLORS.length], strokeWidth: 2 }}
                          activeDot={{ r: isBrand ? 10 : 8 }}
                          connectNulls={true}
                        />
                      );
                    })}
                  </LineChart>
                </ChartContainer>
                </Box>
              );
            })()}
          </>
        ) : (
          <Alert severity="info">
            No share of voice trend data available yet. Data will appear after running data collection.
          </Alert>
        )}
      </Paper>
    </Box>
  );
}
