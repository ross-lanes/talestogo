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
import type { Query, QueryCreate, QueryUpdate } from '../../types';
import { useBrand } from '../../contexts/BrandContext';

export default function Queries() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { activeBrand } = useBrand();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedQuery, setSelectedQuery] = useState<Query | null>(null);
  const [menuAnchorEl, setMenuAnchorEl] = useState<null | HTMLElement>(null);
  const [formData, setFormData] = useState<Omit<QueryCreate, 'query_id'>>({
    query_text: '',
    category: '',
    priority: 'Medium',
    target_outcome: 'mention',
    brand_in_query: false,
    active: true,
    notes: '',
  });

  // Fetch queries - refetch when active brand changes
  const { data: queries = [], isLoading } = useQuery({
    queryKey: ['queries', activeBrand?.id],
    queryFn: async () => {
      const response = await api.get<Query[]>('/queries/');
      return response.data;
    },
    enabled: !!activeBrand, // Only fetch if there's an active brand
  });

  // Invalidate queries when active brand changes
  useEffect(() => {
    if (activeBrand) {
      queryClient.invalidateQueries({ queryKey: ['queries', activeBrand.id] });
    }
  }, [activeBrand?.id, queryClient]);

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
        brand_in_query: query.brand_in_query ?? false,
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
  };

  const handleSubmit = () => {
    if (selectedQuery) {
      // For update, send the form data (query_id is already excluded)
      updateMutation.mutate({ query_id: selectedQuery.query_id, data: formData });
    } else {
      // For create, send form data (backend will auto-generate query_id)
      createMutation.mutate(formData as any);
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

  const handleDownloadCSV = () => {
    if (queries.length === 0) return;

    const csvHeaders = ['Query ID', 'Query Text', 'Category', 'Priority', 'Target Outcome', 'Brand in Query', 'Active', 'Notes'];
    const csvRows = queries.map((query) => [
      `"${query.query_id}"`,
      `"${query.query_text.replace(/"/g, '""')}"`,
      `"${query.category}"`,
      `"${query.priority}"`,
      `"${query.target_outcome}"`,
      query.brand_in_query ? 'Yes' : 'No',
      query.active ? 'Yes' : 'No',
      `"${(query.notes || '').replace(/"/g, '""')}"`
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

    link.download = `Queries_${dateStr}.csv`;
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
      field: 'query_id',
      headerName: 'Query ID',
      width: 75,
      align: 'left',
      headerAlign: 'left',
      renderCell: (params) => (
        <Typography variant="body2" sx={{ color: '#80A1D4', fontWeight: 'bold', display: 'flex', alignItems: 'center', height: '100%' }}>
          {params.value}
        </Typography>
      ),
    },
    {
      field: 'query_text',
      headerName: 'Query Text',
      flex: 1,
      minWidth: 300,
      align: 'left',
      headerAlign: 'left',
    },
    {
      field: 'category',
      headerName: 'Category',
      width: 150,
      align: 'left',
      headerAlign: 'left',
    },
    {
      field: 'priority',
      headerName: 'Priority',
      width: 90,
      align: 'left',
      headerAlign: 'left',
      renderCell: (params) => {
        const color =
          params.value === 'High'
            ? '#d32f2f'
            : params.value === 'Medium'
            ? '#ed6c02'
            : '#2e7d32';
        return (
          <Typography variant="body2" sx={{ color, fontWeight: 'bold', display: 'flex', alignItems: 'center', height: '100%' }}>
            {params.value}
          </Typography>
        );
      },
    },
    {
      field: 'target_outcome',
      headerName: 'Target Outcome',
      width: 150,
      align: 'left',
      headerAlign: 'left',
    },
    {
      field: 'brand_in_query',
      headerName: 'Brand in Query',
      width: 120,
      align: 'left',
      headerAlign: 'left',
      renderCell: (params) => (
        <Typography
          variant="body2"
          sx={{
            color: params.value ? '#1976d2' : '#757575',
            fontWeight: params.value ? 'bold' : 'normal',
            display: 'flex',
            alignItems: 'center',
            height: '100%'
          }}
        >
          {params.value ? 'Yes' : 'No'}
        </Typography>
      ),
    },
    {
      field: 'active',
      headerName: 'Active',
      width: 75,
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
            fontWeight: 'bold',
            cursor: 'pointer',
            '&:hover': { opacity: 0.8 }
          }}
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
            cursor: 'pointer',
            '&:hover': { opacity: 0.8 }
          }}
          onClick={() => navigate('/manage/competitors')}
        >
          Competitors
        </Typography>
      </Box>

      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h2">Customize Queries</Typography>
        <Box>
          <IconButton onClick={() => queryClient.invalidateQueries({ queryKey: ['queries', activeBrand?.id] })}>
            <RefreshIcon />
          </IconButton>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleDownloadCSV}
            sx={{ ml: 1 }}
            disabled={queries.length === 0 || !activeBrand}
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
            Add Query
          </Button>
        </Box>
      </Box>

      {!activeBrand && (
        <Alert severity="info" sx={{ mb: 3 }}>
          Please select or create a brand using the Brand Switcher in the top navigation to manage queries.
        </Alert>
      )}

      <Paper sx={{ height: 600, width: '100%', maxWidth: '100%', overflow: 'auto' }}>
        <DataGrid
          rows={queries}
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
        <MenuItem onClick={() => handleNavigate('/manage/descriptors')}>
          Descriptors
        </MenuItem>
        <MenuItem onClick={() => handleNavigate('/manage/competitors')}>
          Competitors
        </MenuItem>
      </Menu>

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
                  checked={formData.brand_in_query}
                  onChange={(e) => setFormData({ ...formData, brand_in_query: e.target.checked })}
                />
              }
              label="Brand in Query"
            />
            <Typography variant="caption" color="text.secondary" sx={{ mt: -1, mb: 1 }}>
              Check this if the brand name is explicitly mentioned in the query (e.g., "Tell me about [Brand]").
              These queries won't count toward mention/positioning metrics but will count for sentiment/descriptors.
            </Typography>
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
