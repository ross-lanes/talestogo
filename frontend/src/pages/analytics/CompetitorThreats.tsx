import { Box, Typography, Paper, CircularProgress, Alert, Chip, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp as ThreatIcon } from '@mui/icons-material';
import { api } from '../../services/api';

export default function CompetitorThreats() {
  const { data: shareOfVoice, isLoading: loadingSov } = useQuery({
    queryKey: ['share-of-voice-threats'],
    queryFn: async () => {
      const response = await api.get('/analytics/share-of-voice');
      return response.data;
    },
  });

  const { data: responses, isLoading: loadingResponses } = useQuery({
    queryKey: ['responses-threats'],
    queryFn: async () => {
      const response = await api.get('/responses/');
      return response.data;
    },
  });

  const isLoading = loadingSov || loadingResponses;

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  // Analyze competitor threats
  const brandName = shareOfVoice?.find((item: any) => item.is_brand)?.organization || 'Your Brand';
  const competitors = Array.isArray(shareOfVoice) ? shareOfVoice.filter((item: any) => !item.is_brand) : [];

  // Calculate threat scores based on mention count and sentiment
  const competitorThreats = competitors.map((comp: any) => {
    // Count negative mentions about our brand when competitor is mentioned
    const competitiveResponses = Array.isArray(responses) ? responses.filter((r: any) =>
      r.competitors && r.competitors.includes(comp.organization)
    ) : [];

    const negativeWhenCompetitorPresent = competitiveResponses.filter((r: any) =>
      r.sentiment === 'Negative' || r.sentiment === 'Very Negative'
    ).length;

    const positiveCompetitor = competitiveResponses.filter((r: any) =>
      r.sentiment === 'Positive' || r.sentiment === 'Very Positive'
    ).length;

    // Threat score: higher mention count + negative sentiment for us = higher threat
    const threatScore = (comp.total_mentions || 0) * 0.7 +
                        negativeWhenCompetitorPresent * 2 +
                        positiveCompetitor * 1.5;

    return {
      name: comp.organization,
      mention_count: comp.total_mentions || 0,
      share_of_voice: comp.share_of_voice || 0,
      competitive_responses: competitiveResponses.length,
      negative_overlap: negativeWhenCompetitorPresent,
      positive_competitor: positiveCompetitor,
      threatScore: Math.round(threatScore),
      threatLevel: threatScore > 50 ? 'High' : threatScore > 20 ? 'Medium' : 'Low'
    };
  }).sort((a, b) => b.threatScore - a.threatScore);

  const chartData = competitorThreats.slice(0, 10);

  const getThreatColor = (level: string) => {
    switch(level) {
      case 'High': return '#75C9C8';   // High - TALES teal
      case 'Medium': return '#80A1D4'; // Medium - TALES blue
      case 'Low': return '#665775';    // Low - TALES purple
      default: return '#80a1d4';       // TALES blue for unknown
    }
  };

  return (
    <Box>
      <Typography variant="h2" component="h1" gutterBottom>
        Competitor Threats
      </Typography>

      {/* Static Explanatory Text */}
      <Paper sx={{ p: 3, mb: 4, backgroundColor: '#f9f9f9' }}>
        <Typography variant="body1" sx={{ mb: 2 }}>
          TALES' threat risk calculation considers three key factors: how often the competitor appears in AI responses (mention frequency), whether your brand receives negative sentiment when this competitor is mentioned (competitive pressure), and whether the competitor receives positive sentiment (competitive advantage).
        </Typography>
        <Typography variant="body1">
          Competitors are rated as <strong>High</strong> threat (score &gt;50) requiring immediate strategic attention, <strong>Medium</strong> threat (score 20-50) requiring monitoring, or <strong>Low</strong> threat (score &lt;20) representing minimal competitive pressure.
        </Typography>
      </Paper>

      {/* Summary Metrics */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 3, mb: 4 }}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h4" sx={{ color: '#75C9C8' }}>
            {competitorThreats.filter(c => c.threatLevel === 'High').length}
          </Typography>
          <Typography variant="body1">High Threat Competitors</Typography>
          <Typography variant="caption" color="text.secondary">Require immediate attention</Typography>
        </Paper>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h4" sx={{ color: '#80A1D4' }}>
            {competitorThreats.filter(c => c.threatLevel === 'Medium').length}
          </Typography>
          <Typography variant="body1">Medium Threat</Typography>
          <Typography variant="caption" color="text.secondary">Monitor closely</Typography>
        </Paper>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h4" sx={{ color: '#665775' }}>
            {competitorThreats.filter(c => c.threatLevel === 'Low').length}
          </Typography>
          <Typography variant="body1">Low Threat</Typography>
          <Typography variant="caption" color="text.secondary">Minimal competition</Typography>
        </Paper>
      </Box>

      {/* Detailed Threat Analysis Table */}
      <Paper sx={{ p: 4 }}>
        <Typography variant="h6" gutterBottom>
          Detailed Threat Analysis
        </Typography>
        {competitorThreats.length > 0 ? (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Rank</TableCell>
                  <TableCell>Competitor</TableCell>
                  <TableCell>Threat Level</TableCell>
                  <TableCell align="right">Threat Score</TableCell>
                  <TableCell align="right">Mentions</TableCell>
                  <TableCell align="right">Share of Voice</TableCell>
                  <TableCell>Competing Descriptors</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {competitorThreats.map((comp, index) => {
                  // Extract descriptors for this competitor
                  const compResponses = Array.isArray(responses) ? responses.filter((r: any) =>
                    r.competitors && r.competitors.includes(comp.name)
                  ) : [];

                  const descriptorsInCompResponses = compResponses
                    .filter((r: any) => r.descriptors)
                    .map((r: any) => r.descriptors)
                    .join(', ')
                    .split(',')
                    .map(d => d.trim())
                    .filter(d => d.length > 0);

                  const uniqueDescriptors = [...new Set(descriptorsInCompResponses)];
                  const descriptorDisplay = uniqueDescriptors.length > 0
                    ? uniqueDescriptors.slice(0, 3).join(', ') + (uniqueDescriptors.length > 3 ? '...' : '')
                    : 'None identified';

                  return (
                    <TableRow key={index}>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {index < 3 && <ThreatIcon color="error" />}
                          {index + 1}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontWeight="bold">
                          {comp.name}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={comp.threatLevel}
                          size="small"
                          sx={{
                            backgroundColor: getThreatColor(comp.threatLevel),
                            color: 'white'
                          }}
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" fontWeight="bold">
                          {comp.threatScore}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">{comp.mention_count}</TableCell>
                      <TableCell align="right">{comp.share_of_voice.toFixed(1)}%</TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontSize: '0.875rem' }}>
                          {descriptorDisplay}
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
            No competitor threat data available yet. Run analysis to identify competitive threats.
          </Alert>
        )}
      </Paper>

    </Box>
  );
}
