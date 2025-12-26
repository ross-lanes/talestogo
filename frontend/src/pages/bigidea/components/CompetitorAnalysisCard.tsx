import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Divider,
  LinearProgress,
} from '@mui/material';
import type { CompetitorAnalysis } from '../../../types/bigidea';

interface CompetitorAnalysisCardProps {
  analysis: CompetitorAnalysis;
}

export default function CompetitorAnalysisCard({ analysis }: CompetitorAnalysisCardProps) {
  return (
    <Card
      elevation={0}
      sx={{
        border: '1px solid',
        borderColor: 'divider',
        borderRadius: 2,
        bgcolor: 'grey.50',
      }}
    >
      <CardContent>
        <Typography variant="h6" fontWeight={600} gutterBottom>
          Competitor Analysis
        </Typography>

        {/* Competitors List */}
        {analysis.competitors.length > 0 && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Key Competitors
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {analysis.competitors.map((competitor, idx) => (
                <Chip key={idx} label={competitor} size="small" variant="outlined" />
              ))}
            </Box>
          </Box>
        )}

        {/* Market Share Chart */}
        {analysis.marketShareData && analysis.marketShareData.length > 0 && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Estimated Market Share
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
              {analysis.marketShareData.map((item, idx) => (
                <Box key={idx}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="body2">{item.name}</Typography>
                    <Typography variant="body2" fontWeight={500}>
                      {item.percentage}%
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={Math.min(item.percentage, 100)}
                    sx={{
                      height: 8,
                      borderRadius: 4,
                      bgcolor: 'grey.200',
                      '& .MuiLinearProgress-bar': {
                        borderRadius: 4,
                      },
                    }}
                  />
                </Box>
              ))}
            </Box>
          </Box>
        )}

        <Divider sx={{ my: 2 }} />

        {/* Competitor Strategies */}
        {analysis.competitorStrategies && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Competitor Strategies
            </Typography>
            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
              {analysis.competitorStrategies}
            </Typography>
          </Box>
        )}

        {/* Differentiation Strategies */}
        {analysis.differentiationStrategies && (
          <Box>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Differentiation Opportunities
            </Typography>
            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
              {analysis.differentiationStrategies}
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
