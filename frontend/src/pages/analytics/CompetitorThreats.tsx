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
  const brandName = shareOfVoice?.find((item: any) => item.is_brand)?.name || 'Your Brand';
  const competitors = Array.isArray(shareOfVoice) ? shareOfVoice.filter((item: any) => !item.is_brand) : [];

  // Calculate threat scores based on mention count and sentiment
  const competitorThreats = competitors.map((comp: any) => {
    // Count negative mentions about our brand when competitor is mentioned
    const competitiveResponses = Array.isArray(responses) ? responses.filter((r: any) =>
      r.competitors && r.competitors.includes(comp.name)
    ) : [];

    const negativeWhenCompetitorPresent = competitiveResponses.filter((r: any) =>
      r.sentiment === 'Negative' || r.sentiment === 'Very Negative'
    ).length;

    const positiveCompetitor = competitiveResponses.filter((r: any) =>
      r.sentiment === 'Positive' || r.sentiment === 'Very Positive'
    ).length;

    // Threat score: higher mention count + negative sentiment for us = higher threat
    const threatScore = (comp.mention_count || 0) * 0.7 +
                        negativeWhenCompetitorPresent * 2 +
                        positiveCompetitor * 1.5;

    return {
      name: comp.name,
      mention_count: comp.mention_count || 0,
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
      case 'High': return '#f44336';
      case 'Medium': return '#e65100';  // Darker orange for better readability
      case 'Low': return '#4caf50';
      default: return '#9e9e9e';
    }
  };

  return (
    <Box>
      <Typography variant="h2" component="h1" gutterBottom>
        Competitor Threats
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Identify which competitors pose the greatest threat to your brand's visibility in AI responses.
      </Typography>

      {/* Summary Metrics */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 3, mb: 4 }}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h4" color="error.main">
            {competitorThreats.filter(c => c.threatLevel === 'High').length}
          </Typography>
          <Typography variant="body1">High Threat Competitors</Typography>
          <Typography variant="caption" color="text.secondary">Require immediate attention</Typography>
        </Paper>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h4" sx={{ color: '#e65100' }}>
            {competitorThreats.filter(c => c.threatLevel === 'Medium').length}
          </Typography>
          <Typography variant="body1">Medium Threat</Typography>
          <Typography variant="caption" color="text.secondary">Monitor closely</Typography>
        </Paper>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h4" color="success.main">
            {competitorThreats.filter(c => c.threatLevel === 'Low').length}
          </Typography>
          <Typography variant="body1">Low Threat</Typography>
          <Typography variant="caption" color="text.secondary">Minimal competition</Typography>
        </Paper>
      </Box>

      {/* Threat Score Chart */}
      {chartData.length > 0 && (
        <Paper sx={{ p: 4, mb: 4 }}>
          <Typography variant="h6" gutterBottom>
            Top Competitor Threat Scores
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Higher scores indicate stronger competitive pressure based on mention frequency and sentiment.
          </Typography>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="threatScore" name="Threat Score" fill="#f44336" />
            </BarChart>
          </ResponsiveContainer>
        </Paper>
      )}

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
                  <TableCell align="right">Competitive Overlap</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {competitorThreats.map((comp, index) => (
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
                    <TableCell align="right">
                      {comp.competitive_responses} responses
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <Alert severity="info">
            No competitor threat data available yet. Run analysis to identify competitive threats.
          </Alert>
        )}
      </Paper>

      {/* Threat Explanation */}
      <Paper sx={{ p: 4, mt: 4, backgroundColor: '#f5f5f5' }}>
        <Typography variant="h6" gutterBottom>
          How Threat Scores Are Calculated
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Threat scores are calculated based on multiple factors:
        </Typography>
        <ul>
          <li>
            <Typography variant="body2"><strong>Mention Frequency (70%):</strong> How often the competitor appears in AI responses</Typography>
          </li>
          <li>
            <Typography variant="body2"><strong>Negative Brand Sentiment (2x weight):</strong> When your brand receives negative sentiment in responses that mention this competitor</Typography>
          </li>
          <li>
            <Typography variant="body2"><strong>Positive Competitor Sentiment (1.5x weight):</strong> When the competitor receives positive sentiment</Typography>
          </li>
        </ul>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          <strong>Threat Levels:</strong> High (&gt;50), Medium (20-50), Low (&lt;20)
        </Typography>
      </Paper>
    </Box>
  );
}
