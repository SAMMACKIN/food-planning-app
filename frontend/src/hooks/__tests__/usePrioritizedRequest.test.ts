import { renderHook, act, waitFor } from '@testing-library/react';
import { usePrioritizedRequest } from '../usePrioritizedRequest';
import { requestQueue } from '../../utils/requestQueue';

// Mock the requestQueue module
jest.mock('../../utils/requestQueue', () => ({
  requestQueue: {
    add: jest.fn(),
    cancel: jest.fn(),
  },
}));

describe('usePrioritizedRequest', () => {
  let mockRequestQueue: jest.Mocked<typeof requestQueue>;

  beforeEach(() => {
    mockRequestQueue = requestQueue as jest.Mocked<typeof requestQueue>;
    mockRequestQueue.add.mockClear();
    mockRequestQueue.cancel.mockClear();
  });

  it('should make a request with default priority', async () => {
    const mockResult = { data: 'test' };
    const mockRequestFn = jest.fn().mockResolvedValue(mockResult);
    let executeCallback: () => Promise<any>;

    // Capture the execute callback
    mockRequestQueue.add.mockImplementation((request) => {
      executeCallback = request.execute;
      return 'request-id-1';
    });

    const { result } = renderHook(() => usePrioritizedRequest());

    // Make request
    let requestPromise: Promise<any>;
    act(() => {
      requestPromise = result.current.makeRequest(mockRequestFn);
    });

    // Verify request was added to queue with normal priority
    expect(mockRequestQueue.add).toHaveBeenCalledWith({
      priority: 'normal',
      execute: expect.any(Function),
    });

    // Execute the request
    await act(async () => {
      const executeResult = await executeCallback!();
      expect(executeResult).toEqual(mockResult);
    });

    // Wait for the promise to resolve
    const finalResult = await requestPromise!;
    expect(finalResult).toEqual(mockResult);
    expect(mockRequestFn).toHaveBeenCalled();
  });

  it('should make a request with custom priority', async () => {
    const mockRequestFn = jest.fn().mockResolvedValue({ data: 'high-priority' });
    mockRequestQueue.add.mockReturnValue('request-id-2');

    const { result } = renderHook(() => usePrioritizedRequest());

    act(() => {
      result.current.makeRequest(mockRequestFn, 'high');
    });

    expect(mockRequestQueue.add).toHaveBeenCalledWith({
      priority: 'high',
      execute: expect.any(Function),
    });
  });

  it('should handle request errors', async () => {
    const mockError = new Error('Request failed');
    const mockRequestFn = jest.fn().mockRejectedValue(mockError);
    let executeCallback: () => Promise<any>;

    mockRequestQueue.add.mockImplementation((request) => {
      executeCallback = request.execute;
      return 'request-id-3';
    });

    const { result } = renderHook(() => usePrioritizedRequest());

    // Make request
    let requestPromise: Promise<any>;
    act(() => {
      requestPromise = result.current.makeRequest(mockRequestFn);
    });

    // Execute and expect error
    await act(async () => {
      await expect(executeCallback!()).rejects.toThrow('Request failed');
    });

    // Verify the promise rejects
    await expect(requestPromise!).rejects.toThrow('Request failed');
  });

  it('should track and clean up pending requests', async () => {
    const requestIds = ['req-1', 'req-2', 'req-3'];
    let requestIndex = 0;

    mockRequestQueue.add.mockImplementation(() => requestIds[requestIndex++]);

    const { result } = renderHook(() => usePrioritizedRequest());

    // Make multiple requests
    const mockRequestFn = jest.fn().mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    act(() => {
      result.current.makeRequest(mockRequestFn, 'high');
      result.current.makeRequest(mockRequestFn, 'normal');
      result.current.makeRequest(mockRequestFn, 'low');
    });

    expect(mockRequestQueue.add).toHaveBeenCalledTimes(3);
  });

  it('should cancel pending requests on unmount', () => {
    const requestIds = ['req-1', 'req-2'];
    let requestIndex = 0;

    mockRequestQueue.add.mockImplementation(() => requestIds[requestIndex++]);

    const { result, unmount } = renderHook(() => usePrioritizedRequest());

    // Make requests that won't complete
    const mockRequestFn = jest.fn().mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    act(() => {
      result.current.makeRequest(mockRequestFn);
      result.current.makeRequest(mockRequestFn);
    });

    // Unmount should cancel all pending requests
    unmount();

    expect(mockRequestQueue.cancel).toHaveBeenCalledWith('req-1');
    expect(mockRequestQueue.cancel).toHaveBeenCalledWith('req-2');
    expect(mockRequestQueue.cancel).toHaveBeenCalledTimes(2);
  });

  it('should remove request ID from pending set after completion', async () => {
    const mockResult = { success: true };
    const mockRequestFn = jest.fn().mockResolvedValue(mockResult);
    let executeCallback: () => Promise<any>;

    mockRequestQueue.add.mockImplementation((request) => {
      executeCallback = request.execute;
      return 'completed-request';
    });

    const { result, unmount } = renderHook(() => usePrioritizedRequest());

    // Make request
    let requestPromise: Promise<any>;
    act(() => {
      requestPromise = result.current.makeRequest(mockRequestFn);
    });

    // Execute the request
    await act(async () => {
      await executeCallback!();
    });

    await requestPromise!;

    // Unmount - should not try to cancel completed request
    unmount();

    // Should not cancel a completed request
    expect(mockRequestQueue.cancel).not.toHaveBeenCalledWith('completed-request');
  });

  it('should handle multiple concurrent requests', async () => {
    const results = ['result1', 'result2', 'result3'];
    const executeCallbacks: Array<() => Promise<any>> = [];

    mockRequestQueue.add.mockImplementation((request) => {
      executeCallbacks.push(request.execute);
      return `request-${executeCallbacks.length}`;
    });

    const { result } = renderHook(() => usePrioritizedRequest());

    // Make multiple concurrent requests
    const promises: Promise<any>[] = [];
    act(() => {
      promises.push(
        result.current.makeRequest(() => Promise.resolve(results[0]), 'high'),
        result.current.makeRequest(() => Promise.resolve(results[1]), 'normal'),
        result.current.makeRequest(() => Promise.resolve(results[2]), 'low')
      );
    });

    // Execute all requests
    await act(async () => {
      await Promise.all(executeCallbacks.map(cb => cb()));
    });

    // Verify all promises resolve with correct values
    const resolvedResults = await Promise.all(promises);
    expect(resolvedResults).toEqual(results);
  });

  it('should handle request function that throws synchronously', async () => {
    const mockError = new Error('Sync error');
    const mockRequestFn = jest.fn().mockImplementation(() => {
      throw mockError;
    });
    let executeCallback: () => Promise<any>;

    mockRequestQueue.add.mockImplementation((request) => {
      executeCallback = request.execute;
      return 'error-request';
    });

    const { result } = renderHook(() => usePrioritizedRequest());

    // Make request
    let requestPromise: Promise<any>;
    act(() => {
      requestPromise = result.current.makeRequest(mockRequestFn);
    });

    // Execute and expect error
    await act(async () => {
      await expect(executeCallback!()).rejects.toThrow('Sync error');
    });

    // Verify the promise rejects
    await expect(requestPromise!).rejects.toThrow('Sync error');
  });
});