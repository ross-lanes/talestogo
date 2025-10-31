import { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Visibility as VisibilityIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { DataGrid, GridActionsCellItem } from '@mui/x-data-grid';
import type { GridColDef } from '@mui/x-data-grid';
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { api } from '../../services/api';

interface Response {
  id: number;
  query_id: string;
  query_text: string;
  platform: string;
  response_text: string;
  timestamp: string;
  pppl_mentioned?: string;
  pppl_position?: string;
  sentiment?: string;
  analyzed_at?: string;
}

export default function Responses() {
  const queryClient = useQueryClient();
  const [selectedResponse, setSelectedResponse] = useState<Response | null>(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [responseToDelete, setResponseToDelete] = useState<Response | null>(null);

  // Fetch responses
  const { data: responses = [], isLoading } = useQuery({
    queryKey: ['responses'],
    queryFn: async () => {
      const response = await api.get<Response[]>('/responses/');
      console.log('API Response:', response.data);
      console.log('First response:', response.data[0]);
      return response.data;
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async (responseId: number) => {
      await api.delete(`/responses/${responseId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['responses'] });
      setDeleteDialogOpen(false);
      setResponseToDelete(null);
    },
  });

  const handleViewResponse = (response: Response) => {
    setSelectedResponse(response);
    setViewDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setViewDialogOpen(false);
    setSelectedResponse(null);
  };

  const handleDeleteClick = (response: Response) => {
    setResponseToDelete(response);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = () => {
    if (responseToDelete) {
      deleteMutation.mutate(responseToDelete.id);
    }
  };

  const handleCancelDelete = () => {
    setDeleteDialogOpen(false);
    setResponseToDelete(null);
  };

  const columns: GridColDef<Response>[] = [
    {
      field: 'id',
      headerName: 'ID',
      width: 70,
    },
    {
      field: 'query_id',
      headerName: 'Query',
      width: 90,
    },
    {
      field: 'query_text',
      headerName: 'Query Text',
      flex: 1,
      minWidth: 200,
      renderCell: (params) => (
        <Typography variant="body2" sx={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {params.value}
        </Typography>
      ),
    },
    {
      field: 'platform',
      headerName: 'Platform',
      width: 120,
      renderCell: (params) => {
        const color =
          params.value === 'ChatGPT' ? '#2e7d32' :
          params.value === 'Claude' ? '#80A1D4' :
          params.value === 'Gemini' ? '#9c27b0' : '#757575';
        return (
          <Typography variant="body2" sx={{ color, fontWeight: 'bold' }}>
            {params.value}
          </Typography>
        );
      },
    },
    {
      field: 'timestamp',
      headerName: 'Collected',
      width: 180,
    },
    {
      field: 'pppl_mentioned',
      headerName: 'PPPL',
      width: 100,
      renderCell: (params) => {
        if (!params.value) return (
          <Typography variant="body2" sx={{ color: '#757575' }}>
            Not Analyzed
          </Typography>
        );
        const color =
          params.value === 'Yes' ? '#2e7d32' :
          params.value === 'Indirect' ? '#ed6c02' : '#d32f2f';
        return (
          <Typography variant="body2" sx={{ color, fontWeight: 'bold' }}>
            {params.value}
          </Typography>
        );
      },
    },
    {
      field: 'sentiment',
      headerName: 'Sentiment',
      width: 120,
      renderCell: (params) => {
        if (!params.value) return null;
        const color =
          params.value === 'Very Positive' || params.value === 'Positive' ? '#2e7d32' :
          params.value === 'Neutral' ? '#757575' :
          params.value === 'Negative' ? '#d32f2f' : '#ed6c02';
        return (
          <Typography variant="body2" sx={{ color, fontWeight: 'bold' }}>
            {params.value}
          </Typography>
        );
      },
    },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Actions',
      width: 100,
      getActions: (params) => [
        <GridActionsCellItem
          icon={<VisibilityIcon />}
          label="View"
          onClick={() => handleViewResponse(params.row)}
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
          Responses
        </Typography>
        <IconButton
          color="primary"
          onClick={() => queryClient.invalidateQueries({ queryKey: ['responses'] })}
          title="Refresh"
        >
          <RefreshIcon />
        </IconButton>
      </Box>

      <Paper sx={{ height: 600, width: '100%' }}>
        <DataGrid
          rows={responses}
          columns={columns}
          loading={isLoading}
          initialState={{
            pagination: {
              paginationModel: { pageSize: 25, page: 0 },
            },
            sorting: {
              sortModel: [{ field: 'timestamp', sort: 'desc' }],
            },
          }}
          pageSizeOptions={[10, 25, 50, 100]}
          disableRowSelectionOnClick
          sx={{
            '& .MuiDataGrid-cell': {
              py: 1,
            },
          }}
        />
      </Paper>

      {/* View Dialog */}
      <Dialog
        open={viewDialogOpen}
        onClose={handleCloseDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Response Details - {selectedResponse?.platform}
        </DialogTitle>
        <DialogContent dividers>
          {selectedResponse && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Box>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Query ID: {selectedResponse.query_id}
                </Typography>
                <Typography variant="body1" gutterBottom>
                  <strong>Query:</strong> {selectedResponse.query_text}
                </Typography>
              </Box>

              <Box>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Platform: <Chip label={selectedResponse.platform} size="small" sx={{ ml: 1 }} />
                </Typography>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Collected: {new Date(selectedResponse.timestamp).toLocaleString()}
                </Typography>
              </Box>

              <Box>
                <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>
                  Response Text:
                </Typography>
                <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50', maxHeight: 400, overflow: 'auto' }}>
                  <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                    {selectedResponse.response_text}
                  </Typography>
                </Paper>
              </Box>

              {selectedResponse.analyzed_at && (
                <Box>
                  <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>
                    Analysis:
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {selectedResponse.pppl_mentioned && (
                      <Chip label={`PPPL: ${selectedResponse.pppl_mentioned}`} />
                    )}
                    {selectedResponse.pppl_position && (
                      <Chip label={`Position: ${selectedResponse.pppl_position}`} />
                    )}
                    {selectedResponse.sentiment && (
                      <Chip label={`Sentiment: ${selectedResponse.sentiment}`} />
                    )}
                  </Box>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    Analyzed: {new Date(selectedResponse.analyzed_at).toLocaleString()}
                  </Typography>
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleCancelDelete}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Delete Response</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete response ID {responseToDelete?.id}?
          </Typography>
          {responseToDelete && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Query: {responseToDelete.query_text}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Platform: {responseToDelete.platform}
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
