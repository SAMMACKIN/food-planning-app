import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { ThemeProvider as MuiThemeProvider, PaletteMode } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import { createAppTheme } from '../theme';

interface ThemeContextType {
  mode: PaletteMode;
  toggleTheme: () => void;
  setTheme: (mode: PaletteMode) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

interface ThemeProviderProps {
  children: ReactNode;
}

const THEME_STORAGE_KEY = 'food-app-theme-mode';

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  // Initialize theme from localStorage or system preference
  const [mode, setMode] = useState<PaletteMode>(() => {
    try {
      const savedMode = localStorage.getItem(THEME_STORAGE_KEY);
      if (savedMode === 'light' || savedMode === 'dark') {
        return savedMode as PaletteMode;
      }
    } catch (error) {
      console.warn('Failed to load theme from localStorage:', error);
    }
    
    // Fallback to system preference
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });

  // Save theme to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem(THEME_STORAGE_KEY, mode);
    } catch (error) {
      console.warn('Failed to save theme to localStorage:', error);
    }
  }, [mode]);

  // Listen for system theme changes
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleChange = (e: MediaQueryListEvent) => {
      // Only auto-update if user hasn't manually set a preference
      const savedMode = localStorage.getItem(THEME_STORAGE_KEY);
      if (!savedMode) {
        setMode(e.matches ? 'dark' : 'light');
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  const toggleTheme = () => {
    setMode(prevMode => prevMode === 'light' ? 'dark' : 'light');
  };

  const setTheme = (newMode: PaletteMode) => {
    setMode(newMode);
  };

  const theme = createAppTheme(mode);

  const contextValue: ThemeContextType = {
    mode,
    toggleTheme,
    setTheme,
  };

  return (
    <ThemeContext.Provider value={contextValue}>
      <MuiThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </MuiThemeProvider>
    </ThemeContext.Provider>
  );
};