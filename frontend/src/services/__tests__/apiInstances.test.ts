import { navigationApi, dataApi, recommendationsApi, getApiInstance } from '../apiInstances';

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

// Mock window.location
Object.defineProperty(window, 'location', {
  value: {
    href: '',
  },
  writable: true,
});

describe('API Instances', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
    window.location.href = '';
  });

  describe('Instance Configuration', () => {
    test('navigationApi should be configured correctly', () => {
      expect(navigationApi.defaults.baseURL).toMatch(/\/api\/v1$/);
      expect(navigationApi.defaults.timeout).toBe(10000); // 10 seconds
      expect(navigationApi.defaults.headers['Content-Type']).toBe('application/json');
    });

    test('dataApi should be configured correctly', () => {
      expect(dataApi.defaults.baseURL).toMatch(/\/api\/v1$/);
      expect(dataApi.defaults.timeout).toBe(60000); // 60 seconds
      expect(dataApi.defaults.headers['Content-Type']).toBe('application/json');
    });

    test('recommendationsApi should be configured correctly', () => {
      expect(recommendationsApi.defaults.baseURL).toMatch(/\/api\/v1$/);
      expect(recommendationsApi.defaults.timeout).toBe(300000); // 5 minutes
      expect(recommendationsApi.defaults.headers['Content-Type']).toBe('application/json');
    });

    test('all instances should use same base URL', () => {
      const baseUrl = navigationApi.defaults.baseURL;
      expect(dataApi.defaults.baseURL).toBe(baseUrl);
      expect(recommendationsApi.defaults.baseURL).toBe(baseUrl);
    });

    test('instances should have different timeout values', () => {
      expect(navigationApi.defaults.timeout).toBeLessThan(dataApi.defaults.timeout!);
      expect(dataApi.defaults.timeout).toBeLessThan(recommendationsApi.defaults.timeout!);
    });
  });

  describe('Request Interceptors', () => {
    test('should add Authorization header when token exists', () => {
      localStorageMock.getItem.mockReturnValue('test-token');

      // Test navigationApi interceptor
      const navigationInterceptor = navigationApi.interceptors.request;
      expect(navigationInterceptor).toBeDefined();

      // Mock config object
      const config = {
        headers: {},
      };

      // Get the interceptor function (should be the first one added)
      const interceptorFn = (navigationInterceptor as any).handlers[0]?.fulfilled;
      expect(interceptorFn).toBeDefined();

      const result = interceptorFn(config);
      expect(result.headers.Authorization).toBe('Bearer test-token');
    });

    test('should not add Authorization header when no token exists', () => {
      localStorageMock.getItem.mockReturnValue(null);

      const config = {
        headers: {},
      };

      const interceptorFn = (navigationApi.interceptors.request as any).handlers[0]?.fulfilled;
      const result = interceptorFn(config);
      expect(result.headers.Authorization).toBeUndefined();
    });

    test('should preserve existing headers', () => {
      localStorageMock.getItem.mockReturnValue('test-token');

      const config = {
        headers: {
          'Custom-Header': 'custom-value',
          'Content-Type': 'multipart/form-data',
        },
      };

      const interceptorFn = (navigationApi.interceptors.request as any).handlers[0]?.fulfilled;
      const result = interceptorFn(config);
      
      expect(result.headers['Custom-Header']).toBe('custom-value');
      expect(result.headers['Content-Type']).toBe('multipart/form-data');
      expect(result.headers.Authorization).toBe('Bearer test-token');
    });
  });

  describe('Response Interceptors', () => {
    test('should pass through successful responses', () => {
      const response = { status: 200, data: { success: true } };
      
      const responseInterceptor = (navigationApi.interceptors.response as any).handlers[0]?.fulfilled;
      const result = responseInterceptor(response);
      
      expect(result).toBe(response);
    });

    test('should handle canceled requests without redirect', async () => {
      const cancelError = new Error('Request canceled') as Error & { code: string };
      cancelError.code = 'ERR_CANCELED';

      const errorInterceptor = (navigationApi.interceptors.response as any).handlers[0]?.rejected;
      
      await expect(errorInterceptor(cancelError)).rejects.toEqual(cancelError);
      expect(window.location.href).toBe('');
    });

    test('should handle abort errors without redirect', async () => {
      const abortError = new Error('canceled');
      abortError.name = 'AbortError';

      const errorInterceptor = (navigationApi.interceptors.response as any).handlers[0]?.rejected;
      
      await expect(errorInterceptor(abortError)).rejects.toEqual(abortError);
      expect(window.location.href).toBe('');
    });

    test('should redirect on invalid token error', async () => {
      const authError = {
        response: {
          status: 401,
          data: {
            detail: 'Invalid token'
          }
        }
      };

      const errorInterceptor = (navigationApi.interceptors.response as any).handlers[0]?.rejected;
      
      await expect(errorInterceptor(authError)).rejects.toEqual(authError);
      
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('refresh_token');
      expect(window.location.href).toBe('/login');
    });

    test('should redirect on user not found error', async () => {
      const authError = {
        response: {
          status: 401,
          data: {
            detail: 'User not found'
          }
        }
      };

      const errorInterceptor = (dataApi.interceptors.response as any).handlers[0]?.rejected;
      
      await expect(errorInterceptor(authError)).rejects.toEqual(authError);
      
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('refresh_token');
      expect(window.location.href).toBe('/login');
    });

    test('should not redirect on other 401 errors', async () => {
      const authError = {
        response: {
          status: 401,
          data: {
            detail: 'Unauthorized access'
          }
        }
      };

      const errorInterceptor = (recommendationsApi.interceptors.response as any).handlers[0]?.rejected;
      
      await expect(errorInterceptor(authError)).rejects.toEqual(authError);
      
      expect(localStorageMock.removeItem).not.toHaveBeenCalled();
      expect(window.location.href).toBe('');
    });

    test('should not redirect on non-401 errors', async () => {
      const serverError = {
        response: {
          status: 500,
          data: {
            detail: 'Internal server error'
          }
        }
      };

      const errorInterceptor = (dataApi.interceptors.response as any).handlers[0]?.rejected;
      
      await expect(errorInterceptor(serverError)).rejects.toEqual(serverError);
      
      expect(localStorageMock.removeItem).not.toHaveBeenCalled();
      expect(window.location.href).toBe('');
    });

    test('should handle errors without response data', async () => {
      const networkError = new Error('Network Error');

      const errorInterceptor = (navigationApi.interceptors.response as any).handlers[0]?.rejected;
      
      await expect(errorInterceptor(networkError)).rejects.toEqual(networkError);
      
      expect(localStorageMock.removeItem).not.toHaveBeenCalled();
      expect(window.location.href).toBe('');
    });
  });

  describe('getApiInstance Function', () => {
    test('should return dataApi by default', () => {
      const instance = getApiInstance();
      expect(instance).toBe(dataApi);
    });

    test('should return dataApi for "data" request type', () => {
      const instance = getApiInstance('data');
      expect(instance).toBe(dataApi);
    });

    test('should return navigationApi for "navigation" request type', () => {
      const instance = getApiInstance('navigation');
      expect(instance).toBe(navigationApi);
    });

    test('should return recommendationsApi for "recommendations" request type', () => {
      const instance = getApiInstance('recommendations');
      expect(instance).toBe(recommendationsApi);
    });

    test('should return dataApi for invalid request type', () => {
      const instance = getApiInstance('invalid' as any);
      expect(instance).toBe(dataApi);
    });

    test('should return dataApi for undefined request type', () => {
      const instance = getApiInstance(undefined);
      expect(instance).toBe(dataApi);
    });
  });

  describe('Interceptor Application', () => {
    test('all instances should have request interceptors', () => {
      expect((navigationApi.interceptors.request as any).handlers).toHaveLength(1);
      expect((dataApi.interceptors.request as any).handlers).toHaveLength(1);
      expect((recommendationsApi.interceptors.request as any).handlers).toHaveLength(1);
    });

    test('all instances should have response interceptors', () => {
      expect((navigationApi.interceptors.response as any).handlers).toHaveLength(1);
      expect((dataApi.interceptors.response as any).handlers).toHaveLength(1);
      expect((recommendationsApi.interceptors.response as any).handlers).toHaveLength(1);
    });

    test('interceptors should work consistently across all instances', () => {
      localStorageMock.getItem.mockReturnValue('consistent-token');

      const instances = [navigationApi, dataApi, recommendationsApi];
      
      instances.forEach(instance => {
        const config = { headers: {} };
        const interceptorFn = (instance.interceptors.request as any).handlers[0]?.fulfilled;
        const result = interceptorFn(config);
        
        expect(result.headers.Authorization).toBe('Bearer consistent-token');
      });
    });
  });

  describe('Environment Configuration', () => {
    test('should use environment variable for base URL when available', () => {
      // The baseURL should be constructed from environment variables
      expect(navigationApi.defaults.baseURL).toBeDefined();
      expect(dataApi.defaults.baseURL).toBeDefined();
      expect(recommendationsApi.defaults.baseURL).toBeDefined();
    });

    test('should fallback to localhost when environment variable not set', () => {
      // When no REACT_APP_API_URL is set, should use localhost:8001
      const baseUrl = navigationApi.defaults.baseURL;
      if (!process.env.REACT_APP_API_URL) {
        expect(baseUrl).toContain('localhost:8001');
      }
    });
  });

  describe('Timeout Configuration', () => {
    test('timeout values should be appropriate for each use case', () => {
      // Navigation should be fastest (10s)
      expect(navigationApi.defaults.timeout).toBe(10000);
      
      // Data requests should be moderate (60s)
      expect(dataApi.defaults.timeout).toBe(60000);
      
      // AI recommendations should be longest (300s)
      expect(recommendationsApi.defaults.timeout).toBe(300000);
    });

    test('timeout hierarchy should be navigation < data < recommendations', () => {
      const navTimeout = navigationApi.defaults.timeout!;
      const dataTimeout = dataApi.defaults.timeout!;
      const recTimeout = recommendationsApi.defaults.timeout!;
      
      expect(navTimeout).toBeLessThan(dataTimeout);
      expect(dataTimeout).toBeLessThan(recTimeout);
    });
  });

  describe('Headers Configuration', () => {
    test('all instances should have JSON content type by default', () => {
      expect(navigationApi.defaults.headers['Content-Type']).toBe('application/json');
      expect(dataApi.defaults.headers['Content-Type']).toBe('application/json');
      expect(recommendationsApi.defaults.headers['Content-Type']).toBe('application/json');
    });

    test('headers should be consistent across instances', () => {
      const navHeaders = navigationApi.defaults.headers;
      const dataHeaders = dataApi.defaults.headers;
      const recHeaders = recommendationsApi.defaults.headers;
      
      expect(navHeaders['Content-Type']).toBe(dataHeaders['Content-Type']);
      expect(dataHeaders['Content-Type']).toBe(recHeaders['Content-Type']);
    });
  });
});