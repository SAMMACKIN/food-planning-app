import { renderHook, act, waitFor } from '@testing-library/react';
import { useAuthStore } from '../authStore';
import { apiRequest } from '../../services/api';

// Mock the api module
jest.mock('../../services/api');

// Mock window.location
delete (window as any).location;
window.location = { href: '' } as any;

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

describe('AuthStore Edge Cases', () => {
  const mockApiRequest = apiRequest as jest.MockedFunction<typeof apiRequest>;

  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
    window.location.href = '';
    console.log = jest.fn();
    console.error = jest.fn();
  });

  describe('login edge cases', () => {
    it('should handle network timeout during login', async () => {
      const timeoutError = new Error('Network timeout');
      (timeoutError as any).code = 'ECONNABORTED';
      mockApiRequest.mockRejectedValueOnce(timeoutError);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.login({ email: 'test@example.com', password: 'password' });
      });

      expect(result.current.error).toBe('Login failed');
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isLoading).toBe(false);
    });

    it('should handle malformed server response during login', async () => {
      // First call returns invalid tokens object
      mockApiRequest.mockResolvedValueOnce({ invalid: 'response' } as any);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        try {
          await result.current.login({ email: 'test@example.com', password: 'password' });
        } catch (e) {
          // Expected to fail
        }
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(localStorageMock.setItem).not.toHaveBeenCalled();
    });

    it('should handle token storage failure', async () => {
      const tokens = { access_token: 'token123', refresh_token: 'refresh123' };
      mockApiRequest.mockResolvedValueOnce(tokens);
      
      // Make localStorage.setItem throw
      localStorageMock.setItem.mockImplementation(() => {
        throw new Error('QuotaExceededError');
      });

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        try {
          await result.current.login({ email: 'test@example.com', password: 'password' });
        } catch (e) {
          // Expected to fail
        }
      });

      expect(result.current.isAuthenticated).toBe(false);
    });

    it('should handle user fetch failure after successful token receipt', async () => {
      const tokens = { access_token: 'token123', refresh_token: 'refresh123' };
      mockApiRequest
        .mockResolvedValueOnce(tokens) // Login success
        .mockRejectedValueOnce(new Error('User fetch failed')); // User fetch fails

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.login({ email: 'test@example.com', password: 'password' });
      });

      expect(localStorageMock.setItem).toHaveBeenCalledWith('access_token', 'token123');
      expect(result.current.error).toBe('Login failed');
      expect(result.current.isAuthenticated).toBe(false);
    });

    it('should handle concurrent login attempts', async () => {
      const tokens = { access_token: 'token123', refresh_token: 'refresh123' };
      const user = { id: '1', email: 'test@example.com', is_admin: false };
      
      let resolveFirst: (value: any) => void;
      const firstPromise = new Promise(resolve => { resolveFirst = resolve; });
      
      mockApiRequest
        .mockReturnValueOnce(firstPromise as any) // First login hangs
        .mockResolvedValueOnce(tokens) // Second login
        .mockResolvedValueOnce(user);

      const { result } = renderHook(() => useAuthStore());

      // Start first login
      act(() => {
        result.current.login({ email: 'test1@example.com', password: 'password1' });
      });

      expect(result.current.isLoading).toBe(true);

      // Start second login while first is pending
      await act(async () => {
        await result.current.login({ email: 'test2@example.com', password: 'password2' });
      });

      // Resolve first login
      resolveFirst!(tokens);

      // Second login should have completed
      expect(result.current.user).toEqual(user);
      expect(window.location.href).toBe('/dashboard');
    });
  });

  describe('register edge cases', () => {
    it('should handle registration with existing email', async () => {
      const error = {
        response: {
          status: 409,
          data: { detail: 'Email already registered' }
        }
      };
      mockApiRequest.mockRejectedValueOnce(error);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.register({
          email: 'existing@example.com',
          password: 'password',
          name: 'Test User'
        });
      });

      expect(result.current.error).toBe('Email already registered');
      expect(result.current.isAuthenticated).toBe(false);
    });

    it('should handle registration with invalid data format', async () => {
      const error = {
        response: {
          status: 422,
          data: { 
            detail: [
              { loc: ['body', 'email'], msg: 'invalid email format' },
              { loc: ['body', 'password'], msg: 'password too short' }
            ]
          }
        }
      };
      mockApiRequest.mockRejectedValueOnce(error);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.register({
          email: 'invalid-email',
          password: '123',
          name: 'Test'
        });
      });

      expect(result.current.error).toBeDefined();
      expect(console.error).toHaveBeenCalled();
    });

    it('should handle checkAuth failure after successful registration', async () => {
      const tokens = { access_token: 'token123', refresh_token: 'refresh123' };
      mockApiRequest
        .mockResolvedValueOnce(tokens) // Registration success
        .mockRejectedValueOnce(new Error('Auth check failed')); // checkAuth fails

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.register({
          email: 'new@example.com',
          password: 'password',
          name: 'New User'
        });
      });

      // Tokens should still be stored
      expect(localStorageMock.setItem).toHaveBeenCalledWith('access_token', 'token123');
      // But error state should be set
      expect(result.current.error).toContain('failed');
    });
  });

  describe('checkAuth edge cases', () => {
    it('should handle expired token gracefully', async () => {
      localStorageMock.getItem.mockReturnValue('expired-token');
      const error = {
        response: {
          status: 401,
          data: { detail: 'Token expired' }
        }
      };
      mockApiRequest.mockRejectedValueOnce(error);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.checkAuth();
      });

      // Should not logout on token expiration (might be refreshable)
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.error).toBe('Connection issue - please refresh');
      expect(localStorageMock.removeItem).not.toHaveBeenCalled();
    });

    it('should logout on invalid token', async () => {
      localStorageMock.getItem.mockReturnValue('invalid-token');
      const error = {
        response: {
          status: 401,
          data: { detail: 'Invalid token' }
        }
      };
      mockApiRequest.mockRejectedValueOnce(error);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.checkAuth();
      });

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('refresh_token');
      expect(result.current.isAuthenticated).toBe(false);
    });

    it('should handle network errors without logging out', async () => {
      localStorageMock.getItem.mockReturnValue('valid-token');
      const error = new Error('Network error');
      (error as any).code = 'ERR_NETWORK';
      mockApiRequest.mockRejectedValueOnce(error);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.checkAuth();
      });

      expect(result.current.error).toBe('Connection issue - please refresh');
      expect(localStorageMock.removeItem).not.toHaveBeenCalled();
      expect(console.log).toHaveBeenCalledWith(
        expect.stringContaining('not logging out')
      );
    });

    it('should handle server 500 errors', async () => {
      localStorageMock.getItem.mockReturnValue('valid-token');
      const error = {
        response: {
          status: 500,
          data: { detail: 'Internal server error' }
        }
      };
      mockApiRequest.mockRejectedValueOnce(error);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.checkAuth();
      });

      expect(result.current.error).toBe('Connection issue - please refresh');
      expect(localStorageMock.removeItem).not.toHaveBeenCalled();
    });

    it('should handle malformed user response', async () => {
      localStorageMock.getItem.mockReturnValue('valid-token');
      // Return user object missing required fields
      mockApiRequest.mockResolvedValueOnce({ invalid: 'user' } as any);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.checkAuth();
      });

      // Should still set as authenticated but with incomplete user
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual({ invalid: 'user' });
    });
  });

  describe('logout edge cases', () => {
    it('should handle localStorage errors during logout', () => {
      localStorageMock.removeItem.mockImplementation(() => {
        throw new Error('Storage error');
      });

      const { result } = renderHook(() => useAuthStore());
      
      // Set initial authenticated state
      act(() => {
        result.current.user = { id: '1', email: 'test@example.com', is_admin: false } as any;
        result.current.isAuthenticated = true;
      });

      // Logout should still complete despite storage error
      act(() => {
        result.current.logout();
      });

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });

    it('should clear all state on logout', () => {
      const { result } = renderHook(() => useAuthStore());
      
      // Set various state values
      act(() => {
        result.current.user = { id: '1', email: 'test@example.com', is_admin: true } as any;
        result.current.isAuthenticated = true;
        result.current.error = 'Some previous error';
        result.current.isLoading = true;
      });

      act(() => {
        result.current.logout();
      });

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('clearError', () => {
    it('should only clear error without affecting other state', () => {
      const { result } = renderHook(() => useAuthStore());
      
      // Set initial state
      act(() => {
        result.current.user = { id: '1', email: 'test@example.com', is_admin: false } as any;
        result.current.isAuthenticated = true;
        result.current.error = 'Test error';
        result.current.isLoading = true;
      });

      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBeNull();
      expect(result.current.user).not.toBeNull();
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.isLoading).toBe(true);
    });
  });

  describe('admin navigation', () => {
    it('should redirect admin users to /admin', async () => {
      const tokens = { access_token: 'token123', refresh_token: 'refresh123' };
      const adminUser = { id: '1', email: 'admin@example.com', is_admin: true };
      
      mockApiRequest
        .mockResolvedValueOnce(tokens)
        .mockResolvedValueOnce(adminUser);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.login({ email: 'admin@example.com', password: 'password' });
      });

      expect(window.location.href).toBe('/admin');
    });

    it('should redirect non-admin users to /dashboard', async () => {
      const tokens = { access_token: 'token123', refresh_token: 'refresh123' };
      const regularUser = { id: '1', email: 'user@example.com', is_admin: false };
      
      mockApiRequest
        .mockResolvedValueOnce(tokens)
        .mockResolvedValueOnce(regularUser);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.login({ email: 'user@example.com', password: 'password' });
      });

      expect(window.location.href).toBe('/dashboard');
    });
  });
});