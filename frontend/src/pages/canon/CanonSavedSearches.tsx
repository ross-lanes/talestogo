import React from 'react';
import { Container, Typography, Box, Paper } from '@mui/material';
import { Bookmark as BookmarkIcon } from '@mui/icons-material';

const CanonSavedSearches: React.FC = () => {
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <BookmarkIcon sx={{ mr: 2, fontSize: 32, color: 'primary.main' }} />
        <Typography variant="h4" component="h1">
          Saved Searches
        </Typography>
      </Box>
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="body1" color="text.secondary">
          Saved searches list coming soon...
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          View and manage your saved FDA data searches.
        </Typography>
      </Paper>
    </Container>
  );
};

export default CanonSavedSearches;
