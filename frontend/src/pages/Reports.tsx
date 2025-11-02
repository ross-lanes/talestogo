import { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Chip,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Visibility as VisibilityIcon,
  Delete as DeleteIcon,
  Download as DownloadIcon,
  Description as WordIcon,
  PictureAsPdf as PdfIcon,
} from '@mui/icons-material';
import { DataGrid, GridActionsCellItem } from '@mui/x-data-grid';
import type { GridColDef } from '@mui/x-data-grid';
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';
import { api } from '../services/api';

interface Report {
  id: number;
  title: string;
  report_content: string;
  start_date?: string;
  end_date?: string;
  total_responses: number;
  mention_rate?: number;
  google_doc_url?: string;
  created_at: string;
  updated_at: string;
}

export default function Reports() {
  const queryClient = useQueryClient();
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [reportToDelete, setReportToDelete] = useState<Report | null>(null);

  // Fetch reports
  const { data: reports = [], isLoading } = useQuery({
    queryKey: ['reports'],
    queryFn: async () => {
      const response = await api.get<Report[]>('/reports/');
      return response.data;
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async (reportId: number) => {
      await api.delete(`/reports/${reportId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      setDeleteDialogOpen(false);
      setReportToDelete(null);
    },
  });

  const handleViewReport = (report: Report) => {
    setSelectedReport(report);
    setViewDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setViewDialogOpen(false);
    setSelectedReport(null);
  };

  const handleDeleteClick = (report: Report) => {
    setReportToDelete(report);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = () => {
    if (reportToDelete) {
      deleteMutation.mutate(reportToDelete.id);
    }
  };

  const handleCancelDelete = () => {
    setDeleteDialogOpen(false);
    setReportToDelete(null);
  };

  const handleDownloadMarkdown = (report: Report) => {
    const blob = new Blob([report.report_content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${report.title.replace(/[^a-z0-9]/gi, '_')}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleDownloadWord = async (report: Report) => {
    try {
      const response = await api.get(`/reports/${report.id}/export/word`, {
        responseType: 'blob',
      });
      const url = URL.createObjectURL(response.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${report.title.replace(/[^a-z0-9]/gi, '_')}.docx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error: any) {
      console.error('Error downloading Word document:', error);
      alert(`Failed to download Word document: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleDownloadPDF = async (report: Report) => {
    try {
      const response = await api.get(`/reports/${report.id}/export/pdf`, {
        responseType: 'blob',
      });
      const url = URL.createObjectURL(response.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${report.title.replace(/[^a-z0-9]/gi, '_')}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading PDF:', error);
    }
  };

  const columns: GridColDef<Report>[] = [
    {
      field: 'id',
      headerName: 'ID',
      width: 70,
    },
    {
      field: 'title',
      headerName: 'Report Title',
      flex: 1,
      minWidth: 300,
    },
    {
      field: 'created_at',
      headerName: 'Created',
      width: 180,
      valueFormatter: (params) => {
        return new Date(params).toLocaleString();
      },
    },
    {
      field: 'total_responses',
      headerName: 'Responses',
      width: 120,
      align: 'center',
      headerAlign: 'center',
    },
    {
      field: 'mention_rate',
      headerName: 'Mention Rate',
      width: 140,
      align: 'center',
      headerAlign: 'center',
      renderCell: (params) => {
        if (params.value === null || params.value === undefined) return '-';
        return <Chip label={`${params.value}%`} color="primary" size="small" />;
      },
    },
    {
      field: 'google_doc_url',
      headerName: 'Status',
      width: 120,
      renderCell: (params) => {
        return params.value ? (
          <Chip label="Exported" color="success" size="small" />
        ) : (
          <Chip label="Not Exported" variant="outlined" size="small" />
        );
      },
    },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Actions',
      width: 120,
      getActions: (params) => [
        <GridActionsCellItem
          icon={<VisibilityIcon />}
          label="View"
          onClick={() => handleViewReport(params.row)}
        />,
        <GridActionsCellItem
          icon={<WordIcon />}
          label="Word"
          onClick={() => handleDownloadWord(params.row)}
          showInMenu
        />,
        <GridActionsCellItem
          icon={<PdfIcon />}
          label="Download PDF"
          onClick={() => handleDownloadPDF(params.row)}
          showInMenu
        />,
        <GridActionsCellItem
          icon={<DownloadIcon />}
          label="Download Markdown"
          onClick={() => handleDownloadMarkdown(params.row)}
          showInMenu
        />,
        <GridActionsCellItem
          icon={<DeleteIcon />}
          label="Delete"
          onClick={() => handleDeleteClick(params.row)}
          showInMenu
        />,
      ],
    },
  ];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Reports
        </Typography>
        <IconButton
          color="primary"
          onClick={() => queryClient.invalidateQueries({ queryKey: ['reports'] })}
          title="Refresh"
        >
          <RefreshIcon />
        </IconButton>
      </Box>

      <Paper sx={{ height: 600, width: '100%' }}>
        <DataGrid
          rows={reports}
          columns={columns}
          loading={isLoading}
          initialState={{
            pagination: {
              paginationModel: { pageSize: 25, page: 0 },
            },
            sorting: {
              sortModel: [{ field: 'created_at', sort: 'desc' }],
            },
          }}
          pageSizeOptions={[10, 25, 50]}
          disableRowSelectionOnClick
          sx={{
            '& .MuiDataGrid-cell': {
              py: 1,
            },
          }}
        />
      </Paper>

      {/* View Report Dialog */}
      <Dialog
        open={viewDialogOpen}
        onClose={handleCloseDialog}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: { height: '90vh' }
        }}
      >
        <DialogTitle>
          {selectedReport?.title}
        </DialogTitle>
        <DialogContent dividers>
          {selectedReport && (
            <Box
              sx={{
                '& h1': { fontSize: '2rem', fontWeight: 'bold', mt: 3, mb: 2 },
                '& h2': { fontSize: '1.5rem', fontWeight: 'bold', mt: 2, mb: 1.5 },
                '& h3': { fontSize: '1.25rem', fontWeight: 'bold', mt: 1.5, mb: 1 },
                '& p': { mb: 1.5 },
                '& ul, & ol': { mb: 1.5, pl: 3 },
                '& li': { mb: 0.5 },
                '& table': {
                  borderCollapse: 'collapse',
                  width: '100%',
                  mb: 2,
                  mt: 2,
                },
                '& th, & td': {
                  border: '1px solid #ddd',
                  padding: '8px 12px',
                  textAlign: 'left',
                },
                '& th': {
                  backgroundColor: '#f5f5f5',
                  fontWeight: 'bold',
                },
                '& hr': {
                  my: 3,
                  border: 'none',
                  borderTop: '1px solid #ddd',
                },
                '& code': {
                  backgroundColor: '#f5f5f5',
                  padding: '2px 6px',
                  borderRadius: '3px',
                  fontFamily: 'monospace',
                },
                '& pre': {
                  backgroundColor: '#f5f5f5',
                  padding: '12px',
                  borderRadius: '4px',
                  overflow: 'auto',
                  mb: 2,
                },
              }}
            >
              <ReactMarkdown>{selectedReport.report_content}</ReactMarkdown>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button
            startIcon={<WordIcon />}
            onClick={() => selectedReport && handleDownloadWord(selectedReport)}
          >
            Word
          </Button>
          <Button
            startIcon={<PdfIcon />}
            onClick={() => selectedReport && handleDownloadPDF(selectedReport)}
          >
            PDF
          </Button>
          <Button
            startIcon={<DownloadIcon />}
            onClick={() => selectedReport && handleDownloadMarkdown(selectedReport)}
          >
            Markdown
          </Button>
          <Button onClick={handleCloseDialog} variant="contained">
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleCancelDelete}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Delete Report</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete this report?
          </Typography>
          {reportToDelete && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Title: {reportToDelete.title}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Created: {new Date(reportToDelete.created_at).toLocaleString()}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancelDelete}>Cancel</Button>
          <Button
            onClick={handleConfirmDelete}
            color="error"
            variant="contained"
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
