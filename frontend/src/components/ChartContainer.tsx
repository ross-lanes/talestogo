import React, { type ReactNode } from 'react';
import { Box } from '@mui/material';
import { ResponsiveContainer } from 'recharts';

interface ChartContainerProps {
  children: ReactNode;
  width?: number | `${number}%`;
  height?: number;
  logoOpacity?: number;
  logoPosition?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
  logoSize?: number;
  showLogo?: boolean;
}

/**
 * ChartContainer - A wrapper component for all Recharts visualizations
 * that adds consistent RobotRachel branding to charts.
 *
 * Features:
 * - Wraps ResponsiveContainer from Recharts
 * - Adds RobotRachel logo overlay in configurable position
 * - Logo appears in chart screenshots/downloads (html2canvas)
 * - Fully responsive and customizable
 *
 * @param children - Recharts components (BarChart, LineChart, PieChart, etc.)
 * @param width - Chart width (default: "100%")
 * @param height - Chart height (default: 400)
 * @param logoOpacity - Logo opacity 0-1 (default: 0.4)
 * @param logoPosition - Logo corner placement (default: "bottom-right")
 * @param logoSize - Logo width in pixels (default: 50)
 * @param showLogo - Whether to display logo (default: true)
 */
export const ChartContainer: React.FC<ChartContainerProps> = ({
  children,
  width = '100%',
  height = 400,
  logoOpacity = 0.4,
  logoPosition = 'bottom-right',
  logoSize = 50,
  showLogo = true,
}) => {
  // Calculate logo positioning based on logoPosition prop
  const getLogoPosition = () => {
    const offset = 8; // 8px padding from edges

    switch (logoPosition) {
      case 'bottom-right':
        return { bottom: offset, right: offset };
      case 'bottom-left':
        return { bottom: offset, left: offset };
      case 'top-right':
        return { top: offset, right: offset };
      case 'top-left':
        return { top: offset, left: offset };
      default:
        return { bottom: offset, right: offset };
    }
  };

  return (
    <Box sx={{ position: 'relative', width: '100%' }}>
      <ResponsiveContainer width={width} height={height}>
        {children}
      </ResponsiveContainer>

      {showLogo && (
        <Box
          component="img"
          src="/logos/robotrachel-logo.png"
          alt="RobotRachel"
          sx={{
            position: 'absolute',
            width: `${logoSize}px`,
            height: 'auto',
            opacity: logoOpacity,
            pointerEvents: 'none', // Don't interfere with chart interactions
            zIndex: 1,
            ...getLogoPosition(),
          }}
        />
      )}
    </Box>
  );
};

export default ChartContainer;
