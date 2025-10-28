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

  const handleDownloadSpreadsheet = () => {
    // Prepare data for export
    const exportData = competitors.map((competitor) => ({
      'Organization': competitor.organization,
      'Type': competitor.type,
      'Focus Area': competitor.focus_area || '',
      'Track': competitor.track ? 'Yes' : 'No',
      'Key Descriptors': competitor.key_descriptors || '',
      'Website': competitor.website || '',
      'Notes': competitor.notes || '',
    }));

    // Create worksheet
    const ws = XLSX.utils.json_to_sheet(exportData);

    // Create workbook
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Competitors');

    // Generate file and trigger download
    XLSX.writeFile(wb, 'TALES_Competitors.xlsx');
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
    },
    {
      field: 'type',
      headerName: 'Type',
      width: 150,
      renderCell: (params) => (
        <Chip label={params.value} size="small" color="primary" variant="outlined" />
      ),
    },
    {
      field: 'focus_area',
      headerName: 'Focus Area',
      width: 180,
    },
    {
      field: 'track',
      headerName: 'Tracking',
      width: 120,
      renderCell: (params) => (
        <Chip
          label={params.value ? 'Active' : 'Inactive'}
          size="small"
          color={params.value ? 'success' : 'default'}
        />
      ),
    },
    {
      field: 'website',
      headerName: 'Website',
      width: 200,
      renderCell: (params) =>
        params.value ? (
          <a href={params.value} target="_blank" rel="noopener noreferrer">
            Link
          </a>
        ) : null,
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
              Competitors
            </Typography>
            <ArrowDropDownIcon sx={{ fontSize: 40, color: '#665775' }} />
          </Box>
        </Box>
        <Box>
          <IconButton
            onClick={() => queryClient.invalidateQueries({ queryKey: ['competitors', activeBrand?.id] })}
          >
            <RefreshIcon />
          </IconButton>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleDownloadSpreadsheet}
            sx={{ ml: 1 }}
            disabled={competitors.length === 0 || !activeBrand}
          >
            Download
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

      <Paper sx={{ height: 600, width: '100%' }}>
        <DataGrid
          rows={competitors}
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
