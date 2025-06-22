import { createTheme, Theme, PaletteMode } from '@mui/material/styles';

// Professional, minimal color system
const getDesignTokens = (mode: PaletteMode) => ({
  palette: {
    mode,
    ...(mode === 'light'
      ? {
          // Light mode - clean and professional
          primary: {
            main: '#0F172A', // Slate 900 - sophisticated dark
            light: '#334155', // Slate 700
            dark: '#020617', // Slate 950
            contrastText: '#ffffff',
          },
          secondary: {
            main: '#64748B', // Slate 500 - muted secondary
            light: '#94A3B8', // Slate 400
            dark: '#475569', // Slate 600
            contrastText: '#ffffff',
          },
          background: {
            default: '#FAFBFC', // Very subtle gray
            paper: '#FFFFFF',
          },
          text: {
            primary: '#0F172A', // Slate 900 - high contrast
            secondary: '#64748B', // Slate 500 - readable gray
          },
          success: {
            main: '#059669', // Emerald 600 - professional green
            light: '#34D399', // Emerald 400
            dark: '#047857', // Emerald 700
          },
          warning: {
            main: '#D97706', // Amber 600 - warm warning
            light: '#FCD34D', // Amber 300
            dark: '#B45309', // Amber 700
          },
          error: {
            main: '#DC2626', // Red 600 - clear error
            light: '#F87171', // Red 400
            dark: '#B91C1C', // Red 700
          },
          info: {
            main: '#2563EB', // Blue 600 - professional blue
            light: '#60A5FA', // Blue 400
            dark: '#1D4ED8', // Blue 700
          },
          divider: 'rgba(15, 23, 42, 0.08)', // Subtle dividers
          action: {
            hover: 'rgba(15, 23, 42, 0.04)',
            selected: 'rgba(15, 23, 42, 0.08)',
            disabled: 'rgba(15, 23, 42, 0.26)',
            disabledBackground: 'rgba(15, 23, 42, 0.12)',
          },
        }
      : {
          // Dark mode - sophisticated dark theme
          primary: {
            main: '#E2E8F0', // Slate 200 - light text on dark
            light: '#F1F5F9', // Slate 100
            dark: '#CBD5E1', // Slate 300
            contrastText: '#0F172A',
          },
          secondary: {
            main: '#94A3B8', // Slate 400 - muted secondary
            light: '#CBD5E1', // Slate 300
            dark: '#64748B', // Slate 500
            contrastText: '#0F172A',
          },
          background: {
            default: '#0B1120', // Very dark blue-gray
            paper: '#1E293B', // Slate 800 - elevated surfaces
          },
          text: {
            primary: '#F8FAFC', // Slate 50 - high contrast white
            secondary: '#94A3B8', // Slate 400 - readable gray
          },
          success: {
            main: '#10B981', // Emerald 500
            light: '#34D399', // Emerald 400
            dark: '#059669', // Emerald 600
          },
          warning: {
            main: '#F59E0B', // Amber 500
            light: '#FCD34D', // Amber 300
            dark: '#D97706', // Amber 600
          },
          error: {
            main: '#EF4444', // Red 500
            light: '#F87171', // Red 400
            dark: '#DC2626', // Red 600
          },
          info: {
            main: '#3B82F6', // Blue 500
            light: '#60A5FA', // Blue 400
            dark: '#2563EB', // Blue 600
          },
          divider: 'rgba(248, 250, 252, 0.12)', // Subtle dividers in dark
          action: {
            hover: 'rgba(248, 250, 252, 0.08)',
            selected: 'rgba(248, 250, 252, 0.12)',
            disabled: 'rgba(248, 250, 252, 0.26)',
            disabledBackground: 'rgba(248, 250, 252, 0.12)',
          },
        }),
  },
  typography: {
    fontFamily: [
      '"Inter"',
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'system-ui',
      'sans-serif',
    ].join(','),
    fontSize: 14, // Slightly smaller base for density
    htmlFontSize: 16,
    fontWeightLight: 300,
    fontWeightRegular: 400,
    fontWeightMedium: 500,
    fontWeightBold: 600,
    h1: {
      fontSize: '2.25rem', // 36px
      fontWeight: 700,
      lineHeight: 1.2,
      letterSpacing: '-0.02em',
      '@media (max-width:600px)': {
        fontSize: '1.875rem', // 30px on mobile
      },
    },
    h2: {
      fontSize: '1.875rem', // 30px
      fontWeight: 600,
      lineHeight: 1.3,
      letterSpacing: '-0.01em',
      '@media (max-width:600px)': {
        fontSize: '1.5rem', // 24px on mobile
      },
    },
    h3: {
      fontSize: '1.5rem', // 24px
      fontWeight: 600,
      lineHeight: 1.4,
      letterSpacing: '-0.01em',
      '@media (max-width:600px)': {
        fontSize: '1.25rem', // 20px on mobile
      },
    },
    h4: {
      fontSize: '1.25rem', // 20px
      fontWeight: 600,
      lineHeight: 1.4,
      '@media (max-width:600px)': {
        fontSize: '1.125rem', // 18px on mobile
      },
    },
    h5: {
      fontSize: '1.125rem', // 18px
      fontWeight: 600,
      lineHeight: 1.5,
    },
    h6: {
      fontSize: '1rem', // 16px
      fontWeight: 600,
      lineHeight: 1.5,
    },
    subtitle1: {
      fontSize: '1rem',
      fontWeight: 500,
      lineHeight: 1.5,
      letterSpacing: '0.00938em',
    },
    subtitle2: {
      fontSize: '0.875rem',
      fontWeight: 500,
      lineHeight: 1.57,
      letterSpacing: '0.00714em',
    },
    body1: {
      fontSize: '1rem',
      fontWeight: 400,
      lineHeight: 1.6,
      letterSpacing: '0.00938em',
    },
    body2: {
      fontSize: '0.875rem',
      fontWeight: 400,
      lineHeight: 1.57,
      letterSpacing: '0.00714em',
    },
    button: {
      fontSize: '0.875rem',
      fontWeight: 500,
      lineHeight: 1.43,
      letterSpacing: '0.02857em',
      textTransform: 'none' as const,
    },
    caption: {
      fontSize: '0.75rem',
      fontWeight: 400,
      lineHeight: 1.66,
      letterSpacing: '0.03333em',
    },
    overline: {
      fontSize: '0.75rem',
      fontWeight: 500,
      lineHeight: 2.66,
      letterSpacing: '0.08333em',
      textTransform: 'uppercase' as const,
    },
  },
  shape: {
    borderRadius: 8, // Slightly tighter for professional look
  },
  spacing: 8, // 8px base unit
  shadows: mode === 'light' ? [
    'none',
    '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)', // subtle
    '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)', // small
    '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)', // medium
    '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)', // large
    '0 25px 50px -12px rgba(0, 0, 0, 0.25)', // xl
    '0 25px 50px -12px rgba(0, 0, 0, 0.25)', // 2xl
    '0 25px 50px -12px rgba(0, 0, 0, 0.25)', // 3xl
    // ... fill the rest with the last shadow
    ...Array(17).fill('0 25px 50px -12px rgba(0, 0, 0, 0.25)')
  ] : [
    'none',
    '0 1px 3px 0 rgba(0, 0, 0, 0.3), 0 1px 2px 0 rgba(0, 0, 0, 0.2)',
    '0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2)',
    '0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.2)',
    '0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2)',
    '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
    '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
    '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
    // ... fill the rest
    ...Array(17).fill('0 25px 50px -12px rgba(0, 0, 0, 0.5)')
  ],
  components: {
    // CssBaseline for consistent styling
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          scrollbarWidth: 'thin',
          scrollbarColor: mode === 'light' ? '#CBD5E1 #F1F5F9' : '#475569 #1E293B',
          '&::-webkit-scrollbar': {
            width: '8px',
            height: '8px',
          },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: mode === 'light' ? '#CBD5E1' : '#475569',
            borderRadius: '4px',
            '&:hover': {
              backgroundColor: mode === 'light' ? '#94A3B8' : '#64748B',
            },
          },
          '&::-webkit-scrollbar-track': {
            backgroundColor: mode === 'light' ? '#F1F5F9' : '#1E293B',
          },
        },
      },
    },

    // Buttons - professional and refined
    MuiButton: {
      styleOverrides: {
        root: {
          fontWeight: 500,
          borderRadius: 8,
          textTransform: 'none' as const,
          fontSize: '0.875rem',
          lineHeight: 1.43,
          letterSpacing: '0.02857em',
          boxShadow: 'none',
          minHeight: 44, // Accessibility
          transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            boxShadow: 'none',
            transform: 'translateY(-1px)',
          },
          '&:active': {
            transform: 'translateY(0)',
          },
          '@media (max-width:600px)': {
            minHeight: 48, // Larger touch target on mobile
            fontSize: '1rem',
          },
        },
        contained: {
          fontWeight: 500,
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
          '&:hover': {
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
            transform: 'translateY(-1px)',
          },
          '&:active': {
            transform: 'translateY(0)',
            boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
          },
        },
        outlined: {
          borderWidth: '1.5px',
          fontWeight: 500,
          '&:hover': {
            borderWidth: '1.5px',
            transform: 'translateY(-1px)',
          },
        },
        text: {
          fontWeight: 500,
          '&:hover': {
            backgroundColor: mode === 'light' ? 'rgba(15, 23, 42, 0.04)' : 'rgba(248, 250, 252, 0.08)',
          },
        },
        sizeSmall: {
          minHeight: 36,
          fontSize: '0.8125rem',
          '@media (max-width:600px)': {
            minHeight: 40,
          },
        },
        sizeLarge: {
          minHeight: 52,
          fontSize: '1rem',
          '@media (max-width:600px)': {
            minHeight: 56,
          },
        },
      },
    },

    // Cards - elevated and sophisticated
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          backgroundColor: mode === 'light' ? '#FFFFFF' : '#1E293B',
          border: mode === 'light' ? '1px solid rgba(15, 23, 42, 0.08)' : '1px solid rgba(248, 250, 252, 0.08)',
          boxShadow: mode === 'light' 
            ? '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)'
            : '0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2)',
          transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: mode === 'light'
              ? '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)'
              : '0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2)',
          },
          '@media (max-width:600px)': {
            borderRadius: 8,
          },
        },
      },
    },

    MuiCardContent: {
      styleOverrides: {
        root: {
          padding: '24px',
          '&:last-child': {
            paddingBottom: '24px',
          },
          '@media (max-width:600px)': {
            padding: '20px',
            '&:last-child': {
              paddingBottom: '20px',
            },
          },
        },
      },
    },

    // Paper - consistent elevated surfaces
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundColor: mode === 'light' ? '#FFFFFF' : '#1E293B',
          backgroundImage: 'none', // Remove MUI's default gradient
        },
        elevation1: {
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        },
        elevation2: {
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        },
        elevation3: {
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        },
      },
    },

    // AppBar - clean and modern
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: mode === 'light' ? '#FFFFFF' : '#1E293B',
          color: mode === 'light' ? '#0F172A' : '#F8FAFC',
          boxShadow: mode === 'light'
            ? '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)'
            : '0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2)',
          borderBottom: mode === 'light' ? '1px solid rgba(15, 23, 42, 0.08)' : '1px solid rgba(248, 250, 252, 0.08)',
        },
      },
    },

    // Text Fields - clean and accessible
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
            backgroundColor: mode === 'light' ? '#FFFFFF' : '#1E293B',
            transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
            '& fieldset': {
              borderColor: mode === 'light' ? 'rgba(15, 23, 42, 0.2)' : 'rgba(248, 250, 252, 0.2)',
              borderWidth: '1.5px',
            },
            '&:hover fieldset': {
              borderColor: mode === 'light' ? 'rgba(15, 23, 42, 0.4)' : 'rgba(248, 250, 252, 0.4)',
            },
            '&.Mui-focused fieldset': {
              borderWidth: '2px',
            },
            '& input': {
              padding: '14px 16px',
              fontSize: '0.875rem',
              '@media (max-width:600px)': {
                padding: '16px',
                fontSize: '1rem', // Better for mobile
              },
            },
          },
        },
      },
    },

    // Chips - refined and minimal
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 6,
          fontWeight: 500,
          fontSize: '0.8125rem',
          height: 28,
          transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
          '@media (max-width:600px)': {
            height: 32,
            fontSize: '0.875rem',
          },
        },
        filled: {
          backgroundColor: mode === 'light' ? 'rgba(15, 23, 42, 0.08)' : 'rgba(248, 250, 252, 0.12)',
          color: mode === 'light' ? '#0F172A' : '#F8FAFC',
          '&:hover': {
            backgroundColor: mode === 'light' ? 'rgba(15, 23, 42, 0.12)' : 'rgba(248, 250, 252, 0.16)',
          },
        },
      },
    },

    // Dialogs - sophisticated modals
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: 16,
          backgroundColor: mode === 'light' ? '#FFFFFF' : '#1E293B',
          boxShadow: mode === 'light'
            ? '0 25px 50px -12px rgba(0, 0, 0, 0.25)'
            : '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
          '@media (max-width:600px)': {
            margin: 16,
            width: 'calc(100% - 32px)',
            maxWidth: 'none',
            borderRadius: 12,
          },
        },
      },
    },

    // Tabs - clean navigation
    MuiTabs: {
      styleOverrides: {
        root: {
          minHeight: 48,
          '& .MuiTabs-indicator': {
            height: 3,
            borderRadius: '3px 3px 0 0',
          },
        },
      },
    },

    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none' as const,
          fontWeight: 500,
          fontSize: '0.875rem',
          minHeight: 48,
          color: mode === 'light' ? '#64748B' : '#94A3B8',
          '&.Mui-selected': {
            color: mode === 'light' ? '#0F172A' : '#F8FAFC',
            fontWeight: 600,
          },
          '&:hover': {
            color: mode === 'light' ? '#334155' : '#CBD5E1',
          },
        },
      },
    },

    // Bottom Navigation - mobile optimized
    MuiBottomNavigation: {
      styleOverrides: {
        root: {
          height: 64,
          backgroundColor: mode === 'light' ? '#FFFFFF' : '#1E293B',
          borderTop: mode === 'light' ? '1px solid rgba(15, 23, 42, 0.08)' : '1px solid rgba(248, 250, 252, 0.08)',
          paddingTop: 8,
          paddingBottom: 8,
        },
      },
    },

    MuiBottomNavigationAction: {
      styleOverrides: {
        root: {
          color: mode === 'light' ? '#64748B' : '#94A3B8',
          '&.Mui-selected': {
            color: mode === 'light' ? '#0F172A' : '#F8FAFC',
          },
          '&:hover': {
            color: mode === 'light' ? '#334155' : '#CBD5E1',
          },
          minWidth: 'auto',
        },
      },
    },

    // List Items - consistent spacing
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          margin: '2px 8px',
          '&:hover': {
            backgroundColor: mode === 'light' ? 'rgba(15, 23, 42, 0.04)' : 'rgba(248, 250, 252, 0.08)',
          },
          '&.Mui-selected': {
            backgroundColor: mode === 'light' ? 'rgba(15, 23, 42, 0.08)' : 'rgba(248, 250, 252, 0.12)',
            '&:hover': {
              backgroundColor: mode === 'light' ? 'rgba(15, 23, 42, 0.12)' : 'rgba(248, 250, 252, 0.16)',
            },
          },
        },
      },
    },

    // Dividers - subtle separation
    MuiDivider: {
      styleOverrides: {
        root: {
          borderColor: mode === 'light' ? 'rgba(15, 23, 42, 0.08)' : 'rgba(248, 250, 252, 0.12)',
        },
      },
    },

    // Loading components
    MuiCircularProgress: {
      styleOverrides: {
        root: {
          color: mode === 'light' ? '#0F172A' : '#F8FAFC',
        },
      },
    },

    // Backdrop for modals
    MuiBackdrop: {
      styleOverrides: {
        root: {
          backgroundColor: mode === 'light' ? 'rgba(15, 23, 42, 0.4)' : 'rgba(0, 0, 0, 0.6)',
          backdropFilter: 'blur(8px)',
        },
      },
    },

    // Ensure all surfaces are properly themed
    MuiContainer: {
      styleOverrides: {
        root: {
          backgroundColor: 'transparent',
        },
      },
    },

    MuiBox: {
      styleOverrides: {
        root: {
          // Ensure boxes don't override theme colors
          backgroundColor: 'inherit',
        },
      },
    },

    // Menu components
    MuiMenu: {
      styleOverrides: {
        paper: {
          backgroundColor: mode === 'light' ? '#FFFFFF' : '#1E293B',
          border: mode === 'light' ? '1px solid rgba(15, 23, 42, 0.08)' : '1px solid rgba(248, 250, 252, 0.08)',
          boxShadow: mode === 'light'
            ? '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)'
            : '0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.2)',
          borderRadius: 8,
        },
      },
    },

    MuiMenuItem: {
      styleOverrides: {
        root: {
          color: mode === 'light' ? '#0F172A' : '#F8FAFC',
          '&:hover': {
            backgroundColor: mode === 'light' ? 'rgba(15, 23, 42, 0.04)' : 'rgba(248, 250, 252, 0.08)',
          },
          '&.Mui-selected': {
            backgroundColor: mode === 'light' ? 'rgba(15, 23, 42, 0.08)' : 'rgba(248, 250, 252, 0.12)',
            '&:hover': {
              backgroundColor: mode === 'light' ? 'rgba(15, 23, 42, 0.12)' : 'rgba(248, 250, 252, 0.16)',
            },
          },
        },
      },
    },

    // Tooltips
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: mode === 'light' ? '#1E293B' : '#475569',
          color: '#F8FAFC',
          fontSize: '0.75rem',
          borderRadius: 6,
          boxShadow: mode === 'light'
            ? '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)'
            : '0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2)',
        },
        arrow: {
          color: mode === 'light' ? '#1E293B' : '#475569',
        },
      },
    },

    // Snackbars  
    MuiSnackbar: {
      styleOverrides: {
        root: {
          '& .MuiSnackbarContent-root': {
            backgroundColor: mode === 'light' ? '#1E293B' : '#475569',
            color: '#F8FAFC',
          },
        },
      },
    },

    // Alert components
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          border: '1px solid',
          '&.MuiAlert-standardSuccess': {
            backgroundColor: mode === 'light' ? 'rgba(5, 150, 105, 0.1)' : 'rgba(16, 185, 129, 0.1)',
            borderColor: mode === 'light' ? 'rgba(5, 150, 105, 0.2)' : 'rgba(16, 185, 129, 0.2)',
            color: mode === 'light' ? '#047857' : '#10B981',
          },
          '&.MuiAlert-standardError': {
            backgroundColor: mode === 'light' ? 'rgba(220, 38, 38, 0.1)' : 'rgba(239, 68, 68, 0.1)',
            borderColor: mode === 'light' ? 'rgba(220, 38, 38, 0.2)' : 'rgba(239, 68, 68, 0.2)',
            color: mode === 'light' ? '#DC2626' : '#EF4444',
          },
          '&.MuiAlert-standardWarning': {
            backgroundColor: mode === 'light' ? 'rgba(217, 119, 6, 0.1)' : 'rgba(245, 158, 11, 0.1)',
            borderColor: mode === 'light' ? 'rgba(217, 119, 6, 0.2)' : 'rgba(245, 158, 11, 0.2)',
            color: mode === 'light' ? '#D97706' : '#F59E0B',
          },
          '&.MuiAlert-standardInfo': {
            backgroundColor: mode === 'light' ? 'rgba(37, 99, 235, 0.1)' : 'rgba(59, 130, 246, 0.1)',
            borderColor: mode === 'light' ? 'rgba(37, 99, 235, 0.2)' : 'rgba(59, 130, 246, 0.2)',
            color: mode === 'light' ? '#2563EB' : '#3B82F6',
          },
        },
      },
    },

    // Drawer components
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: mode === 'light' ? '#FFFFFF' : '#1E293B',
          borderColor: mode === 'light' ? 'rgba(15, 23, 42, 0.08)' : 'rgba(248, 250, 252, 0.08)',
        },
      },
    },

    // Table components
    MuiTableContainer: {
      styleOverrides: {
        root: {
          backgroundColor: mode === 'light' ? '#FFFFFF' : '#1E293B',
          borderRadius: 8,
        },
      },
    },

    MuiTable: {
      styleOverrides: {
        root: {
          backgroundColor: 'transparent',
        },
      },
    },

    MuiTableHead: {
      styleOverrides: {
        root: {
          backgroundColor: mode === 'light' ? '#F8FAFC' : '#0F172A',
        },
      },
    },

    MuiTableCell: {
      styleOverrides: {
        root: {
          borderColor: mode === 'light' ? 'rgba(15, 23, 42, 0.08)' : 'rgba(248, 250, 252, 0.12)',
          color: mode === 'light' ? '#0F172A' : '#F8FAFC',
        },
        head: {
          fontWeight: 600,
          color: mode === 'light' ? '#475569' : '#CBD5E1',
        },
      },
    },

    // Accordion components
    MuiAccordion: {
      styleOverrides: {
        root: {
          backgroundColor: mode === 'light' ? '#FFFFFF' : '#1E293B',
          border: mode === 'light' ? '1px solid rgba(15, 23, 42, 0.08)' : '1px solid rgba(248, 250, 252, 0.08)',
          borderRadius: 8,
          '&:before': {
            display: 'none',
          },
          boxShadow: 'none',
        },
      },
    },

    MuiAccordionSummary: {
      styleOverrides: {
        root: {
          backgroundColor: 'transparent',
          '&:hover': {
            backgroundColor: mode === 'light' ? 'rgba(15, 23, 42, 0.04)' : 'rgba(248, 250, 252, 0.08)',
          },
        },
      },
    },

    MuiAccordionDetails: {
      styleOverrides: {
        root: {
          backgroundColor: 'transparent',
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