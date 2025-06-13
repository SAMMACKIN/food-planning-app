import axios, { AxiosResponse } from 'axios';
import { ApiResponse, AuthTokens } from '../types';

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
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token } = response.data;
          localStorage.setItem('access_token', access_token);

          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
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
  data?: any
): Promise<T> => {
  try {
    console.log(`🚀 Making ${method} request to ${api.defaults.baseURL}${url}`, data);
    console.log('🔗 Full URL:', `${api.defaults.baseURL}${url}`);
    const response: AxiosResponse<T> = await api.request({
      method,
      url,
      data,
    });
    console.log('✅ API Response received:', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ API Error:', error);
    throw error;
  }
};