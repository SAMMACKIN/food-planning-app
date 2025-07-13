import { useCallback, useRef, useEffect } from 'react';
import { requestQueue } from '../utils/requestQueue';

export const usePrioritizedRequest = () => {
  const pendingRequests = useRef<Set<string>>(new Set());

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      // Cancel any pending requests when component unmounts
      pendingRequests.current.forEach(id => {
        requestQueue.cancel(id);
      });
      pendingRequests.current.clear();
    };
  }, []);

  const makeRequest = useCallback(async <T,>(
    requestFn: () => Promise<T>,
    priority: 'high' | 'normal' | 'low' = 'normal'
  ): Promise<T> => {
    return new Promise((resolve, reject) => {
      const requestId = requestQueue.add({
        priority,
        execute: async () => {
          try {
            const result = await requestFn();
            pendingRequests.current.delete(requestId);
            resolve(result);
            return result;
          } catch (error) {
            pendingRequests.current.delete(requestId);
            reject(error);
            throw error;
          }
        },
      });

      pendingRequests.current.add(requestId);
    });
  }, []);

  return { makeRequest };
};