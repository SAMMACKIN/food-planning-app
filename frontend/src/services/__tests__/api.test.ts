import { api, apiRequest } from '../api';
import { navigationApi, dataApi, recommendationsApi, getApiInstance } from '../apiInstances';
import { apiDebugger } from '../../utils/debugApi';

// Mock apiDebugger
jest.mock('../../utils/debugApi', () => ({
  apiDebugger: {
    startRequest: jest.fn().mockReturnValue('mock-request-id'),
    endRequest: jest.fn(),
    cancelRequest: jest.fn(),
  },
}));

// Mock axios instances
jest.mock('../apiInstances', () => {
  const mockAxiosInstance = {
    request: jest.fn(),
    defaults: {
      baseURL: 'http://localhost:8001/api/v1',
      headers: {
        'Content-Type': 'application/json',
      },
    },
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
  };

  return {
    navigationApi: mockAxiosInstance,
    dataApi: mockAxiosInstance,
    recommendationsApi: mockAxiosInstance,
    getApiInstance: jest.fn().mockReturnValue(mockAxiosInstance),
  };
});

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
};
Object.defineProperty(console, 'log', { value: consoleMock.log });
Object.defineProperty(console, 'error', { value: consoleMock.error });

// Mock environment variable
const originalEnv = process.env;

const mockApiDebugger = apiDebugger as jest.Mocked<typeof apiDebugger>;
const mockDataApi = dataApi as jest.Mocked<typeof dataApi>;
const mockNavigationApi = navigationApi as jest.Mocked<typeof navigationApi>;
const mockRecommendationsApi = recommendationsApi as jest.Mocked<typeof recommendationsApi>;
const mockGetApiInstance = getApiInstance as jest.MockedFunction<typeof getApiInstance>;

