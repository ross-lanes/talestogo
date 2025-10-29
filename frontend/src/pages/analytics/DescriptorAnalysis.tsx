import { Box, Typography, Paper, CircularProgress, Alert, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { api } from '../../services/api';

export default function DescriptorAnalysis() {
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

  // Count descriptor occurrences in responses
  const descriptorCounts = new Map<string, number>();

  if (responses && Array.isArray(responses)) {
    responses.forEach((response: any) => {
      if (response.descriptors) {
        const descList = response.descriptors.split(',').map((d: string) => d.trim());
        descList.forEach((desc: string) => {
          if (desc) {
            descriptorCounts.set(desc, (descriptorCounts.get(desc) || 0) + 1);
          }
        });
      }
    });
  }

  // Convert to array and sort by count
  const descriptorStats = Array.from(descriptorCounts.entries())
    .map(([name, count]) => ({
      name,
      count,
      percentage: responses ? ((count / responses.length) * 100).toFixed(1) : 0
    }))
    .sort((a, b) => b.count - a.count);

  // Top 10 for chart
  const chartData = descriptorStats.slice(0, 10);

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
        <Typography variant="h6" gutterBottom>
          Your Target Descriptors
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Track your ideal brand descriptors. Green checkmarks (✓) show descriptors found in AI responses. Usage Rate indicates what percentage
          of all responses include each descriptor. Status reflects performance: Strong (≥20% usage), Moderate (10-20%), Weak (&lt;10%), or Not Used (0%).
        </Typography>
        {descriptors && descriptors.length > 0 ? (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Used</TableCell>
                  <TableCell>Target Descriptor</TableCell>
                  <TableCell>Category</TableCell>
                  <TableCell align="right">Mentions</TableCell>
                  <TableCell align="right">Usage Rate</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {descriptors
                  .map((desc: any) => {
                    const usage = descriptorCounts.get(desc.descriptor) || 0;
                    const usageRate = responses ? ((usage / responses.length) * 100).toFixed(1) : 0;
                    const isUsed = usage > 0;

                    let status = 'Not Used';
                    let statusColor = '#EA4A4A'; // Red for not used

                    if (usage > 0) {
                      if (Number(usageRate) >= 20) {
                        status = 'Strong';
                        statusColor = '#75C9C8'; // High - TALES teal
                      } else if (Number(usageRate) >= 10) {
                        status = 'Moderate';
                        statusColor = '#80A1D4'; // Medium - TALES blue
                      } else {
                        status = 'Weak';
                        statusColor = '#665775'; // Low - TALES purple
                      }
                    }

                    return { desc, usage, usageRate, isUsed, status, statusColor };
                  })
                  .sort((a: any, b: any) => Number(b.usageRate) - Number(a.usageRate))
                  .map(({ desc, usage, usageRate, isUsed, status, statusColor }: any, index: number) => (
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
                        <Chip
                          label={status}
                          size="small"
                          sx={{
                            backgroundColor: statusColor,
                            color: 'white'
                          }}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <Alert severity="info">
            No target descriptors defined yet. Add them in the Customize → Descriptors section.
          </Alert>
        )}
      </Paper>

      {/* All Descriptors Table */}
      <Paper sx={{ p: 4 }}>
        <Typography variant="h6" gutterBottom>
          All Descriptors Performance
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Complete ranking of every descriptor found in AI responses. Usage Rate shows what percentage of total responses include each descriptor.
        </Typography>
        {descriptorStats.length > 0 ? (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Rank</TableCell>
                  <TableCell>Descriptor</TableCell>
                  <TableCell align="right">Mentions</TableCell>
                  <TableCell align="right">Usage Rate</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {descriptorStats.map((desc, index) => (
                  <TableRow key={index}>
                    <TableCell>{index + 1}</TableCell>
                    <TableCell>
                      <Chip label={desc.name} color={index < 5 ? 'primary' : 'default'} size="small" />
                    </TableCell>
                    <TableCell align="right">{desc.count}</TableCell>
                    <TableCell align="right">{desc.percentage}%</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <Alert severity="info">
            No descriptor usage data available yet. Run analysis to see which descriptors are being used.
          </Alert>
        )}
      </Paper>
    </Box>
  );
}
