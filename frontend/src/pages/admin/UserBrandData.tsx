import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Paper,
  Typography,
  Button,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
  Breadcrumbs,
  Link,
  Card,
  CardContent,
  Grid,
} from '@mui/material';
import { ArrowBack as ArrowBackIcon } from '@mui/icons-material';
import { adminAPI } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import AdminQueriesTab from '../../components/admin/AdminQueriesTab';
import AdminDescriptorsTab from '../../components/admin/AdminDescriptorsTab';
import AdminCompetitorsTab from '../../components/admin/AdminCompetitorsTab';
import AdminBrandInfoTab from '../../components/admin/AdminBrandInfoTab';

interface User {
  id: number;
  email: string;
  full_name?: string;
  organization?: string;
}

interface Brand {
  id: number;
  user_id: number;
  brand_name: string;
  website_url?: string;
  industry?: string;
  description?: string;
  strategic_messages?: string;
  is_active: boolean;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`admin-tabpanel-${index}`}
      aria-labelledby={`admin-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

const UserBrandData: React.FC = () => {
  const { userId: userIdParam, brandId: brandIdParam } = useParams<{ userId: string; brandId: string }>();
  const userId = parseInt(userIdParam || '0');
  const brandId = parseInt(brandIdParam || '0');
  const navigate = useNavigate();
  const { isAdmin } = useAuth();

  const [user, setUser] = useState<User | null>(null);
  const [brand, setBrand] = useState<Brand | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentTab, setCurrentTab] = useState(0);

  useEffect(() => {
    if (isAdmin && userId && brandId) {
      loadData();
    }
  }, [isAdmin, userId, brandId]);

  const loadData = async () => {
    setLoading(true);
    setError('');

    try {
      const [userData, brandData] = await Promise.all([
        adminAPI.getUser(userId),
        adminAPI.getBrand(brandId),
      ]);

      setUser(userData);
      setBrand(brandData);
    } catch (err: any) {
      console.error('Failed to load data:', err);
      setError('Failed to load user or brand data');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  if (!isAdmin) {
    return (
      <Container maxWidth={false} sx={{ py: 4, px: 3 }}>
        <Alert severity="error">You do not have permission to access this page.</Alert>
      </Container>
    );
  }

  if (loading) {
    return (
      <Container maxWidth={false} sx={{ py: 4, px: 3, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error || !user || !brand) {
    return (
      <Container maxWidth={false} sx={{ py: 4, px: 3 }}>
        <Alert severity="error">{error || 'User or brand not found'}</Alert>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/settings/users')}
          sx={{ mt: 2 }}
        >
          Back to Users
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth={false} sx={{ py: 4, px: 3 }}>
      {/* Header with breadcrumbs */}
      <Box sx={{ mb: 3 }}>
        <Breadcrumbs sx={{ mb: 2 }}>
          <Link
            component="button"
            variant="body1"
            onClick={() => navigate('/settings/users')}
            sx={{ cursor: 'pointer', textDecoration: 'none' }}
          >
            Admin
          </Link>
          <Link
            component="button"
            variant="body1"
            onClick={() => navigate('/settings/users')}
            sx={{ cursor: 'pointer', textDecoration: 'none' }}
          >
            Users
          </Link>
          <Typography color="text.primary">{user.email}</Typography>
          <Typography color="text.primary">{brand.brand_name}</Typography>
        </Breadcrumbs>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography variant="h4" gutterBottom>
              Manage User Brand Data
            </Typography>
            <Typography variant="subtitle1" color="text.secondary">
              User: {user.full_name || user.email}
            </Typography>
            <Typography variant="subtitle1" color="text.secondary">
              Brand: {brand.brand_name}
            </Typography>
          </Box>

          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/settings/users')}
          >
            Back to Users
          </Button>
        </Box>
      </Box>

      {/* Brand Info Summary Card */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" color="text.secondary">
                Website
              </Typography>
              <Typography variant="body1">
                {brand.website_url || 'N/A'}
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" color="text.secondary">
                Industry
              </Typography>
              <Typography variant="body1">
                {brand.industry || 'N/A'}
              </Typography>
            </Grid>
            <Grid item xs={12}>
              <Typography variant="body2" color="text.secondary">
                Description
              </Typography>
              <Typography variant="body1">
                {brand.description || 'N/A'}
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Tabs for different data types */}
      <Paper elevation={2}>
        <Tabs
          value={currentTab}
          onChange={handleTabChange}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="Brand Info" />
          <Tab label="Queries" />
          <Tab label="Descriptors" />
          <Tab label="Competitors" />
        </Tabs>

        <TabPanel value={currentTab} index={0}>
          <AdminBrandInfoTab userId={userId} brandId={brandId} brand={brand} onUpdate={loadData} />
        </TabPanel>

        <TabPanel value={currentTab} index={1}>
          <AdminQueriesTab userId={userId} brandId={brandId} />
        </TabPanel>

        <TabPanel value={currentTab} index={2}>
          <AdminDescriptorsTab userId={userId} brandId={brandId} />
        </TabPanel>

        <TabPanel value={currentTab} index={3}>
          <AdminCompetitorsTab userId={userId} brandId={brandId} />
        </TabPanel>
      </Paper>
    </Container>
  );
};

export default UserBrandData;
