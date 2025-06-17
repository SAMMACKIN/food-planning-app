// Mock axios for Jest
export default {
  create: jest.fn(() => ({
    request: jest.fn(),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
    defaults: {
      baseURL: 'http://localhost:8001/api/v1',
      headers: {},
    },
  })),
  request: jest.fn(),
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
  patch: jest.fn(),
};