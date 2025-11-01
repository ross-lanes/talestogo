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
  Alert,
  Chip,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { DataGrid, GridActionsCellItem } from '@mui/x-data-grid';
import type { GridColDef } from '@mui/x-data-grid';
import { adminAPI } from '../../services/api';

interface Competitor {
  id: number;
  organization: string;
  type: string;
  focus_area?: string;
  track: boolean;
  key_descriptors?: string;
  website?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

interface AdminCompetitorsTabProps {
  userId: number;
  brandId: number;
}

const AdminCompetitorsTab: React.FC<AdminCompetitorsTabProps> = ({ userId, brandId }) => {
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedCompetitor, setSelectedCompetitor] = useState<Competitor | null>(null);
  const [formData, setFormData] = useState({
    organization: '',
    type: '',
    focus_area: '',
    track: true,
    key_descriptors: '',
    website: '',
    notes: '',
  });

  useEffect(() => {
    loadCompetitors();
  }, [userId, brandId]);

  const loadCompetitors = async () => {
    setLoading(true);
    setError('');

    try {
      const data = await adminAPI.getUserBrandCompetitors(userId, brandId);
      setCompetitors(data);
    } catch (err: any) {
      console.error('Failed to load competitors:', err);
      setError('Failed to load competitors');
    } finally {
      setLoading(false);
    }
  };

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
    setError('');
  };

  const handleSave = async () => {
    setError('');
    setSuccess('');

    try {
      if (selectedCompetitor) {
        await adminAPI.updateCompetitor(userId, brandId, selectedCompetitor.id, formData);
        setSuccess('Competitor updated successfully');
      } else {
        await adminAPI.createCompetitor(userId, brandId, formData);
        setSuccess('Competitor created successfully');
      }

      handleCloseDialog();
      loadCompetitors();
    } catch (err: any) {
      console.error('Failed to save competitor:', err);
      setError(err.response?.data?.detail || 'Failed to save competitor');
    }
  };

  const handleDelete = async () => {
    if (!selectedCompetitor) return;

    setError('');
    setSuccess('');

    try {
      await adminAPI.deleteCompetitor(userId, brandId, selectedCompetitor.id);
      setSuccess('Competitor deleted successfully');
      setDeleteDialogOpen(false);
      setSelectedCompetitor(null);
      loadCompetitors();
    } catch (err: any) {
      console.error('Failed to delete competitor:', err);
      setError(err.response?.data?.detail || 'Failed to delete competitor');
    }
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
    },
    {
      field: 'focus_area',
      headerName: 'Focus Area',
      flex: 1,
      minWidth: 200,
    },
    {
      field: 'track',
      headerName: 'Tracked',
      width: 100,
      renderCell: (params) => (
        <Chip
          label={params.value ? 'Yes' : 'No'}
          color={params.value ? 'success' : 'default'}
          size="small"
        />
      ),
    },
    {
      field: 'website',
      headerName: 'Website',
      width: 150,
      renderCell: (params) => (
        params.value ? (
          <a href={params.value} target="_blank" rel="noopener noreferrer">
            Link
          </a>
        ) : null
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
          onClick={() => handleOpenDialog(params.row as Competitor)}
        />,
        <GridActionsCellItem
          icon={<DeleteIcon />}
          label="Delete"
          onClick={() => {
            setSelectedCompetitor(params.row as Competitor);
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
          Total: {competitors.length} competitors
        </Typography>
        <Button
          startIcon={<RefreshIcon />}
          onClick={loadCompetitors}
          size="small"
        >
          Refresh
        </Button>
      </Box>

      <DataGrid
        rows={competitors}
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
        <DialogTitle>{selectedCompetitor ? 'Edit Competitor' : 'Create Competitor'}</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              fullWidth
              label="Organization"
              value={formData.organization}
              onChange={(e) => setFormData({ ...formData, organization: e.target.value })}
              required
            />

            <TextField
              fullWidth
              label="Type"
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value })}
              placeholder="e.g., Direct Competitor, Adjacent Alternative"
              required
            />

            <TextField
              fullWidth
              label="Focus Area"
              value={formData.focus_area}
              onChange={(e) => setFormData({ ...formData, focus_area: e.target.value })}
              multiline
              rows={2}
              placeholder="Brief description of their main focus"
            />

            <TextField
              fullWidth
              label="Website"
              value={formData.website}
              onChange={(e) => setFormData({ ...formData, website: e.target.value })}
              placeholder="https://example.com"
            />

            <TextField
              fullWidth
              label="Key Descriptors"
              value={formData.key_descriptors}
              onChange={(e) => setFormData({ ...formData, key_descriptors: e.target.value })}
              multiline
              rows={2}
              placeholder="Comma-separated key descriptors"
            />

            <FormControlLabel
              control={
                <Switch
                  checked={formData.track}
                  onChange={(e) => setFormData({ ...formData, track: e.target.checked })}
                />
              }
              label="Track this competitor"
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
          <Button onClick={handleSave} variant="contained" disabled={!formData.organization || !formData.type}>
            Save
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Competitor</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete this competitor? This action cannot be undone.
          </Typography>
          {selectedCompetitor && (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
              <Typography variant="body2" fontWeight="bold">
                {selectedCompetitor.organization}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Type: {selectedCompetitor.type}
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

export default AdminCompetitorsTab;
