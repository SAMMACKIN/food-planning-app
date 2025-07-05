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
  const [error, setError] = useState<string | null>(null);
  const [availableProviders, setAvailableProviders] = useState<string[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>('perplexity');
  const lastRequestRef = useRef<string>('');

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

  const fetchRecommendations = useCallback(async (request: MealRecommendationRequest = {}, forceRefresh = false) => {
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

    try {
      setLoading(true);
      setError(null);
      
      const requestWithTimestamp = {
        ...request,
        ai_provider: selectedProvider,
        timestamp: Date.now()
      };
      
      console.log(`🤖 Fetching fresh AI recommendations from ${selectedProvider}...`);
      const recs = await apiRequest<MealRecommendation[]>('POST', '/recommendations', requestWithTimestamp);
      console.log('✅ Received recommendations:', recs.map(r => ({ name: r.name, ai_generated: r.ai_generated, ai_provider: r.ai_provider })));
      
      setRecommendations(recs);
      saveToCache(recs, requestKey);
      lastRequestRef.current = requestKey;
    } catch (error: any) {
      setError(`Failed to get meal recommendations from ${selectedProvider}`);
      console.error('Error fetching recommendations:', error);
    } finally {
      setLoading(false);
    }
  }, [selectedProvider, generateRequestKey, loadFromCache, saveToCache, recommendations.length]);

  const refreshRecommendations = useCallback((request: MealRecommendationRequest = {}) => {
    fetchRecommendations(request, true);
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

  return {
    recommendations,
    loading,
    error,
    availableProviders,
    selectedProvider,
    setSelectedProvider,
    fetchRecommendations,
    refreshRecommendations,
    handleMealTypeFilter,
    clearCache,
    clearError: () => setError(null)
  };
};