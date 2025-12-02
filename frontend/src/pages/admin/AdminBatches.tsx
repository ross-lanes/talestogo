import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Button,
  Alert,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import type { GridColDef } from '@mui/x-data-grid';
import {
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { api } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import { formatDateEST } from '../../utils/dateUtils';

interface Batch {
  id: number;
  batch_name: string;
  user_id: number;
  user_email: string | null;
  brand_id: number;
  brand_name: string | null;
  started_at: string | null;
  completed_at: string | null;
  status: string;
  response_count: number;
}

const AdminBatches: React.FC = () => {
  const { isAdmin } = useAuth();

  const [batches, setBatches] = useState<Batch[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Filter state
  const [brandFilter, setBrandFilter] = useState<string>('all');
  const [uniqueBrands, setUniqueBrands] = useState<{ id: number; name: string }[]>([]);

  // Delete confirmation dialog
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [batchToDelete, setBatchToDelete] = useState<Batch | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (isAdmin) {
      loadBatches();
    }
  }, [isAdmin]);

  const loadBatches = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await api.get('/admin/batches?limit=100');
      setBatches(response.data);

      // Extract unique brands for filter
      const brands = new Map<number, string>();
      response.data.forEach((b: Batch) => {
        if (b.brand_id && b.brand_name) {
          brands.set(b.brand_id, b.brand_name);
        }
      });
      setUniqueBrands(Array.from(brands.entries()).map(([id, name]) => ({ id, name })));
    } catch (err: any) {
      console.error('Failed to load batches:', err);
      setError('Failed to load batches');
    } finally {
      setLoading(false);
    }
  };

  const formatDateTime = (dateString: string | null) => {
    if (!dateString) return '-';
    return formatDateEST(dateString, 'full');
  };

  const formatDateShort = (dateString: string | null) => {
    if (!dateString) return '-';
    return formatDateEST(dateString, 'short');
  };

  const handleDeleteClick = (batch: Batch) => {
    setBatchToDelete(batch);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!batchToDelete) return;

    setDeleting(true);
    setError('');

    try {
      await api.delete(`/admin/batches/${batchToDelete.id}`);
      setSuccess(`Batch "${batchToDelete.batch_name}" deleted successfully (${batchToDelete.response_count} responses removed)`);
      setDeleteDialogOpen(false);
      setBatchToDelete(null);
      // Refresh the list
      loadBatches();
    } catch (err: any) {
      console.error('Failed to delete batch:', err);
      setError(err.response?.data?.detail || 'Failed to delete batch');
    } finally {
      setDeleting(false);
    }
  };

  const handleCancelDelete = () => {
    setDeleteDialogOpen(false);
    setBatchToDelete(null);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'running':
        return 'warning';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  const filteredBatches = brandFilter === 'all'
    ? batches
    : batches.filter(b => b.brand_id === parseInt(brandFilter));

  const columns: GridColDef[] = [
    {
      field: 'id',
      headerName: 'ID',
      width: 70,
    },
    {
      field: 'brand_name',
      headerName: 'Brand',
      flex: 0.8,
      minWidth: 120,
      renderCell: (params) => params.value || '-',
    },
    {
      field: 'batch_name',
      headerName: 'Batch Name',
      flex: 1,
      minWidth: 200,
    },
    {
      field: 'started_at',
      headerName: 'Date',
      width: 120,
      renderCell: (params) => formatDateShort(params.value),
    },
    {
      field: 'started_at_full',
      headerName: 'Start Time',
      width: 180,
      renderCell: (params) => formatDateTime(params.row.started_at),
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 110,
      renderCell: (params) => (
        <Chip
          label={params.value || 'unknown'}
          color={getStatusColor(params.value)}
          size="small"
        />
      ),
    },
    {
      field: 'response_count',
      headerName: 'Data Points',
      width: 110,
      align: 'right',
      headerAlign: 'right',
    },
    {
      field: 'user_email',
      headerName: 'User',
      flex: 0.8,
      minWidth: 150,
      renderCell: (params) => params.value || '-',
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 80,
      sortable: false,
      renderCell: (params) => (
        <IconButton
          onClick={() => handleDeleteClick(params.row as Batch)}
          size="small"
          color="error"
          title="Delete batch"
        >
          <DeleteIcon />
        </IconButton>
      ),
    },
  ];

  if (!isAdmin) {
    return (
      <Container maxWidth={false} sx={{ py: 4, px: 3 }}>
        <Alert severity="error">You do not have permission to access this page.</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth={false} sx={{ py: 4, px: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Data Collection Batches</Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Filter by Brand</InputLabel>
            <Select
              value={brandFilter}
              label="Filter by Brand"
              onChange={(e) => setBrandFilter(e.target.value)}
            >
              <MenuItem value="all">All Brands</MenuItem>
              {uniqueBrands.map((brand) => (
                <MenuItem key={brand.id} value={brand.id.toString()}>
                  {brand.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadBatches}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>
      </Box>

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

      <Paper elevation={2}>
        <DataGrid
          rows={filteredBatches}
          columns={columns}
          loading={loading}
          autoHeight
          pageSizeOptions={[10, 25, 50, 100]}
          initialState={{
            pagination: { paginationModel: { pageSize: 25 } },
            sorting: { sortModel: [{ field: 'started_at', sort: 'desc' }] },
          }}
          disableRowSelectionOnClick
        />
      </Paper>

      <Box sx={{ mt: 2 }}>
        <Typography variant="body2" color="text.secondary">
          Showing {filteredBatches.length} batch{filteredBatches.length !== 1 ? 'es' : ''}.
          Total data points: {filteredBatches.reduce((sum, b) => sum + b.response_count, 0).toLocaleString()}
        </Typography>
      </Box>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={handleCancelDelete}>
        <DialogTitle>Delete Batch</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete the batch <strong>{batchToDelete?.batch_name}</strong>?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            This will permanently delete:
          </Typography>
          <Box component="ul" sx={{ mt: 1, mb: 0 }}>
            <li>
              <Typography variant="body2">
                <strong>{batchToDelete?.response_count}</strong> data points (responses)
              </Typography>
            </li>
            <li>
              <Typography variant="body2">
                Associated batch analytics
              </Typography>
            </li>
          </Box>
          <Alert severity="warning" sx={{ mt: 2 }}>
            This action cannot be undone.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancelDelete} disabled={deleting}>
            Cancel
          </Button>
          <Button
            onClick={handleConfirmDelete}
            color="error"
            variant="contained"
            disabled={deleting}
          >
            {deleting ? 'Deleting...' : 'Delete Batch'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default AdminBatches;
