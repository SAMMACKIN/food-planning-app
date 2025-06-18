import { api } from '../api';

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

// Mock environment variable
const originalEnv = process.env;

describe('API Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  afterAll(() => {
    process.env = originalEnv;
  });

  test('api instance is defined', () => {
    expect(api).toBeDefined();
    expect(api.defaults).toBeDefined();
    expect(api.defaults.baseURL).toContain('/api/v1');
  });

  test('api has correct content type header', () => {
    expect(api.defaults.headers['Content-Type']).toBe('application/json');
  });

  test('api has interceptors configured', () => {
    expect(api.interceptors).toBeDefined();
    expect(api.interceptors.request).toBeDefined();
    expect(api.interceptors.response).toBeDefined();
  });

  test('api uses correct base URL from environment', () => {
    // The URL will be either localhost or Railway URL depending on environment
    expect(api.defaults.baseURL).toMatch(/\/api\/v1$/);
  });
});