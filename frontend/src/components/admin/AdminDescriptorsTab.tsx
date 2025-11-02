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
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Upload as UploadIcon,
} from '@mui/icons-material';
import { DataGrid, GridActionsCellItem } from '@mui/x-data-grid';
import type { GridColDef } from '@mui/x-data-grid';
import { adminAPI } from '../../services/api';

interface Descriptor {
  id: number;
  descriptor: string;
  is_target: boolean;
  current_ownership?: string;
  priority: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

interface AdminDescriptorsTabProps {
  userId: number;
  brandId: number;
}

const AdminDescriptorsTab: React.FC<AdminDescriptorsTabProps> = ({ userId, brandId }) => {
  const [descriptors, setDescriptors] = useState<Descriptor[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedDescriptor, setSelectedDescriptor] = useState<Descriptor | null>(null);
  const [formData, setFormData] = useState({
    descriptor: '',
    is_target: true,
    current_ownership: '',
    priority: 'Medium',
    notes: '',
  });

  useEffect(() => {
    loadDescriptors();
  }, [userId, brandId]);

  const loadDescriptors = async () => {
    setLoading(true);
    setError('');

    try {
      const data = await adminAPI.getUserBrandDescriptors(userId, brandId);
      setDescriptors(data);
    } catch (err: any) {
      console.error('Failed to load descriptors:', err);
      setError('Failed to load descriptors');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (descriptor?: Descriptor) => {
    if (descriptor) {
      setSelectedDescriptor(descriptor);
      setFormData({
        descriptor: descriptor.descriptor,
        is_target: descriptor.is_target,
        current_ownership: descriptor.current_ownership || '',
        priority: descriptor.priority,
        notes: descriptor.notes || '',
      });
    } else {
      setSelectedDescriptor(null);
      setFormData({
        descriptor: '',
        is_target: true,
        current_ownership: '',
        priority: 'Medium',
        notes: '',
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setSelectedDescriptor(null);
    setError('');
  };

  const handleSave = async () => {
    setError('');
    setSuccess('');

    try {
      if (selectedDescriptor) {
        await adminAPI.updateDescriptor(userId, brandId, selectedDescriptor.id, formData);
        setSuccess('Descriptor updated successfully');
      } else {
        await adminAPI.createDescriptor(userId, brandId, formData);
        setSuccess('Descriptor created successfully');
      }

      handleCloseDialog();
      loadDescriptors();
    } catch (err: any) {
      console.error('Failed to save descriptor:', err);
      setError(err.response?.data?.detail || 'Failed to save descriptor');
    }
  };

  const handleDelete = async () => {
    if (!selectedDescriptor) return;

    setError('');
    setSuccess('');

    try {
      await adminAPI.deleteDescriptor(userId, brandId, selectedDescriptor.id);
      setSuccess('Descriptor deleted successfully');
      setDeleteDialogOpen(false);
      setSelectedDescriptor(null);
      loadDescriptors();
    } catch (err: any) {
      console.error('Failed to delete descriptor:', err);
      setError(err.response?.data?.detail || 'Failed to delete descriptor');
    }
  };

  const columns: GridColDef[] = [
    {
      field: 'descriptor',
      headerName: 'Descriptor',
      flex: 1,
      minWidth: 200,
    },
    {
      field: 'is_target',
      headerName: 'Target',
      width: 120,
      renderCell: (params) => (
        params.value ? <Chip label="Target" color="primary" size="small" /> : <Chip label="Competitor" size="small" />
      ),
    },
    {
      field: 'current_ownership',
      headerName: 'Current Ownership',
      width: 180,
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
      field: 'notes',
      headerName: 'Notes',
      flex: 0.5,
      minWidth: 150,
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
          onClick={() => handleOpenDialog(params.row as Descriptor)}
        />,
        <GridActionsCellItem
          icon={<DeleteIcon />}
          label="Delete"
          onClick={() => {
            setSelectedDescriptor(params.row as Descriptor);
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
          Total: {descriptors.length} descriptors
        </Typography>
        <Button
          startIcon={<RefreshIcon />}
          onClick={loadDescriptors}
          size="small"
        >
          Refresh
        </Button>
      </Box>

      <DataGrid
        rows={descriptors}
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
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>{selectedDescriptor ? 'Edit Descriptor' : 'Create Descriptor'}</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              fullWidth
              label="Descriptor"
              value={formData.descriptor}
              onChange={(e) => setFormData({ ...formData, descriptor: e.target.value })}
              required
            />

            <FormControlLabel
              control={
                <Switch
                  checked={formData.is_target}
                  onChange={(e) => setFormData({ ...formData, is_target: e.target.checked })}
                />
              }
              label="Is Target Descriptor"
            />

            <TextField
              fullWidth
              label="Current Ownership"
              value={formData.current_ownership}
              onChange={(e) => setFormData({ ...formData, current_ownership: e.target.value })}
              placeholder="Who currently owns this descriptor"
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
          <Button onClick={handleSave} variant="contained" disabled={!formData.descriptor}>
            Save
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Descriptor</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete this descriptor? This action cannot be undone.
          </Typography>
          {selectedDescriptor && (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
              <Typography variant="body2" fontWeight="bold">
                {selectedDescriptor.descriptor}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Priority: {selectedDescriptor.priority}
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

export default AdminDescriptorsTab;
