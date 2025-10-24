import { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControlLabel,
  Switch,
  MenuItem,
  IconButton,
  Chip,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { DataGrid, GridActionsCellItem } from '@mui/x-data-grid';
import type { GridColDef } from '@mui/x-data-grid';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../../services/api';
import type { Query, QueryCreate, QueryUpdate } from '../../types';

export default function Queries() {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedQuery, setSelectedQuery] = useState<Query | null>(null);
  const [formData, setFormData] = useState<Omit<QueryCreate, 'query_id'>>({
    query_text: '',
    category: '',
    priority: 'Medium',
    target_outcome: 'mention',
    active: true,
    notes: '',
  });

  // Fetch queries
  const { data: queries = [], isLoading } = useQuery({
    queryKey: ['queries'],
    queryFn: async () => {
      const response = await api.get<Query[]>('/queries/');
      return response.data;
    },
  });

  // Create query mutation
  const createMutation = useMutation({
    mutationFn: async (data: QueryCreate) => {
      const response = await api.post<Query>('/queries/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['queries'] });
      handleCloseDialog();
    },
  });

  // Update query mutation
  const updateMutation = useMutation({
    mutationFn: async ({ query_id, data }: { query_id: string; data: QueryUpdate }) => {
      const response = await api.put<Query>(`/queries/${query_id}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['queries'] });
      handleCloseDialog();
    },
  });

  // Delete query mutation
  const deleteMutation = useMutation({
    mutationFn: async (query_id: string) => {
      await api.delete(`/queries/${query_id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['queries'] });
      setDeleteDialogOpen(false);
      setSelectedQuery(null);
    },
  });

  const handleOpenDialog = (query?: Query) => {
    if (query) {
      setSelectedQuery(query);
      setFormData({
        query_text: query.query_text || '',
        category: query.category || '',
        priority: query.priority || 'Medium',
        target_outcome: query.target_outcome || '',
        active: query.active ?? true,
        notes: query.notes || '',
      });
    } else {
      setSelectedQuery(null);
      setFormData({
        query_text: '',
        category: '',
        priority: 'Medium',
        target_outcome: '',
        active: true,
        notes: '',
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setSelectedQuery(null);
  };

  const handleSubmit = () => {
    if (selectedQuery) {
      // For update, send the form data (query_id is already excluded)
      updateMutation.mutate({ query_id: selectedQuery.query_id, data: formData });
    } else {
      // For create, send form data (backend will auto-generate query_id)
      createMutation.mutate(formData);
    }
  };

  const handleDeleteClick = (query: Query) => {
    setSelectedQuery(query);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = () => {
    if (selectedQuery) {
      deleteMutation.mutate(selectedQuery.query_id);
    }
  };

  const columns: GridColDef[] = [
    {
      field: 'query_id',
      headerName: 'Query ID',
      width: 100,
      renderCell: (params) => (
        <Chip label={params.value} size="small" color="primary" variant="outlined" />
      ),
    },
    {
      field: 'query_text',
      headerName: 'Query Text',
      flex: 1,
      minWidth: 300,
    },
    {
      field: 'category',
      headerName: 'Category',
      width: 150,
    },
    {
      field: 'priority',
      headerName: 'Priority',
      width: 120,
      renderCell: (params) => {
        const color =
          params.value === 'High'
            ? 'error'
            : params.value === 'Medium'
            ? 'warning'
            : 'success';
        return <Chip label={params.value} size="small" color={color} />;
      },
    },
    {
      field: 'target_outcome',
      headerName: 'Target Outcome',
      width: 150,
    },
    {
      field: 'active',
      headerName: 'Active',
      width: 100,
      renderCell: (params) => (
        <Chip
          label={params.value ? 'Active' : 'Inactive'}
          size="small"
          color={params.value ? 'success' : 'default'}
        />
      ),
    },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Actions',
      width: 100,
      getActions: (params) => [
        <GridActionsCellItem
          icon={<EditIcon />}
          label="Edit"
          onClick={() => handleOpenDialog(params.row)}
        />,
        <GridActionsCellItem
          icon={<DeleteIcon />}
          label="Delete"
          onClick={() => handleDeleteClick(params.row)}
        />,
      ],
    },
  ];

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h2">Manage Queries</Typography>
        <Box>
          <IconButton onClick={() => queryClient.invalidateQueries({ queryKey: ['queries'] })}>
            <RefreshIcon />
          </IconButton>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
            sx={{ ml: 1 }}
          >
            Add Query
          </Button>
        </Box>
      </Box>

      <Paper sx={{ height: 600, width: '100%' }}>
        <DataGrid
          rows={queries}
          columns={columns}
          loading={isLoading}
          pageSizeOptions={[10, 25, 50]}
          initialState={{
            pagination: { paginationModel: { pageSize: 25 } },
          }}
          disableRowSelectionOnClick
        />
      </Paper>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>{selectedQuery ? 'Edit Query' : 'Add New Query'}</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
            <TextField
              label="Query Text"
              value={formData.query_text}
              onChange={(e) => setFormData({ ...formData, query_text: e.target.value })}
              required
              fullWidth
              multiline
              rows={3}
            />
            <TextField
              label="Category"
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              required
              fullWidth
            />
            <TextField
              select
              label="Priority"
              value={formData.priority}
              onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
              required
              fullWidth
            >
              <MenuItem value="High">High</MenuItem>
              <MenuItem value="Medium">Medium</MenuItem>
              <MenuItem value="Low">Low</MenuItem>
            </TextField>
            <TextField
              label="Target Outcome"
              value={formData.target_outcome}
              onChange={(e) => setFormData({ ...formData, target_outcome: e.target.value })}
              fullWidth
            />
            <TextField
              label="Notes"
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              fullWidth
              multiline
              rows={2}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={formData.active}
                  onChange={(e) => setFormData({ ...formData, active: e.target.checked })}
                />
              }
              label="Active"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={
              !formData.query_text?.trim() ||
              !formData.category?.trim() ||
              createMutation.isPending ||
              updateMutation.isPending
            }
          >
            {selectedQuery ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Query</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete the query "{selectedQuery?.query_text}"? This action
            cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleDeleteConfirm}
            variant="contained"
            color="error"
            disabled={deleteMutation.isPending}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
