import { Box, Typography, Paper, CircularProgress, Alert, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Button } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { TrendingUp as ThreatIcon, Download as DownloadIcon, Image as ImageIcon } from '@mui/icons-material';
import { api } from '../../services/api';
import html2canvas from 'html2canvas';
import { useRef, useState } from 'react';
import { competitorsInclude } from '../../utils/organizationNormalizer';
import BatchSelector from '../../components/BatchSelector';
import { formatDateForFilename } from '../../utils/dateUtils';
import ChartContainer from '../../components/ChartContainer';

// Platform colors for consistency
const PLATFORM_COLORS: Record<string, string> = {
  'ChatGPT': '#10A37F',
  'Claude': '#CC785C',
  'Gemini': '#4285F4',
  'Perplexity': '#1FB8CD'
};

export default function CompetitorThreats() {
  const tableRef = useRef<HTMLDivElement>(null);
  const llmChartRef = useRef<HTMLDivElement>(null);
  const [selectedBatchId, setSelectedBatchId] = useState<number | null>(null);

  // Fetch competitor threats from API (includes all calculations)
  const { data: competitorThreats, isLoading } = useQuery({
    queryKey: ['competitor-threats', selectedBatchId],
    queryFn: async () => {
      const params = selectedBatchId ? { batch_id: selectedBatchId } : {};
      const response = await api.get('/analytics/competitor-threats', { params });
      return response.data;
    },
  });

  // Fetch responses for descriptor display only
  const { data: responses } = useQuery({
    queryKey: ['responses-threats'],
    queryFn: async () => {
      const response = await api.get('/responses/');
      return response.data;
    },
  });

  // Fetch LLM breakdown data
  const { data: llmData, isLoading: llmLoading, error: llmError } = useQuery({
    queryKey: ['threats-by-llm'],
    queryFn: async () => {
      const response = await api.get('/analytics/threats-by-llm');
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

  // Use threat data from API (already sorted by threat score)
  const threats = competitorThreats || [];

  const chartData = threats.slice(0, 10);

  const getThreatColor = (level: string) => {
    switch(level) {
      case 'High': return '#75C9C8';   // High - TALES teal
      case 'Medium': return '#80A1D4'; // Medium - TALES blue
      case 'Low': return '#003e60';    // Low - TALES purple
      default: return '#80a1d4';       // TALES blue for unknown
    }
  };

  const handleDownloadCSV = () => {
    if (!threats || threats.length === 0) return;

    const csvHeaders = ['Rank', 'Competitor', 'Threat Level', 'Threat Score', 'Mentions', 'Share of Voice'];
    const csvRows = threats.map((comp: any, index: number) => [
      index + 1,
      `"${comp.name.replace(/"/g, '""')}"`,
      comp.threat_level,
      comp.threat_score,
      comp.mention_count,
      `${Math.round(comp.share_of_voice)}%`
    ]);

    const csvContent = [
      csvHeaders.join(','),
      ...csvRows.map((row: any) => row.join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const today = new Date();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    const year = today.getFullYear();
    const dateStr = `${month}_${day}_${year}`;

    link.download = `ThreatAnalysis_${dateStr}.csv`;
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

          link.download = `Top5_ThreatAnalysis_${dateStr}.png`;
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

      link.download = `ThreatsByLLM_${dateStr}.png`;
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
          Competitor Threats
        </Typography>
        <Box sx={{ minWidth: 300 }}>
          <BatchSelector
            selectedBatchId={selectedBatchId}
            onBatchChange={setSelectedBatchId}
            showAllOption={true}
            label="Filter by Collection"
            autoSelectLatest={true}
          />
        </Box>
      </Box>

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
            {threats.filter((c: any) => c.threat_level === 'High').length}
          </Typography>
          <Typography variant="body1">High Threat Competitors</Typography>
          <Typography variant="caption" color="text.secondary">Require immediate attention</Typography>
        </Paper>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h4" sx={{ color: '#80A1D4' }}>
            {threats.filter((c: any) => c.threat_level === 'Medium').length}
          </Typography>
          <Typography variant="body1">Medium Threat</Typography>
          <Typography variant="caption" color="text.secondary">Monitor closely</Typography>
        </Paper>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h4" sx={{ color: '#003e60' }}>
            {threats.filter((c: any) => c.threat_level === 'Low').length}
          </Typography>
          <Typography variant="body1">Low Threat</Typography>
          <Typography variant="caption" color="text.secondary">Minimal competition</Typography>
        </Paper>
      </Box>

      {/* Detailed Threat Analysis Table */}
      <Paper sx={{ p: 4 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">
            Detailed Threat Analysis
          </Typography>
          <Box display="flex" gap={1}>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={handleDownloadCSV}
              size="small"
              disabled={threats.length === 0}
            >
              Download as CSV
            </Button>
            <Button
              variant="outlined"
              startIcon={<ImageIcon />}
              onClick={handleDownloadTop5Image}
              size="small"
              disabled={threats.length === 0}
            >
              Download Top 5 as Image
            </Button>
          </Box>
        </Box>
        {threats.length > 0 ? (
          <TableContainer ref={tableRef}>
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
                {threats.map((comp: any, index: number) => {
                  // Extract descriptors for this competitor
                  const compResponses = Array.isArray(responses) ? responses.filter((r: any) =>
                    r.competitors && competitorsInclude(r.competitors, comp.name)
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
                        <Typography
                          variant="body2"
                          sx={{
                            color: getThreatColor(comp.threat_level),
                            fontWeight: 'bold'
                          }}
                        >
                          {comp.threat_level}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2" fontWeight="bold">
                          {comp.threat_score}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">{comp.mention_count}</TableCell>
                      <TableCell align="right">{Math.round(comp.share_of_voice)}%</TableCell>
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

      {/* LLM Breakdown - Top Competitors by Platform */}
      {llmData && llmData.length > 0 && (
        <Paper sx={{ p: 4, mt: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box>
              <Typography variant="h6">
                Top Competitor Threats by LLM Platform
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Most frequently mentioned competitors by each AI platform (Top 5)
              </Typography>
            </Box>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={handleDownloadLLMChart}
              size="small"
            >
              Image
            </Button>
          </Box>

          <Box ref={llmChartRef} sx={{ backgroundColor: 'white', p: 2, border: '1px solid #e0e0e0', mt: 2 }}>
            {llmData.map((platformData: any, index: number) => (
              <Box key={index} sx={{ mb: 4 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <Box
                    sx={{
                      width: 16,
                      height: 16,
                      borderRadius: '50%',
                      backgroundColor: PLATFORM_COLORS[platformData.platform] || '#003e60'
                    }}
                  />
                  <Typography variant="h6">{platformData.platform}</Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                    ({platformData.total_competitor_mentions} total competitor mentions)
                  </Typography>
                </Box>
                {platformData.competitors && platformData.competitors.length > 0 ? (
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell><strong>Rank</strong></TableCell>
                          <TableCell><strong>Competitor</strong></TableCell>
                          <TableCell align="right"><strong>Mentions</strong></TableCell>
                          <TableCell align="right"><strong>Negative Overlap</strong></TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {platformData.competitors.map((comp: any, compIndex: number) => (
                          <TableRow key={compIndex}>
                            <TableCell>{compIndex + 1}</TableCell>
                            <TableCell>{comp.name}</TableCell>
                            <TableCell align="right">{comp.mentions}</TableCell>
                            <TableCell align="right">{comp.negative_overlap}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No competitors found for this platform
                  </Typography>
                )}
              </Box>
            ))}
          </Box>
        </Paper>
      )}

    </Box>
  );
}
