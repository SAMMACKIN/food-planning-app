import { apiDebugger } from '../debugApi';

// Mock console methods to suppress debug logs and test output
const consoleMock = {
  log: jest.fn(),
};
Object.defineProperty(console, 'log', { value: consoleMock.log });

// Mock Date.now for consistent timing tests
const mockDateNow = jest.spyOn(Date, 'now');

describe('ApiDebugger', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    consoleMock.log.mockClear();
    
    // Reset the debugger state
    // Since apiDebugger is a singleton, we need to clear any existing requests
    while (apiDebugger.getActiveRequestCount() > 0) {
      // Get the first active request and end it
      const mockId = `req-${Math.random()}`;
      apiDebugger.endRequest(mockId, true);
    }
  });

  afterEach(() => {
    mockDateNow.mockRestore();
  });

  describe('Request Tracking', () => {
    test('should start request and return unique ID', () => {
      const url = 'GET /api/test';
      
      const id = apiDebugger.startRequest(url);
      
      expect(id).toBeDefined();
      expect(id).toMatch(/^req-\d+$/);
      expect(apiDebugger.getActiveRequestCount()).toBe(1);
    });

    test('should generate unique IDs for multiple requests', () => {
      const id1 = apiDebugger.startRequest('GET /api/test1');
      const id2 = apiDebugger.startRequest('POST /api/test2');
      const id3 = apiDebugger.startRequest('PUT /api/test3');
      
      expect(id1).not.toBe(id2);
      expect(id2).not.toBe(id3);
      expect(id1).not.toBe(id3);
      expect(apiDebugger.getActiveRequestCount()).toBe(3);
    });

    test('should track active request count correctly', () => {
      expect(apiDebugger.getActiveRequestCount()).toBe(0);
      
      const id1 = apiDebugger.startRequest('GET /api/test1');
      expect(apiDebugger.getActiveRequestCount()).toBe(1);
      
      const id2 = apiDebugger.startRequest('POST /api/test2');
      expect(apiDebugger.getActiveRequestCount()).toBe(2);
      
      apiDebugger.endRequest(id1, true);
      expect(apiDebugger.getActiveRequestCount()).toBe(1);
      
      apiDebugger.endRequest(id2, false);
      expect(apiDebugger.getActiveRequestCount()).toBe(0);
    });
  });

  describe('Request Completion', () => {
    test('should handle successful request completion', () => {
      mockDateNow.mockReturnValueOnce(1000).mockReturnValueOnce(1500);
      
      const id = apiDebugger.startRequest('GET /api/success');
      apiDebugger.endRequest(id, true);
      
      expect(consoleMock.log).toHaveBeenCalledWith(
        expect.stringContaining('🚀 API Request Started')
      );
      expect(consoleMock.log).toHaveBeenCalledWith(
        expect.stringContaining('✅ API Request Ended')
      );
      expect(consoleMock.log).toHaveBeenCalledWith(
        expect.stringContaining('(500ms)')
      );
      expect(apiDebugger.getActiveRequestCount()).toBe(0);
    });

    test('should handle failed request completion', () => {
      mockDateNow.mockReturnValueOnce(2000).mockReturnValueOnce(2300);
      
      const id = apiDebugger.startRequest('POST /api/failure');
      apiDebugger.endRequest(id, false);
      
      expect(consoleMock.log).toHaveBeenCalledWith(
        expect.stringContaining('❌ API Request Ended')
      );
      expect(consoleMock.log).toHaveBeenCalledWith(
        expect.stringContaining('(300ms)')
      );
      expect(apiDebugger.getActiveRequestCount()).toBe(0);
    });

    test('should handle ending non-existent request gracefully', () => {
      apiDebugger.endRequest('non-existent-id', true);
      
      // Should not crash and should not log anything for non-existent request
      expect(apiDebugger.getActiveRequestCount()).toBe(0);
    });

    test('should calculate duration correctly', () => {
      const startTime = 5000;
      const endTime = 5750;
      
      mockDateNow.mockReturnValueOnce(startTime).mockReturnValueOnce(endTime);
      
      const id = apiDebugger.startRequest('GET /api/duration-test');
      apiDebugger.endRequest(id, true);
      
      expect(consoleMock.log).toHaveBeenCalledWith(
        expect.stringContaining('(750ms)')
      );
    });
  });

  describe('Request Cancellation', () => {
    test('should handle request cancellation', () => {
      const id = apiDebugger.startRequest('GET /api/cancel-test');
      expect(apiDebugger.getActiveRequestCount()).toBe(1);
      
      apiDebugger.cancelRequest(id);
      
      expect(consoleMock.log).toHaveBeenCalledWith(
        expect.stringContaining('🛑 API Request Cancelled')
      );
      expect(apiDebugger.getActiveRequestCount()).toBe(0);
    });

    test('should handle cancelling non-existent request gracefully', () => {
      apiDebugger.cancelRequest('non-existent-id');
      
      // Should not crash and should not log anything for non-existent request
      expect(apiDebugger.getActiveRequestCount()).toBe(0);
    });

    test('should cancel correct request among multiple active requests', () => {
      const id1 = apiDebugger.startRequest('GET /api/test1');
      const id2 = apiDebugger.startRequest('POST /api/test2');
      const id3 = apiDebugger.startRequest('PUT /api/test3');
      
      expect(apiDebugger.getActiveRequestCount()).toBe(3);
      
      apiDebugger.cancelRequest(id2);
      
      expect(apiDebugger.getActiveRequestCount()).toBe(2);
      
      // Verify the correct request was cancelled
      expect(consoleMock.log).toHaveBeenCalledWith(
        expect.stringContaining(`🛑 API Request Cancelled [${id2}]`)
      );
    });
  });

  describe('Logging Functionality', () => {
    test('should log request start with details', () => {
      const url = 'GET /api/users';
      
      apiDebugger.startRequest(url);
      
      expect(consoleMock.log).toHaveBeenCalledWith(
        expect.stringContaining('🚀 API Request Started')
      );
      expect(consoleMock.log).toHaveBeenCalledWith(
        expect.stringContaining(url)
      );
      expect(consoleMock.log).toHaveBeenCalledWith(
        expect.stringContaining('(1 active)')
      );
    });

    test('should log active requests when starting new request', () => {
      apiDebugger.startRequest('GET /api/test1');
      consoleMock.log.mockClear();
      
      apiDebugger.startRequest('POST /api/test2');
      
      expect(consoleMock.log).toHaveBeenCalledWith(
        expect.stringContaining('📊 Active Requests:')
      );
    });

    test('should log active requests when ending request', () => {
      const id1 = apiDebugger.startRequest('GET /api/test1');
      const id2 = apiDebugger.startRequest('POST /api/test2');
      consoleMock.log.mockClear();
      
      apiDebugger.endRequest(id1, true);
      
      expect(consoleMock.log).toHaveBeenCalledWith(
        expect.stringContaining('📊 Active Requests:')
      );
    });

    test('should not log active requests when none are active', () => {
      const id = apiDebugger.startRequest('GET /api/test');
      consoleMock.log.mockClear();
      
      apiDebugger.endRequest(id, true);
      
      // Should log the end request but not active requests since none are active
      expect(consoleMock.log).toHaveBeenCalledWith(
        expect.stringContaining('✅ API Request Ended')
      );
      
      // Check that active requests log is not called when count is 0
      const activeRequestsLog = consoleMock.log.mock.calls.find(call => 
        call[0].includes('📊 Active Requests:')
      );
      expect(activeRequestsLog).toBeUndefined();
    });

    test('should include request details in active requests log', () => {
      mockDateNow.mockReturnValue(10000);
      
      const id = apiDebugger.startRequest('GET /api/detailed-test');
      
      // Advance time
      mockDateNow.mockReturnValue(10500);
      
      // Start another request to trigger active requests log
      apiDebugger.startRequest('POST /api/another-test');
      
      expect(consoleMock.log).toHaveBeenCalledWith(
        '📊 Active Requests:',
        expect.arrayContaining([
          expect.objectContaining({
            id: expect.stringMatching(/^req-\d+$/),
            url: 'GET /api/detailed-test',
            duration: expect.stringMatching(/\d+ms$/)
          })
        ])
      );
    });
  });

  describe('Edge Cases and Error Handling', () => {
    test('should handle rapid request additions and removals', () => {
      const ids: string[] = [];
      
      // Add multiple requests rapidly
      for (let i = 0; i < 5; i++) {
        ids.push(apiDebugger.startRequest(`GET /api/rapid-${i}`));
      }
      
      expect(apiDebugger.getActiveRequestCount()).toBe(5);
      
      // Remove them in different order
      apiDebugger.endRequest(ids[2], true);
      apiDebugger.cancelRequest(ids[0]);
      apiDebugger.endRequest(ids[4], false);
      
      expect(apiDebugger.getActiveRequestCount()).toBe(2);
    });

    test('should handle multiple operations on same request ID gracefully', () => {
      const id = apiDebugger.startRequest('GET /api/multi-op-test');
      
      apiDebugger.endRequest(id, true);
      expect(apiDebugger.getActiveRequestCount()).toBe(0);
      
      // Try to end and cancel the same request again
      apiDebugger.endRequest(id, false);
      apiDebugger.cancelRequest(id);
      
      expect(apiDebugger.getActiveRequestCount()).toBe(0);
    });

    test('should maintain state consistency during concurrent operations', () => {
      const ids: string[] = [];
      
      // Start multiple requests
      for (let i = 0; i < 10; i++) {
        ids.push(apiDebugger.startRequest(`GET /api/concurrent-${i}`));
      }
      
      expect(apiDebugger.getActiveRequestCount()).toBe(10);
      
      // Complete some, cancel others
      apiDebugger.endRequest(ids[0], true);
      apiDebugger.endRequest(ids[1], false);
      apiDebugger.cancelRequest(ids[2]);
      apiDebugger.endRequest(ids[3], true);
      
      expect(apiDebugger.getActiveRequestCount()).toBe(6);
      
      // Complete remaining
      for (let i = 4; i < 10; i++) {
        if (i % 2 === 0) {
          apiDebugger.endRequest(ids[i], true);
        } else {
          apiDebugger.cancelRequest(ids[i]);
        }
      }
      
      expect(apiDebugger.getActiveRequestCount()).toBe(0);
    });
  });

  describe('Performance and Memory', () => {
    test('should not accumulate completed requests in memory', () => {
      // Start and complete many requests
      for (let i = 0; i < 100; i++) {
        const id = apiDebugger.startRequest(`GET /api/memory-test-${i}`);
        apiDebugger.endRequest(id, true);
      }
      
      // Should not have any active requests
      expect(apiDebugger.getActiveRequestCount()).toBe(0);
    });

    test('should handle large number of concurrent requests', () => {
      const ids: string[] = [];
      
      // Start many concurrent requests
      for (let i = 0; i < 50; i++) {
        ids.push(apiDebugger.startRequest(`GET /api/concurrent-${i}`));
      }
      
      expect(apiDebugger.getActiveRequestCount()).toBe(50);
      
      // Complete them all
      ids.forEach(id => apiDebugger.endRequest(id, true));
      
      expect(apiDebugger.getActiveRequestCount()).toBe(0);
    });
  });
});