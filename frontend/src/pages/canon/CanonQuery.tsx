import React from 'react';
import { Container, Typography, Box, Paper } from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';

const CanonQuery: React.FC = () => {
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <SearchIcon sx={{ mr: 2, fontSize: 32, color: 'primary.main' }} />
        <Typography variant="h4" component="h1">
          Ask a Question
        </Typography>
      </Box>
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="body1" color="text.secondary">
          Natural language query interface coming soon...
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          This feature will allow you to ask questions about FDA drug data in plain English.
        </Typography>
      </Paper>
    </Container>
  );
};

export default CanonQuery;
