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
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Analyze which descriptive terms are most commonly associated with your brand in AI responses.
      </Typography>

      {/* Key Metrics */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 3, mb: 4 }}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h4">{descriptors?.length || 0}</Typography>
          <Typography variant="body1">Target Descriptors</Typography>
          <Typography variant="caption" color="text.secondary">Defined in your profile</Typography>
        </Paper>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h4">{descriptorStats.length}</Typography>
          <Typography variant="body1">Unique Descriptors Used</Typography>
          <Typography variant="caption" color="text.secondary">Found in responses</Typography>
        </Paper>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h4">{responses?.length || 0}</Typography>
          <Typography variant="body1">Total Responses</Typography>
          <Typography variant="caption" color="text.secondary">Analyzed for descriptors</Typography>
        </Paper>
      </Box>

      {/* Top 10 Bar Chart */}
      {chartData.length > 0 && (
        <Paper sx={{ p: 4, mb: 4 }}>
          <Typography variant="h6" gutterBottom>
            Top 10 Most Common Descriptors
          </Typography>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={chartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="name" type="category" width={150} />
              <Tooltip formatter={(value: number) => [`${value} mentions`, 'Count']} />
              <Legend />
              <Bar dataKey="count" name="Mentions" fill="#665775" />
            </BarChart>
          </ResponsiveContainer>
        </Paper>
      )}

      {/* All Descriptors Table */}
      <Paper sx={{ p: 4, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          All Descriptors Performance
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

      {/* Target Descriptors */}
      <Paper sx={{ p: 4 }}>
        <Typography variant="h6" gutterBottom>
          Your Target Descriptors
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          These are the descriptors you've defined as ideal for your brand. Track how often they appear in AI responses.
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 2 }}>
          {descriptors && descriptors.length > 0 ? (
            descriptors.map((desc: any, index: number) => {
              const usage = descriptorCounts.get(desc.descriptor_text) || 0;
              return (
                <Chip
                  key={index}
                  label={`${desc.descriptor_text} ${usage > 0 ? `(${usage})` : ''}`}
                  color={usage > 0 ? 'success' : 'default'}
                  variant={usage > 0 ? 'filled' : 'outlined'}
                />
              );
            })
          ) : (
            <Typography variant="body2" color="text.secondary">
              No target descriptors defined yet. Add them in the Customize section.
            </Typography>
          )}
        </Box>
      </Paper>
    </Box>
  );
}
