import React from 'react';
import {
  Box,
  Container,
  Typography,
  Grid2 as Grid,
  Card,
  CardContent,
  CardActionArea,
  TextField,
  InputAdornment,
} from '@mui/material';
import {
  Search as SearchIcon,
  Warning as WarningIcon,
  Description as DescriptionIcon,
  CompareArrows as CompareIcon,
  Bookmark as BookmarkIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const CanonDashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const quickActions = [
    {
      title: 'Ask a Question',
      description: 'Search FDA data using natural language',
      icon: <SearchIcon sx={{ fontSize: 48, color: 'primary.main' }} />,
      path: '/canon/query',
      color: 'primary.light',
    },
    {
      title: 'Adverse Events',
      description: 'Search reported side effects and reactions',
      icon: <WarningIcon sx={{ fontSize: 48, color: 'warning.main' }} />,
      path: '/canon/adverse-events',
      color: 'warning.light',
    },
    {
      title: 'Compare Drugs',
      description: 'Side-by-side drug label comparison',
      icon: <CompareIcon sx={{ fontSize: 48, color: 'info.main' }} />,
      path: '/canon/compare',
      color: 'info.light',
    },
    {
      title: 'Check Document',
      description: 'Verify claims against FDA labels',
      icon: <DescriptionIcon sx={{ fontSize: 48, color: 'success.main' }} />,
      path: '/canon/documents',
      color: 'success.light',
    },
  ];

  const exampleQueries = [
    'What are the most common side effects of Lipitor?',
    'Compare warnings for Humira vs Enbrel',
    'Has metformin been recalled recently?',
    'What does the FDA label say about pediatric use of Adderall?',
  ];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Welcome Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Welcome{user?.full_name ? `, ${user.full_name}` : ''}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Research FDA drug data, compare products, and verify manuscript content.
        </Typography>
      </Box>

      {/* Main Search Bar */}
      <Card sx={{ mb: 4, bgcolor: 'primary.main', color: 'white' }}>
        <CardContent sx={{ p: 4 }}>
          <Typography variant="h6" gutterBottom sx={{ color: 'white' }}>
            Ask anything about FDA drug data...
          </Typography>
          <TextField
            fullWidth
            placeholder="e.g., What adverse events have been reported for Ozempic?"
            variant="outlined"
            onClick={() => navigate('/canon/query')}
            InputProps={{
              readOnly: true,
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon sx={{ color: 'text.secondary' }} />
                </InputAdornment>
              ),
              sx: {
                bgcolor: 'white',
                '&:hover': {
                  cursor: 'pointer',
                },
              },
            }}
          />
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
        Quick Actions
      </Typography>
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {quickActions.map((action) => (
          <Grid size={{ xs: 12, sm: 6, md: 3 }} key={action.title}>
            <Card
              sx={{
                height: '100%',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                },
              }}
            >
              <CardActionArea
                onClick={() => navigate(action.path)}
                sx={{ height: '100%', p: 2 }}
              >
                <CardContent sx={{ textAlign: 'center' }}>
                  <Box sx={{ mb: 2 }}>{action.icon}</Box>
                  <Typography variant="h6" gutterBottom>
                    {action.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {action.description}
                  </Typography>
                </CardContent>
              </CardActionArea>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Example Queries */}
      <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
        Example Queries
      </Typography>
      <Grid container spacing={2} sx={{ mb: 4 }}>
        {exampleQueries.map((query, index) => (
          <Grid size={{ xs: 12, sm: 6 }} key={index}>
            <Card
              sx={{
                cursor: 'pointer',
                transition: 'background-color 0.2s',
                '&:hover': {
                  bgcolor: 'action.hover',
                },
              }}
              onClick={() => navigate(`/canon/query?q=${encodeURIComponent(query)}`)}
            >
              <CardContent sx={{ display: 'flex', alignItems: 'center' }}>
                <SearchIcon sx={{ mr: 2, color: 'text.secondary' }} />
                <Typography variant="body1">"{query}"</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Saved Searches Placeholder */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <BookmarkIcon sx={{ mr: 1, color: 'primary.main' }} />
        <Typography variant="h5">Saved Searches</Typography>
      </Box>
      <Card sx={{ bgcolor: 'grey.50' }}>
        <CardContent sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="body1" color="text.secondary">
            Your saved searches will appear here.
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Save searches to quickly access them later.
          </Typography>
        </CardContent>
      </Card>
    </Container>
  );
};

export default CanonDashboard;
