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
import { DataGrid, GridActionsCellItem } from '@mui/x-data-grid';
import type { GridColDef } from '@mui/x-data-grid';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../../services/api';
import type { Competitor, CompetitorCreate, CompetitorUpdate } from '../../types';
import { useBrand } from '../../contexts/BrandContext';

export default function Competitors() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { activeBrand } = useBrand();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedCompetitor, setSelectedCompetitor] = useState<Competitor | null>(null);
  const [menuAnchorEl, setMenuAnchorEl] = useState<null | HTMLElement>(null);
  const [formData, setFormData] = useState<CompetitorCreate>({
    organization: '',
    type: '',
    focus_area: '',
    track: true,
    key_descriptors: '',
    website: '',
    notes: '',
  });

  // Fetch competitors - refetch when active brand changes
  const { data: competitors = [], isLoading } = useQuery({
    queryKey: ['competitors', activeBrand?.id],
    queryFn: async () => {
      const response = await api.get<Competitor[]>('/competitors/');
      return response.data;
    },
    enabled: !!activeBrand, // Only fetch if there's an active brand
  });

  // Invalidate competitors when active brand changes
  useEffect(() => {
    if (activeBrand) {
      queryClient.invalidateQueries({ queryKey: ['competitors', activeBrand.id] });
    }
  }, [activeBrand?.id, queryClient]);

  // Create competitor mutation
  const createMutation = useMutation({
    mutationFn: async (data: CompetitorCreate) => {
      const response = await api.post<Competitor>('/competitors/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['competitors'] });
      handleCloseDialog();
    },
  });

  // Update competitor mutation
  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: number; data: CompetitorUpdate }) => {
      const response = await api.put<Competitor>(`/competitors/${id}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['competitors'] });
      handleCloseDialog();
    },
    onError: (error: any) => {
      alert(`Failed to update competitor: ${error.response?.data?.detail || error.message}`);
    },
  });

  // Delete competitor mutation
  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/competitors/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['competitors'] });
      setDeleteDialogOpen(false);
      setSelectedCompetitor(null);
    },
  });

  const handleOpenDialog = (competitor?: Competitor) => {
    if (competitor) {
      setSelectedCompetitor(competitor);
      setFormData({
        organization: competitor.organization,
        type: competitor.type,
        focus_area: competitor.focus_area || '',
        track: competitor.track,
        key_descriptors: competitor.key_descriptors || '',
        website: competitor.website || '',
        notes: competitor.notes || '',
      });
    } else {
      setSelectedCompetitor(null);
      setFormData({
        organization: '',
        type: '',
        focus_area: '',
        track: true,
        key_descriptors: '',
        website: '',
        notes: '',
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setSelectedCompetitor(null);
  };

  const handleSubmit = () => {
    if (selectedCompetitor) {
      updateMutation.mutate({ id: selectedCompetitor.id, data: formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  const handleDeleteClick = (competitor: Competitor) => {
    setSelectedCompetitor(competitor);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = () => {
    if (selectedCompetitor) {
      deleteMutation.mutate(selectedCompetitor.id);
    }
  };

  const handleDownloadCSV = () => {
    if (competitors.length === 0) return;

    const csvHeaders = ['Organization', 'Type', 'Focus Area', 'Track', 'Key Descriptors', 'Website', 'Notes'];
    const csvRows = competitors.map((competitor) => [
      `"${competitor.organization.replace(/"/g, '""')}"`,
      `"${competitor.type}"`,
      `"${(competitor.focus_area || '').replace(/"/g, '""')}"`,
      competitor.track ? 'Yes' : 'No',
      `"${(competitor.key_descriptors || '').replace(/"/g, '""')}"`,
      `"${(competitor.website || '').replace(/"/g, '""')}"`,
      `"${(competitor.notes || '').replace(/"/g, '""')}"`
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

    link.download = `Competitors_${dateStr}.csv`;
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
      field: 'organization',
      headerName: 'Organization',
      flex: 1,
      minWidth: 200,
      align: 'left',
      headerAlign: 'left',
    },
    {
      field: 'type',
      headerName: 'Type',
      width: 150,
      align: 'left',
      headerAlign: 'left',
      renderCell: (params) => (
        <Typography variant="body2" sx={{ color: '#80A1D4', fontWeight: 'bold', display: 'flex', alignItems: 'center', height: '100%' }}>
          {params.value}
        </Typography>
      ),
    },
    {
      field: 'focus_area',
      headerName: 'Focus Area',
      width: 180,
      align: 'left',
      headerAlign: 'left',
    },
    {
      field: 'track',
      headerName: 'Tracking',
      width: 120,
      align: 'left',
      headerAlign: 'left',
      renderCell: (params) => (
        <Typography
          variant="body2"
          sx={{
            color: params.value ? '#2e7d32' : '#757575',
            fontWeight: 'bold',
            display: 'flex',
            alignItems: 'center',
            height: '100%'
          }}
        >
          {params.value ? 'Active' : 'Inactive'}
        </Typography>
      ),
    },
    {
      field: 'website',
      headerName: 'Website',
      width: 100,
      align: 'left',
      headerAlign: 'left',
      renderCell: (params) => {
        if (!params.value) return null;
        // Ensure URL has protocol
        const url = params.value.startsWith('http://') || params.value.startsWith('https://')
          ? params.value
          : `https://${params.value}`;
        return (
          <a href={url} target="_blank" rel="noopener noreferrer" style={{ display: 'flex', alignItems: 'center', height: '100%' }}>
            Link
          </a>
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
    <Box sx={{ width: '100%', maxWidth: '100%', overflow: 'hidden' }}>
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
            cursor: 'pointer',
            '&:hover': { opacity: 0.8 }
          }}
          onClick={() => navigate('/manage/descriptors')}
        >
          Descriptors
        </Typography>
        <Typography variant="body1" sx={{ color: 'black' }}>|</Typography>
        <Typography
          variant="body1"
          sx={{
            color: '#9FA8DA',
            fontWeight: 'bold',
            cursor: 'pointer',
            '&:hover': { opacity: 0.8 }
          }}
        >
          Competitors
        </Typography>
      </Box>

      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h2">Customize Competitors</Typography>
        <Box>
          <IconButton
            onClick={() => queryClient.invalidateQueries({ queryKey: ['competitors', activeBrand?.id] })}
          >
            <RefreshIcon />
          </IconButton>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleDownloadCSV}
            sx={{ ml: 1 }}
            disabled={competitors.length === 0 || !activeBrand}
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
            Add Competitor
          </Button>
        </Box>
      </Box>

      {!activeBrand && (
        <Alert severity="info" sx={{ mb: 3 }}>
          Please select or create a brand using the Brand Switcher in the top navigation to manage competitors.
        </Alert>
      )}

      <Paper sx={{ height: 600, width: '100%', maxWidth: '100%', overflow: 'auto' }}>
        <DataGrid
          rows={competitors}
          columns={columns}
          loading={isLoading}
          pageSizeOptions={[10, 25, 50]}
          initialState={{
            pagination: { paginationModel: { pageSize: 25 } },
          }}
          disableRowSelectionOnClick
          sx={{ width: '100%' }}
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
        <MenuItem onClick={() => handleNavigate('/manage/descriptors')}>
          Descriptors
        </MenuItem>
      </Menu>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {selectedCompetitor ? 'Edit Competitor' : 'Add New Competitor'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
            <TextField
              label="Organization"
              value={formData.organization}
              onChange={(e) => setFormData({ ...formData, organization: e.target.value })}
              required
              fullWidth
            />
            <TextField
              label="Type"
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value })}
              required
              fullWidth
              helperText="Examples: Research Lab, University, Private Company"
            />
            <TextField
              label="Focus Area"
              value={formData.focus_area}
              onChange={(e) => setFormData({ ...formData, focus_area: e.target.value })}
              fullWidth
            />
            <TextField
              label="Key Descriptors"
              value={formData.key_descriptors}
              onChange={(e) => setFormData({ ...formData, key_descriptors: e.target.value })}
              fullWidth
              multiline
              rows={2}
              helperText="Comma-separated list of descriptors"
            />
            <TextField
              label="Website"
              value={formData.website}
              onChange={(e) => setFormData({ ...formData, website: e.target.value })}
              fullWidth
              type="url"
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
                  checked={formData.track}
                  onChange={(e) => setFormData({ ...formData, track: e.target.checked })}
                />
              }
              label="Track in Analysis"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={
              !formData.organization ||
              !formData.type ||
              createMutation.isPending ||
              updateMutation.isPending
            }
          >
            {selectedCompetitor ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Competitor</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete "{selectedCompetitor?.organization}"? This action
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
