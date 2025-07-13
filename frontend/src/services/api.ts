import axios, { AxiosResponse } from 'axios';
import { apiDebugger } from '../utils/debugApi';
import { navigationApi, dataApi, recommendationsApi } from './apiInstances';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';
console.log('🔗 API Base URL:', API_BASE_URL);

// Legacy api export for backward compatibility
export const api = dataApi;

export const apiRequest = async <T>(
  method: 'GET' | 'POST' | 'PUT' | 'DELETE',
  url: string,
  data?: any,
  config?: { signal?: AbortSignal; requestType?: 'navigation' | 'data' | 'recommendations' }
): Promise<T> => {
  const requestId = apiDebugger.startRequest(`${method} ${url}`);
  
  // Determine which axios instance to use
  const requestType = config?.requestType || 'data';
  let apiInstance = dataApi;
  
  if (requestType === 'navigation') {
    apiInstance = navigationApi;
  } else if (requestType === 'recommendations' || url.includes('/recommendations')) {
    apiInstance = recommendationsApi;
  }
  
  try {
    const token = localStorage.getItem('access_token');
    console.log(`🚀 Making ${method} request to ${apiInstance.defaults.baseURL}${url}`, data);
    console.log('🔗 Full URL:', `${apiInstance.defaults.baseURL}${url}`);
    console.log('🔑 Authorization token available:', token ? 'Yes' : 'No');
    console.log('📡 Using instance:', requestType);
    
    const response: AxiosResponse<T> = await apiInstance.request({
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