import { Box, Typography, Paper, CircularProgress, Alert, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Button } from '@mui/material';
import { Download as DownloadIcon, Image as ImageIcon } from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { api } from '../../services/api';
import html2canvas from 'html2canvas';
import { useRef } from 'react';

export default function DescriptorAnalysis() {
  const tableRef = useRef<HTMLDivElement>(null);

  const { data: descriptors, isLoading, error } = useQuery({
    queryKey: ['descriptors'],
    queryFn: async () => {
      const response = await api.get('/descriptors/');
      return response.data;
    },
  });

  const { data: responses } = useQuery({
    queryKey: ['responses'],
    queryFn: async () => {
      const response = await api.get('/responses/');
      return response.data;
    },
  });

  const { data: insights, isLoading: insightsLoading } = useQuery({
    queryKey: ['descriptor-insights'],
    queryFn: async () => {
      const response = await api.get('/analytics/descriptors/insights');
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
        Failed to load descriptor analysis. Please try again later.
      </Alert>
    );
  }

  // Count descriptor occurrences in responses where brand is mentioned
  const descriptorCounts = new Map<string, number>();
  let brandMentionCount = 0;

  if (responses && Array.isArray(responses)) {
    responses.forEach((response: any) => {
      // Only count descriptors from responses where the brand is mentioned
      if (response.brand_mentioned === 'Yes') {
        brandMentionCount++;
        if (response.descriptors) {
          const descList = response.descriptors.split(',').map((d: string) => d.trim());
          descList.forEach((desc: string) => {
            if (desc) {
              descriptorCounts.set(desc, (descriptorCounts.get(desc) || 0) + 1);
            }
          });
        }
      }
    });
  }

  // Convert to array and sort by count
  const descriptorStats = Array.from(descriptorCounts.entries())
    .map(([name, count]) => ({
      name,
      count,
      percentage: brandMentionCount > 0 ? ((count / brandMentionCount) * 100).toFixed(1) : 0
    }))
    .sort((a, b) => b.count - a.count);

  // Top 10 for chart
  const chartData = descriptorStats.slice(0, 10);

  // Prepare sorted data for table display and downloads
  const sortedDescriptorsData = descriptors
    ? descriptors
        .map((desc: any) => {
          const usage = descriptorCounts.get(desc.descriptor) || 0;
          const usageRate = brandMentionCount > 0 ? ((usage / brandMentionCount) * 100).toFixed(1) : 0;
          const isUsed = usage > 0;

          let status = 'Not Used';
          if (usage > 0) {
            if (Number(usageRate) >= 20) {
              status = 'Strong';
            } else if (Number(usageRate) >= 10) {
              status = 'Moderate';
            } else {
              status = 'Weak';
            }
          }

          return { desc, usage, usageRate, isUsed, status };
        })
        .sort((a: any, b: any) => Number(b.usageRate) - Number(a.usageRate))
    : [];

  const handleDownloadCSV = () => {
    if (!sortedDescriptorsData || sortedDescriptorsData.length === 0) return;

    const csvHeaders = ['Used with Brand', 'Target Descriptor', 'Category', 'Mentions', 'Usage Rate', 'Status'];
    const csvRows = sortedDescriptorsData.map((item: any) => [
      item.isUsed ? 'Yes' : 'No',
      `"${item.desc.descriptor.replace(/"/g, '""')}"`,
      `"${(item.desc.category || 'Uncategorized').replace(/"/g, '""')}"`,
      item.usage,
      `${item.usageRate}%`,
      item.status
    ]);

    const csvContent = [
      csvHeaders.join(','),
      ...csvRows.map(row => row.join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const today = new Date();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    const year = today.getFullYear();
    const dateStr = `${month}_${day}_${year}`;

    link.download = `TargetDescriptors_${dateStr}.csv`;
    link.href = URL.createObjectURL(blob);
    link.click();
    URL.revokeObjectURL(link.href);
  };

  const handleDownloadTop5Image = async () => {
    if (!tableRef.current) return;

    // Temporarily hide all rows except top 5
    const allRows = tableRef.current.querySelectorAll('tbody tr');
    const rowsToHide: HTMLElement[] = [];

    allRows.forEach((row, index) => {
      if (index >= 5) {
        rowsToHide.push(row as HTMLElement);
        (row as HTMLElement).style.display = 'none';
      }
    });

    try {
      const canvas = await html2canvas(tableRef.current, {
        backgroundColor: '#ffffff',
        scale: 2,
        useCORS: true,
        logging: false,
        allowTaint: true,
      });

      canvas.toBlob((blob) => {
        if (blob) {
          const url = URL.createObjectURL(blob);
          const link = document.createElement('a');
          const today = new Date();
          const month = String(today.getMonth() + 1).padStart(2, '0');
          const day = String(today.getDate()).padStart(2, '0');
          const year = today.getFullYear();
          const dateStr = `${month}_${day}_${year}`;

          link.download = `Top5_TargetDescriptors_${dateStr}.png`;
          link.href = url;
          link.click();
          URL.revokeObjectURL(url);
        }
      });
    } finally {
      // Restore hidden rows
      rowsToHide.forEach(row => {
        row.style.display = '';
      });
    }
  };

  return (
    <Box>
      <Typography variant="h2" component="h1" gutterBottom>
        Descriptor Analysis
      </Typography>

      {/* Explanatory Text */}
      <Paper sx={{ p: 3, mb: 4, backgroundColor: '#f9f9f9' }}>
        <Typography variant="body1">
          <strong>Descriptors</strong> are the specific words and phrases AI systems use to characterize your brand. TALES identifies descriptors by analyzing the language patterns in AI responses where your brand is mentioned, tracking which adjectives and descriptive terms appear most frequently. Understanding your descriptor profile reveals how AI models perceive and present your brand identity, helping you align your messaging strategy with how you're actually being described in AI-generated content.
        </Typography>
      </Paper>

      {/* Target Descriptors - Consolidated Table */}
      <Paper sx={{ p: 4, mb: 4 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">
            Your Target Descriptors
          </Typography>
          <Box display="flex" gap={1}>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={handleDownloadCSV}
              size="small"
              disabled={!descriptors || descriptors.length === 0}
            >
              Download as CSV
            </Button>
            <Button
              variant="outlined"
              startIcon={<ImageIcon />}
              onClick={handleDownloadTop5Image}
              size="small"
              disabled={!descriptors || descriptors.length === 0}
            >
              Download Top 5 as Image
            </Button>
          </Box>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Track your ideal brand descriptors. Green checkmarks (✓) show descriptors found in AI responses where your brand is mentioned. Usage Rate indicates what percentage
          of brand mentions include each descriptor. Status reflects performance: Strong (≥20% usage), Moderate (10-20%), Weak (&lt;10%), or Not Used (0%).
        </Typography>
        {descriptors && descriptors.length > 0 ? (
          <TableContainer ref={tableRef}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Used with Brand</TableCell>
                  <TableCell>Target Descriptor</TableCell>
                  <TableCell>Category</TableCell>
                  <TableCell align="right">Mentions</TableCell>
                  <TableCell align="right">Usage Rate</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {sortedDescriptorsData.map((item: any, index: number) => {
                  const { desc, usage, usageRate, isUsed, status } = item;

                  let statusColor = '#EA4A4A'; // Red for not used
                  if (status === 'Strong') {
                    statusColor = '#75C9C8'; // High - TALES teal
                  } else if (status === 'Moderate') {
                    statusColor = '#80A1D4'; // Medium - TALES blue
                  } else if (status === 'Weak') {
                    statusColor = '#665775'; // Low - TALES purple
                  }

                  return (
                    <TableRow key={index}>
                      <TableCell>
                        {isUsed ? (
                          <Box sx={{ color: '#58A13B', fontSize: '24px', fontWeight: 'bold' }}>✓</Box>
                        ) : (
                          <Box sx={{ color: '#EA4A4A', fontSize: '24px' }}>✗</Box>
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontWeight={isUsed ? 'bold' : 'normal'}>
                          {desc.descriptor}
                        </Typography>
                      </TableCell>
                      <TableCell>{desc.category || 'Uncategorized'}</TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" fontWeight={isUsed ? 'bold' : 'normal'}>
                          {usage}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" fontWeight={isUsed ? 'bold' : 'normal'}>
                          {usageRate}%
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography
                          variant="body2"
                          sx={{
                            color: statusColor,
                            fontWeight: 'bold'
                          }}
                        >
                          {status}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <Alert severity="info">
            No target descriptors defined yet. Add them in the Customize → Descriptors section.
          </Alert>
        )}
      </Paper>

      {/* AI-Generated Descriptor Insights */}
      <Paper sx={{ p: 4, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Descriptor Analysis & Insights
        </Typography>
        {insightsLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress size={40} />
          </Box>
        ) : insights?.analysis ? (
          <Box>
            {insights.summary_stats && (
              <Box sx={{ mb: 3, p: 2, backgroundColor: '#f5f5f5', borderRadius: 1 }}>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Quick Stats:</strong>
                </Typography>
                <Typography variant="body2">
                  • Total unique descriptors found: {insights.summary_stats.total_unique_descriptors}
                </Typography>
                <Typography variant="body2">
                  • Target descriptors tracked: {insights.summary_stats.target_descriptors_tracked}
                </Typography>
                <Typography variant="body2">
                  • Target descriptors used: {insights.summary_stats.target_descriptors_used}
                </Typography>
                <Typography variant="body2">
                  • Target descriptors unused: {insights.summary_stats.target_descriptors_unused}
                </Typography>
                {insights.summary_stats.most_frequent_descriptor && (
                  <Typography variant="body2">
                    • Most frequent descriptor: "{insights.summary_stats.most_frequent_descriptor}" ({insights.summary_stats.most_frequent_count} mentions)
                  </Typography>
                )}
              </Box>
            )}
            <Typography
              variant="body1"
              sx={{
                whiteSpace: 'pre-wrap',
                lineHeight: 1.8
              }}
            >
              {insights.analysis}
            </Typography>
          </Box>
        ) : (
          <Alert severity="info">
            Descriptor insights are being generated. This may take a moment...
          </Alert>
        )}
      </Paper>
    </Box>
  );
}
