import React from 'react';
import { Container, Typography, Box, Paper } from '@mui/material';
import { Description as DescriptionIcon } from '@mui/icons-material';

const CanonDocuments: React.FC = () => {
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <DescriptionIcon sx={{ mr: 2, fontSize: 32, color: 'success.main' }} />
        <Typography variant="h4" component="h1">
          Check Document
        </Typography>
      </Box>
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="body1" color="text.secondary">
          Document verification interface coming soon...
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          Upload Word documents to verify claims against FDA-approved labeling.
        </Typography>
      </Paper>
    </Container>
  );
};

export default CanonDocuments;
