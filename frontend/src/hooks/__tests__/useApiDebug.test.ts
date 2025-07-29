import { renderHook } from '@testing-library/react';
import { useApiDebug } from '../useApiDebug';

describe('useApiDebug', () => {
  let consoleLogSpy: jest.SpyInstance;

  beforeEach(() => {
    consoleLogSpy = jest.spyOn(console, 'log').mockImplementation();
    jest.useFakeTimers();
  });

  afterEach(() => {
    consoleLogSpy.mockRestore();
    jest.useRealTimers();
  });

  it('should log component mount', () => {
    const { unmount } = renderHook(() => useApiDebug('TestComponent'));

    expect(consoleLogSpy).toHaveBeenCalledWith(
      expect.stringContaining('🚀 TestComponent mounted at'),
      expect.any(String)
    );

    unmount();
  });

  it('should log component unmount with API call count', () => {
    const { result, unmount } = renderHook(() => useApiDebug('TestComponent'));

    // Make some API calls
    result.current.trackApiCall('/api/test1');
    result.current.trackApiCall('/api/test2');

    unmount();

    expect(consoleLogSpy).toHaveBeenCalledWith(
      '🔚 TestComponent unmounted after 2 API calls'
    );
  });

  it('should track API calls with timing information', () => {
    const { result } = renderHook(() => useApiDebug('TestComponent'));

    // Initial mount time
    const mountTime = Date.now();
    jest.setSystemTime(mountTime);

    // Advance time and make API call
    jest.advanceTimersByTime(1000);
    result.current.trackApiCall('/api/endpoint1');

    expect(consoleLogSpy).toHaveBeenCalledWith(
      expect.stringContaining('📡 TestComponent API Call #1 to /api/endpoint1 (1000ms after mount)')
    );

    // Make another call after more time
    jest.advanceTimersByTime(500);
    result.current.trackApiCall('/api/endpoint2');

    expect(consoleLogSpy).toHaveBeenCalledWith(
      expect.stringContaining('📡 TestComponent API Call #2 to /api/endpoint2 (1500ms after mount)')
    );
  });

  it('should increment API call count correctly', () => {
    const { result } = renderHook(() => useApiDebug('TestComponent'));

    // Make multiple API calls
    const endpoints = ['/api/test1', '/api/test2', '/api/test3'];
    endpoints.forEach((endpoint, index) => {
      result.current.trackApiCall(endpoint);
      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining(`API Call #${index + 1} to ${endpoint}`)
      );
    });
  });

  it('should handle component name changes', () => {
    const { rerender } = renderHook(
      ({ name }) => useApiDebug(name),
      { initialProps: { name: 'Component1' } }
    );

    expect(consoleLogSpy).toHaveBeenCalledWith(
      expect.stringContaining('🚀 Component1 mounted at'),
      expect.any(String)
    );

    // Clear previous logs
    consoleLogSpy.mockClear();

    // Change component name
    rerender({ name: 'Component2' });

    expect(consoleLogSpy).toHaveBeenCalledWith(
      expect.stringContaining('🚀 Component2 mounted at'),
      expect.any(String)
    );
  });

  it('should preserve state across rerenders', () => {
    const { result, rerender } = renderHook(() => useApiDebug('TestComponent'));

    // Make an API call
    result.current.trackApiCall('/api/test');
    expect(consoleLogSpy).toHaveBeenCalledWith(
      expect.stringContaining('API Call #1')
    );

    // Clear logs and rerender
    consoleLogSpy.mockClear();
    rerender();

    // Make another API call - count should continue
    result.current.trackApiCall('/api/test2');
    expect(consoleLogSpy).toHaveBeenCalledWith(
      expect.stringContaining('API Call #2')
    );
  });

  it('should calculate timing correctly with real timestamps', () => {
    const startTime = new Date('2024-01-01T12:00:00').getTime();
    jest.setSystemTime(startTime);

    const { result } = renderHook(() => useApiDebug('TestComponent'));

    // Advance time by 2.5 seconds
    jest.setSystemTime(startTime + 2500);
    result.current.trackApiCall('/api/delayed');

    expect(consoleLogSpy).toHaveBeenCalledWith(
      expect.stringContaining('(2500ms after mount)')
    );
  });
});