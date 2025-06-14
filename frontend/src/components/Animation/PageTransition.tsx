import React from 'react';
import { Box, Fade, Slide } from '@mui/material';
import { useTheme, useMediaQuery } from '@mui/material';

interface PageTransitionProps {
  children: React.ReactNode;
  direction?: 'up' | 'down' | 'left' | 'right';
  duration?: number;
  delay?: number;
}

const PageTransition: React.FC<PageTransitionProps> = ({
  children,
  direction = 'up',
  duration = 500,
  delay = 0,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  // Reduced animations for mobile performance
  const effectiveDuration = isMobile ? Math.min(duration, 300) : duration;

  return (
    <Slide
      direction={direction}
      in={true}
      timeout={effectiveDuration}
      style={{ transitionDelay: `${delay}ms` }}
    >
      <Fade
        in={true}
        timeout={effectiveDuration + 100}
        style={{ transitionDelay: `${delay + 50}ms` }}
      >
        <Box
          sx={{
            width: '100%',
            height: '100%',
          }}
        >
          {children}
        </Box>
      </Fade>
    </Slide>
  );
};

export default PageTransition;