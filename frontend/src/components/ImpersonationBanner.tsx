import React from 'react';
import { Alert, Button, Box } from '@mui/material';
import { ExitToApp as ExitIcon } from '@mui/icons-material';
import { useImpersonation } from '../contexts/ImpersonationContext';

export const ImpersonationBanner: React.FC = () => {
  const { impersonatedUser, isImpersonating, exitImpersonation } = useImpersonation();

  if (!isImpersonating || !impersonatedUser) {
    return null;
  }

  return (
    <Alert
      severity="warning"
      sx={{
        borderRadius: 0,
        position: 'sticky',
        top: 0,
        zIndex: 1200,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}
      action={
        <Button
          color="inherit"
          size="small"
          startIcon={<ExitIcon />}
          onClick={exitImpersonation}
        >
          Exit View
        </Button>
      }
    >
      <Box>
        <strong>Viewing as User:</strong> {impersonatedUser.full_name || impersonatedUser.email} ({impersonatedUser.email})
      </Box>
    </Alert>
  );
};
