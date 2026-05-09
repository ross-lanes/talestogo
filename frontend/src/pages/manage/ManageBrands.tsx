import { useState } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Button,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  TextField,
  Tooltip,
  IconButton,
  Card,
  CardContent,
  Grid,
} from '@mui/material';
import {
  Delete,
  SwapHoriz,
  Share,
  Edit,
  QuestionAnswer,
  Description,
  Business,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useBrand } from '../../contexts/BrandContext';
import { brandsAPI } from '../../services/api';
import ShareBrandDialog from '../../components/ShareBrandDialog';

const ManageBrand: React.FC = () => {
  const { user } = useAuth();
  const { activeBrand, loading: brandsLoading, refreshBrands } = useBrand();
  const navigate = useNavigate();

  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Transfer dialog state
  const [transferDialogOpen, setTransferDialogOpen] = useState(false);
  const [transferEmail, setTransferEmail] = useState('');
  const [transferring, setTransferring] = useState(false);

  // Remove dialog state
  const [removeDialogOpen, setRemoveDialogOpen] = useState(false);
  const [removing, setRemoving] = useState(false);

  // Delete dialog state (admin only)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Share dialog state
  const [shareDialogOpen, setShareDialogOpen] = useState(false);

  const isAdmin = user?.is_admin === true;

  const handleTransferSubmit = async () => {
    if (!activeBrand || !transferEmail) return;

    try {
      setTransferring(true);
      setError('');
      const result = await brandsAPI.transferBrand(activeBrand.id, transferEmail);
      setSuccess(result.message);
      setTransferDialogOpen(false);
      await refreshBrands();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to transfer brand');
    } finally {
      setTransferring(false);
    }
  };

  const handleRemoveConfirm = async () => {
    if (!activeBrand) return;

    try {
      setRemoving(true);
      setError('');
      const result = await brandsAPI.removeBrand(activeBrand.id);
      setSuccess(result.message);
      setRemoveDialogOpen(false);
      await refreshBrands();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to remove brand');
    } finally {
      setRemoving(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!activeBrand) return;

    try {
      setDeleting(true);
      setError('');
      await brandsAPI.deleteBrand(activeBrand.id);
      setSuccess(`Brand "${activeBrand.brand_name}" permanently deleted`);
      setDeleteDialogOpen(false);
      await refreshBrands();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete brand');
    } finally {
      setDeleting(false);
    }
  };

  if (brandsLoading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (!activeBrand) {
    return (
      <Container maxWidth="lg" sx={{ mt: { xs: 2, sm: 4 }, mb: { xs: 2, sm: 4 }, px: { xs: 2, sm: 3 } }}>
        <Paper sx={{ p: { xs: 3, sm: 4 }, textAlign: 'center' }}>
          <Typography variant="h5" gutterBottom>
            No Brand Selected
          </Typography>
          <Typography color="textSecondary" sx={{ mb: 3 }}>
            Please select a brand from the Brand Switcher in the top navigation, or create a new brand.
          </Typography>
          <Button
            variant="contained"
            color="primary"
            onClick={() => navigate('/manage/brand-info?new=true')}
          >
            Create New Brand
          </Button>
        </Paper>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: { xs: 2, sm: 4 }, mb: { xs: 2, sm: 4 }, px: { xs: 2, sm: 3 } }}>
      <Box sx={{ mb: { xs: 2, sm: 3 }, display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' }, gap: { xs: 2, sm: 0 } }}>
        <Box>
          <Typography variant="h4" component="h1">
            Manage Brand
          </Typography>
          <Typography variant="h6" color="textSecondary">
            {activeBrand.brand_name}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: { xs: 0.5, sm: 1 } }}>
          <Tooltip title="Share Brand">
            <IconButton onClick={() => setShareDialogOpen(true)}>
              <Share />
            </IconButton>
          </Tooltip>
          <Tooltip title="Transfer to Another User">
            <IconButton
              onClick={() => {
                setTransferEmail('');
                setTransferDialogOpen(true);
              }}
              color="primary"
            >
              <SwapHoriz />
            </IconButton>
          </Tooltip>
          {!isAdmin && (
            <Tooltip title="Remove Brand (Transfer to Admin)">
              <IconButton
                onClick={() => setRemoveDialogOpen(true)}
                color="warning"
              >
                <Delete />
              </IconButton>
            </Tooltip>
          )}
          {isAdmin && (
            <Tooltip title="Permanently Delete (Admin Only)">
              <IconButton
                onClick={() => setDeleteDialogOpen(true)}
                color="error"
              >
                <Delete />
              </IconButton>
            </Tooltip>
          )}
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

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card
            sx={{
              cursor: 'pointer',
              '&:hover': { boxShadow: 4 },
              height: '100%'
            }}
            onClick={() => navigate('/manage/brand-info')}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Edit sx={{ fontSize: 40, color: '#80A1D4', mr: 2 }} />
                <Typography variant="h6">Brand Info</Typography>
              </Box>
              <Typography color="textSecondary">
                Edit brand name, description, industry, and website URL.
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card
            sx={{
              cursor: 'pointer',
              '&:hover': { boxShadow: 4 },
              height: '100%'
            }}
            onClick={() => navigate('/manage/queries')}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <QuestionAnswer sx={{ fontSize: 40, color: '#75C9C8', mr: 2 }} />
                <Typography variant="h6">Queries</Typography>
              </Box>
              <Typography color="textSecondary">
                Manage the questions asked to AI platforms about your brand.
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card
            sx={{
              cursor: 'pointer',
              '&:hover': { boxShadow: 4 },
              height: '100%'
            }}
            onClick={() => navigate('/manage/descriptors')}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Description sx={{ fontSize: 40, color: '#44809C', mr: 2 }} />
                <Typography variant="h6">Descriptors</Typography>
              </Box>
              <Typography color="textSecondary">
                Define the target descriptors you want associated with your brand.
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card
            sx={{
              cursor: 'pointer',
              '&:hover': { boxShadow: 4 },
              height: '100%'
            }}
            onClick={() => navigate('/manage/competitors')}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Business sx={{ fontSize: 40, color: '#9FA8DA', mr: 2 }} />
                <Typography variant="h6">Competitors</Typography>
              </Box>
              <Typography color="textSecondary">
                Track competitors to compare your brand's AI visibility.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Transfer Brand Dialog */}
      <Dialog open={transferDialogOpen} onClose={() => setTransferDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Transfer Brand</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>
            Transfer "{activeBrand.brand_name}" to another user in your organization.
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
            Remove "{activeBrand.brand_name}" from your account? This will transfer ownership to
            an admin. All data will be preserved but you will no longer have access to this brand.
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
            <strong>WARNING:</strong> This will permanently delete "{activeBrand.brand_name}" and ALL
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

      {/* Share Brand Dialog */}
      <ShareBrandDialog
        open={shareDialogOpen}
        onClose={() => setShareDialogOpen(false)}
        brandId={activeBrand.id}
        brandName={activeBrand.brand_name}
      />
    </Container>
  );
};

export default ManageBrand;
