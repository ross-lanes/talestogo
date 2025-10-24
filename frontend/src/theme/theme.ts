import { createTheme } from '@mui/material/styles';

// PPPL Brand Colors
// Core: Orange #f58025, Grey #405965, Magenta #c12d63, Yellow #ffdd00, Cyan #008c9d
export const theme = createTheme({
  palette: {
    primary: {
      main: '#405965', // PPPL Grey - primary base color
      light: '#5a7685',
      dark: '#2d3f47',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#f58025', // PPPL Orange - accent color
      light: '#ff9a4d',
      dark: '#d66a19',
      contrastText: '#000000',
    },
    error: {
      main: '#c12d63', // PPPL Magenta
      light: '#d65083',
      dark: '#8d1e47',
    },
    warning: {
      main: '#ffdd00', // PPPL Yellow
      light: '#ffe74d',
      dark: '#ccb100',
      contrastText: '#000000',
    },
    info: {
      main: '#008c9d', // PPPL Cyan
      light: '#33a6b5',
      dark: '#00616e',
    },
    success: {
      main: '#4caf50',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
  },
  typography: {
    // PPPL uses Montserrat for headers, Roboto Condensed for body
    fontFamily: '"Roboto Condensed", "Roboto", "Arial", sans-serif',
    h1: {
      fontFamily: '"Montserrat", "Arial", sans-serif',
      fontSize: '2.5rem',
      fontWeight: 300, // Light weight for large headers
      letterSpacing: '-0.01562em',
    },
    h2: {
      fontFamily: '"Montserrat", "Arial", sans-serif',
      fontSize: '2rem',
      fontWeight: 500, // Medium weight for smaller headers
      letterSpacing: '-0.00833em',
    },
    h3: {
      fontFamily: '"Montserrat", "Arial", sans-serif',
      fontSize: '1.75rem',
      fontWeight: 700, // Bold weight for subheaders
      letterSpacing: '0em',
    },
    h4: {
      fontFamily: '"Montserrat", "Arial", sans-serif',
      fontSize: '1.5rem',
      fontWeight: 700,
      letterSpacing: '0.00735em',
    },
    h5: {
      fontFamily: '"Montserrat", "Arial", sans-serif',
      fontSize: '1.25rem',
      fontWeight: 700,
      letterSpacing: '0em',
    },
    h6: {
      fontFamily: '"Montserrat", "Arial", sans-serif',
      fontSize: '1rem',
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
        },
        contained: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
          },
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