describe('API Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
    consoleMock.log.mockClear();
    consoleMock.error.mockClear();
  });

  afterAll(() => {
    process.env = originalEnv;
  });

  describe('Basic Configuration', () => {
    test('api instance is defined and properly configured', () => {
      expect(api).toBeDefined();
      expect(api.defaults).toBeDefined();
      expect(api.defaults.baseURL).toContain('/api/v1');
    });

    test('api has correct content type header', () => {
      expect(api.defaults.headers['Content-Type']).toBe('application/json');
    });

    test('api has interceptors configured', () => {
      expect(api.interceptors).toBeDefined();
      expect(api.interceptors.request).toBeDefined();
      expect(api.interceptors.response).toBeDefined();
    });

    test('api uses correct base URL from environment', () => {
      expect(api.defaults.baseURL).toMatch(/\/api\/v1$/);
    });
  });

  describe('apiRequest Function', () => {
    const mockResponseData = { id: 1, name: 'Test Data' };

    beforeEach(() => {
      mockDataApi.request.mockResolvedValue({ data: mockResponseData });
    });

    test('should make successful GET request', async () => {
      const result = await apiRequest('GET', '/test');

      expect(mockApiDebugger.startRequest).toHaveBeenCalledWith('GET /test');
      expect(mockDataApi.request).toHaveBeenCalledWith({
        method: 'GET',
        url: '/test',
        data: undefined,
        signal: undefined,
      });
      expect(mockApiDebugger.endRequest).toHaveBeenCalledWith('mock-request-id', true);
      expect(result).toEqual(mockResponseData);
    });

    test('should make successful POST request with data', async () => {
      const postData = { name: 'New Item' };
      const result = await apiRequest('POST', '/items', postData);

      expect(mockDataApi.request).toHaveBeenCalledWith({
        method: 'POST',
        url: '/items',
        data: postData,
        signal: undefined,
      });
      expect(result).toEqual(mockResponseData);
    });

    test('should include abort signal when provided', async () => {
      const abortController = new AbortController();
      await apiRequest('GET', '/test', undefined, { signal: abortController.signal });

      expect(mockDataApi.request).toHaveBeenCalledWith({
        method: 'GET',
        url: '/test',
        data: undefined,
        signal: abortController.signal,
      });
    });

    test('should use navigation API for navigation requests', async () => {
      mockGetApiInstance.mockReturnValue(mockNavigationApi);
      
      await apiRequest('GET', '/auth/me', undefined, { requestType: 'navigation' });

      expect(mockNavigationApi.request).toHaveBeenCalled();
    });

    test('should use recommendations API for recommendation requests', async () => {
      mockGetApiInstance.mockReturnValue(mockRecommendationsApi);
      
      await apiRequest('POST', '/recommendations', {}, { requestType: 'recommendations' });

      expect(mockRecommendationsApi.request).toHaveBeenCalled();
    });

    test('should auto-detect recommendations API from URL', async () => {
      mockGetApiInstance.mockReturnValue(mockRecommendationsApi);
      
      await apiRequest('GET', '/recommendations/status');

      expect(mockRecommendationsApi.request).toHaveBeenCalled();
    });

    test('should log request details', async () => {
      localStorageMock.getItem.mockReturnValue('mock-token');
      
      await apiRequest('POST', '/test', { data: 'test' });

      expect(consoleMock.log).toHaveBeenCalledWith(
        expect.stringContaining('🚀 Making POST request'),
        { data: 'test' }
      );
      expect(consoleMock.log).toHaveBeenCalledWith(
        '🔑 Authorization token available:',
        'Yes'
      );
    });

    test('should log when no token is available', async () => {
      localStorageMock.getItem.mockReturnValue(null);
      
      await apiRequest('GET', '/test');

      expect(consoleMock.log).toHaveBeenCalledWith(
        '🔑 Authorization token available:',
        'No'
      );
    });
  });

  describe('Error Handling', () => {
    test('should handle network errors', async () => {
      const networkError = new Error('Network Error');
      mockDataApi.request.mockRejectedValue(networkError);

      await expect(apiRequest('GET', '/test')).rejects.toThrow('Network Error');
      
      expect(mockApiDebugger.endRequest).toHaveBeenCalledWith('mock-request-id', false);
      expect(consoleMock.error).toHaveBeenCalledWith(
        '❌ API Error details:',
        expect.objectContaining({
          status: undefined,
          data: undefined,
          headers: undefined,
          url: undefined,
          method: undefined
        })
      );
    });

    test('should handle HTTP errors with response data', async () => {
      const httpError = {
        response: {
          status: 400,
          data: { detail: 'Validation error' },
          headers: { 'content-type': 'application/json' },
        },
        config: {
          url: '/test',
          method: 'post',
        },
      };
      mockDataApi.request.mockRejectedValue(httpError);

      await expect(apiRequest('POST', '/test')).rejects.toEqual(httpError);
      
      expect(consoleMock.error).toHaveBeenCalledWith(
        '❌ API Error details:',
        expect.objectContaining({
          status: 400,
          data: { detail: 'Validation error' },
          headers: { 'content-type': 'application/json' },
          url: '/test',
          method: 'post',
        })
      );
    });

    test('should handle abort errors gracefully', async () => {
      const abortError = new Error('canceled');
      abortError.name = 'AbortError';
      mockDataApi.request.mockRejectedValue(abortError);

      await expect(apiRequest('GET', '/test')).rejects.toThrow('canceled');
      
      expect(mockApiDebugger.cancelRequest).toHaveBeenCalledWith('mock-request-id');
      expect(consoleMock.log).toHaveBeenCalledWith('🛑 Request was cancelled');
      expect(consoleMock.error).not.toHaveBeenCalled();
    });

    test('should handle ERR_CANCELED errors', async () => {
      const cancelError = new Error('Request canceled');
      cancelError.code = 'ERR_CANCELED';
      mockDataApi.request.mockRejectedValue(cancelError);

      await expect(apiRequest('GET', '/test')).rejects.toThrow('Request canceled');
      
      expect(mockApiDebugger.cancelRequest).toHaveBeenCalledWith('mock-request-id');
      expect(consoleMock.log).toHaveBeenCalledWith('🛑 Request was cancelled');
    });
  });

  describe('Request Type Selection', () => {
    test('should default to data API when no request type specified', async () => {
      mockGetApiInstance.mockReturnValue(mockDataApi);
      
      await apiRequest('GET', '/test');

      expect(mockDataApi.request).toHaveBeenCalled();
    });

    test('should use navigation API for urgent requests', async () => {
      mockGetApiInstance.mockReturnValue(mockNavigationApi);
      
      await apiRequest('GET', '/auth/logout', undefined, { requestType: 'navigation' });

      expect(mockNavigationApi.request).toHaveBeenCalled();
    });

    test('should use recommendations API for AI requests', async () => {
      mockGetApiInstance.mockReturnValue(mockRecommendationsApi);
      
      await apiRequest('POST', '/ai/recommendations', {}, { requestType: 'recommendations' });

      expect(mockRecommendationsApi.request).toHaveBeenCalled();
    });

    test('should prioritize explicit requestType over URL detection', async () => {
      mockGetApiInstance.mockReturnValue(mockNavigationApi);
      
      // URL contains 'recommendations' but explicit type is 'navigation'
      await apiRequest('GET', '/recommendations/cancel', undefined, { requestType: 'navigation' });

      expect(mockNavigationApi.request).toHaveBeenCalled();
    });
  });

  describe('Integration with API Debugger', () => {
    test('should start and end request tracking', async () => {
      await apiRequest('GET', '/test');

      expect(mockApiDebugger.startRequest).toHaveBeenCalledWith('GET /test');
      expect(mockApiDebugger.endRequest).toHaveBeenCalledWith('mock-request-id', true);
    });

    test('should mark request as failed on error', async () => {
      mockDataApi.request.mockRejectedValue(new Error('Test error'));

      await expect(apiRequest('GET', '/test')).rejects.toThrow('Test error');
      
      expect(mockApiDebugger.endRequest).toHaveBeenCalledWith('mock-request-id', false);
    });

    test('should cancel request tracking on abort', async () => {
      const abortError = new Error('canceled');
      abortError.name = 'AbortError';
      mockDataApi.request.mockRejectedValue(abortError);

      await expect(apiRequest('GET', '/test')).rejects.toThrow('canceled');
      
      expect(mockApiDebugger.cancelRequest).toHaveBeenCalledWith('mock-request-id');
      expect(mockApiDebugger.endRequest).not.toHaveBeenCalled();
    });
  });

  describe('HTTP Methods', () => {
    test('should support all HTTP methods', async () => {
      const methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'] as const;
      
      for (const method of methods) {
        mockDataApi.request.mockResolvedValue({ data: { method } });
        
        const result = await apiRequest(method, '/test', { test: 'data' });
        
        expect(mockDataApi.request).toHaveBeenCalledWith({
          method,
          url: '/test',
          data: { test: 'data' },
          signal: undefined,
        });
        expect(result).toEqual({ method });
      }
    });
  });

  describe('Configuration Options', () => {
    test('should pass through all config options', async () => {
      const abortController = new AbortController();
      const config = {
        signal: abortController.signal,
        requestType: 'recommendations' as const,
      };
      
      mockGetApiInstance.mockReturnValue(mockRecommendationsApi);
      
      await apiRequest('POST', '/test', { data: 'test' }, config);

      expect(mockRecommendationsApi.request).toHaveBeenCalledWith({
        method: 'POST',
        url: '/test',
        data: { data: 'test' },
        signal: abortController.signal,
      });
    });

    test('should work with minimal parameters', async () => {
      mockDataApi.request.mockResolvedValue({ data: 'success' });
      
      const result = await apiRequest('GET', '/simple');

      expect(result).toBe('success');
      expect(mockDataApi.request).toHaveBeenCalledWith({
        method: 'GET',
        url: '/simple',
        data: undefined,
        signal: undefined,
      });
    });
  });
});