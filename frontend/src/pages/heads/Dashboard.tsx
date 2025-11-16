import { useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Box,
  Alert,
} from '@mui/material';
import {
  Business as BusinessIcon,
  Create as CreateIcon,
  History as HistoryIcon,
} from '@mui/icons-material';
import { useBrand } from '../../contexts/BrandContext';
import { useAuth } from '../../contexts/AuthContext';

export default function Dashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { brands, activeBrand } = useBrand();

  const dashboardCards = [
    {
      title: 'Manage Brands',
      description: 'Create and manage pharmaceutical brands',
      icon: <BusinessIcon sx={{ fontSize: 48, color: 'primary.main' }} />,
      action: () => navigate('/manage/brand-info'),
      buttonText: 'Go to Brands',
    },
    {
      title: 'Generate Personas',
      description: 'Create patient and HCP personas for your active brand',
      icon: <CreateIcon sx={{ fontSize: 48, color: 'secondary.main' }} />,
      action: () => navigate('/heads/generate'),
      buttonText: 'Generate Now',
      disabled: !activeBrand,
    },
    {
      title: 'View Generations',
      description: 'Browse and download previously generated personas',
      icon: <HistoryIcon sx={{ fontSize: 48, color: 'success.main' }} />,
      action: () => navigate('/heads/generations'),
      buttonText: 'View History',
    },
  ];

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Welcome to Heads, {user?.full_name || user?.email}
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Generate professional healthcare personas for pharmaceutical brands
        </Typography>
      </Box>

      {!activeBrand && brands.length > 0 && (
        <Alert severity="info" sx={{ mb: 3 }}>
          Please select an active brand to generate personas.
        </Alert>
      )}

      {brands.length === 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          You don't have any brands yet. Create a brand to get started!
        </Alert>
      )}

      {activeBrand && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Active Brand: <strong>{activeBrand.brand_name}</strong>
        </Alert>
      )}

      <Grid container spacing={3}>
        {dashboardCards.map((card, index) => (
          <Grid item xs={12} md={4} key={index}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flexGrow: 1, textAlign: 'center' }}>
                <Box sx={{ mb: 2 }}>{card.icon}</Box>
                <Typography variant="h5" component="h2" gutterBottom>
                  {card.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {card.description}
                </Typography>
              </CardContent>
              <CardActions sx={{ justifyContent: 'center', pb: 2 }}>
                <Button
                  variant="contained"
                  onClick={card.action}
                  disabled={card.disabled}
                >
                  {card.buttonText}
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Box sx={{ mt: 4 }}>
        <Typography variant="h6" gutterBottom>
          Quick Stats
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={4}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Total Brands
                </Typography>
                <Typography variant="h4">{brands.length}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Active Brand
                </Typography>
                <Typography variant="h6">
                  {activeBrand?.brand_name || 'None'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Account Status
                </Typography>
                <Typography variant="h6">
                  {user?.is_active ? 'Active' : 'Pending'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    </Container>
  );
}
