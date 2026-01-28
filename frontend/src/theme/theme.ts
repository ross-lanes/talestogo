import { createTheme } from '@mui/material/styles';

// Custom Brand Colors
// Palette: #003e60, #80a1d4, #75c9c8 (removed #c0b9dd and #ded9e2 - too light for charts)
export const theme = createTheme({
  palette: {
    primary: {
      main: '#003e60', // Deep purple - primary base color
      light: '#8876a3',
      dark: '#4a3d52',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#80a1d4', // Soft blue - accent color
      light: '#a3b9e0',
      dark: '#5a7599',
      contrastText: '#ffffff',
    },
    error: {
      main: '#c12d63',
      light: '#d65083',
      dark: '#8d1e47',
    },
    warning: {
      main: '#ffdd00',
      light: '#ffe74d',
      dark: '#ccb100',
      contrastText: '#000000',
    },
    info: {
      main: '#75c9c8', // Teal - info color
      light: '#95d8d7',
      dark: '#528c8b',
      contrastText: '#000000',
    },
    success: {
      main: '#4caf50',
    },
    background: {
      default: '#ffffff',
      paper: '#ffffff',
    },
  },
  typography: {
    // Uses Montserrat for headers, Roboto Condensed for body
    fontFamily: '"Roboto Condensed", "Roboto", "Arial", sans-serif',
    h1: {
      fontFamily: '"Montserrat", "Arial", sans-serif',
      fontSize: '2.5rem', // Desktop default, use RESPONSIVE_FONT_SIZE from utils/responsive.ts for responsive sizing
      fontWeight: 300, // Light weight for large headers
      letterSpacing: '-0.01562em',
    },
    h2: {
      fontFamily: '"Montserrat", "Arial", sans-serif',
      fontSize: '2rem', // Desktop default
      fontWeight: 500, // Medium weight for smaller headers
      letterSpacing: '-0.00833em',
    },
    h3: {
      fontFamily: '"Montserrat", "Arial", sans-serif',
      fontSize: '1.75rem', // Desktop default
      fontWeight: 700, // Bold weight for subheaders
      letterSpacing: '0em',
    },
    h4: {
      fontFamily: '"Montserrat", "Arial", sans-serif',
      fontSize: '1.5rem', // Desktop default
      fontWeight: 700,
      letterSpacing: '0.00735em',
    },
    h5: {
      fontFamily: '"Montserrat", "Arial", sans-serif',
      fontSize: '1.25rem', // Desktop default
      fontWeight: 700,
      letterSpacing: '0em',
    },
    h6: {
      fontFamily: '"Montserrat", "Arial", sans-serif',
      fontSize: '1rem', // Desktop default
      fontWeight: 700,
      letterSpacing: '0.0075em',
    },
    subtitle1: {
      fontFamily: '"Roboto Condensed", "Arial", sans-serif',
      fontSize: '1rem',
      fontWeight: 300, // Light for subheaders
      letterSpacing: '0.00938em',
    },
    body1: {
      fontFamily: '"Roboto Condensed", "Arial", sans-serif',
      fontSize: '1rem',
      fontWeight: 400, // Regular for body text
      letterSpacing: '0.00938em',
    },
    body2: {
      fontFamily: '"Roboto Condensed", "Arial", sans-serif',
      fontSize: '0.875rem',
      fontWeight: 400,
      letterSpacing: '0.01071em',
    },
    button: {
      fontFamily: '"Roboto Condensed", "Arial", sans-serif',
      fontSize: '0.875rem',
      fontWeight: 700, // Bold for captions/buttons
      letterSpacing: '0.02857em',
      textTransform: 'none',
    },
    caption: {
      fontFamily: '"Roboto Condensed", "Arial", sans-serif',
      fontSize: '0.75rem',
      fontWeight: 700, // Bold for captions
      letterSpacing: '0.03333em',
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 700,
          borderRadius: 8,
          minHeight: 44, // Touch-friendly minimum height (Apple guideline)
          paddingLeft: 16,
          paddingRight: 16,
        },
        contained: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
          },
        },
        sizeSmall: {
          minHeight: 36,
          paddingLeft: 12,
          paddingRight: 12,
        },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          minHeight: 44, // Touch-friendly minimum size
          minWidth: 44,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          '&:hover': {
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          },
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: '0 1px 4px rgba(0,0,0,0.1)',
        },
      },
    },
  },
});
