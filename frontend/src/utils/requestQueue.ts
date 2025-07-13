// Request queue manager to prioritize critical requests
interface QueuedRequest {
  id: string;
  priority: 'high' | 'normal' | 'low';
  execute: () => Promise<any>;
  timestamp: number;
}

class RequestQueueManager {
  private queue: QueuedRequest[] = [];
  private activeRequests = 0;
  private maxConcurrent = 3; // Allow 3 concurrent requests
  private processing = false;

  // Add a request to the queue
  add(request: Omit<QueuedRequest, 'id' | 'timestamp'>): string {
    const id = `req-${Date.now()}-${Math.random()}`;
    const queuedRequest: QueuedRequest = {
      ...request,
      id,
      timestamp: Date.now(),
    };

    // Add to queue based on priority
    if (request.priority === 'high') {
      // High priority goes to front
      this.queue.unshift(queuedRequest);
    } else {
      // Normal and low priority go to back
      this.queue.push(queuedRequest);
    }

    console.log(`📥 Request queued [${id}] with priority: ${request.priority}`);
    this.processQueue();
    
    return id;
  }

  // Process the queue
  private async processQueue() {
    if (this.processing || this.activeRequests >= this.maxConcurrent) {
      return;
    }

    this.processing = true;

    while (this.queue.length > 0 && this.activeRequests < this.maxConcurrent) {
      const request = this.queue.shift();
      if (!request) continue;

      this.activeRequests++;
      console.log(`🚀 Processing request [${request.id}] - Active: ${this.activeRequests}`);

      // Execute the request
      request.execute()
        .then(() => {
          console.log(`✅ Request completed [${request.id}]`);
        })
        .catch((error) => {
          console.error(`❌ Request failed [${request.id}]:`, error);
        })
        .finally(() => {
          this.activeRequests--;
          console.log(`📊 Active requests: ${this.activeRequests}`);
          
          // Process next request
          if (this.queue.length > 0) {
            this.processQueue();
          }
        });
    }

    this.processing = false;
  }

  // Cancel a request if it's still in queue
  cancel(id: string): boolean {
    const index = this.queue.findIndex(req => req.id === id);
    if (index !== -1) {
      this.queue.splice(index, 1);
      console.log(`🛑 Request cancelled [${id}]`);
      return true;
    }
    return false;
  }

  // Clear all pending requests
  clearQueue() {
    const count = this.queue.length;
    this.queue = [];
    console.log(`🧹 Cleared ${count} pending requests`);
  }

  // Get queue status
  getStatus() {
    return {
      pending: this.queue.length,
      active: this.activeRequests,
      maxConcurrent: this.maxConcurrent,
    };
  }
}

// Create singleton instance
export const requestQueue = new RequestQueueManager();