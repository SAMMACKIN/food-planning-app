import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

// Create separate axios instances for different features to prevent blocking
// Each instance has its own request queue and can operate independently

// High-priority instance for navigation and critical UI updates
export const navigationApi = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 10000, // 10 seconds - quick timeout for UI responsiveness
  headers: {
    'Content-Type': 'application/json',
  },
});

// Standard instance for regular data fetching (pantry, family, recipes)
export const dataApi = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Long-running instance for AI recommendations
export const recommendationsApi = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 120000, // 2 minutes - AI requests can take longer
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth interceptor to all instances
const addAuthInterceptor = (instance: AxiosInstance) => {
  instance.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  });

  instance.interceptors.response.use(
    (response) => response,
    async (error) => {
      // Don't redirect on abort
      if (error.code === 'ERR_CANCELED' || error.message === 'canceled') {
        return Promise.reject(error);
      }

      // Handle auth errors
      if (error.response?.status === 401) {
        if (error.response?.data?.detail === 'Invalid token' || 
            error.response?.data?.detail === 'User not found') {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }

      return Promise.reject(error);
    }
  );
};

// Apply auth interceptor to all instances
addAuthInterceptor(navigationApi);
addAuthInterceptor(dataApi);
addAuthInterceptor(recommendationsApi);

// Export a function to get the appropriate instance based on the request type
export const getApiInstance = (requestType: 'navigation' | 'data' | 'recommendations' = 'data') => {
  switch (requestType) {
    case 'navigation':
      return navigationApi;
    case 'recommendations':
      return recommendationsApi;
    default:
      return dataApi;
  }
};