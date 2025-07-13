import { useEffect, useRef } from 'react';

export const useApiDebug = (componentName: string) => {
  const mountTime = useRef<number>(Date.now());
  const apiCallCount = useRef<number>(0);

  useEffect(() => {
    console.log(`🚀 ${componentName} mounted at`, new Date(mountTime.current).toLocaleTimeString());
    
    return () => {
      console.log(`🔚 ${componentName} unmounted after ${apiCallCount.current} API calls`);
    };
  }, [componentName]);

  const trackApiCall = (endpoint: string) => {
    apiCallCount.current++;
    const timeSinceMount = Date.now() - mountTime.current;
    console.log(`📡 ${componentName} API Call #${apiCallCount.current} to ${endpoint} (${timeSinceMount}ms after mount)`);
  };

  return { trackApiCall };
};