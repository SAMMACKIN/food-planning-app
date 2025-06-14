import React from 'react';
import {
  Box,
  CircularProgress,
  Typography,
  useTheme,
  useMediaQuery,
} from '@mui/material';

interface LoadingSpinnerProps {
  message?: string;
  size?: number;
  fullPage?: boolean;
  color?: 'primary' | 'secondary';
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message = 'Loading...',
  size,
  fullPage = false,
  color = 'primary',
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  const spinnerSize = size || (isMobile ? 48 : 40);

  const content = (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      gap={2}
      sx={{
        ...(fullPage && {
          minHeight: '60vh',
          width: '100%',
        }),
      }}
    >
      {/* Custom animated loading spinner */}
      <Box
        sx={{
          position: 'relative',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <CircularProgress
          size={spinnerSize}
          thickness={4}
          color={color}
          sx={{
            animationDuration: '1.5s',
          }}
        />
        
        {/* Food emoji that rotates */}
        <Box
          sx={{
            position: 'absolute',
            fontSize: isMobile ? '1.5rem' : '1.2rem',
            animation: 'bounce 2s ease-in-out infinite',
            '@keyframes bounce': {
              '0%, 100%': {
                transform: 'translateY(0)',
              },
              '50%': {
                transform: 'translateY(-4px)',
              },
            },
          }}
        >
          🍽️
        </Box>
      </Box>

      {message && (
        <Typography
          variant={isMobile ? 'body1' : 'body2'}
          color="text.secondary"
          sx={{
            fontWeight: 500,
            textAlign: 'center',
            px: 2,
          }}
        >
          {message}
        </Typography>
      )}
    </Box>
  );

  if (fullPage) {
    return (
      <Box
        sx={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(255, 255, 255, 0.9)',
          backdropFilter: 'blur(4px)',
          zIndex: 9999,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {content}
      </Box>
    );
  }

  return content;
};

export default LoadingSpinner;