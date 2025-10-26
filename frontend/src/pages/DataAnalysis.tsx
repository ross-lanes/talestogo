import { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
  Alert,
  Snackbar,
} from '@mui/material';
import { Analytics as AnalysisIcon } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { format } from 'date-fns';

interface Report {
  id: number;
  title: string;
  created_at: string;
  status: string;
  google_doc_url?: string;
}

export default function DataAnalysis() {
  const queryClient = useQueryClient();
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' | 'info' }>({
    open: false,
    message: '',
    severity: 'info',
  });

  // Fetch reports
  const { data: reports, isLoading } = useQuery<Report[]>({
    queryKey: ['reports'],
    queryFn: async () => {
      const response = await api.get('/reports/');
      return response.data;
    },
  });

  // Analysis mutation
  const analysisMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post('/tasks/run-analysis/');
      return response.data;
    },
    onSuccess: (data) => {
      setSnackbar({
        open: true,
        message: data.message + ' ' + (data.note || ''),
        severity: 'info',
      });
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['reports'] });
        queryClient.invalidateQueries({ queryKey: ['dashboard-metrics'] });
        queryClient.invalidateQueries({ queryKey: ['responses'] });
      }, 2000);
    },
    onError: (error: any) => {
      setSnackbar({
        open: true,
        message: error.response?.data?.detail || 'Failed to start analysis',
        severity: 'error',
      });
    },
  });

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'success';
      case 'in_progress':
        return 'warning';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h2" component="h1">
          Data Analysis
        </Typography>
        <Button
          variant="contained"
          color="secondary"
          startIcon={<AnalysisIcon />}
          onClick={() => analysisMutation.mutate()}
          disabled={analysisMutation.isPending}
        >
          {analysisMutation.isPending ? 'Running...' : 'Run Analysis'}
        </Button>
      </Box>

      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Run analysis to process collected responses and generate insights. View your report archive below.
      </Typography>

      {/* Report Archive */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" gutterBottom>
          Report Archive
        </Typography>

        {isLoading ? (
          <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
            <CircularProgress />
          </Box>
        ) : reports && reports.length > 0 ? (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Title</strong></TableCell>
                  <TableCell><strong>Created</strong></TableCell>
                  <TableCell><strong>Status</strong></TableCell>
                  <TableCell><strong>Actions</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {reports.map((report) => (
                  <TableRow key={report.id} hover>
                    <TableCell>{report.title}</TableCell>
                    <TableCell>
                      {format(new Date(report.created_at), 'MMM dd, yyyy h:mm a')}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={report.status}
                        color={getStatusColor(report.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {report.google_doc_url ? (
                        <Button
                          variant="outlined"
                          size="small"
                          href={report.google_doc_url}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          View Report
                        </Button>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          No link available
                        </Typography>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <Box sx={{ py: 4, textAlign: 'center' }}>
            <Typography variant="body1" color="text.secondary">
              No reports generated yet. Click "Run Analysis" to create your first report.
            </Typography>
          </Box>
        )}
      </Paper>

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
