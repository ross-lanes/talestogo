import { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  CircularProgress,
  Alert,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Snackbar,
} from '@mui/material';
import {
  Lightbulb as LightbulbIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Visibility as ViewIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../services/api';
import ReactMarkdown from 'react-markdown';
import { useNavigate } from 'react-router-dom';

interface Report {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
  report_content: string;
  total_responses: number;
  mention_rate?: number;
  google_doc_url?: string;
}

export default function Recommendations() {
  const navigate = useNavigate();
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' | 'info' }>({
    open: false,
    message: '',
    severity: 'info',
  });

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['recommendations'],
    queryFn: async () => {
      const response = await api.get('/analytics/recommendations');
      return response.data;
    },
  });

  // Fetch reports for archive
  const { data: reports, isLoading: reportsLoading } = useQuery<Report[]>({
    queryKey: ['reports'],
    queryFn: async () => {
      const response = await api.get('/reports/');
      return response.data;
    },
  });

  const formatDate = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'America/New_York',
      timeZoneName: 'short'
    });
  };

  const handleViewInBrowser = (report: Report) => {
    setSelectedReport(report);
    setViewDialogOpen(true);
  };

  const handleDownloadWord = async (report: Report) => {
    try {
      const response = await api.get(`/reports/${report.id}/export/word`, {
        responseType: 'blob',
      });

      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${report.title}.docx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      setSnackbar({
        open: true,
        message: 'Word document with charts downloaded successfully',
        severity: 'success',
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Failed to download Word document',
        severity: 'error',
      });
    }
  };

  const handleDownloadHTML = async (report: Report) => {
    try {
      const response = await api.get(`/reports/${report.id}/export/html`, {
        responseType: 'blob',
      });

      const blob = new Blob([response.data], { type: 'text/html' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${report.title}.html`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      setSnackbar({
        open: true,
        message: 'HTML report with charts downloaded successfully',
        severity: 'success',
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Failed to download HTML report',
        severity: 'error',
      });
    }
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
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
          <Alert severity="info" sx={{ mb: 2 }}>
            {data?.message || 'No recommendations available yet.'}
          </Alert>
          <Button
            variant="contained"
            sx={{ mt: 3 }}
            onClick={() => navigate('/collect-analyze')}
          >
            Run Collection & Analysis
          </Button>
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
                fontSize: '1.5rem',
                fontWeight: 600,
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

      {/* Report Archive */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" gutterBottom>
          Report Archive
        </Typography>

        {reportsLoading ? (
          <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
            <CircularProgress />
          </Box>
        ) : reports && reports.length > 0 ? (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Report</strong></TableCell>
                  <TableCell align="right"><strong>Actions</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {reports.map((report) => (
                  <TableRow key={report.id} hover>
                    <TableCell>{report.title}</TableCell>
                    <TableCell align="right">
                      <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                        <Button
                          variant="outlined"
                          size="small"
                          startIcon={<ViewIcon />}
                          onClick={() => handleViewInBrowser(report)}
                        >
                          View
                        </Button>
                        <Button
                          variant="contained"
                          size="small"
                          startIcon={<DownloadIcon />}
                          onClick={() => handleDownloadWord(report)}
                          sx={{ bgcolor: '#665775', '&:hover': { bgcolor: '#80a1d4' } }}
                        >
                          Word
                        </Button>
                        <Button
                          variant="outlined"
                          size="small"
                          startIcon={<DownloadIcon />}
                          onClick={() => handleDownloadHTML(report)}
                        >
                          HTML
                        </Button>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <Box sx={{ py: 4, textAlign: 'center' }}>
            <Typography variant="body1" color="text.secondary">
              No reports generated yet. Run analysis to create your first report.
            </Typography>
          </Box>
        )}
      </Paper>

      {/* View Report Dialog */}
      <Dialog
        open={viewDialogOpen}
        onClose={() => setViewDialogOpen(false)}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: { height: '90vh' }
        }}
      >
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">{selectedReport?.title}</Typography>
            <IconButton onClick={() => setViewDialogOpen(false)} size="small">
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          <Box sx={{
            '& h1': { fontSize: '2rem', fontWeight: 'bold', mb: 2, mt: 3 },
            '& h2': { fontSize: '1.5rem', fontWeight: 'bold', mb: 2, mt: 2 },
            '& h3': { fontSize: '1.25rem', fontWeight: 'bold', mb: 1.5, mt: 1.5 },
            '& p': { mb: 2 },
            '& ul, & ol': { mb: 2, pl: 3 },
            '& table': {
              width: '100%',
              borderCollapse: 'collapse',
              mb: 2,
              '& th, & td': {
                border: '1px solid #ddd',
                padding: '8px',
                textAlign: 'left'
              },
              '& th': {
                backgroundColor: '#f5f5f5',
                fontWeight: 'bold'
              }
            },
            '& code': {
              backgroundColor: '#f5f5f5',
              padding: '2px 6px',
              borderRadius: '4px',
              fontFamily: 'monospace'
            },
            '& pre': {
              backgroundColor: '#f5f5f5',
              padding: '12px',
              borderRadius: '4px',
              overflow: 'auto',
              mb: 2
            }
          }}>
            {selectedReport && (
              <ReactMarkdown>{selectedReport.report_content}</ReactMarkdown>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => handleDownloadWord(selectedReport!)}
            variant="contained"
            sx={{ bgcolor: '#665775', color: 'white', '&:hover': { bgcolor: '#80a1d4' } }}
          >
            Word
          </Button>
          <Button onClick={() => handleDownloadHTML(selectedReport!)}>
            HTML
          </Button>
          <Button onClick={() => setViewDialogOpen(false)} variant="contained">
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}
