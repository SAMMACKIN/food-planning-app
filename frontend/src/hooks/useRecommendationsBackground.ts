import { useState, useCallback, useRef, useEffect } from 'react';
import { MealRecommendation, MealRecommendationRequest } from '../types';
import { apiRequest } from '../services/api';

// This is a truly non-blocking recommendations fetcher
export const useRecommendationsBackground = () => {
  const [isLoading, setIsLoading] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const fetchInBackground = useCallback(async (
    request: MealRecommendationRequest,
    provider: string,
    onSuccess: (data: MealRecommendation[]) => void,
    onError: (error: string) => void
  ) => {
    // Cancel any previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const controller = new AbortController();
    abortControllerRef.current = controller;
    setIsLoading(true);

    // Use setTimeout to ensure this doesn't block the event loop
    setTimeout(async () => {
      try {
        const requestWithProvider = {
          ...request,
          ai_provider: provider,
          timestamp: Date.now()
        };

        console.log('🌟 Starting background recommendation fetch...');
        const recommendations = await apiRequest<MealRecommendation[]>(
          'POST',
          '/recommendations',
          requestWithProvider,
          { signal: controller.signal }
        );

        if (!controller.signal.aborted) {
          console.log('✨ Background fetch completed with', recommendations.length, 'recommendations');
          onSuccess(recommendations);
          setIsLoading(false);
        }
      } catch (error: any) {
        if (!controller.signal.aborted) {
          console.error('💥 Background fetch error:', error);
          onError('Failed to fetch recommendations');
          setIsLoading(false);
        }
      }
    }, 0); // Execute on next tick
  }, []);

  const cancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsLoading(false);
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cancel();
    };
  }, [cancel]);

  return { fetchInBackground, cancel, isLoading };
};