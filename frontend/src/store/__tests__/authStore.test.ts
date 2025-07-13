import { useAuthStore } from '../authStore';
import { act, renderHook, waitFor } from '@testing-library/react';
import { apiRequest } from '../../services/api';

// Mock API service
jest.mock('../../services/api', () => ({
  apiRequest: jest.fn(),
}));

// Mock window.location
Object.defineProperty(window, 'location', {
  value: {
    href: '',
  },
  writable: true,
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

// Mock console methods to suppress debug logs in tests
const consoleMock = {
  log: jest.fn(),
  error: jest.fn(),
};
Object.defineProperty(console, 'log', { value: consoleMock.log });
Object.defineProperty(console, 'error', { value: consoleMock.error });

const mockApiRequest = apiRequest as jest.MockedFunction<typeof apiRequest>;

describe('AuthStore', () => {
  const mockUser = {
    id: '1',
    email: 'test@example.com',
    name: 'Test User',
    timezone: 'UTC',
    is_active: true,
    is_admin: false,
    created_at: '2024-01-01T00:00:00Z'
  };

  const mockTokens = {
    access_token: 'mock-access-token',
    refresh_token: 'mock-refresh-token',
    token_type: 'bearer',
    expires_in: 3600
  };

  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
    window.location.href = '';
    
    // Reset store state
    act(() => {
      useAuthStore.setState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      });
    });
  });

  describe('Initial State', () => {
    test('should have correct initial state', () => {
      const { result } = renderHook(() => useAuthStore());
      
      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });
  });

  describe('clearError', () => {
    test('should clear error state', () => {
      const { result } = renderHook(() => useAuthStore());
      
      act(() => {
        useAuthStore.setState({ error: 'Test error' });
      });
      
      expect(result.current.error).toBe('Test error');
      
      act(() => {
        result.current.clearError();
      });
      
      expect(result.current.error).toBeNull();
    });
  });

  describe('logout', () => {
    test('should clear user state and localStorage', () => {
      const { result } = renderHook(() => useAuthStore());
      
      // Set initial authenticated state
      act(() => {
        useAuthStore.setState({
          user: mockUser,
          isAuthenticated: true,
        });
      });
      
      expect(result.current.isAuthenticated).toBe(true);
      
      act(() => {
        result.current.logout();
      });
      
      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('refresh_token');
    });
  });

  describe('login', () => {
    test('should successfully login regular user', async () => {
      const { result } = renderHook(() => useAuthStore());
      
      mockApiRequest
        .mockResolvedValueOnce(mockTokens) // login response
        .mockResolvedValueOnce(mockUser); // /auth/me response
      
      const credentials = { email: 'test@example.com', password: 'password123' };
      
      await act(async () => {
        await result.current.login(credentials);
      });
      
      expect(mockApiRequest).toHaveBeenCalledWith('POST', '/auth/login', credentials);
      expect(mockApiRequest).toHaveBeenCalledWith('GET', '/auth/me');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('access_token', mockTokens.access_token);
      expect(localStorageMock.setItem).toHaveBeenCalledWith('refresh_token', mockTokens.refresh_token);
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(window.location.href).toBe('/dashboard');
    });

    test('should navigate admin users to admin dashboard', async () => {
      const { result } = renderHook(() => useAuthStore());
      
      const adminUser = { ...mockUser, is_admin: true };
      mockApiRequest
        .mockResolvedValueOnce(mockTokens)
        .mockResolvedValueOnce(adminUser);
      
      const credentials = { email: 'admin@example.com', password: 'password123' };
      
      await act(async () => {
        await result.current.login(credentials);
      });
      
      expect(result.current.user).toEqual(adminUser);
      expect(window.location.href).toBe('/admin');
    });

    test('should handle login failure with error response', async () => {
      const { result } = renderHook(() => useAuthStore());
      
      const errorResponse = {
        response: {
          data: {
            detail: 'Invalid credentials'
          }
        }
      };
      mockApiRequest.mockRejectedValueOnce(errorResponse);
      
      const credentials = { email: 'wrong@example.com', password: 'wrongpass' };
      
      await act(async () => {
        await result.current.login(credentials);
      });
      
      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBe('Invalid credentials');
      expect(localStorageMock.setItem).not.toHaveBeenCalled();
    });

    test('should handle login failure without error response', async () => {
      const { result } = renderHook(() => useAuthStore());
      
      mockApiRequest.mockRejectedValueOnce(new Error('Network error'));
      
      const credentials = { email: 'test@example.com', password: 'password123' };
      
      await act(async () => {
        await result.current.login(credentials);
      });
      
      expect(result.current.error).toBe('Login failed');
      expect(result.current.isLoading).toBe(false);
    });

    test('should set loading state during login', async () => {
      const { result } = renderHook(() => useAuthStore());
      
      let resolveLogin: (value: any) => void;
      const loginPromise = new Promise((resolve) => {
        resolveLogin = resolve;
      });
      mockApiRequest.mockReturnValueOnce(loginPromise);
      
      const credentials = { email: 'test@example.com', password: 'password123' };
      
      act(() => {
        result.current.login(credentials);
      });
      
      expect(result.current.isLoading).toBe(true);
      expect(result.current.error).toBeNull();
      
      await act(async () => {
        resolveLogin!(mockTokens);
        await loginPromise;
      });
    });
  });

  describe('register', () => {
    test('should successfully register user', async () => {
      const { result } = renderHook(() => useAuthStore());
      
      // Set up token in localStorage for checkAuth
      localStorageMock.getItem.mockReturnValue('mock-token');
      
      mockApiRequest
        .mockResolvedValueOnce(mockTokens) // register response
        .mockResolvedValueOnce(mockUser); // checkAuth -> /auth/me response
      
      const userData = {
        email: 'new@example.com',
        password: 'password123',
        name: 'New User'
      };
      
      await act(async () => {
        await result.current.register(userData);
      });
      
      expect(mockApiRequest).toHaveBeenNthCalledWith(1, 'POST', '/auth/register', userData);
      expect(mockApiRequest).toHaveBeenNthCalledWith(2, 'GET', '/auth/me');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('access_token', mockTokens.access_token);
      expect(localStorageMock.setItem).toHaveBeenCalledWith('refresh_token', mockTokens.refresh_token);
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.isLoading).toBe(false);
    });

    test('should handle registration failure with error response', async () => {
      const { result } = renderHook(() => useAuthStore());
      
      const errorResponse = {
        response: {
          data: {
            detail: 'Email already exists'
          }
        }
      };
      mockApiRequest.mockRejectedValueOnce(errorResponse);
      
      const userData = {
        email: 'existing@example.com',
        password: 'password123',
        name: 'Test User'
      };
      
      await act(async () => {
        await result.current.register(userData);
      });
      
      expect(result.current.error).toBe('Email already exists');
      expect(result.current.isLoading).toBe(false);
      expect(localStorageMock.setItem).not.toHaveBeenCalled();
    });

    test('should handle registration failure with generic error', async () => {
      const { result } = renderHook(() => useAuthStore());
      
      const error = new Error('Network connection failed');
      mockApiRequest.mockRejectedValueOnce(error);
      
      const userData = {
        email: 'test@example.com',
        password: 'password123',
        name: 'Test User'
      };
      
      await act(async () => {
        await result.current.register(userData);
      });
      
      expect(result.current.error).toBe('Network connection failed');
    });

    test('should fallback to "Registration failed" for unknown errors', async () => {
      const { result } = renderHook(() => useAuthStore());
      
      mockApiRequest.mockRejectedValueOnce({});
      
      const userData = {
        email: 'test@example.com',
        password: 'password123',
        name: 'Test User'
      };
      
      await act(async () => {
        await result.current.register(userData);
      });
      
      expect(result.current.error).toBe('Registration failed');
    });
  });

  describe('checkAuth', () => {
    test('should set unauthenticated when no token exists', async () => {
      const { result } = renderHook(() => useAuthStore());
      
      localStorageMock.getItem.mockReturnValue(null);
      
      await act(async () => {
        await result.current.checkAuth();
      });
      
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(result.current.isLoading).toBe(false);
      expect(mockApiRequest).not.toHaveBeenCalled();
    });

    test('should successfully validate existing token', async () => {
      const { result } = renderHook(() => useAuthStore());
      
      localStorageMock.getItem.mockReturnValue('valid-token');
      mockApiRequest.mockResolvedValueOnce(mockUser);
      
      await act(async () => {
        await result.current.checkAuth();
      });
      
      expect(mockApiRequest).toHaveBeenCalledWith('GET', '/auth/me');
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    test('should logout on invalid token (401 with specific error)', async () => {
      const { result } = renderHook(() => useAuthStore());
      
      localStorageMock.getItem.mockReturnValue('invalid-token');
      const error = {
        response: {
          status: 401,
          data: {
            detail: 'Invalid token'
          }
        }
      };
      mockApiRequest.mockRejectedValueOnce(error);
      
      await act(async () => {
        await result.current.checkAuth();
      });
      
      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('refresh_token');
    });

    test('should logout on user not found (401)', async () => {
      const { result } = renderHook(() => useAuthStore());
      
      localStorageMock.getItem.mockReturnValue('token-for-deleted-user');
      const error = {
        response: {
          status: 401,
          data: {
            detail: 'User not found'
          }
        }
      };
      mockApiRequest.mockRejectedValueOnce(error);
      
      await act(async () => {
        await result.current.checkAuth();
      });
      
      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });

    test('should not logout on network errors', async () => {
      const { result } = renderHook(() => useAuthStore());
      
      // Set initial authenticated state
      act(() => {
        useAuthStore.setState({
          user: mockUser,
          isAuthenticated: true,
        });
      });
      
      localStorageMock.getItem.mockReturnValue('valid-token');
      const networkError = {
        response: {
          status: 500,
          data: {
            detail: 'Internal server error'
          }
        }
      };
      mockApiRequest.mockRejectedValueOnce(networkError);
      
      await act(async () => {
        await result.current.checkAuth();
      });
      
      expect(result.current.user).toEqual(mockUser); // User should remain
      expect(result.current.isAuthenticated).toBe(true); // Should stay authenticated
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBe('Connection issue - please refresh');
      expect(localStorageMock.removeItem).not.toHaveBeenCalled();
    });

    test('should set loading state during auth check', async () => {
      const { result } = renderHook(() => useAuthStore());
      
      localStorageMock.getItem.mockReturnValue('token');
      
      let resolveAuth: (value: any) => void;
      const authPromise = new Promise((resolve) => {
        resolveAuth = resolve;
      });
      mockApiRequest.mockReturnValueOnce(authPromise);
      
      act(() => {
        result.current.checkAuth();
      });
      
      expect(result.current.isLoading).toBe(true);
      
      await act(async () => {
        resolveAuth!(mockUser);
        await authPromise;
      });
      
      expect(result.current.isLoading).toBe(false);
    });
  });
});