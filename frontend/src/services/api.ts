import axios, { AxiosResponse } from 'axios';
import { apiDebugger } from '../utils/debugApi';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';
console.log('🔗 API Base URL:', API_BASE_URL);

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  
  // Only add Authorization header to API requests, not static files
  const isApiRequest = config.url?.includes('/api/') || config.baseURL?.includes('/api/');
  
  if (token && isApiRequest) {
    config.headers.Authorization = `Bearer ${token}`;
    console.log('🔑 Adding Authorization header to API request:', config.url);
  } else if (!isApiRequest) {
    console.log('📄 Static file request (no auth needed):', config.url);
  } else {
    console.log('⚠️ No access token found for API request:', config.url);
  }
  
  // Add a reasonable timeout for all requests (30 seconds)
  // This prevents requests from hanging indefinitely
  if (!config.timeout) {
    config.timeout = 30000; // 30 seconds
  }
  
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    console.error('🔥 API Response Error:', error.response?.status, error.response?.data);
    
    // Don't redirect to login on every 401 - let the calling code handle it
    if (error.response?.status === 401) {
      console.warn('🚫 401 Unauthorized - token may be invalid');
      // Only clear tokens and redirect if this is a critical auth failure
      if (error.response?.data?.detail === 'Invalid token' || 
          error.response?.data?.detail === 'User not found') {
        console.log('🧹 Clearing invalid tokens and redirecting to login');
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

export const apiRequest = async <T>(
  method: 'GET' | 'POST' | 'PUT' | 'DELETE',
  url: string,
  data?: any,
  config?: { signal?: AbortSignal }
): Promise<T> => {
  const requestId = apiDebugger.startRequest(`${method} ${url}`);
  
  try {
    const token = localStorage.getItem('access_token');
    console.log(`🚀 Making ${method} request to ${api.defaults.baseURL}${url}`, data);
    console.log('🔗 Full URL:', `${api.defaults.baseURL}${url}`);
    console.log('🔑 Authorization token available:', token ? 'Yes' : 'No');
    
    const response: AxiosResponse<T> = await api.request({
      method,
      url,
      data,
      signal: config?.signal,
    });
    console.log('✅ API Response received:', response.data);
    apiDebugger.endRequest(requestId, true);
    return response.data;
  } catch (error: any) {
    // Don't log abort errors as failures
    if (error.name === 'AbortError' || error.code === 'ERR_CANCELED' || error.message === 'canceled') {
      console.log('🛑 Request was cancelled');
      apiDebugger.cancelRequest(requestId);
      throw error;
    }
    
    console.error('❌ API Error details:', {
      status: error.response?.status,
      data: error.response?.data,
      headers: error.response?.headers,
      url: error.config?.url,
      method: error.config?.method
    });
    apiDebugger.endRequest(requestId, false);
    throw error;
  }
};