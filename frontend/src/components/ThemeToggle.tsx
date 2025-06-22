import React from 'react';
import {
  IconButton,
  Tooltip,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Box,
  Typography,
} from '@mui/material';
import {
  DarkMode,
  LightMode,
  SettingsBrightness,
  Check,
} from '@mui/icons-material';
import { useTheme } from '../contexts/ThemeContext';

interface ThemeToggleProps {
  variant?: 'icon' | 'menu';
  showLabel?: boolean;
}

export const ThemeToggle: React.FC<ThemeToggleProps> = ({ 
  variant = 'icon', 
  showLabel = false 
}) => {
  const { mode, setTheme } = useTheme();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    if (variant === 'icon') {
      // Simple toggle for icon variant
      setTheme(mode === 'light' ? 'dark' : 'light');
    } else {
      // Open menu for menu variant
      setAnchorEl(event.currentTarget);
    }
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleThemeSelect = (selectedMode: 'light' | 'dark') => {
    setTheme(selectedMode);
    handleClose();
  };

  const getIcon = () => {
    switch (mode) {
      case 'dark':
        return <DarkMode />;
      case 'light':
        return <LightMode />;
      default:
        return <SettingsBrightness />;
    }
  };

  const getTooltip = () => {
    switch (mode) {
      case 'dark':
        return 'Switch to light mode';
      case 'light':
        return 'Switch to dark mode';
      default:
        return 'Toggle theme';
    }
  };

  if (variant === 'icon') {
    return (
      <Box display="flex" alignItems="center" gap={1}>
        <Tooltip title={getTooltip()}>
          <IconButton
            onClick={handleClick}
            color="inherit"
            size="medium"
            sx={{
              borderRadius: 2,
              transition: 'all 0.2s ease-in-out',
              '&:hover': {
                backgroundColor: 'action.hover',
                transform: 'scale(1.05)',
              },
            }}
          >
            {getIcon()}
          </IconButton>
        </Tooltip>
        {showLabel && (
          <Typography variant="body2" color="text.secondary">
            {mode === 'light' ? 'Light' : 'Dark'} Mode
          </Typography>
        )}
      </Box>
    );
  }

  return (
    <>
      <Tooltip title="Theme Settings">
        <IconButton
          onClick={handleClick}
          color="inherit"
          size="medium"
        >
          <SettingsBrightness />
        </IconButton>
      </Tooltip>
      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        PaperProps={{
          sx: {
            mt: 1,
            minWidth: 180,
          },
        }}
      >
        <MenuItem 
          onClick={() => handleThemeSelect('light')}
          selected={mode === 'light'}
        >
          <ListItemIcon>
            <LightMode fontSize="small" />
          </ListItemIcon>
          <ListItemText>Light Mode</ListItemText>
          {mode === 'light' && (
            <Check fontSize="small" color="primary" />
          )}
        </MenuItem>
        <MenuItem 
          onClick={() => handleThemeSelect('dark')}
          selected={mode === 'dark'}
        >
          <ListItemIcon>
            <DarkMode fontSize="small" />
          </ListItemIcon>
          <ListItemText>Dark Mode</ListItemText>
          {mode === 'dark' && (
            <Check fontSize="small" color="primary" />
          )}
        </MenuItem>
      </Menu>
    </>
  );
};