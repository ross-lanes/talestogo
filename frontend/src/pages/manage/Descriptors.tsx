import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
  Menu,
  Alert,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  ArrowDropDown as ArrowDropDownIcon,
} from '@mui/icons-material';
import * as XLSX from 'xlsx';
import { DataGrid, GridActionsCellItem } from '@mui/x-data-grid';
import type { GridColDef } from '@mui/x-data-grid';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../../services/api';
import type { TargetDescriptor, TargetDescriptorCreate, TargetDescriptorUpdate } from '../../types';
import { useBrand } from '../../contexts/BrandContext';

export default function Descriptors() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { activeBrand } = useBrand();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedDescriptor, setSelectedDescriptor] = useState<TargetDescriptor | null>(null);
  const [menuAnchorEl, setMenuAnchorEl] = useState<null | HTMLElement>(null);
  const [error, setError] = useState<string>('');
  const [formData, setFormData] = useState<TargetDescriptorCreate>({
    descriptor: '',
    category: '',
    is_target: true,
    current_ownership: '',
    priority: 'Medium',
    notes: '',
  });

  // Fetch descriptors - refetch when active brand changes
  const { data: descriptors = [], isLoading } = useQuery({
    queryKey: ['descriptors', activeBrand?.id],
    queryFn: async () => {
      const response = await api.get<TargetDescriptor[]>('/descriptors/');
      return response.data;
    },
    enabled: !!activeBrand, // Only fetch if there's an active brand
  });

  // Invalidate descriptors when active brand changes
  useEffect(() => {
    if (activeBrand) {
      queryClient.invalidateQueries({ queryKey: ['descriptors', activeBrand.id] });
    }
  }, [activeBrand?.id, queryClient]);

  // Create descriptor mutation
  const createMutation = useMutation({
    mutationFn: async (data: TargetDescriptorCreate) => {
      const response = await api.post<TargetDescriptor>('/descriptors/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['descriptors'] });
      handleCloseDialog();
    },
  });

  // Update descriptor mutation
  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: number; data: TargetDescriptorUpdate }) => {
      console.log('Updating descriptor:', id, data);
      const response = await api.put<TargetDescriptor>(`/descriptors/${id}`, data);
      console.log('Update response:', response.data);
      return response.data;
    },
    onSuccess: () => {
      console.log('Update successful, invalidating queries and closing dialog');
      queryClient.invalidateQueries({ queryKey: ['descriptors'] });
      handleCloseDialog();
      setError('');
    },
    onError: (error: any) => {
      console.error('Update failed:', error);
      const errorMessage = error?.response?.data?.detail || error?.message || 'Failed to update descriptor';
      setError(errorMessage);
    },
  });

  // Delete descriptor mutation
  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/descriptors/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['descriptors'] });
      setDeleteDialogOpen(false);
      setSelectedDescriptor(null);
    },
  });

  const handleOpenDialog = (descriptor?: TargetDescriptor) => {
    setError(''); // Clear any previous errors
    if (descriptor) {
      setSelectedDescriptor(descriptor);
      console.log('Opening dialog with descriptor:', descriptor);
      setFormData({
        descriptor: descriptor.descriptor,
        category: descriptor.category,
        is_target: descriptor.is_target,
        current_ownership: descriptor.current_ownership || '',
        priority: descriptor.priority,
        notes: descriptor.notes || '',
      });
    } else {
      setSelectedDescriptor(null);
      setFormData({
        descriptor: '',
        category: '',
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
  };

  const handleSubmit = () => {
    if (selectedDescriptor) {
      updateMutation.mutate({ id: selectedDescriptor.id, data: formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  const handleDeleteClick = (descriptor: TargetDescriptor) => {
    setSelectedDescriptor(descriptor);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = () => {
    if (selectedDescriptor) {
      deleteMutation.mutate(selectedDescriptor.id);
    }
  };

  const handleDownloadCSV = () => {
    if (descriptors.length === 0) return;

    const csvHeaders = ['Descriptor', 'Category', 'Target for Brand', 'Current Ownership', 'Priority', 'Notes'];
    const csvRows = descriptors.map((descriptor) => [
      `"${descriptor.descriptor.replace(/"/g, '""')}"`,
      `"${descriptor.category}"`,
      descriptor.is_target ? 'Yes' : 'No',
      `"${(descriptor.current_ownership || '').replace(/"/g, '""')}"`,
      `"${descriptor.priority}"`,
      `"${(descriptor.notes || '').replace(/"/g, '""')}"`
    ]);

    const csvContent = [
      csvHeaders.join(','),
      ...csvRows.map(row => row.join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const today = new Date();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    const year = today.getFullYear();
    const dateStr = `${month}_${day}_${year}`;

    link.download = `Descriptors_${dateStr}.csv`;
    link.href = URL.createObjectURL(blob);
    link.click();
    URL.revokeObjectURL(link.href);
  };

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setMenuAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setMenuAnchorEl(null);
  };

  const handleNavigate = (path: string) => {
    navigate(path);
    handleMenuClose();
  };

  const columns: GridColDef[] = [
    {
      field: 'descriptor',
      headerName: 'Descriptor',
      flex: 1,
      minWidth: 200,
    },
    {
      field: 'category',
      headerName: 'Category',
      width: 150,
      renderCell: (params) => (
        <Chip label={params.value} size="small" color="primary" variant="outlined" />
      ),
    },
    {
      field: 'is_target',
      headerName: 'Target',
      width: 100,
      renderCell: (params) => (
        <Chip
          label={params.value ? 'Yes' : 'No'}
          size="small"
          color={params.value ? 'success' : 'default'}
        />
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
    <Box sx={{ width: '100%', maxWidth: '100%', px: 3, py: 2, boxSizing: 'border-box' }}>
      <Box display="flex" alignItems="center" justifyContent="flex-end" gap={1} mb={2}>
        <Typography
          variant="body1"
          sx={{
            color: '#80A1D4',
            cursor: 'pointer',
            '&:hover': { opacity: 0.8 }
          }}
          onClick={() => navigate('/manage/brand-info')}
        >
          Brand Info
        </Typography>
        <Typography variant="body1" sx={{ color: 'black' }}>|</Typography>
        <Typography
          variant="body1"
          sx={{
            color: '#75C9C8',
            cursor: 'pointer',
            '&:hover': { opacity: 0.8 }
          }}
          onClick={() => navigate('/manage/queries')}
        >
          Queries
        </Typography>
        <Typography variant="body1" sx={{ color: 'black' }}>|</Typography>
        <Typography
          variant="body1"
          sx={{
            color: '#44809C',
            fontWeight: 'bold',
            cursor: 'pointer',
            '&:hover': { opacity: 0.8 }
          }}
        >
          Descriptors
        </Typography>
        <Typography variant="body1" sx={{ color: 'black' }}>|</Typography>
        <Typography
          variant="body1"
          sx={{
            color: '#9FA8DA',
            cursor: 'pointer',
            '&:hover': { opacity: 0.8 }
          }}
          onClick={() => navigate('/manage/competitors')}
        >
          Competitors
        </Typography>
      </Box>

      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h2">Customize Descriptors</Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleDownloadCSV}
            disabled={descriptors.length === 0 || !activeBrand}
          >
            Download as CSV
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
            sx={{ ml: 1 }}
            disabled={!activeBrand}
          >
            Add Descriptor
          </Button>
        </Box>
      </Box>

      {!activeBrand && (
        <Alert severity="info" sx={{ mb: 3 }}>
          Please select or create a brand using the Brand Switcher in the top navigation to manage descriptors.
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Paper sx={{ height: 600, width: '100%' }}>
        <DataGrid
          rows={descriptors}
          columns={columns}
          loading={isLoading}
          pageSizeOptions={[10, 25, 50]}
          initialState={{
            pagination: { paginationModel: { pageSize: 25 } },
          }}
          disableRowSelectionOnClick
        />
      </Paper>

      {/* Navigation Menu */}
      <Menu
        anchorEl={menuAnchorEl}
        open={Boolean(menuAnchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => handleNavigate('/manage/brand-info')}>
          Brand Info
        </MenuItem>
        <MenuItem onClick={() => handleNavigate('/manage/queries')}>
          Queries
        </MenuItem>
        <MenuItem onClick={() => handleNavigate('/manage/competitors')}>
          Competitors
        </MenuItem>
      </Menu>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {selectedDescriptor ? 'Edit Descriptor' : 'Add New Descriptor'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
            <TextField
              label="Descriptor"
              value={formData.descriptor}
              onChange={(e) => setFormData({ ...formData, descriptor: e.target.value })}
              required
              fullWidth
              helperText="The descriptor term or phrase (e.g., 'innovative', 'cutting-edge')"
            />
            <TextField
              label="Category"
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              required
              fullWidth
              helperText="Examples: Technical, Leadership, Innovation"
            />
            <TextField
              label="Current Ownership"
              value={formData.current_ownership}
              onChange={(e) => setFormData({ ...formData, current_ownership: e.target.value })}
              fullWidth
              helperText="Which organization currently owns this descriptor"
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
                  checked={formData.is_target}
                  onChange={(e) =>
                    setFormData({ ...formData, is_target: e.target.checked })
                  }
                />
              }
              label="Target for PPPL"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={
              !formData.descriptor ||
              !formData.category ||
              createMutation.isPending ||
              updateMutation.isPending
            }
          >
            {selectedDescriptor ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Descriptor</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete the descriptor "{selectedDescriptor?.descriptor}"? This
            action cannot be undone.
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
