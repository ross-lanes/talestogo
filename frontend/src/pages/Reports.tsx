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
  Delete as DeleteIcon,
  Download as DownloadIcon,
  Description as WordIcon,
} from '@mui/icons-material';
import { DataGrid, GridActionsCellItem } from '@mui/x-data-grid';
import type { GridColDef } from '@mui/x-data-grid';
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { api } from '../services/api';
import { formatDateEST } from '../utils/dateUtils';

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
        return formatDateEST(params, 'full');
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
          icon={<WordIcon />}
          label="Word"
          onClick={() => handleDownloadWord(params.row)}
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
                Created: {formatDateEST(reportToDelete.created_at, 'full')}
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
