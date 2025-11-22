import { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  TextField,
  Tooltip,
} from '@mui/material';
import {
  Delete,
  SwapHoriz,
  RemoveCircleOutline,
  Edit,
  Share,
  CheckCircle,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useBrand } from '../../contexts/BrandContext';
import { brandsAPI } from '../../services/api';

interface BrandInfo {
  id: number;
  user_id?: number;
  brand_name: string;
  website_url: string | null;
  industry: string | null;
  description: string | null;
  is_active: boolean;
  created_at: string;
}

const ManageBrands: React.FC = () => {
  const { user } = useAuth();
  const { switchBrand, activeBrand } = useBrand();
  const navigate = useNavigate();

  const { brands, loading: brandsLoading, refreshBrands } = useBrand();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Transfer dialog state
  const [transferDialogOpen, setTransferDialogOpen] = useState(false);
  const [transferBrandId, setTransferBrandId] = useState<number | null>(null);
  const [transferBrandName, setTransferBrandName] = useState('');
  const [transferEmail, setTransferEmail] = useState('');
  const [transferring, setTransferring] = useState(false);

  // Remove dialog state
  const [removeDialogOpen, setRemoveDialogOpen] = useState(false);
  const [removeBrandId, setRemoveBrandId] = useState<number | null>(null);
  const [removeBrandName, setRemoveBrandName] = useState('');
  const [removing, setRemoving] = useState(false);

  // Delete dialog state (admin only)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteBrandId, setDeleteBrandId] = useState<number | null>(null);
  const [deleteBrandName, setDeleteBrandName] = useState('');
  const [deleting, setDeleting] = useState(false);

  const isAdmin = user?.email === 'robotrachel@gmail.com';

  const handleTransferClick = (brand: BrandInfo) => {
    setTransferBrandId(brand.id);
    setTransferBrandName(brand.brand_name);
    setTransferEmail('');
    setTransferDialogOpen(true);
  };

  const handleTransferSubmit = async () => {
    if (!transferBrandId || !transferEmail) return;

    try {
      setTransferring(true);
      setError('');
      const result = await brandsAPI.transferBrand(transferBrandId, transferEmail);
      setSuccess(result.message);
      setTransferDialogOpen(false);
      await refreshBrands(); // Reload to remove transferred brand
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to transfer brand');
    } finally {
      setTransferring(false);
    }
  };

  const handleRemoveClick = (brand: BrandInfo) => {
    setRemoveBrandId(brand.id);
    setRemoveBrandName(brand.brand_name);
    setRemoveDialogOpen(true);
  };

  const handleRemoveConfirm = async () => {
    if (!removeBrandId) return;

    try {
      setRemoving(true);
      setError('');
      const result = await brandsAPI.removeBrand(removeBrandId);
      setSuccess(result.message);
      setRemoveDialogOpen(false);
      await refreshBrands(); // Reload to remove brand from list
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to remove brand');
    } finally {
      setRemoving(false);
    }
  };

  const handleDeleteClick = (brand: BrandInfo) => {
    setDeleteBrandId(brand.id);
    setDeleteBrandName(brand.brand_name);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!deleteBrandId) return;

    try {
      setDeleting(true);
      setError('');
      await brandsAPI.deleteBrand(deleteBrandId);
      setSuccess(`Brand "${deleteBrandName}" permanently deleted`);
      setDeleteDialogOpen(false);
      await refreshBrands(); // Reload to remove deleted brand
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete brand');
    } finally {
      setDeleting(false);
    }
  };

  const handleActivate = async (brand: BrandInfo) => {
    try {
      await switchBrand(brand.id);
      // No need to reload - switchBrand already updates the context
    } catch (err: any) {
      setError('Failed to activate brand');
    }
  };

  if (brandsLoading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1">
          Manage Brands
        </Typography>
        <Button
          variant="contained"
          color="primary"
          onClick={() => navigate('/manage/brand-info?new=true')}
        >
          Create New Brand
        </Button>
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

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Brand Name</TableCell>
              <TableCell>Industry</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Created</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {brands.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  <Typography color="textSecondary" sx={{ py: 3 }}>
                    No brands found. Create your first brand to get started.
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              brands.map((brand) => (
                <TableRow key={brand.id}>
                  <TableCell>
                    <Typography variant="body1" fontWeight={brand.is_active ? 'bold' : 'normal'}>
                      {brand.brand_name}
                    </Typography>
                  </TableCell>
                  <TableCell>{brand.industry || '-'}</TableCell>
                  <TableCell>
                    {brand.is_active ? (
                      <Chip
                        icon={<CheckCircle />}
                        label="Active"
                        color="success"
                        size="small"
                      />
                    ) : (
                      <Button
                        size="small"
                        onClick={() => handleActivate(brand)}
                      >
                        Activate
                      </Button>
                    )}
                  </TableCell>
                  <TableCell>
                    {new Date(brand.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="Edit">
                      <IconButton
                        size="small"
                        onClick={() => navigate(`/manage/brand-info?brand_id=${brand.id}`)}
                      >
                        <Edit />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Share">
                      <IconButton
                        size="small"
                        onClick={() => navigate(`/manage/brand-info?brand_id=${brand.id}`)}
                      >
                        <Share />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Transfer to Another User">
                      <IconButton
                        size="small"
                        onClick={() => handleTransferClick(brand)}
                        color="primary"
                      >
                        <SwapHoriz />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Remove Brand (Transfer to Admin)">
                      <IconButton
                        size="small"
                        onClick={() => handleRemoveClick(brand)}
                        color="warning"
                        disabled={isAdmin}
                      >
                        <Delete />
                      </IconButton>
                    </Tooltip>
                    {isAdmin && (
                      <Tooltip title="Permanently Delete (Admin Only)">
                        <IconButton
                          size="small"
                          onClick={() => handleDeleteClick(brand)}
                          color="error"
                        >
                          <RemoveCircleOutline />
                        </IconButton>
                      </Tooltip>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Transfer Brand Dialog */}
      <Dialog open={transferDialogOpen} onClose={() => setTransferDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Transfer Brand</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>
            Transfer "{transferBrandName}" to another user in your organization.
            The new owner will receive all brand data and you will no longer have access.
          </DialogContentText>
          <TextField
            autoFocus
            margin="dense"
            label="New Owner's Email"
            type="email"
            fullWidth
            value={transferEmail}
            onChange={(e) => setTransferEmail(e.target.value)}
            placeholder="colleague@company.com"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTransferDialogOpen(false)} disabled={transferring}>
            Cancel
          </Button>
          <Button
            onClick={handleTransferSubmit}
            variant="contained"
            disabled={!transferEmail || transferring}
          >
            {transferring ? <CircularProgress size={24} /> : 'Transfer'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Remove Brand Dialog */}
      <Dialog open={removeDialogOpen} onClose={() => setRemoveDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Remove Brand</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Remove "{removeBrandName}" from your account? This will transfer ownership to
            the admin (robotrachel@gmail.com). All data will be preserved but you will
            no longer have access to this brand.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRemoveDialogOpen(false)} disabled={removing}>
            Cancel
          </Button>
          <Button
            onClick={handleRemoveConfirm}
            variant="contained"
            color="warning"
            disabled={removing}
          >
            {removing ? <CircularProgress size={24} /> : 'Remove'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Brand Dialog (Admin Only) */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Permanently Delete Brand</DialogTitle>
        <DialogContent>
          <DialogContentText color="error">
            <strong>WARNING:</strong> This will permanently delete "{deleteBrandName}" and ALL
            associated data including queries, responses, competitors, descriptors, reports,
            and analytics. This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)} disabled={deleting}>
            Cancel
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            variant="contained"
            color="error"
            disabled={deleting}
          >
            {deleting ? <CircularProgress size={24} /> : 'Permanently Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default ManageBrands;
