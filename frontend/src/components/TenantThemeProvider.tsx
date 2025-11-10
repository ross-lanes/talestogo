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
    // If tenant exists (either from cache or API), use it immediately
    // This prevents the flash of default theme on page load
    if (tenant) {
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
    }

    // Only fall back to baseTheme if loading and no cached tenant
    return baseTheme;
  }, [tenant, loading]);

  return <ThemeProvider theme={tenantTheme}>{children}</ThemeProvider>;
};
