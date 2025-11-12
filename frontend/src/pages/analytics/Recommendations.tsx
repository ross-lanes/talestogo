import { Box, Typography, Paper, CircularProgress, Alert, Button } from '@mui/material';
import { Lightbulb as LightbulbIcon, Refresh as RefreshIcon } from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../services/api';
import ReactMarkdown from 'react-markdown';
import { formatDateEST } from '../../utils/dateUtils';

export default function Recommendations() {

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['recommendations'],
    queryFn: async () => {
      const response = await api.get('/analytics/recommendations');
      return response.data;
    },
  });

  const formatDate = (isoString: string) => {
    return formatDateEST(isoString, 'full');
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
      <Box sx={{ p: 4 }}>
        <Alert severity="error">
          Failed to load recommendations. Please try again.
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 4 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <LightbulbIcon sx={{ fontSize: 40, color: '#1976d2' }} />
          <Typography variant="h4" component="h1">
            Strategic Recommendations
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={() => refetch()}
        >
          Refresh
        </Button>
      </Box>

      {!data?.has_recommendations ? (
        <Paper sx={{ p: 4 }}>
          <Alert severity="info">
            {data?.message || 'No recommendations available yet.'}
          </Alert>
        </Paper>
      ) : (
        <Paper sx={{ p: 4, mb: 4 }}>
          {data.report_date && (
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 3 }}>
              Generated from analysis on {formatDate(data.report_date)}
            </Typography>
          )}

          <Box
            sx={{
              '& h3': {
                mt: 3,
                mb: 2,
                fontSize: '1.75rem',
                fontWeight: 700,
              },
              '& h4': {
                mt: 2,
                mb: 1,
                fontSize: '1.25rem',
                fontWeight: 500,
              },
              '& p': {
                mb: 2,
                lineHeight: 1.7,
              },
              '& ul, & ol': {
                mb: 2,
                pl: 3,
              },
              '& li': {
                mb: 1,
                lineHeight: 1.7,
              },
              '& strong': {
                fontWeight: 600,
              },
              '& em': {
                fontStyle: 'italic',
              },
              '& code': {
                backgroundColor: '#f5f5f5',
                padding: '2px 6px',
                borderRadius: 1,
                fontFamily: 'monospace',
              },
            }}
          >
            <ReactMarkdown>{data.recommendations}</ReactMarkdown>
          </Box>
        </Paper>
      )}
    </Box>
  );
}
