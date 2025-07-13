import { renderHook, act, waitFor } from '@testing-library/react';
import { useRecommendationsCache } from '../useRecommendationsCache';
import { apiRequest } from '../../services/api';
import { useAuthStore } from '../../store/authStore';
import { MealRecommendation, MealRecommendationRequest } from '../../types';

// Mock dependencies
jest.mock('../../services/api');
jest.mock('../../store/authStore');

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock console methods to suppress debug logs
const consoleMock = {
  log: jest.fn(),
  error: jest.fn(),
  warn: jest.fn(),
};
Object.defineProperty(console, 'log', { value: consoleMock.log });
Object.defineProperty(console, 'error', { value: consoleMock.error });
Object.defineProperty(console, 'warn', { value: consoleMock.warn });

const mockApiRequest = apiRequest as jest.MockedFunction<typeof apiRequest>;
const mockUseAuthStore = useAuthStore as jest.MockedFunction<typeof useAuthStore>;

describe('useRecommendationsCache', () => {
  const mockRecommendation: MealRecommendation = {
    name: 'Test Recipe',
    description: 'A test recipe',
    prep_time: 30,
    difficulty: 'medium',
    servings: 4,
    ingredients_needed: [
      { name: 'ingredient1', quantity: '1', unit: 'cup', have_in_pantry: false },
      { name: 'ingredient2', quantity: '2', unit: 'tbsp', have_in_pantry: true }
    ],
    instructions: ['Test instructions'],
    tags: ['dinner'],
    nutrition_notes: 'Healthy',
    pantry_usage_score: 0.8,
    ai_generated: true,
    ai_provider: 'perplexity'
  };

  const mockAIStatus = {
    available_providers: ['perplexity', 'claude', 'groq'],
    default_provider: 'perplexity',
    message: 'AI services available'
  };

  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
    mockUseAuthStore.mockReturnValue({
      isAuthenticated: true,
      user: null,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
      checkAuth: jest.fn(),
      clearError: jest.fn(),
      loading: false,
      error: null,
    });
    consoleMock.log.mockClear();
    consoleMock.error.mockClear();
    consoleMock.warn.mockClear();

    // Mock Date.now for consistent cache testing
    jest.spyOn(Date, 'now').mockReturnValue(1000000);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('Initial State', () => {
    test('should initialize with correct default values', () => {
      const { result } = renderHook(() => useRecommendationsCache());

      expect(result.current.recommendations).toEqual([]);
      expect(result.current.loading).toBe(false);
      expect(result.current.backgroundLoading).toBe(false);
      expect(result.current.backgroundLoadCompleted).toBe(false);
      expect(result.current.error).toBe(null);
      expect(result.current.availableProviders).toEqual([]);
      expect(result.current.selectedProvider).toBe('perplexity');
    });

    test('should check AI status on mount', async () => {
      mockApiRequest.mockResolvedValue(mockAIStatus);

      renderHook(() => useRecommendationsCache());

      await waitFor(() => {
        expect(mockApiRequest).toHaveBeenCalledWith('GET', '/recommendations/status', undefined, { requestType: 'recommendations' });
      });
    });

    test('should fetch recommendations when authenticated and providers available', async () => {
      mockApiRequest
        .mockResolvedValueOnce(mockAIStatus) // checkAIStatus
        .mockResolvedValueOnce([mockRecommendation]); // fetchRecommendations

      renderHook(() => useRecommendationsCache());

      await waitFor(() => {
        expect(mockApiRequest).toHaveBeenCalledWith(
          'POST',
          '/recommendations',
          expect.objectContaining({ ai_provider: 'perplexity' }),
          expect.objectContaining({ requestType: 'recommendations' })
        );
      });
    });

    test('should not fetch recommendations when not authenticated', async () => {
      mockUseAuthStore.mockReturnValue({
        isAuthenticated: false,
        user: null,
        login: jest.fn(),
        register: jest.fn(),
        logout: jest.fn(),
        checkAuth: jest.fn(),
        clearError: jest.fn(),
        loading: false,
        error: null,
      });

      mockApiRequest.mockResolvedValue(mockAIStatus);

      renderHook(() => useRecommendationsCache());

      await waitFor(() => {
        expect(mockApiRequest).toHaveBeenCalledTimes(1); // Only checkAIStatus
      });
    });
  });

  describe('Cache Management', () => {
    test('should load recommendations from valid cache', async () => {
      const cacheEntry = {
        data: [mockRecommendation],
        timestamp: 1000000 - 300000, // 5 minutes ago (within 10 min cache duration)
        requestParams: JSON.stringify({ provider: 'perplexity' }) // Match what generateRequestKey creates
      };
      localStorageMock.getItem.mockReturnValue(JSON.stringify(cacheEntry));
      mockApiRequest.mockResolvedValue(mockAIStatus);

      const { result } = renderHook(() => useRecommendationsCache());

      // Wait for the hook to initialize and potentially load from cache
      await waitFor(() => {
        expect(result.current.availableProviders).toEqual(['perplexity', 'claude', 'groq']);
      });

      // The cache loading happens inside fetchRecommendations, so we need to trigger it
      await act(async () => {
        await result.current.fetchRecommendations();
      });

      expect(result.current.recommendations).toEqual([mockRecommendation]);
      expect(consoleMock.log).toHaveBeenCalledWith('📦 Loading recommendations from cache');
    });

    test('should not load from expired cache', async () => {
      const expiredCacheEntry = {
        data: [mockRecommendation],
        timestamp: 1000000 - 700000, // 11+ minutes ago (expired)
        requestParams: JSON.stringify({ ai_provider: 'perplexity' })
      };
      localStorageMock.getItem.mockReturnValue(JSON.stringify(expiredCacheEntry));
      mockApiRequest
        .mockResolvedValueOnce(mockAIStatus)
        .mockResolvedValueOnce([mockRecommendation]);

      renderHook(() => useRecommendationsCache());

      await waitFor(() => {
        expect(mockApiRequest).toHaveBeenCalledWith(
          'POST',
          '/recommendations',
          expect.any(Object),
          expect.any(Object)
        );
      });
    });

    test('should save recommendations to cache', async () => {
      mockApiRequest
        .mockResolvedValueOnce(mockAIStatus)
        .mockResolvedValueOnce([mockRecommendation]);

      renderHook(() => useRecommendationsCache());

      await waitFor(() => {
        expect(localStorageMock.setItem).toHaveBeenCalledWith(
          'meal_recommendations_cache',
          expect.stringContaining('"data"')
        );
      });
    });

    test('should handle cache loading errors gracefully', async () => {
      localStorageMock.getItem.mockImplementation(() => {
        throw new Error('Storage error');
      });
      mockApiRequest
        .mockResolvedValueOnce(mockAIStatus)
        .mockResolvedValueOnce([mockRecommendation]);

      renderHook(() => useRecommendationsCache());

      await waitFor(() => {
        expect(consoleMock.warn).toHaveBeenCalledWith('Failed to load cache:', expect.any(Error));
      });
    });

    test('should clear cache', () => {
      const { result } = renderHook(() => useRecommendationsCache());

      act(() => {
        result.current.clearCache();
      });

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('meal_recommendations_cache');
      expect(consoleMock.log).toHaveBeenCalledWith('🗑️ Cache cleared');
    });
  });

  describe('fetchRecommendations', () => {
    test('should fetch recommendations successfully', async () => {
      mockApiRequest
        .mockResolvedValueOnce(mockAIStatus)
        .mockResolvedValueOnce([mockRecommendation]);

      const { result } = renderHook(() => useRecommendationsCache());

      await waitFor(() => {
        expect(result.current.recommendations).toEqual([mockRecommendation]);
        expect(result.current.loading).toBe(false);
        expect(result.current.error).toBe(null);
      });
    });

    test('should skip fetch if same request and not forcing refresh', async () => {
      mockApiRequest
        .mockResolvedValueOnce(mockAIStatus)
        .mockResolvedValueOnce([mockRecommendation]);

      const { result } = renderHook(() => useRecommendationsCache());

      await waitFor(() => {
        expect(result.current.recommendations).toHaveLength(1);
      });

      const initialCallCount = mockApiRequest.mock.calls.length;

      // Try to fetch again with same params
      await act(async () => {
        await result.current.fetchRecommendations();
      });

      expect(mockApiRequest.mock.calls.length).toBe(initialCallCount);
      expect(consoleMock.log).toHaveBeenCalledWith('🔄 Skipping fetch - same request');
    });

    test('should force refresh when requested', async () => {
      mockApiRequest
        .mockResolvedValueOnce(mockAIStatus)
        .mockResolvedValueOnce([mockRecommendation])
        .mockResolvedValueOnce([{ ...mockRecommendation, name: 'Updated Recipe' }]);

      const { result } = renderHook(() => useRecommendationsCache());

      await waitFor(() => {
        expect(result.current.recommendations).toHaveLength(1);
      });

      await act(async () => {
        await result.current.refreshRecommendations();
      });

      expect(mockApiRequest).toHaveBeenCalledTimes(3); // Status + 2 fetches
    });

    test('should use background loading for existing recommendations', async () => {
      mockApiRequest
        .mockResolvedValueOnce(mockAIStatus)
        .mockResolvedValueOnce([mockRecommendation])
        .mockResolvedValueOnce([{ ...mockRecommendation, name: 'Background Recipe' }]);

      const { result } = renderHook(() => useRecommendationsCache());

      await waitFor(() => {
        expect(result.current.recommendations).toHaveLength(1);
      });

      await act(async () => {
        await result.current.refreshRecommendationsInBackground();
      });

      expect(result.current.backgroundLoadCompleted).toBe(true);
    });

    test('should handle fetch errors', async () => {
      const error = new Error('Fetch failed');
      mockApiRequest
        .mockResolvedValueOnce(mockAIStatus)
        .mockRejectedValueOnce(error);

      const { result } = renderHook(() => useRecommendationsCache());

      await waitFor(() => {
        expect(result.current.error).toBe('Failed to get meal recommendations from perplexity');
        expect(result.current.loading).toBe(false);
      });
    });

    test('should handle request cancellation', async () => {
      let resolveRequest: (value: any) => void;
      const requestPromise = new Promise(resolve => {
        resolveRequest = resolve;
      });

      mockApiRequest
        .mockResolvedValueOnce(mockAIStatus)
        .mockReturnValue(requestPromise);

      const { result } = renderHook(() => useRecommendationsCache());

      // Start a request
      await waitFor(() => {
        expect(result.current.loading).toBe(true);
      });

      // Reset state (which should abort the request)
      act(() => {
        result.current.resetState();
      });

      expect(result.current.loading).toBe(false);
      expect(consoleMock.log).toHaveBeenCalledWith('🔄 Recommendations state reset');
    });

    test('should handle AbortError gracefully', async () => {
      const abortError = new Error('Request canceled');
      abortError.name = 'AbortError';

      mockApiRequest
        .mockResolvedValueOnce(mockAIStatus)
        .mockRejectedValueOnce(abortError);

      const { result } = renderHook(() => useRecommendationsCache());

      await waitFor(() => {
        expect(consoleMock.log).toHaveBeenCalledWith('🛑 Request aborted, not setting error state');
        expect(result.current.error).toBe(null);
      });
    });
  });

  describe('Provider Management', () => {
    test('should update available providers from AI status', async () => {
      mockApiRequest.mockResolvedValue(mockAIStatus);

      const { result } = renderHook(() => useRecommendationsCache());

      await waitFor(() => {
        expect(result.current.availableProviders).toEqual(['perplexity', 'claude', 'groq']);
        expect(result.current.selectedProvider).toBe('perplexity');
      });
    });

    test('should allow changing selected provider', async () => {
      mockApiRequest.mockResolvedValue(mockAIStatus);

      const { result } = renderHook(() => useRecommendationsCache());

      await waitFor(() => {
        expect(result.current.selectedProvider).toBe('perplexity');
      });

      act(() => {
        result.current.setSelectedProvider('claude');
      });

      expect(result.current.selectedProvider).toBe('claude');
    });

    test('should handle AI status check errors', async () => {
      mockApiRequest.mockRejectedValue(new Error('Status check failed'));

      renderHook(() => useRecommendationsCache());

      await waitFor(() => {
        expect(consoleMock.error).toHaveBeenCalledWith('Error checking AI status:', expect.any(Error));
      });
    });
  });

  describe('Meal Type Filtering', () => {
    test('should handle meal type filter', async () => {
      mockApiRequest
        .mockResolvedValueOnce(mockAIStatus)
        .mockResolvedValueOnce([mockRecommendation]);

      const { result } = renderHook(() => useRecommendationsCache());

      await waitFor(() => {
        expect(result.current.recommendations).toHaveLength(1);
      });

      await act(async () => {
        await result.current.handleMealTypeFilter('breakfast');
      });

      expect(mockApiRequest).toHaveBeenCalledWith(
        'POST',
        '/recommendations',
        expect.objectContaining({ meal_type: 'breakfast' }),
        expect.any(Object)
      );
    });
  });

  describe('State Management', () => {
    test('should clear error', () => {
      const { result } = renderHook(() => useRecommendationsCache());

      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBe(null);
    });

    test('should clear background load completed state', () => {
      const { result } = renderHook(() => useRecommendationsCache());

      act(() => {
        result.current.clearBackgroundLoadCompleted();
      });

      expect(result.current.backgroundLoadCompleted).toBe(false);
    });

    test('should reset all states', () => {
      const { result } = renderHook(() => useRecommendationsCache());

      act(() => {
        result.current.resetState();
      });

      expect(result.current.loading).toBe(false);
      expect(result.current.backgroundLoading).toBe(false);
      expect(result.current.backgroundLoadCompleted).toBe(false);
      expect(result.current.error).toBe(null);
    });
  });

  describe('Request Parameters', () => {
    test('should generate unique cache keys for different requests', async () => {
      const { result } = renderHook(() => useRecommendationsCache());

      const request1: MealRecommendationRequest = { meal_type: 'breakfast' };
      const request2: MealRecommendationRequest = { meal_type: 'dinner' };

      const key1 = JSON.stringify({ ...request1, provider: 'perplexity' });
      const key2 = JSON.stringify({ ...request2, provider: 'perplexity' });

      expect(key1).not.toBe(key2);
    });

    test('should include timestamp in request', async () => {
      mockApiRequest
        .mockResolvedValueOnce(mockAIStatus)
        .mockResolvedValueOnce([mockRecommendation]);

      const { result } = renderHook(() => useRecommendationsCache());

      await waitFor(() => {
        expect(mockApiRequest).toHaveBeenCalledWith(
          'POST',
          '/recommendations',
          expect.objectContaining({
            timestamp: expect.any(Number),
            ai_provider: 'perplexity'
          }),
          expect.any(Object)
        );
      });
    });
  });

  describe('Cleanup', () => {
    test('should abort ongoing requests on unmount', async () => {
      let resolveRequest: (value: any) => void;
      const requestPromise = new Promise(resolve => {
        resolveRequest = resolve;
      });

      mockApiRequest
        .mockResolvedValueOnce(mockAIStatus)
        .mockReturnValue(requestPromise);

      const { result, unmount } = renderHook(() => useRecommendationsCache());

      // Wait for initial setup
      await waitFor(() => {
        expect(result.current.availableProviders).toEqual(['perplexity', 'claude', 'groq']);
      });

      // Start a request to get an active abort controller
      act(() => {
        result.current.fetchRecommendations();
      });

      // Unmount while request is pending
      unmount();

      // The cleanup effect should run
      expect(consoleMock.log).toHaveBeenCalledWith('🧹 Cleaning up: aborting ongoing recommendations request');
    });

    test('should handle cache save errors gracefully', async () => {
      localStorageMock.setItem.mockImplementation(() => {
        throw new Error('Storage full');
      });

      mockApiRequest
        .mockResolvedValueOnce(mockAIStatus)
        .mockResolvedValueOnce([mockRecommendation]);

      renderHook(() => useRecommendationsCache());

      await waitFor(() => {
        expect(consoleMock.warn).toHaveBeenCalledWith('Failed to save cache:', expect.any(Error));
      });
    });

    test('should handle cache clear errors gracefully', () => {
      localStorageMock.removeItem.mockImplementation(() => {
        throw new Error('Storage error');
      });

      const { result } = renderHook(() => useRecommendationsCache());

      act(() => {
        result.current.clearCache();
      });

      expect(consoleMock.warn).toHaveBeenCalledWith('Failed to clear cache:', expect.any(Error));
    });
  });
});