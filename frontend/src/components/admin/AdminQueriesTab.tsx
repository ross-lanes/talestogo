import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControlLabel,
  Switch,
  MenuItem,
  Alert,
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
import { adminAPI } from '../../services/api';
import type { Query, QueryCreate, QueryUpdate } from '../../types';

interface AdminQueriesTabProps {
  userId: number;
  brandId: number;
}

const AdminQueriesTab: React.FC<AdminQueriesTabProps> = ({ userId, brandId }) => {
  const [queries, setQueries] = useState<Query[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedQuery, setSelectedQuery] = useState<Query | null>(null);
  const [formData, setFormData] = useState<Partial<QueryCreate>>({
    query_text: '',
    category: '',
    priority: 'Medium',
    target_outcome: '',
    brand_in_query: false,
    active: true,
    notes: '',
  });

  useEffect(() => {
    loadQueries();
  }, [userId, brandId]);

  const loadQueries = async () => {
    setLoading(true);
    setError('');

    try {
      const data = await adminAPI.getUserBrandQueries(userId, brandId);
      setQueries(data);
    } catch (err: any) {
      console.error('Failed to load queries:', err);
      setError('Failed to load queries');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (query?: Query) => {
    if (query) {
      setSelectedQuery(query);
      setFormData({
        query_text: query.query_text,
        category: query.category,
        priority: query.priority,
        target_outcome: query.target_outcome,
        brand_in_query: query.brand_in_query,
        active: query.active,
        notes: query.notes || '',
      });
    } else {
      setSelectedQuery(null);
      setFormData({
        query_text: '',
        category: '',
        priority: 'Medium',
        target_outcome: '',
        brand_in_query: false,
        active: true,
        notes: '',
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setSelectedQuery(null);
    setError('');
  };

  const handleSave = async () => {
    setError('');
    setSuccess('');

    try {
      if (selectedQuery) {
        // Update existing query
        await adminAPI.updateQuery(userId, brandId, selectedQuery.query_id, formData);
        setSuccess('Query updated successfully');
      } else {
        // Create new query - would need to generate query_id
        setError('Creating new queries from admin panel is not yet supported');
        return;
      }

      handleCloseDialog();
      loadQueries();
    } catch (err: any) {
      console.error('Failed to save query:', err);
      setError(err.response?.data?.detail || 'Failed to save query');
    }
  };

  const handleDelete = async () => {
    if (!selectedQuery) return;

    setError('');
    setSuccess('');

    try {
      await adminAPI.deleteQuery(userId, brandId, selectedQuery.query_id);
      setSuccess('Query deleted successfully');
      setDeleteDialogOpen(false);
      setSelectedQuery(null);
      loadQueries();
    } catch (err: any) {
      console.error('Failed to delete query:', err);
      setError(err.response?.data?.detail || 'Failed to delete query');
    }
  };

  const columns: GridColDef[] = [
    {
      field: 'query_id',
      headerName: 'ID',
      width: 80,
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
      width: 100,
      renderCell: (params) => (
        <Chip
          label={params.value}
          color={
            params.value === 'High' ? 'error' :
            params.value === 'Medium' ? 'warning' :
            'default'
          }
          size="small"
        />
      ),
    },
    {
      field: 'brand_in_query',
      headerName: 'Brand in Query',
      width: 130,
      renderCell: (params) => (
        params.value ? <Chip label="Yes" color="primary" size="small" /> : <Chip label="No" size="small" />
      ),
    },
    {
      field: 'active',
      headerName: 'Active',
      width: 100,
      renderCell: (params) => (
        <Chip
          label={params.value ? 'Active' : 'Inactive'}
          color={params.value ? 'success' : 'default'}
          size="small"
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
          onClick={() => handleOpenDialog(params.row as Query)}
        />,
        <GridActionsCellItem
          icon={<DeleteIcon />}
          label="Delete"
          onClick={() => {
            setSelectedQuery(params.row as Query);
            setDeleteDialogOpen(true);
          }}
        />,
      ],
    },
  ];

  return (
    <Box sx={{ px: 2 }}>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="body2" color="text.secondary">
          Total: {queries.length} queries
        </Typography>
        <Button
          startIcon={<RefreshIcon />}
          onClick={loadQueries}
          size="small"
        >
          Refresh
        </Button>
      </Box>

      <DataGrid
        rows={queries}
        columns={columns}
        loading={loading}
        autoHeight
        pageSizeOptions={[10, 25, 50, 100]}
        initialState={{
          pagination: { paginationModel: { pageSize: 25 } },
        }}
        disableRowSelectionOnClick
      />

      {/* Edit Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>{selectedQuery ? 'Edit Query' : 'Create Query'}</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              fullWidth
              label="Query Text"
              value={formData.query_text}
              onChange={(e) => setFormData({ ...formData, query_text: e.target.value })}
              multiline
              rows={3}
              required
            />

            <TextField
              fullWidth
              label="Category"
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
            />

            <TextField
              select
              fullWidth
              label="Priority"
              value={formData.priority}
              onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
            >
              <MenuItem value="High">High</MenuItem>
              <MenuItem value="Medium">Medium</MenuItem>
              <MenuItem value="Low">Low</MenuItem>
            </TextField>

            <TextField
              fullWidth
              label="Target Outcome"
              value={formData.target_outcome}
              onChange={(e) => setFormData({ ...formData, target_outcome: e.target.value })}
            />

            <FormControlLabel
              control={
                <Switch
                  checked={formData.brand_in_query || false}
                  onChange={(e) => setFormData({ ...formData, brand_in_query: e.target.checked })}
                />
              }
              label="Brand mentioned in query"
            />

            <FormControlLabel
              control={
                <Switch
                  checked={formData.active !== false}
                  onChange={(e) => setFormData({ ...formData, active: e.target.checked })}
                />
              }
              label="Active"
            />

            <TextField
              fullWidth
              label="Notes"
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              multiline
              rows={2}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSave} variant="contained" disabled={!formData.query_text}>
            Save
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Query</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete this query? This action cannot be undone.
          </Typography>
          {selectedQuery && (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
              <Typography variant="body2" fontWeight="bold">
                Query ID: {selectedQuery.query_id}
              </Typography>
              <Typography variant="body2">
                {selectedQuery.query_text}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDelete} variant="contained" color="error">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AdminQueriesTab;
