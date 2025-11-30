import React from 'react';
import { Container, Typography, Box, Paper } from '@mui/material';
import { CompareArrows as CompareIcon } from '@mui/icons-material';

const CanonCompare: React.FC = () => {
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <CompareIcon sx={{ mr: 2, fontSize: 32, color: 'info.main' }} />
        <Typography variant="h4" component="h1">
          Compare Drugs
        </Typography>
      </Box>
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="body1" color="text.secondary">
          Drug comparison interface coming soon...
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          Compare FDA-approved labeling for multiple drugs side-by-side.
        </Typography>
      </Paper>
    </Container>
  );
};

export default CanonCompare;
