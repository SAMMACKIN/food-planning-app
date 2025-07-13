import React from 'react';
import { useLocation } from 'react-router-dom';

interface RouteWrapperProps {
  children: React.ReactNode;
  path: string;
}

// This wrapper ensures components properly unmount when navigating away
export const RouteWrapper: React.FC<RouteWrapperProps> = ({ children, path }) => {
  const location = useLocation();
  
  // Force remount by using location.pathname as key
  return (
    <div key={location.pathname}>
      {children}
    </div>
  );
};