/**
 * ResponsiveTable component for mobile-friendly tables
 * Provides horizontal scroll on mobile and optional card view
 */

import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Card,
  CardContent,
  Typography,
  Box,
  SxProps,
  Theme,
} from '@mui/material';
import { ReactNode } from 'react';
import { useIsMobile } from '../utils/responsive';

export interface Column {
  id: string;
  label: string;
  minWidth?: number;
  align?: 'left' | 'right' | 'center';
  format?: (value: any) => ReactNode;
  hideOnMobile?: boolean; // Hide this column on mobile
}

export interface ResponsiveTableProps {
  columns: Column[];
  rows: any[];
  /**
   * Use card view on mobile instead of horizontal scroll table
   * Default: false
   */
  useCardView?: boolean;
  /**
   * Custom card renderer for card view mode
   * If not provided, will use default card layout
   */
  renderCard?: (row: any, index: number) => ReactNode;
  /**
   * Additional sx props for the container
   */
  sx?: SxProps<Theme>;
  /**
   * Make first column sticky on horizontal scroll
   */
  stickyFirstColumn?: boolean;
  /**
   * Row click handler
   */
  onRowClick?: (row: any) => void;
}

/**
 * ResponsiveTable - Mobile-friendly table component
 *
 * Features:
 * - Horizontal scroll on mobile by default
 * - Optional card view for very small screens
 * - Sticky first column option
 * - Hide specific columns on mobile
 * - Touch-friendly row heights
 */
export default function ResponsiveTable({
  columns,
  rows,
  useCardView = false,
  renderCard,
  sx,
  stickyFirstColumn = false,
  onRowClick,
}: ResponsiveTableProps) {
  const isMobile = useIsMobile();

  // Filter columns for mobile (hide columns marked hideOnMobile)
  const visibleColumns = isMobile
    ? columns.filter(col => !col.hideOnMobile)
    : columns;

  // Card view for mobile
  if (isMobile && useCardView) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, ...sx }}>
        {rows.map((row, index) => (
          <Card
            key={index}
            onClick={() => onRowClick?.(row)}
            sx={{
              cursor: onRowClick ? 'pointer' : 'default',
              '&:hover': onRowClick ? {
                boxShadow: (theme) => theme.shadows[4],
              } : {},
            }}
          >
            <CardContent>
              {renderCard ? (
                renderCard(row, index)
              ) : (
                // Default card layout
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                  {visibleColumns.map((column) => (
                    <Box key={column.id}>
                      <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700 }}>
                        {column.label}
                      </Typography>
                      <Typography variant="body2">
                        {column.format
                          ? column.format(row[column.id])
                          : row[column.id] || '-'}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        ))}
        {rows.length === 0 && (
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary" align="center">
                No data available
              </Typography>
            </CardContent>
          </Card>
        )}
      </Box>
    );
  }

  // Table view (with horizontal scroll on mobile)
  return (
    <TableContainer
      component={Paper}
      sx={{
        maxWidth: '100%',
        overflowX: 'auto',
        // Ensure smooth scrolling on touch devices
        WebkitOverflowScrolling: 'touch',
        ...sx,
      }}
    >
      <Table
        stickyHeader
        sx={{
          minWidth: isMobile ? 'auto' : 650,
        }}
      >
        <TableHead>
          <TableRow>
            {visibleColumns.map((column, index) => (
              <TableCell
                key={column.id}
                align={column.align || 'left'}
                sx={{
                  minWidth: column.minWidth,
                  fontWeight: 700,
                  ...(stickyFirstColumn && index === 0 && {
                    position: 'sticky',
                    left: 0,
                    backgroundColor: 'background.paper',
                    zIndex: 1,
                    boxShadow: '2px 0 4px rgba(0,0,0,0.1)',
                  }),
                  // Touch-friendly padding on mobile
                  py: isMobile ? 1.5 : 2,
                  px: isMobile ? 1 : 2,
                }}
              >
                {column.label}
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.map((row, rowIndex) => (
            <TableRow
              key={rowIndex}
              hover={!!onRowClick}
              onClick={() => onRowClick?.(row)}
              sx={{
                cursor: onRowClick ? 'pointer' : 'default',
                // Touch-friendly row height
                '& > *': {
                  py: isMobile ? 1.5 : 2,
                  px: isMobile ? 1 : 2,
                },
              }}
            >
              {visibleColumns.map((column, colIndex) => (
                <TableCell
                  key={column.id}
                  align={column.align || 'left'}
                  sx={{
                    ...(stickyFirstColumn && colIndex === 0 && {
                      position: 'sticky',
                      left: 0,
                      backgroundColor: 'background.paper',
                      zIndex: 1,
                      boxShadow: '2px 0 4px rgba(0,0,0,0.1)',
                    }),
                  }}
                >
                  {column.format
                    ? column.format(row[column.id])
                    : row[column.id] !== null && row[column.id] !== undefined
                    ? row[column.id]
                    : '-'}
                </TableCell>
              ))}
            </TableRow>
          ))}
          {rows.length === 0 && (
            <TableRow>
              <TableCell colSpan={visibleColumns.length} align="center">
                <Typography variant="body2" color="text.secondary" sx={{ py: 3 }}>
                  No data available
                </Typography>
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
