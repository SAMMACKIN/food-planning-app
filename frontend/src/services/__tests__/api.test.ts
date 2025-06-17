import axios from 'axios';
import { api, apiRequest } from '../api';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

// Mock window.location
delete (window as any).location;
window.location = { href: '' } as any;

describe('API Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Reset axios create mock
    mockedAxios.create.mockReturnValue({
      request: jest.fn(),
      interceptors: {
        request: { use: jest.fn() },
        response: { use: jest.fn() },
      },
      defaults: {
        baseURL: 'http://localhost:8001/api/v1',
        headers: {},
      },
    } as any);
  });

  test('creates axios instance with correct config', () => {
    expect(mockedAxios.create).toHaveBeenCalledWith({
      baseURL: 'http://localhost:8001/api/v1',
      headers: {
        'Content-Type': 'application/json',
      },
    });
  });

  test('uses custom API URL from environment', () => {
    const originalEnv = process.env.REACT_APP_API_URL;
    process.env.REACT_APP_API_URL = 'https://api.example.com';
    
    // Re-import to get new environment variable
    jest.resetModules();
    require('../api');
    
    expect(mockedAxios.create).toHaveBeenCalledWith({
      baseURL: 'https://api.example.com/api/v1',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    // Restore original environment
    process.env.REACT_APP_API_URL = originalEnv;
  });

  describe('Request Interceptor', () => {
    let requestInterceptor: (config: any) => any;

    beforeEach(() => {
      const mockApi = {
        interceptors: {
          request: { use: jest.fn() },
          response: { use: jest.fn() },
        },
        defaults: { baseURL: 'http://localhost:8001/api/v1' },
      };
      
      mockedAxios.create.mockReturnValue(mockApi as any);
      
      // Re-import to set up interceptors
      jest.resetModules();
      require('../api');
      
      // Get the request interceptor
      requestInterceptor = mockApi.interceptors.request.use.mock.calls[0][0];
    });

    test('adds authorization header when token exists', () => {
      mockLocalStorage.getItem.mockReturnValue('test-token');
      
      const config = {
        headers: {},
        url: '/test',
      };
      
      const result = requestInterceptor(config);
      
      expect(mockLocalStorage.getItem).toHaveBeenCalledWith('access_token');
      expect(result.headers.Authorization).toBe('Bearer test-token');
    });

    test('does not add authorization header when token is missing', () => {
      mockLocalStorage.getItem.mockReturnValue(null);
      
      const config = {
        headers: {},
        url: '/test',
      };
      
      const result = requestInterceptor(config);
      
      expect(result.headers.Authorization).toBeUndefined();
    });
  });

  describe('Response Interceptor', () => {
    let responseInterceptor: {
      success: (response: any) => any;
      error: (error: any) => Promise<any>;
    };

    beforeEach(() => {
      const mockApi = {
        interceptors: {
          request: { use: jest.fn() },
          response: { use: jest.fn() },
        },
        defaults: { baseURL: 'http://localhost:8001/api/v1' },
      };
      
      mockedAxios.create.mockReturnValue(mockApi as any);
      
      // Re-import to set up interceptors
      jest.resetModules();
      require('../api');
      
      // Get the response interceptor
      const responseInterceptorCall = mockApi.interceptors.response.use.mock.calls[0];
      responseInterceptor = {
        success: responseInterceptorCall[0],
        error: responseInterceptorCall[1],
      };
    });

    test('passes through successful responses', () => {
      const response = { data: 'test', status: 200 };
      const result = responseInterceptor.success(response);
      
      expect(result).toBe(response);
    });

    test('clears tokens and redirects on invalid token 401', async () => {
      const error = {
        response: {
          status: 401,
          data: { detail: 'Invalid token' },
        },
      };
      
      await expect(responseInterceptor.error(error)).rejects.toEqual(error);
      
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('access_token');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('refresh_token');
      expect(window.location.href).toBe('/login');
    });

    test('clears tokens and redirects on user not found 401', async () => {
      const error = {
        response: {
          status: 401,
          data: { detail: 'User not found' },
        },
      };
      
      await expect(responseInterceptor.error(error)).rejects.toEqual(error);
      
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('access_token');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('refresh_token');
      expect(window.location.href).toBe('/login');
    });

    test('does not clear tokens on other 401 errors', async () => {
      const error = {
        response: {
          status: 401,
          data: { detail: 'Other auth error' },
        },
      };
      
      await expect(responseInterceptor.error(error)).rejects.toEqual(error);
      
      expect(mockLocalStorage.removeItem).not.toHaveBeenCalled();
      expect(window.location.href).toBe('');
    });

    test('passes through non-401 errors', async () => {
      const error = {
        response: {
          status: 500,
          data: { detail: 'Server error' },
        },
      };
      
      await expect(responseInterceptor.error(error)).rejects.toEqual(error);
      
      expect(mockLocalStorage.removeItem).not.toHaveBeenCalled();
    });
  });

  describe('apiRequest function', () => {
    let mockApiInstance: jest.Mocked<any>;

    beforeEach(() => {
      mockApiInstance = {
        request: jest.fn(),
        defaults: {
          baseURL: 'http://localhost:8001/api/v1',
          headers: {},
        },
        interceptors: {
          request: { use: jest.fn() },
          response: { use: jest.fn() },
        },
      };
      
      mockedAxios.create.mockReturnValue(mockApiInstance);
      
      // Re-import to get fresh instance
      jest.resetModules();
    });

    test('makes GET request successfully', async () => {
      const responseData = { id: 1, name: 'Test' };
      mockApiInstance.request.mockResolvedValue({ data: responseData });
      
      const { apiRequest } = require('../api');
      const result = await apiRequest('GET', '/test');
      
      expect(mockApiInstance.request).toHaveBeenCalledWith({
        method: 'GET',
        url: '/test',
        data: undefined,
      });
      expect(result).toEqual(responseData);
    });

    test('makes POST request with data', async () => {
      const requestData = { name: 'New Item' };
      const responseData = { id: 2, name: 'New Item' };
      mockApiInstance.request.mockResolvedValue({ data: responseData });
      
      const { apiRequest } = require('../api');
      const result = await apiRequest('POST', '/items', requestData);
      
      expect(mockApiInstance.request).toHaveBeenCalledWith({
        method: 'POST',
        url: '/items',
        data: requestData,
      });
      expect(result).toEqual(responseData);
    });

    test('makes PUT request', async () => {
      const requestData = { name: 'Updated Item' };
      const responseData = { id: 1, name: 'Updated Item' };
      mockApiInstance.request.mockResolvedValue({ data: responseData });
      
      const { apiRequest } = require('../api');
      const result = await apiRequest('PUT', '/items/1', requestData);
      
      expect(mockApiInstance.request).toHaveBeenCalledWith({
        method: 'PUT',
        url: '/items/1',
        data: requestData,
      });
      expect(result).toEqual(responseData);
    });

    test('makes DELETE request', async () => {
      mockApiInstance.request.mockResolvedValue({ data: null });
      
      const { apiRequest } = require('../api');
      const result = await apiRequest('DELETE', '/items/1');
      
      expect(mockApiInstance.request).toHaveBeenCalledWith({
        method: 'DELETE',
        url: '/items/1',
        data: undefined,
      });
      expect(result).toBeNull();
    });

    test('throws error on request failure', async () => {
      const error = {
        response: {
          status: 400,
          data: { detail: 'Bad Request' },
        },
        config: {
          url: '/test',
          method: 'GET',
        },
      };
      
      mockApiInstance.request.mockRejectedValue(error);
      
      const { apiRequest } = require('../api');
      
      await expect(apiRequest('GET', '/test')).rejects.toEqual(error);
    });

    test('handles network errors', async () => {
      const error = new Error('Network Error');
      mockApiInstance.request.mockRejectedValue(error);
      
      const { apiRequest } = require('../api');
      
      await expect(apiRequest('GET', '/test')).rejects.toEqual(error);
    });

    test('logs request and response details', async () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
      const responseData = { test: 'data' };
      
      mockApiInstance.request.mockResolvedValue({ data: responseData });
      
      const { apiRequest } = require('../api');
      await apiRequest('GET', '/test');
      
      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('Making GET request'),
        undefined
      );
      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('API Response received:'),
        responseData
      );
      
      consoleSpy.mockRestore();
    });

    test('logs error details on failure', async () => {
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
      const error = {
        response: {
          status: 404,
          data: { detail: 'Not Found' },
          headers: {},
        },
        config: {
          url: '/test',
          method: 'GET',
        },
      };
      
      mockApiInstance.request.mockRejectedValue(error);
      
      const { apiRequest } = require('../api');
      
      try {
        await apiRequest('GET', '/test');
      } catch (e) {
        // Expected to throw
      }
      
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        expect.stringContaining('API Error details:'),
        expect.objectContaining({
          status: 404,
          data: { detail: 'Not Found' },
          url: '/test',
          method: 'GET',
        })
      );
      
      consoleErrorSpy.mockRestore();
    });
  });
});