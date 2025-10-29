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
      case 'High': return '#EA4A4A';   // Red from extended palette
      case 'Medium': return '#A13C84'; // Purple from extended palette
      case 'Low': return '#58A13B';    // Green from extended palette
      default: return '#c0b9dd';       // TALES lavender for unknown
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
          A <strong>threat</strong> is defined as a competitor whose presence in AI responses correlates with reduced visibility or negative sentiment for your brand. TALES calculates threat risk by analyzing the frequency of competitor mentions, their positioning relative to your brand, and the sentiment patterns when they appear alongside your brand.
        </Typography>
        <Typography variant="body1" sx={{ mb: 2 }}>
          Our threat risk calculation considers three key factors: how often the competitor appears in AI responses (mention frequency), whether your brand receives negative sentiment when this competitor is mentioned (competitive pressure), and whether the competitor receives positive sentiment (competitive advantage).
        </Typography>
        <Typography variant="body1">
          Competitors are rated as <strong>High</strong> threat (score &gt;50) requiring immediate strategic attention, <strong>Medium</strong> threat (score 20-50) requiring monitoring, or <strong>Low</strong> threat (score &lt;20) representing minimal competitive pressure.
        </Typography>
      </Paper>

      {/* Threat Assessment List */}
      <Paper sx={{ p: 4, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Threat Assessment
        </Typography>
        {competitorThreats.length > 0 ? (
          <Box>
            {competitorThreats.map((comp, index) => {
              // Generate assessment reasoning
              let reason = '';
              if (comp.threatLevel === 'High') {
                reason = `${comp.name} appears in ${comp.mention_count} AI responses with significant competitive overlap (${comp.competitive_responses} responses). `;
                if (comp.negative_overlap > 0) {
                  reason += `Your brand received negative sentiment in ${comp.negative_overlap} responses where ${comp.name} was mentioned. `;
                }
                if (comp.positive_competitor > 0) {
                  reason += `${comp.name} received positive sentiment in ${comp.positive_competitor} of these responses. `;
                }
                reason += 'This competitor poses a significant threat to your brand positioning.';
              } else if (comp.threatLevel === 'Medium') {
                reason = `${comp.name} has a moderate presence with ${comp.mention_count} mentions and ${comp.share_of_voice.toFixed(1)}% share of voice. `;
                if (comp.competitive_responses > 0) {
                  reason += `They appear alongside your brand in ${comp.competitive_responses} responses. `;
                }
                reason += 'Monitor this competitor to prevent escalation.';
              } else {
                reason = `${comp.name} has limited visibility with ${comp.mention_count} mentions and ${comp.share_of_voice.toFixed(1)}% share of voice. This competitor currently poses minimal threat to your brand positioning.`;
              }

              return (
                <Box
                  key={index}
                  sx={{
                    mb: 3,
                    pb: 3,
                    borderBottom: index < competitorThreats.length - 1 ? '1px solid #e0e0e0' : 'none'
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                    <Typography variant="h6" component="span">
                      {comp.name}
                    </Typography>
                    <Chip
                      label={`Threat Risk: ${comp.threatLevel}`}
                      size="small"
                      sx={{
                        backgroundColor: getThreatColor(comp.threatLevel),
                        color: 'white',
                        fontWeight: 'bold'
                      }}
                    />
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    {reason}
                  </Typography>
                </Box>
              );
            })}
          </Box>
        ) : (
          <Alert severity="info">
            No competitor threat data available yet. Run analysis to identify competitive threats.
          </Alert>
        )}
      </Paper>

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
          <Typography variant="h4" sx={{ color: '#A13C84' }}>
            {competitorThreats.filter(c => c.threatLevel === 'Medium').length}
          </Typography>
          <Typography variant="body1">Medium Threat</Typography>
          <Typography variant="caption" color="text.secondary">Monitor closely</Typography>
        </Paper>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h4" sx={{ color: '#58A13B' }}>
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

    </Box>
  );
}
