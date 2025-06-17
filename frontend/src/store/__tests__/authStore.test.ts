import { act, renderHook } from '@testing-library/react';
import { useAuthStore } from '../authStore';
import { apiRequest } from '../../services/api';

// Mock dependencies
jest.mock('../../services/api');
const mockApiRequest = apiRequest as jest.MockedFunction<typeof apiRequest>;

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

describe('AuthStore', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockLocalStorage.getItem.mockReturnValue(null);
    window.location.href = '';
    
    // Reset store state
    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  });

  describe('Initial State', () => {
    test('has correct initial state', () => {
      const { result } = renderHook(() => useAuthStore());
      
      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });
  });

  describe('login', () => {
    const mockTokens = {
      access_token: 'test-access-token',
      refresh_token: 'test-refresh-token',
      token_type: 'bearer',
    };

    const mockUser = {
      id: '1',
      email: 'test@example.com',
      name: 'Test User',
      is_admin: false,
    };

    test('logs in regular user successfully', async () => {
      mockApiRequest
        .mockResolvedValueOnce(mockTokens)
        .mockResolvedValueOnce(mockUser);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.login({
          email: 'test@example.com',
          password: 'password123',
        });
      });

      expect(mockApiRequest).toHaveBeenCalledTimes(2);
      expect(mockApiRequest).toHaveBeenNthCalledWith(1, 'POST', '/auth/login', {
        email: 'test@example.com',
        password: 'password123',
      });
      expect(mockApiRequest).toHaveBeenNthCalledWith(2, 'GET', '/auth/me');

      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('access_token', 'test-access-token');
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('refresh_token', 'test-refresh-token');

      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(window.location.href).toBe('/dashboard');
    });

    test('redirects admin user to admin dashboard', async () => {
      const adminUser = { ...mockUser, is_admin: true };
      
      mockApiRequest
        .mockResolvedValueOnce(mockTokens)
        .mockResolvedValueOnce(adminUser);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.login({
          email: 'admin@example.com',
          password: 'password123',
        });
      });

      expect(result.current.user).toEqual(adminUser);
      expect(window.location.href).toBe('/admin');
    });

    test('handles login failure', async () => {
      const error = {
        response: {
          data: { detail: 'Invalid credentials' },
        },
      };

      mockApiRequest.mockRejectedValueOnce(error);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.login({
          email: 'test@example.com',
          password: 'wrongpassword',
        });
      });

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBe('Invalid credentials');
      expect(mockLocalStorage.setItem).not.toHaveBeenCalled();
    });

    test('handles network error during login', async () => {
      const error = new Error('Network error');
      mockApiRequest.mockRejectedValueOnce(error);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.login({
          email: 'test@example.com',
          password: 'password123',
        });
      });

      expect(result.current.error).toBe('Login failed');
      expect(result.current.isLoading).toBe(false);
    });

    test('sets loading state during login', async () => {
      mockApiRequest.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.login({
          email: 'test@example.com',
          password: 'password123',
        });
      });

      expect(result.current.isLoading).toBe(true);
    });
  });

  describe('register', () => {
    const mockTokens = {
      access_token: 'test-access-token',
      refresh_token: 'test-refresh-token',
      token_type: 'bearer',
    };

    const mockUser = {
      id: '1',
      email: 'newuser@example.com',
      name: 'New User',
      is_admin: false,
    };

    test('registers user successfully', async () => {
      mockApiRequest
        .mockResolvedValueOnce(mockTokens)
        .mockResolvedValueOnce(mockUser);

      const { result } = renderHook(() => useAuthStore());

      const userData = {
        email: 'newuser@example.com',
        password: 'password123',
        name: 'New User',
      };

      await act(async () => {
        await result.current.register(userData);
      });

      expect(mockApiRequest).toHaveBeenCalledWith('POST', '/auth/register', userData);
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('access_token', 'test-access-token');
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('refresh_token', 'test-refresh-token');
    });

    test('handles registration failure', async () => {
      const error = {
        response: {
          data: { detail: 'Email already registered' },
        },
      };

      mockApiRequest.mockRejectedValueOnce(error);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.register({
          email: 'existing@example.com',
          password: 'password123',
          name: 'Test User',
        });
      });

      expect(result.current.error).toBe('Email already registered');
      expect(result.current.isLoading).toBe(false);
    });

    test('handles registration network error', async () => {
      const error = new Error('Network error');
      mockApiRequest.mockRejectedValueOnce(error);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.register({
          email: 'test@example.com',
          password: 'password123',
          name: 'Test User',
        });
      });

      expect(result.current.error).toBe('Network error');
    });
  });

  describe('logout', () => {
    test('clears user data and tokens', () => {
      // Set initial authenticated state
      useAuthStore.setState({
        user: {
          id: '1',
          email: 'test@example.com',
          name: 'Test User',
          is_admin: false,
        },
        isAuthenticated: true,
        error: 'Some error',
      });

      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.logout();
      });

      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('access_token');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('refresh_token');
      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });
  });

  describe('clearError', () => {
    test('clears error state', () => {
      useAuthStore.setState({ error: 'Some error' });

      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBeNull();
    });
  });

  describe('checkAuth', () => {
    const mockUser = {
      id: '1',
      email: 'test@example.com',
      name: 'Test User',
      is_admin: false,
    };

    test('authenticates user when valid token exists', async () => {
      mockLocalStorage.getItem.mockReturnValue('valid-token');
      mockApiRequest.mockResolvedValueOnce(mockUser);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.checkAuth();
      });

      expect(mockLocalStorage.getItem).toHaveBeenCalledWith('access_token');
      expect(mockApiRequest).toHaveBeenCalledWith('GET', '/auth/me');
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.isLoading).toBe(false);
    });

    test('sets unauthenticated state when no token exists', async () => {
      mockLocalStorage.getItem.mockReturnValue(null);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.checkAuth();
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(result.current.isLoading).toBe(false);
      expect(mockApiRequest).not.toHaveBeenCalled();
    });

    test('logs out on invalid token error', async () => {
      mockLocalStorage.getItem.mockReturnValue('invalid-token');
      const error = {
        response: {
          status: 401,
          data: { detail: 'Invalid token' },
        },
      };

      mockApiRequest.mockRejectedValueOnce(error);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.checkAuth();
      });

      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('access_token');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('refresh_token');
      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });

    test('logs out on user not found error', async () => {
      mockLocalStorage.getItem.mockReturnValue('token-for-deleted-user');
      const error = {
        response: {
          status: 401,
          data: { detail: 'User not found' },
        },
      };

      mockApiRequest.mockRejectedValueOnce(error);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.checkAuth();
      });

      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('access_token');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('refresh_token');
    });

    test('handles network error without logging out', async () => {
      mockLocalStorage.getItem.mockReturnValue('valid-token');
      const error = {
        response: {
          status: 500,
          data: { detail: 'Server error' },
        },
      };

      mockApiRequest.mockRejectedValueOnce(error);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.checkAuth();
      });

      expect(mockLocalStorage.removeItem).not.toHaveBeenCalled();
      expect(result.current.error).toBe('Connection issue - please refresh');
      expect(result.current.isLoading).toBe(false);
    });

    test('handles 401 error without specific detail', async () => {
      mockLocalStorage.getItem.mockReturnValue('token');
      const error = {
        response: {
          status: 401,
          data: { detail: 'Some other auth error' },
        },
      };

      mockApiRequest.mockRejectedValueOnce(error);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.checkAuth();
      });

      expect(mockLocalStorage.removeItem).not.toHaveBeenCalled();
      expect(result.current.error).toBe('Connection issue - please refresh');
    });

    test('sets loading state during auth check', async () => {
      mockLocalStorage.getItem.mockReturnValue('token');
      mockApiRequest.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

      const { result } = renderHook(() => useAuthStore());

      act(() => {
        result.current.checkAuth();
      });

      expect(result.current.isLoading).toBe(true);
    });
  });
});