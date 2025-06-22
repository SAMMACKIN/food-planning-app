import { createTheme, Theme, PaletteMode } from '@mui/material/styles';

// Define custom color palette
const getDesignTokens = (mode: PaletteMode) => ({
  palette: {
    mode,
    ...(mode === 'light'
      ? {
          // Light mode colors
          primary: {
            main: '#2e7d32', // Green
            light: '#60ad5e',
            dark: '#005005',
            contrastText: '#ffffff',
          },
          secondary: {
            main: '#ff9800', // Orange
            light: '#ffb74d',
            dark: '#f57c00',
            contrastText: '#000000',
          },
          background: {
            default: '#fafafa',
            paper: '#ffffff',
          },
          text: {
            primary: '#212121',
            secondary: '#757575',
          },
          success: {
            main: '#4caf50',
            light: '#81c784',
            dark: '#388e3c',
          },
          warning: {
            main: '#ff9800',
            light: '#ffb74d',
            dark: '#f57c00',
          },
          error: {
            main: '#f44336',
            light: '#e57373',
            dark: '#d32f2f',
          },
          info: {
            main: '#2196f3',
            light: '#64b5f6',
            dark: '#1976d2',
          },
        }
      : {
          // Dark mode colors
          primary: {
            main: '#66bb6a', // Lighter green for dark mode
            light: '#98ee99',
            dark: '#338a3e',
            contrastText: '#000000',
          },
          secondary: {
            main: '#ffb74d', // Lighter orange for dark mode
            light: '#ffe082',
            dark: '#ff8f00',
            contrastText: '#000000',
          },
          background: {
            default: '#121212',
            paper: '#1e1e1e',
          },
          text: {
            primary: '#ffffff',
            secondary: '#b0b0b0',
          },
          success: {
            main: '#66bb6a',
            light: '#98ee99',
            dark: '#338a3e',
          },
          warning: {
            main: '#ffb74d',
            light: '#ffe082',
            dark: '#ff8f00',
          },
          error: {
            main: '#ef5350',
            light: '#ff7961',
            dark: '#c62828',
          },
          info: {
            main: '#42a5f5',
            light: '#80d6ff',
            dark: '#1976d2',
          },
        }),
  },
  typography: {
    fontFamily: [
      'Inter',
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
    h1: {
      fontWeight: 700,
    },
    h2: {
      fontWeight: 600,
    },
    h3: {
      fontWeight: 600,
    },
    h4: {
      fontWeight: 600,
    },
    h5: {
      fontWeight: 500,
    },
    h6: {
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none' as const,
          borderRadius: 8,
          fontWeight: 500,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          backgroundColor: mode === 'light' ? '#ffffff' : '#1e1e1e',
          boxShadow: mode === 'light' 
            ? '0 2px 8px rgba(0,0,0,0.1)' 
            : '0 2px 8px rgba(0,0,0,0.3)',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundColor: mode === 'light' ? '#ffffff' : '#1e1e1e',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 6,
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
          },
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: 12,
          backgroundColor: mode === 'light' ? '#ffffff' : '#1e1e1e',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: mode === 'light' 
            ? '0 1px 3px rgba(0,0,0,0.1)' 
            : '0 1px 3px rgba(0,0,0,0.3)',
        },
      },
    },
  },
});

export const createAppTheme = (mode: PaletteMode): Theme => {
  const tokens = getDesignTokens(mode);
  return createTheme(tokens);
};

// Export default themes
export const lightTheme = createAppTheme('light');
export const darkTheme = createAppTheme('dark');