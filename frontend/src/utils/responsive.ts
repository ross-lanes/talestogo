/**
 * Responsive utility helpers for mobile-friendly design
 * Uses Material-UI breakpoint system
 */

import { useTheme, useMediaQuery } from '@mui/material';
import type { Theme } from '@mui/material';
import type { Breakpoint } from '@mui/system';

/**
 * Hook to check if current viewport is mobile (below sm breakpoint)
 * @returns true if mobile (< 600px)
 */
export const useIsMobile = (): boolean => {
  const theme = useTheme();
  return useMediaQuery(theme.breakpoints.down('sm'));
};

/**
 * Hook to check if current viewport is tablet (sm to md breakpoint)
 * @returns true if tablet (600px - 900px)
 */
export const useIsTablet = (): boolean => {
  const theme = useTheme();
  return useMediaQuery(theme.breakpoints.between('sm', 'md'));
};

/**
 * Hook to check if current viewport is desktop (above md breakpoint)
 * @returns true if desktop (> 900px)
 */
export const useIsDesktop = (): boolean => {
  const theme = useTheme();
  return useMediaQuery(theme.breakpoints.up('md'));
};

/**
 * Hook to check if current viewport is at least a certain breakpoint
 * @param breakpoint - The minimum breakpoint (xs, sm, md, lg, xl)
 * @returns true if viewport is >= breakpoint
 */
export const useBreakpoint = (breakpoint: Breakpoint): boolean => {
  const theme = useTheme();
  return useMediaQuery(theme.breakpoints.up(breakpoint));
};

/**
 * Get responsive value based on current viewport
 * @param mobile - Value for mobile (xs)
 * @param tablet - Value for tablet (sm)
 * @param desktop - Value for desktop (md+)
 * @returns The appropriate value for current viewport
 */
export const useResponsiveValue = <T,>(
  mobile: T,
  tablet?: T,
  desktop?: T
): T => {
  const isMobile = useIsMobile();
  const isTablet = useIsTablet();

  if (isMobile) return mobile;
  if (isTablet && tablet !== undefined) return tablet;
  return desktop !== undefined ? desktop : (tablet || mobile);
};

/**
 * Responsive spacing helper
 * Converts desktop spacing to mobile-friendly spacing
 * @param desktopSpacing - Desktop spacing value
 * @param mobileRatio - Ratio to apply for mobile (default: 0.66)
 * @returns Object with responsive spacing for sx prop
 */
export const responsiveSpacing = (
  desktopSpacing: number,
  mobileRatio: number = 0.66
) => ({
  xs: Math.max(1, Math.round(desktopSpacing * mobileRatio)),
  sm: desktopSpacing,
});

/**
 * Get responsive chart height
 * @param desktopHeight - Desktop chart height in pixels
 * @returns Responsive height object for sx prop
 */
export const responsiveChartHeight = (desktopHeight: number) => ({
  xs: Math.max(200, Math.round(desktopHeight * 0.75)),
  sm: Math.max(250, Math.round(desktopHeight * 0.85)),
  md: desktopHeight,
});

/**
 * Touch-friendly minimum sizes
 */
export const TOUCH_TARGET = {
  minHeight: 44, // Apple HIG guideline
  minWidth: 44,
};

/**
 * Responsive grid column configurations
 * Use these for Material-UI Grid items
 */
export const GRID_COLUMNS = {
  full: { xs: 12 },
  half: { xs: 12, sm: 6 },
  third: { xs: 12, sm: 6, md: 4 },
  quarter: { xs: 12, sm: 6, md: 3 },
  twoThirds: { xs: 12, sm: 12, md: 8 },
  threeQuarters: { xs: 12, sm: 12, md: 9 },
};

/**
 * Standard responsive padding values
 */
export const RESPONSIVE_PADDING = {
  page: { xs: 2, sm: 3 },
  card: { xs: 2, sm: 2.5, md: 3 },
  compact: { xs: 1, sm: 1.5, md: 2 },
};

/**
 * Responsive font sizes (Material-UI theme values)
 */
export const RESPONSIVE_FONT_SIZE = {
  h1: { xs: '1.75rem', sm: '2rem', md: '2.5rem' },
  h2: { xs: '1.5rem', sm: '1.75rem', md: '2rem' },
  h3: { xs: '1.25rem', sm: '1.5rem', md: '1.75rem' },
  h4: { xs: '1.125rem', sm: '1.25rem', md: '1.5rem' },
  h5: { xs: '1rem', sm: '1.125rem', md: '1.25rem' },
  h6: { xs: '0.875rem', sm: '0.9375rem', md: '1rem' },
};

/**
 * Breakpoint values in pixels (for reference)
 */
export const BREAKPOINTS = {
  xs: 0,
  sm: 600,
  md: 900,
  lg: 1200,
  xl: 1536,
};
