import React, { type ReactNode } from 'react';
import { Box } from '@mui/material';
import { ResponsiveContainer } from 'recharts';

interface ChartContainerProps {
  children: ReactNode;
  width?: number | `${number}%`;
  height?: number;
}

/**
 * ChartContainer - A wrapper around Recharts' ResponsiveContainer for
 * consistent chart sizing across the app.
 *
 * @param children - Recharts components (BarChart, LineChart, PieChart, etc.)
 * @param width - Chart width (default: "100%")
 * @param height - Chart height (default: 400)
 */
export const ChartContainer: React.FC<ChartContainerProps> = ({
  children,
  width = '100%',
  height = 400,
}) => {
  return (
    <Box sx={{ position: 'relative', width: '100%' }}>
      <ResponsiveContainer width={width} height={height}>
        {children}
      </ResponsiveContainer>
    </Box>
  );
};

export default ChartContainer;
