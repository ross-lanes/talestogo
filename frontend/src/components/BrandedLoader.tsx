import { Box, LinearProgress, Typography } from '@mui/material';

interface BrandedLoaderProps {
  message?: string;
}

/**
 * A branded loading component that displays the RobotRachel logo
 * with a progress bar underneath. Used during initial page load
 * while waiting for user/brand context to be established.
 */
export default function BrandedLoader({ message = 'Loading...' }: BrandedLoaderProps) {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh',
        gap: 3,
      }}
    >
      <Box
        component="img"
        src="/logos/RobotRachelBB-Black-on-Transparent.png"
        alt="Loading"
        sx={{
          width: 120,
          height: 'auto',
          opacity: 0.9,
        }}
      />
      <Box sx={{ width: 200 }}>
        <LinearProgress
          sx={{
            height: 6,
            borderRadius: 3,
            '& .MuiLinearProgress-bar': {
              backgroundColor: '#003e60',
            },
            backgroundColor: '#e0e0e0',
          }}
        />
      </Box>
      <Typography variant="body2" color="text.secondary">
        {message}
      </Typography>
    </Box>
  );
}
