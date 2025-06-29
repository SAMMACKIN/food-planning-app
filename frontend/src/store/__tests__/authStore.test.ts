import { useAuthStore } from '../authStore';
import { act, renderHook } from '@testing-library/react';

// Mock axios
jest.mock('../../services/api', () => ({
  api: {
    post: jest.fn(),
    get: jest.fn(),
  },
}));

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

describe('AuthStore', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  test('initial state is correct', () => {
    const { result } = renderHook(() => useAuthStore());
    
    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  test('clearError clears error state', () => {
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

  test('logout clears user state and localStorage', () => {
    const { result } = renderHook(() => useAuthStore());
    
    // Set initial authenticated state
    act(() => {
      useAuthStore.setState({
        user: { 
          id: '1', 
          email: 'test@example.com', 
          name: 'Test',
          timezone: 'UTC',
          is_active: true,
          is_admin: false,
          created_at: '2024-01-01T00:00:00Z'
        },
        isAuthenticated: true,
      });
    });
    
    expect(result.current.isAuthenticated).toBe(true);
    
    act(() => {
      result.current.logout();
    });
    
    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('refresh_token');
  });
});