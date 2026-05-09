import { Box, CircularProgress, Typography } from '@mui/material';

interface BrandedLoaderProps {
  message?: string;
}

/**
 * A simple loading component used during initial page load while waiting
 * for user/brand context to be established. Tenants with custom branding
 * can override this via the TenantThemeProvider.
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
      <CircularProgress size={48} sx={{ color: '#003e60' }} />
      <Typography variant="body2" color="text.secondary">
        {message}
      </Typography>
    </Box>
  );
}
