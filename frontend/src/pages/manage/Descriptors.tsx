import { useState } from 'react';
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

export default function Descriptors() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedDescriptor, setSelectedDescriptor] = useState<TargetDescriptor | null>(null);
  const [menuAnchorEl, setMenuAnchorEl] = useState<null | HTMLElement>(null);
  const [formData, setFormData] = useState<TargetDescriptorCreate>({
    descriptor: '',
    category: '',
    target_for_pppl: true,
    current_ownership: '',
    priority: 'Medium',
    notes: '',
  });

  // Fetch descriptors
  const { data: descriptors = [], isLoading } = useQuery({
    queryKey: ['descriptors'],
    queryFn: async () => {
      const response = await api.get<TargetDescriptor[]>('/descriptors/');
      return response.data;
    },
  });

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
      const response = await api.put<TargetDescriptor>(`/descriptors/${id}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['descriptors'] });
      handleCloseDialog();
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
    if (descriptor) {
      setSelectedDescriptor(descriptor);
      setFormData({
        descriptor: descriptor.descriptor,
        category: descriptor.category,
        target_for_pppl: descriptor.target_for_pppl,
        current_ownership: descriptor.current_ownership || '',
        priority: descriptor.priority,
        notes: descriptor.notes || '',
      });
    } else {
      setSelectedDescriptor(null);
      setFormData({
        descriptor: '',
        category: '',
        target_for_pppl: true,
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

  const handleDownloadSpreadsheet = () => {
    // Prepare data for export
    const exportData = descriptors.map((descriptor) => ({
      'Descriptor': descriptor.descriptor,
      'Category': descriptor.category,
      'Target for PPPL': descriptor.target_for_pppl ? 'Yes' : 'No',
      'Current Ownership': descriptor.current_ownership || '',
      'Priority': descriptor.priority,
      'Notes': descriptor.notes || '',
    }));

    // Create worksheet
    const ws = XLSX.utils.json_to_sheet(exportData);

    // Create workbook
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Descriptors');

    // Generate file and trigger download
    XLSX.writeFile(wb, 'AIRO_Descriptors.xlsx');
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
      field: 'target_for_pppl',
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
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center">
          <Typography variant="h2" sx={{ mr: 1 }}>Customize</Typography>
          <Box
            onClick={handleMenuClick}
            sx={{
              display: 'flex',
              alignItems: 'center',
              cursor: 'pointer',
              '&:hover': { opacity: 0.8 },
            }}
          >
            <Typography variant="h2" sx={{ color: '#665775', fontWeight: 'bold' }}>
              Descriptors
            </Typography>
            <ArrowDropDownIcon sx={{ fontSize: 40, color: '#665775' }} />
          </Box>
        </Box>
        <Box>
          <IconButton
            onClick={() => queryClient.invalidateQueries({ queryKey: ['descriptors'] })}
          >
            <RefreshIcon />
          </IconButton>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleDownloadSpreadsheet}
            sx={{ ml: 1 }}
            disabled={descriptors.length === 0}
          >
            Download
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
            sx={{ ml: 1 }}
          >
            Add Descriptor
          </Button>
        </Box>
      </Box>

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
                  checked={formData.target_for_pppl}
                  onChange={(e) =>
                    setFormData({ ...formData, target_for_pppl: e.target.checked })
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
