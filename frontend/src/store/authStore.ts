import { create } from 'zustand';
import { User, AuthTokens, LoginRequest, RegisterRequest } from '../types';
import { apiRequest } from '../services/api';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (userData: RegisterRequest) => Promise<void>;
  logout: () => void;
  clearError: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (credentials: LoginRequest) => {
    set({ isLoading: true, error: null });
    
    try {
      const tokens = await apiRequest<AuthTokens>('POST', '/auth/login', credentials);
      
      localStorage.setItem('access_token', tokens.access_token);
      localStorage.setItem('refresh_token', tokens.refresh_token);
      
      await get().checkAuth();
    } catch (error: any) {
      set({ 
        error: error.response?.data?.detail || 'Login failed',
        isLoading: false 
      });
    }
  },

  register: async (userData: RegisterRequest) => {
    set({ isLoading: true, error: null });
    
    try {
      console.log('Attempting registration with:', userData);
      const tokens = await apiRequest<AuthTokens>('POST', '/auth/register', userData);
      console.log('Registration successful, tokens:', tokens);
      
      localStorage.setItem('access_token', tokens.access_token);
      localStorage.setItem('refresh_token', tokens.refresh_token);
      
      await get().checkAuth();
    } catch (error: any) {
      console.error('Registration error:', error);
      set({ 
        error: error.response?.data?.detail || error.message || 'Registration failed',
        isLoading: false 
      });
    }
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({ 
      user: null, 
      isAuthenticated: false, 
      isLoading: false, 
      error: null 
    });
  },

  clearError: () => {
    set({ error: null });
  },

  checkAuth: async () => {
    const token = localStorage.getItem('access_token');
    
    if (!token) {
      set({ isAuthenticated: false, user: null, isLoading: false });
      return;
    }

    set({ isLoading: true });
    
    try {
      const user = await apiRequest<User>('GET', '/auth/me');
      set({ 
        user, 
        isAuthenticated: true, 
        isLoading: false, 
        error: null 
      });
    } catch (error) {
      get().logout();
    }
  },
}));