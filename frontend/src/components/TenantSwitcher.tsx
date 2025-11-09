import React, { useState } from 'react';
import {
  Box,
  Button,
  Menu,
  MenuItem,
  Typography,
  Chip,
  Divider,
} from '@mui/material';
import {
  SwapHoriz as SwapIcon,
  Check as CheckIcon,
  Business as BusinessIcon,
} from '@mui/icons-material';
import { useTenant } from '../contexts/TenantContext';

const TenantSwitcher: React.FC = () => {
  const { tenant, allTenants, isAdmin, overrideTenant } = useTenant();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  // Don't show if not admin or no tenants
  if (!isAdmin || allTenants.length === 0) {
    return null;
  }

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleSelectTenant = (tenantId: number) => {
    overrideTenant(tenantId);
    handleClose();
  };

  const currentTenantOverride = localStorage.getItem('admin_tenant_override');

  return (
    <Box sx={{ mb: 2 }}>
      <Button
        fullWidth
        variant="outlined"
        onClick={handleClick}
        startIcon={<SwapIcon />}
        sx={{
          justifyContent: 'flex-start',
          textTransform: 'none',
          borderColor: 'rgba(255, 255, 255, 0.23)',
          color: 'white',
          '&:hover': {
            borderColor: 'rgba(255, 255, 255, 0.4)',
            backgroundColor: 'rgba(255, 255, 255, 0.08)',
          },
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flex: 1 }}>
          <BusinessIcon sx={{ fontSize: 18 }} />
          <Typography variant="body2" noWrap sx={{ flex: 1, textAlign: 'left' }}>
            {tenant?.tenant_name || 'Select Tenant'}
          </Typography>
          {currentTenantOverride && (
            <Chip
              label="VIEW MODE"
              size="small"
              sx={{
                height: 20,
                fontSize: '0.65rem',
                fontWeight: 600,
                backgroundColor: 'warning.main',
                color: 'warning.contrastText',
              }}
            />
          )}
        </Box>
      </Button>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        PaperProps={{
          sx: {
            minWidth: 280,
            maxWidth: 320,
          },
        }}
      >
        <Box sx={{ px: 2, py: 1 }}>
          <Typography variant="caption" color="text.secondary" fontWeight={600}>
            ADMIN: VIEW AS TENANT
          </Typography>
        </Box>
        <Divider />

        {allTenants.map((t) => (
          <MenuItem
            key={t.id}
            onClick={() => handleSelectTenant(t.id)}
            selected={tenant?.id === t.id}
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <Box>
              <Typography variant="body2" fontWeight={tenant?.id === t.id ? 600 : 400}>
                {t.tenant_name}
              </Typography>
              {t.subdomain && (
                <Typography variant="caption" color="text.secondary">
                  {t.subdomain}
                </Typography>
              )}
            </Box>
            {tenant?.id === t.id && <CheckIcon sx={{ fontSize: 18, color: 'primary.main' }} />}
          </MenuItem>
        ))}
      </Menu>
    </Box>
  );
};

export default TenantSwitcher;
