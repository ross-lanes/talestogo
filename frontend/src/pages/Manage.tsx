import { Box, Typography, Button, Paper } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import {
  TextFields as QueryIcon,
  Label as DescriptorIcon,
  Groups as CompetitorIcon,
} from '@mui/icons-material';

export default function Manage() {
  const navigate = useNavigate();

  return (
    <Box>
      <Typography variant="h2" component="h1" gutterBottom>
        Customize
      </Typography>

      <Paper sx={{ p: 4, mb: 4 }}>
        <Typography variant="body1" paragraph>
          The first step to using AIRO successfully involves adding the questions you want to ask the AIs (queries),
          the words you want people to use when describing your brand (descriptors), and information about your competitors.
        </Typography>

        <Box sx={{ display: 'flex', gap: 3, mt: 4, flexWrap: 'wrap' }}>
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
              backgroundColor: '#75C9C8',
              '&:hover': {
                backgroundColor: '#5FB3B2',
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
