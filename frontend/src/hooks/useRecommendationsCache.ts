import { useState, useEffect, useCallback, useRef } from 'react';
import { MealRecommendation, MealRecommendationRequest } from '../types';
import { apiRequest } from '../services/api';
import { useAuthStore } from '../store/authStore';

interface CacheEntry {
  data: MealRecommendation[];
  timestamp: number;
  requestParams: string;
}

const CACHE_DURATION = 10 * 60 * 1000; // 10 minutes
const CACHE_KEY = 'meal_recommendations_cache';

export const useRecommendationsCache = () => {
  const { isAuthenticated } = useAuthStore();
  const [recommendations, setRecommendations] = useState<MealRecommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [backgroundLoading, setBackgroundLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [availableProviders, setAvailableProviders] = useState<string[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>('perplexity');
  const [backgroundLoadCompleted, setBackgroundLoadCompleted] = useState(false);
  const lastRequestRef = useRef<string>('');
  const abortControllerRef = useRef<AbortController | null>(null);

  // Load cache from localStorage
  const loadFromCache = useCallback((requestKey: string): MealRecommendation[] | null => {
    try {
      const cached = localStorage.getItem(CACHE_KEY);
      if (!cached) return null;

      const cacheEntry: CacheEntry = JSON.parse(cached);
      const isExpired = Date.now() - cacheEntry.timestamp > CACHE_DURATION;
      const isSameRequest = cacheEntry.requestParams === requestKey;

      if (!isExpired && isSameRequest) {
        console.log('📦 Loading recommendations from cache');
        return cacheEntry.data;
      }
    } catch (error) {
      console.warn('Failed to load cache:', error);
    }
    return null;
  }, []);

  // Save to cache
  const saveToCache = useCallback((data: MealRecommendation[], requestKey: string) => {
    try {
      const cacheEntry: CacheEntry = {
        data,
        timestamp: Date.now(),
        requestParams: requestKey
      };
      localStorage.setItem(CACHE_KEY, JSON.stringify(cacheEntry));
      console.log('💾 Saved recommendations to cache');
    } catch (error) {
      console.warn('Failed to save cache:', error);
    }
  }, []);

  // Generate cache key from request parameters
  const generateRequestKey = useCallback((request: MealRecommendationRequest = {}, provider: string) => {
    return JSON.stringify({ ...request, provider });
  }, []);

  const checkAIStatus = useCallback(async () => {
    try {
      const status = await apiRequest<{ 
        available_providers: string[]; 
        default_provider: string;
        message: string 
      }>('GET', '/recommendations/status');
      
      setAvailableProviders(status.available_providers);
      if (status.default_provider) {
        setSelectedProvider(status.default_provider);
      }
    } catch (error) {
      console.error('Error checking AI status:', error);
    }
  }, []);

  const fetchRecommendations = useCallback(async (request: MealRecommendationRequest = {}, forceRefresh = false, useBackground = false) => {
    const requestKey = generateRequestKey(request, selectedProvider);
    
    // Don't refetch if it's the same request and we're not forcing refresh
    if (lastRequestRef.current === requestKey && !forceRefresh && recommendations.length > 0) {
      console.log('🔄 Skipping fetch - same request');
      return;
    }

    // Try to load from cache first
    if (!forceRefresh) {
      const cachedData = loadFromCache(requestKey);
      if (cachedData) {
        setRecommendations(cachedData);
        lastRequestRef.current = requestKey;
        return;
      }
    }

    // Cancel any ongoing request
    if (abortControllerRef.current) {
      console.log('🛑 Cancelling previous request');
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    
    // Create new abort controller for this request
    const currentAbortController = new AbortController();
    abortControllerRef.current = currentAbortController;
    
    try {
      // Use background loading if requested or if we already have recommendations
      const shouldUseBackground = useBackground || (recommendations.length > 0);
      
      if (shouldUseBackground) {
        setBackgroundLoading(true);
        console.log('🔄 Starting background fetch...');
      } else {
        setLoading(true);
        console.log('🔄 Starting foreground fetch...');
      }
      setError(null);
      
      const requestWithTimestamp = {
        ...request,
        ai_provider: selectedProvider,
        timestamp: Date.now()
      };
      
      console.log(`🤖 Fetching AI recommendations from ${selectedProvider}...`);
      
      // Pass the abort signal to the API request
      const recs = await apiRequest<MealRecommendation[]>(
        'POST', 
        '/recommendations', 
        requestWithTimestamp,
        { signal: currentAbortController.signal }
      );
      
      // Check if this specific request was aborted
      if (currentAbortController.signal.aborted) {
        console.log('🛑 Request was aborted');
        return;
      }
      
      console.log('✅ Received recommendations:', recs.map(r => ({ name: r.name, ai_generated: r.ai_generated, ai_provider: r.ai_provider })));
      
      setRecommendations(recs);
      saveToCache(recs, requestKey);
      lastRequestRef.current = requestKey;
      
      // Show success notification for background loading
      if (shouldUseBackground) {
        console.log('🎉 Background recommendations completed!');
        setBackgroundLoadCompleted(true);
      }
    } catch (error: any) {
      // Check if error is due to abort
      if (error.name === 'AbortError' || error.code === 'ERR_CANCELED' || currentAbortController.signal.aborted) {
        console.log('🛑 Request aborted, not setting error state');
        return;
      }
      
      setError(`Failed to get meal recommendations from ${selectedProvider}`);
      console.error('Error fetching recommendations:', error);
    } finally {
      // Only update loading states if this request wasn't aborted
      if (!currentAbortController.signal.aborted && abortControllerRef.current === currentAbortController) {
        setLoading(false);
        setBackgroundLoading(false);
      }
      
      // Clear the ref if this was the current controller
      if (abortControllerRef.current === currentAbortController) {
        abortControllerRef.current = null;
      }
    }
  }, [selectedProvider, generateRequestKey, loadFromCache, saveToCache, recommendations.length]);

  const refreshRecommendations = useCallback((request: MealRecommendationRequest = {}) => {
    fetchRecommendations(request, true);
  }, [fetchRecommendations]);

  const refreshRecommendationsInBackground = useCallback((request: MealRecommendationRequest = {}) => {
    fetchRecommendations(request, true, true);
  }, [fetchRecommendations]);

  const clearCache = useCallback(() => {
    try {
      localStorage.removeItem(CACHE_KEY);
      lastRequestRef.current = '';
      console.log('🗑️ Cache cleared');
    } catch (error) {
      console.warn('Failed to clear cache:', error);
    }
  }, []);

  const resetState = useCallback(() => {
    // Abort any ongoing request
    if (abortControllerRef.current) {
      console.log('🛑 Aborting ongoing recommendation request');
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    // Reset all states immediately
    setLoading(false);
    setBackgroundLoading(false);
    setBackgroundLoadCompleted(false);
    setError(null);
    console.log('🔄 Recommendations state reset');
  }, []);

  const clearBackgroundLoadCompleted = useCallback(() => {
    setBackgroundLoadCompleted(false);
  }, []);

  const handleMealTypeFilter = useCallback((mealType: string) => {
    fetchRecommendations({ meal_type: mealType });
  }, [fetchRecommendations]);

  // Check AI status on mount
  useEffect(() => {
    checkAIStatus();
  }, [checkAIStatus]);

  // Fetch recommendations when provider changes or on mount, but only when authenticated
  useEffect(() => {
    if (isAuthenticated && availableProviders.length > 0) {
      fetchRecommendations();
    }
  }, [isAuthenticated, selectedProvider, availableProviders]); // eslint-disable-line react-hooks/exhaustive-deps

  // Cleanup: abort any ongoing requests when component unmounts
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        console.log('🧹 Cleaning up: aborting ongoing recommendations request');
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
      // Force reset all loading states on unmount
      setLoading(false);
      setBackgroundLoading(false);
      setBackgroundLoadCompleted(false);
      setError(null);
    };
  }, []);

  return {
    recommendations,
    loading,
    backgroundLoading,
    backgroundLoadCompleted,
    error,
    availableProviders,
    selectedProvider,
    setSelectedProvider,
    fetchRecommendations,
    refreshRecommendations,
    refreshRecommendationsInBackground,
    handleMealTypeFilter,
    clearCache,
    resetState,
    clearBackgroundLoadCompleted,
    clearError: () => setError(null)
  };
};