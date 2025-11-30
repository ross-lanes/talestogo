import React from 'react';
import { Container, Typography, Box, Paper } from '@mui/material';
import { Warning as WarningIcon } from '@mui/icons-material';

const CanonAdverseEvents: React.FC = () => {
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <WarningIcon sx={{ mr: 2, fontSize: 32, color: 'warning.main' }} />
        <Typography variant="h4" component="h1">
          Adverse Events
        </Typography>
      </Box>
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="body1" color="text.secondary">
          Adverse events search interface coming soon...
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          Search the FDA Adverse Event Reporting System (FAERS) database.
        </Typography>
      </Paper>
    </Container>
  );
};

export default CanonAdverseEvents;
