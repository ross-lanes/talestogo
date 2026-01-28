import { Box, Typography, Button, Paper } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import {
  TextFields as QueryIcon,
  Label as DescriptorIcon,
  Groups as CompetitorIcon,
  Business as BrandIcon,
} from '@mui/icons-material';

export default function Manage() {
  const navigate = useNavigate();

  return (
    <Box>
      <Typography variant="h2" component="h1" gutterBottom>
        Customize
      </Typography>

      <Paper sx={{ p: 4, mb: 4 }}>
        <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
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
              backgroundColor: '#003e60',
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
              backgroundColor: '#9FA8DA',
              color: '#ffffff',
              '&:hover': {
                backgroundColor: '#8A3370',
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
