import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  IconButton,
  Card,
  CardContent,
  Grid,
  Avatar,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Business as BusinessIcon,
} from '@mui/icons-material';
import { adminAPI } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';

interface Tenant {
  id: number;
  tenant_name: string;
  subdomain?: string;
  logo_url?: string;
  primary_color: string;
  secondary_color: string;
  custom_domain?: string;
  created_at: string;
  updated_at: string;
}

const TenantManagement: React.FC = () => {
  const { isAdmin } = useAuth();

  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Create/Edit dialog
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingTenant, setEditingTenant] = useState<Tenant | null>(null);
  const [formData, setFormData] = useState({
    tenant_name: '',
    subdomain: '',
    logo_url: '',
    primary_color: '#75C9C8',
    secondary_color: '#665775',
    custom_domain: '',
  });
  const [logoUploadMode, setLogoUploadMode] = useState<'url' | 'file'>('url');
  const [logoFile, setLogoFile] = useState<File | null>(null);

  useEffect(() => {
    if (isAdmin) {
      loadTenants();
    }
  }, [isAdmin]);

  const loadTenants = async () => {
    setLoading(true);
    setError('');

    try {
      const data = await adminAPI.listTenants();
      setTenants(data);
    } catch (err: any) {
      console.error('Failed to load tenants:', err);
      setError('Failed to load tenants');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (tenant?: Tenant) => {
    if (tenant) {
      setEditingTenant(tenant);
      setFormData({
        tenant_name: tenant.tenant_name,
        subdomain: tenant.subdomain || '',
        logo_url: tenant.logo_url || '',
        primary_color: tenant.primary_color,
        secondary_color: tenant.secondary_color,
        custom_domain: tenant.custom_domain || '',
      });
    } else {
      setEditingTenant(null);
      setFormData({
        tenant_name: '',
        subdomain: '',
        logo_url: '',
        primary_color: '#75C9C8',
        secondary_color: '#665775',
        custom_domain: '',
      });
    }
    setLogoFile(null);
    setLogoUploadMode('url');
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingTenant(null);
    setFormData({
      tenant_name: '',
      subdomain: '',
      logo_url: '',
      primary_color: '#75C9C8',
      secondary_color: '#665775',
      custom_domain: '',
    });
    setLogoFile(null);
    setLogoUploadMode('url');
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setLogoFile(file);
      // Create a preview URL
      const reader = new FileReader();
      reader.onloadend = () => {
        setFormData({ ...formData, logo_url: reader.result as string });
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async () => {
    setError('');
    setSuccess('');

    if (!formData.tenant_name) {
      setError('Tenant name is required');
      return;
    }

    try {
      if (editingTenant) {
        // Update existing tenant
        await adminAPI.updateTenant(editingTenant.id, formData);
        setSuccess(`Tenant "${formData.tenant_name}" updated successfully`);
      } else {
        // Create new tenant
        await adminAPI.createTenant(formData);
        setSuccess(`Tenant "${formData.tenant_name}" created successfully`);
      }

      handleCloseDialog();
      await loadTenants();
    } catch (err: any) {
      console.error('Failed to save tenant:', err);
      setError(err.response?.data?.detail || 'Failed to save tenant');
    }
  };

  const handleDelete = async (tenant: Tenant) => {
    if (!window.confirm(`Are you sure you want to delete tenant "${tenant.tenant_name}"? This cannot be undone.`)) {
      return;
    }

    try {
      await adminAPI.deleteTenant(tenant.id);
      setSuccess(`Tenant "${tenant.tenant_name}" deleted successfully`);
      await loadTenants();
    } catch (err: any) {
      console.error('Failed to delete tenant:', err);
      setError(err.response?.data?.detail || 'Failed to delete tenant');
    }
  };

  if (!isAdmin) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error">You must be an admin to access this page.</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Tenant Management
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          Create Tenant
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

      <Grid container spacing={3}>
        {tenants.map((tenant) => (
          <Grid item xs={12} key={tenant.id}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  {/* Left: Logo and Name */}
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, flex: 1 }}>
                    {tenant.logo_url ? (
                      <Box
                        sx={{
                          width: 120,
                          height: 60,
                          bgcolor: tenant.logo_url.toLowerCase().includes('white')
                            ? (tenant.primary_color || tenant.secondary_color || '#000000')
                            : '#000000',
                          border: '1px solid #e0e0e0',
                          borderRadius: 1,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          padding: 1,
                        }}
                      >
                        <img
                          src={tenant.logo_url}
                          alt={`${tenant.tenant_name} logo`}
                          style={{
                            maxWidth: '100%',
                            maxHeight: '100%',
                            objectFit: 'contain'
                          }}
                        />
                      </Box>
                    ) : (
                      <Box
                        sx={{
                          width: 120,
                          height: 60,
                          bgcolor: tenant.primary_color,
                          border: '1px solid #e0e0e0',
                          borderRadius: 1,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        <BusinessIcon fontSize="large" sx={{ color: 'white' }} />
                      </Box>
                    )}
                    <Box>
                      <Typography variant="h5" component="div">
                        {tenant.tenant_name}
                      </Typography>
                      {tenant.subdomain && (
                        <Typography variant="body2" color="text.secondary">
                          {tenant.subdomain}
                        </Typography>
                      )}
                    </Box>
                  </Box>

                  {/* Middle: Colors */}
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flex: 1, justifyContent: 'center' }}>
                    <Box>
                      <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.5 }}>
                        Primary Color
                      </Typography>
                      <Box
                        sx={{
                          width: 100,
                          height: 50,
                          bgcolor: tenant.primary_color,
                          border: '1px solid #ddd',
                          borderRadius: 1,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        <Typography variant="caption" sx={{ color: 'white', fontWeight: 'bold' }}>
                          {tenant.primary_color}
                        </Typography>
                      </Box>
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.5 }}>
                        Secondary Color
                      </Typography>
                      <Box
                        sx={{
                          width: 100,
                          height: 50,
                          bgcolor: tenant.secondary_color,
                          border: '1px solid #ddd',
                          borderRadius: 1,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        <Typography variant="caption" sx={{ color: 'white', fontWeight: 'bold' }}>
                          {tenant.secondary_color}
                        </Typography>
                      </Box>
                    </Box>
                  </Box>

                  {/* Right: Details and Actions */}
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flex: 1, justifyContent: 'flex-end' }}>
                    <Box sx={{ textAlign: 'right' }}>
                      {tenant.custom_domain && (
                        <Typography variant="body2" color="text.secondary">
                          Domain: {tenant.custom_domain}
                        </Typography>
                      )}
                      <Typography variant="caption" color="text.secondary" display="block">
                        Created: {new Date(tenant.created_at).toLocaleDateString()}
                      </Typography>
                    </Box>
                    <Box>
                      <IconButton onClick={() => handleOpenDialog(tenant)}>
                        <EditIcon />
                      </IconButton>
                      <IconButton onClick={() => handleDelete(tenant)} color="error">
                        <DeleteIcon />
                      </IconButton>
                    </Box>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Create/Edit Tenant Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingTenant ? 'Edit Tenant' : 'Create New Tenant'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <TextField
              fullWidth
              label="Tenant Name"
              value={formData.tenant_name}
              onChange={(e) => setFormData({ ...formData, tenant_name: e.target.value })}
              required
              sx={{ mb: 2 }}
              helperText="The company or organization name"
            />

            <TextField
              fullWidth
              label="Subdomain (Optional)"
              value={formData.subdomain}
              onChange={(e) => setFormData({ ...formData, subdomain: e.target.value })}
              sx={{ mb: 2 }}
              helperText="e.g., 'companyx' for companyx.tales.com"
            />

            <Box sx={{ mb: 2 }}>
              <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                <Button
                  size="small"
                  variant={logoUploadMode === 'url' ? 'contained' : 'outlined'}
                  onClick={() => {
                    setLogoUploadMode('url');
                    setLogoFile(null);
                  }}
                >
                  URL
                </Button>
                <Button
                  size="small"
                  variant={logoUploadMode === 'file' ? 'contained' : 'outlined'}
                  onClick={() => setLogoUploadMode('file')}
                >
                  Upload File
                </Button>
              </Box>

              {logoUploadMode === 'url' ? (
                <TextField
                  fullWidth
                  label="Logo URL (Optional)"
                  value={formData.logo_url}
                  onChange={(e) => setFormData({ ...formData, logo_url: e.target.value })}
                  helperText="URL to the company logo image"
                />
              ) : (
                <Box>
                  <Button
                    variant="outlined"
                    component="label"
                    fullWidth
                    sx={{ py: 1.5 }}
                  >
                    {logoFile ? logoFile.name : 'Choose Logo File'}
                    <input
                      type="file"
                      hidden
                      accept="image/*"
                      onChange={handleFileChange}
                    />
                  </Button>
                  <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
                    Supported formats: PNG, JPG, SVG
                  </Typography>
                </Box>
              )}
            </Box>

            {formData.logo_url && (
              <Box sx={{ mb: 2, textAlign: 'center' }}>
                <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
                  Logo Preview:
                </Typography>
                <Box
                  sx={{
                    width: 160,
                    height: 80,
                    margin: '0 auto',
                    bgcolor: formData.logo_url.toLowerCase().includes('white')
                      ? (formData.primary_color || formData.secondary_color || '#000000')
                      : '#000000',
                    border: '1px solid #e0e0e0',
                    borderRadius: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: 1,
                  }}
                >
                  <img
                    src={formData.logo_url}
                    alt="Logo preview"
                    style={{
                      maxWidth: '100%',
                      maxHeight: '100%',
                      objectFit: 'contain'
                    }}
                  />
                </Box>
              </Box>
            )}

            <Typography variant="subtitle2" gutterBottom sx={{ mt: 3 }}>
              Brand Colors
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
              These colors will be used for navigation and UI elements
            </Typography>

            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <Box sx={{ flex: 1 }}>
                <TextField
                  fullWidth
                  label="Primary Color (Nav & Accent)"
                  type="color"
                  value={formData.primary_color}
                  onChange={(e) => setFormData({ ...formData, primary_color: e.target.value })}
                  InputLabelProps={{ shrink: true }}
                />
                <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
                  {formData.primary_color}
                </Typography>
              </Box>

              <Box sx={{ flex: 1 }}>
                <TextField
                  fullWidth
                  label="Secondary Color (Highlights)"
                  type="color"
                  value={formData.secondary_color}
                  onChange={(e) => setFormData({ ...formData, secondary_color: e.target.value })}
                  InputLabelProps={{ shrink: true }}
                />
                <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
                  {formData.secondary_color}
                </Typography>
              </Box>
            </Box>

            <Box sx={{ display: 'flex', gap: 1, mb: 2, justifyContent: 'center' }}>
              <Box
                sx={{
                  width: 100,
                  height: 60,
                  bgcolor: formData.primary_color,
                  border: '1px solid #ddd',
                  borderRadius: 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Typography variant="caption" sx={{ color: 'white', fontWeight: 'bold' }}>
                  Primary
                </Typography>
              </Box>
              <Box
                sx={{
                  width: 100,
                  height: 60,
                  bgcolor: formData.secondary_color,
                  border: '1px solid #ddd',
                  borderRadius: 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Typography variant="caption" sx={{ color: 'white', fontWeight: 'bold' }}>
                  Secondary
                </Typography>
              </Box>
            </Box>

            <TextField
              fullWidth
              label="Custom Domain (Optional)"
              value={formData.custom_domain}
              onChange={(e) => setFormData({ ...formData, custom_domain: e.target.value })}
              sx={{ mb: 2 }}
              helperText="e.g., 'tales.companyx.com'"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained" disabled={!formData.tenant_name}>
            {editingTenant ? 'Update Tenant' : 'Create Tenant'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default TenantManagement;
