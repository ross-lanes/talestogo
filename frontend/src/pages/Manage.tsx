import { Box, Typography, Button, Paper, Alert } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import {
  TextFields as QueryIcon,
  Label as DescriptorIcon,
  Groups as CompetitorIcon,
  Business as BrandIcon,
} from '@mui/icons-material';

export default function Manage() {
  const navigate = useNavigate();

  // Check if brand info exists
  const { data: brandInfo } = useQuery({
    queryKey: ['brand-info'],
    queryFn: async () => {
      const response = await api.get('/brand-info/');
      return response.data;
    },
    retry: false,
  });

  const showFirstTimeMessage = !brandInfo;

  return (
    <Box>
      <Typography variant="h2" component="h1" gutterBottom>
        Customize
      </Typography>

      {showFirstTimeMessage && (
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="body1" fontWeight={600} gutterBottom>
            Step 1: Start with Brand Info
          </Typography>
          <Typography variant="body2">
            Click the <strong>Brand Info</strong> button below to enter your brand information. This is the foundation for everything else in TALES!
          </Typography>
        </Alert>
      )}

      <Paper sx={{ p: 4, mb: 4 }}>
        <Typography variant="body1" paragraph>
          The first step to using TALES successfully involves configuring your brand information, adding the questions you want to ask the AIs (queries),
          the words you want people to use when describing your brand (descriptors), and information about your competitors.
        </Typography>

        <Box sx={{ display: 'flex', gap: 3, mt: 4, flexWrap: 'wrap' }}>
          <Button
            variant="contained"
            size="large"
            startIcon={<BrandIcon />}
            onClick={() => navigate('/manage/brand-info')}
            sx={{
              backgroundColor: '#75C9C8',
              '&:hover': {
                backgroundColor: '#5FB3B2',
              },
              minWidth: 180,
              fontWeight: 'bold',
            }}
          >
            Brand Info
          </Button>

          <Button
            variant="contained"
            size="large"
            startIcon={<QueryIcon />}
            onClick={() => navigate('/manage/queries')}
            sx={{
              backgroundColor: '#665775',
              '&:hover': {
                backgroundColor: '#554863',
              },
              minWidth: 180,
            }}
          >
            Queries
          </Button>

          <Button
            variant="contained"
            size="large"
            startIcon={<DescriptorIcon />}
            onClick={() => navigate('/manage/descriptors')}
            sx={{
              backgroundColor: '#80A1D4',
              '&:hover': {
                backgroundColor: '#6B8BC0',
              },
              minWidth: 180,
            }}
          >
            Descriptors
          </Button>

          <Button
            variant="contained"
            size="large"
            startIcon={<CompetitorIcon />}
            onClick={() => navigate('/manage/competitors')}
            sx={{
              backgroundColor: '#DED9E2',
              color: '#665775',
              '&:hover': {
                backgroundColor: '#CFC9D7',
              },
              minWidth: 180,
            }}
          >
            Competitors
          </Button>
        </Box>
      </Paper>
    </Box>
  );
}
