import { Box, Typography, Paper, CircularProgress, Alert, Button, Divider } from '@mui/material';
import { Lightbulb as LightbulbIcon, Refresh as RefreshIcon } from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../services/api';
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

          {(() => {
            // Split content and render with proper styling for numbered recommendations
            const sections = data.recommendations.split(/###\s+/).filter((s: string) => s.trim());

            return sections.map((section: string, sectionIndex: number) => {
              const lines = section.split('\n').filter((line: string) => line.trim());

              return (
                <Box key={sectionIndex}>
                  {sectionIndex > 0 && (
                    <Divider sx={{ my: 4, borderColor: '#80A1D4', borderWidth: 2 }} />
                  )}
                  {lines.map((line: string, lineIndex: number) => {
                    const trimmedLine = line.trim();
                    // Strip markdown bold syntax (**text**)
                    const cleanedLine = trimmedLine.replace(/\*\*/g, '');

                    // Check if this line is a numbered recommendation title (e.g., "Recommendation 1:", "1.", etc.)
                    const isNumberedTitle = /^(Recommendation\s+\d+|^\d+[\.:)])/i.test(cleanedLine);

                    // Check if this line is a subsection heading (Strategic Rationale, Key Actions, etc.)
                    // Match with or without colon, and handle common variations
                    const isSubsectionHeading = /^(Strategic Rationale|Key Actions|Expected Impact|Implementation Timeline|Success Metrics|Next Steps|Rationale|Actions|Impact|Timeline|Metrics)/i.test(cleanedLine);

                    if (isNumberedTitle) {
                      return (
                        <Typography
                          key={lineIndex}
                          variant="h5"
                          component="h3"
                          sx={{
                            mb: 2,
                            mt: lineIndex > 0 ? 3 : 0,
                            fontWeight: 'bold',
                            fontSize: '1.5rem',
                            color: 'inherit'
                          }}
                        >
                          {cleanedLine}
                        </Typography>
                      );
                    }

                    if (isSubsectionHeading) {
                      return (
                        <Typography
                          key={lineIndex}
                          variant="body1"
                          sx={{ mb: 1, mt: 2, lineHeight: 1.7, fontWeight: 'bold' }}
                        >
                          {cleanedLine}
                        </Typography>
                      );
                    }

                    // Regular content
                    return (
                      <Typography
                        key={lineIndex}
                        variant="body1"
                        sx={{ mb: 1, lineHeight: 1.7 }}
                      >
                        {cleanedLine}
                      </Typography>
                    );
                  })}
                </Box>
              );
            });
          })()}
        </Paper>
      )}
    </Box>
  );
}
