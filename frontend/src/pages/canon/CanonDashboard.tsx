import React from 'react';
import {
  Box,
  Container,
  Typography,
  Grid2 as Grid,
  Card,
  CardContent,
  TextField,
  InputAdornment,
} from '@mui/material';
import {
  Search as SearchIcon,
  Bookmark as BookmarkIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const CanonDashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const exampleQueries = [
    'What are the most common side effects of Galafold?',
    'Compare warnings for Posluma vs Illuccix',
    'Has Salonpas been recalled recently?',
    'What does the FDA label say about Ozempic?',
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
            Ask anything about FDA drug data
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
