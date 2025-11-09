import React, { useMemo } from 'react';
import type { ReactNode } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { useTenant } from '../contexts/TenantContext';
import { theme as baseTheme } from '../theme/theme';

interface TenantThemeProviderProps {
  children: ReactNode;
}

export const TenantThemeProvider: React.FC<TenantThemeProviderProps> = ({ children }) => {
  const { tenant, loading } = useTenant();

  const tenantTheme = useMemo(() => {
    if (loading || !tenant) {
      return baseTheme;
    }

    // Create a new theme based on tenant colors
    return createTheme({
      ...baseTheme,
      palette: {
        ...baseTheme.palette,
        primary: {
          main: tenant.primary_color || '#75C9C8',
          contrastText: '#fff',
        },
        secondary: {
          main: tenant.secondary_color || '#665775',
          contrastText: '#fff',
        },
      },
    });
  }, [tenant, loading]);

  return <ThemeProvider theme={tenantTheme}>{children}</ThemeProvider>;
};
