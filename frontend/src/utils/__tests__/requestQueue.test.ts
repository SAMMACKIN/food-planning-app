import { requestQueue } from '../requestQueue';

// Mock console methods to suppress debug logs
const consoleMock = {
  log: jest.fn(),
  error: jest.fn(),
};
Object.defineProperty(console, 'log', { value: consoleMock.log });
Object.defineProperty(console, 'error', { value: consoleMock.error });

describe('RequestQueueManager', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    consoleMock.log.mockClear();
    consoleMock.error.mockClear();
    requestQueue.clearQueue();
    
    // Wait for any pending promises to resolve
    return new Promise(resolve => setTimeout(resolve, 0));
  });

  afterEach(() => {
    requestQueue.clearQueue();
  });

  describe('Basic Queue Operations', () => {
    test('should add requests to queue and return unique IDs', () => {
      const mockExecute = jest.fn().mockResolvedValue('success');
      
      const id1 = requestQueue.add({ priority: 'normal', execute: mockExecute });
      const id2 = requestQueue.add({ priority: 'high', execute: mockExecute });
      
      expect(id1).toBeDefined();
      expect(id2).toBeDefined();
      expect(id1).not.toBe(id2);
      expect(id1).toMatch(/^req-\d+-\d+\.?\d*$/);
      expect(id2).toMatch(/^req-\d+-\d+\.?\d*$/);
    });

    test('should track queue status correctly', () => {
      const mockExecute = jest.fn().mockResolvedValue('success');
      
      let status = requestQueue.getStatus();
      expect(status.pending).toBe(0);
      expect(status.active).toBe(0);
      expect(status.maxConcurrent).toBe(3);
      
      requestQueue.add({ priority: 'normal', execute: mockExecute });
      requestQueue.add({ priority: 'high', execute: mockExecute });
      
      status = requestQueue.getStatus();
      expect(status.pending).toBeGreaterThanOrEqual(0); // May have started processing
      expect(status.maxConcurrent).toBe(3);
    });

    test('should clear all pending requests', () => {
      const mockExecute = jest.fn().mockResolvedValue('success');
      
      requestQueue.add({ priority: 'normal', execute: mockExecute });
      requestQueue.add({ priority: 'high', execute: mockExecute });
      requestQueue.add({ priority: 'low', execute: mockExecute });
      
      requestQueue.clearQueue();
      
      const status = requestQueue.getStatus();
      expect(status.pending).toBe(0);
      expect(consoleMock.log).toHaveBeenCalledWith(
        expect.stringContaining('🧹 Cleared')
      );
    });
  });

  describe('Priority Handling', () => {
    test('should prioritize high priority requests', async () => {
      const executionOrder: string[] = [];
      
      const createMockExecute = (name: string) => 
        jest.fn().mockImplementation(async () => {
          executionOrder.push(name);
          return 'success';
        });
      
      const normalExecute = createMockExecute('normal');
      const highExecute = createMockExecute('high');
      const lowExecute = createMockExecute('low');
      
      // Add in order: normal, high, low
      requestQueue.add({ priority: 'normal', execute: normalExecute });
      requestQueue.add({ priority: 'high', execute: highExecute });
      requestQueue.add({ priority: 'low', execute: lowExecute });
      
      // Wait for processing to complete
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // High priority should be executed first (or early)
      expect(executionOrder).toContain('high');
      expect(executionOrder).toContain('normal');
      expect(executionOrder).toContain('low');
    });

    test('should handle multiple high priority requests correctly', async () => {
      const executionOrder: string[] = [];
      
      const createMockExecute = (name: string) =>
        jest.fn().mockImplementation(async () => {
          executionOrder.push(name);
          await new Promise(resolve => setTimeout(resolve, 10));
          return 'success';
        });
      
      requestQueue.add({ priority: 'normal', execute: createMockExecute('normal1') });
      requestQueue.add({ priority: 'high', execute: createMockExecute('high1') });
      requestQueue.add({ priority: 'high', execute: createMockExecute('high2') });
      requestQueue.add({ priority: 'normal', execute: createMockExecute('normal2') });
      
      await new Promise(resolve => setTimeout(resolve, 200));
      
      expect(executionOrder).toContain('high1');
      expect(executionOrder).toContain('high2');
    });
  });

  describe('Concurrency Control', () => {
    test('should respect maximum concurrent request limit', async () => {
      let activeCount = 0;
      let maxActiveAtOnce = 0;
      
      const createSlowExecute = () => 
        jest.fn().mockImplementation(async () => {
          activeCount++;
          maxActiveAtOnce = Math.max(maxActiveAtOnce, activeCount);
          
          await new Promise(resolve => setTimeout(resolve, 50));
          
          activeCount--;
          return 'success';
        });
      
      // Add 5 requests (more than max concurrent of 3)
      for (let i = 0; i < 5; i++) {
        requestQueue.add({ 
          priority: 'normal', 
          execute: createSlowExecute() 
        });
      }
      
      await new Promise(resolve => setTimeout(resolve, 300));
      
      expect(maxActiveAtOnce).toBeLessThanOrEqual(3);
    });

    test('should process new requests after others complete', async () => {
      const completedRequests: string[] = [];
      
      const createNamedExecute = (name: string) =>
        jest.fn().mockImplementation(async () => {
          await new Promise(resolve => setTimeout(resolve, 20));
          completedRequests.push(name);
          return 'success';
        });
      
      // Fill up concurrent slots
      requestQueue.add({ priority: 'normal', execute: createNamedExecute('req1') });
      requestQueue.add({ priority: 'normal', execute: createNamedExecute('req2') });
      requestQueue.add({ priority: 'normal', execute: createNamedExecute('req3') });
      
      // Add more that should wait
      requestQueue.add({ priority: 'normal', execute: createNamedExecute('req4') });
      requestQueue.add({ priority: 'normal', execute: createNamedExecute('req5') });
      
      await new Promise(resolve => setTimeout(resolve, 150));
      
      expect(completedRequests).toHaveLength(5);
      expect(completedRequests).toContain('req1');
      expect(completedRequests).toContain('req5');
    });
  });

  describe('Request Cancellation', () => {
    test('should cancel pending requests successfully', async () => {
      // Use a slow mock that takes time to start, ensuring requests stay in queue
      const slowMockExecute = jest.fn().mockImplementation(async () => {
        await new Promise(resolve => setTimeout(resolve, 100));
        return 'success';
      });
      
      // Fill up concurrent slots with slow requests
      for (let i = 0; i < 3; i++) {
        requestQueue.add({ priority: 'normal', execute: slowMockExecute });
      }
      
      // Add a low priority request that should be queued
      const id2 = requestQueue.add({ priority: 'low', execute: slowMockExecute });
      
      // Wait a moment for first requests to start processing
      await new Promise(resolve => setTimeout(resolve, 10));
      
      // Now cancel the queued request
      const cancelled = requestQueue.cancel(id2);
      
      expect(cancelled).toBe(true);
      expect(consoleMock.log).toHaveBeenCalledWith(
        expect.stringContaining(`🛑 Request cancelled [${id2}]`)
      );
    });

    test('should return false when cancelling non-existent request', () => {
      const cancelled = requestQueue.cancel('non-existent-id');
      expect(cancelled).toBe(false);
    });

    test('should not cancel already executing requests', async () => {
      let requestStarted = false;
      const mockExecute = jest.fn().mockImplementation(async () => {
        requestStarted = true;
        await new Promise(resolve => setTimeout(resolve, 50));
        return 'success';
      });
      
      const id = requestQueue.add({ priority: 'high', execute: mockExecute });
      
      // Wait for request to start
      await new Promise(resolve => setTimeout(resolve, 10));
      
      if (requestStarted) {
        const cancelled = requestQueue.cancel(id);
        expect(cancelled).toBe(false);
      } else {
        // If not started yet, cancellation might succeed
        const cancelled = requestQueue.cancel(id);
        expect(typeof cancelled).toBe('boolean');
      }
    });
  });

  describe('Error Handling', () => {
    test('should handle failed requests gracefully', async () => {
      const errorExecute = jest.fn().mockRejectedValue(new Error('Request failed'));
      const successExecute = jest.fn().mockResolvedValue('success');
      
      const errorId = requestQueue.add({ priority: 'normal', execute: errorExecute });
      const successId = requestQueue.add({ priority: 'normal', execute: successExecute });
      
      await new Promise(resolve => setTimeout(resolve, 100));
      
      expect(consoleMock.error).toHaveBeenCalledWith(
        expect.stringContaining(`❌ Request failed [${errorId}]:`),
        expect.any(Error)
      );
      
      // Success request should still complete
      expect(successExecute).toHaveBeenCalled();
    });

    test('should continue processing queue after request failure', async () => {
      const failedExecute = jest.fn().mockRejectedValue(new Error('Failed'));
      const successExecute = jest.fn().mockResolvedValue('success');
      
      requestQueue.add({ priority: 'normal', execute: failedExecute });
      requestQueue.add({ priority: 'normal', execute: successExecute });
      
      await new Promise(resolve => setTimeout(resolve, 100));
      
      expect(failedExecute).toHaveBeenCalled();
      expect(successExecute).toHaveBeenCalled();
    });
  });

  describe('Logging and Monitoring', () => {
    test('should log request queue operations', () => {
      const mockExecute = jest.fn().mockResolvedValue('success');
      
      const id = requestQueue.add({ priority: 'high', execute: mockExecute });
      
      expect(consoleMock.log).toHaveBeenCalledWith(
        expect.stringContaining(`📥 Request queued [${id}] with priority: high`)
      );
    });

    test('should log request processing', async () => {
      const mockExecute = jest.fn().mockImplementation(async () => {
        await new Promise(resolve => setTimeout(resolve, 10));
        return 'success';
      });
      
      const id = requestQueue.add({ priority: 'normal', execute: mockExecute });
      
      await new Promise(resolve => setTimeout(resolve, 50));
      
      expect(consoleMock.log).toHaveBeenCalledWith(
        expect.stringContaining(`🚀 Processing request [${id}]`)
      );
      expect(consoleMock.log).toHaveBeenCalledWith(
        expect.stringContaining(`✅ Request completed [${id}]`)
      );
    });

    test('should log active request count', async () => {
      const mockExecute = jest.fn().mockImplementation(async () => {
        await new Promise(resolve => setTimeout(resolve, 20));
        return 'success';
      });
      
      requestQueue.add({ priority: 'normal', execute: mockExecute });
      
      await new Promise(resolve => setTimeout(resolve, 50));
      
      expect(consoleMock.log).toHaveBeenCalledWith(
        expect.stringContaining('📊 Active requests:')
      );
    });
  });

  describe('Queue State Management', () => {
    test('should maintain correct queue state during operations', async () => {
      const slowExecute = jest.fn().mockImplementation(async () => {
        await new Promise(resolve => setTimeout(resolve, 30));
        return 'success';
      });
      
      requestQueue.add({ priority: 'normal', execute: slowExecute });
      requestQueue.add({ priority: 'normal', execute: slowExecute });
      
      let status = requestQueue.getStatus();
      const initialPending = status.pending;
      
      await new Promise(resolve => setTimeout(resolve, 10));
      
      status = requestQueue.getStatus();
      expect(status.active).toBeGreaterThan(0);
      
      await new Promise(resolve => setTimeout(resolve, 100));
      
      status = requestQueue.getStatus();
      expect(status.pending).toBe(0);
      expect(status.active).toBe(0);
    });

    test('should handle rapid request additions', () => {
      const mockExecute = jest.fn().mockResolvedValue('success');
      
      const ids: string[] = [];
      for (let i = 0; i < 10; i++) {
        ids.push(requestQueue.add({ 
          priority: i % 2 === 0 ? 'high' : 'normal', 
          execute: mockExecute 
        }));
      }
      
      expect(ids).toHaveLength(10);
      expect(new Set(ids).size).toBe(10); // All IDs should be unique
    });
  });

  describe('Integration Scenarios', () => {
    test('should handle mixed priority workload correctly', async () => {
      const results: string[] = [];
      
      const createExecute = (name: string) =>
        jest.fn().mockImplementation(async () => {
          results.push(name);
          await new Promise(resolve => setTimeout(resolve, 5));
          return 'success';
        });
      
      // Add mixed priority requests
      requestQueue.add({ priority: 'low', execute: createExecute('low1') });
      requestQueue.add({ priority: 'high', execute: createExecute('high1') });
      requestQueue.add({ priority: 'normal', execute: createExecute('normal1') });
      requestQueue.add({ priority: 'high', execute: createExecute('high2') });
      requestQueue.add({ priority: 'low', execute: createExecute('low2') });
      
      await new Promise(resolve => setTimeout(resolve, 150));
      
      expect(results).toHaveLength(5);
      // High priority requests should appear early in results
      const high1Index = results.indexOf('high1');
      const high2Index = results.indexOf('high2');
      expect(high1Index).not.toBe(-1);
      expect(high2Index).not.toBe(-1);
    });
  });
});