/**
 * ResponsiveContainer component for wrapping charts and content
 * Provides consistent responsive behavior across the app
 */

import { Box, SxProps, Theme } from '@mui/material';
import { ReactNode } from 'react';

interface ResponsiveContainerProps {
  children: ReactNode;
  /**
   * Height for different breakpoints
   * Can be number (pixels) or responsive object
   */
  height?: number | { xs?: number; sm?: number; md?: number; lg?: number };
  /**
   * Width for different breakpoints (default: 100%)
   */
  width?: string | number | { xs?: string | number; sm?: string | number; md?: string | number };
  /**
   * Additional sx props
   */
  sx?: SxProps<Theme>;
  /**
   * Prevent horizontal overflow
   */
  preventOverflow?: boolean;
}

/**
 * ResponsiveContainer - Wraps content with responsive sizing
 * Especially useful for charts, tables, and other content that needs
 * to adapt to different screen sizes
 */
export default function ResponsiveContainer({
  children,
  height,
  width = '100%',
  sx,
  preventOverflow = true,
}: ResponsiveContainerProps) {
  // Convert simple height number to responsive object
  const responsiveHeight = typeof height === 'number'
    ? {
        xs: Math.max(200, Math.round(height * 0.75)),
        sm: Math.max(250, Math.round(height * 0.85)),
        md: height,
      }
    : height;

  return (
    <Box
      sx={{
        width,
        height: responsiveHeight,
        ...(preventOverflow && {
          maxWidth: '100%',
          overflowX: 'auto',
          overflowY: 'hidden',
        }),
        ...sx,
      }}
    >
      {children}
    </Box>
  );
}
