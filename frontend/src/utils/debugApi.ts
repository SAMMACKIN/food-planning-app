// Debug utility to track API requests
class ApiDebugger {
  private activeRequests: Map<string, { start: number; url: string }> = new Map();
  private requestCount = 0;

  startRequest(url: string): string {
    const id = `req-${++this.requestCount}`;
    this.activeRequests.set(id, { start: Date.now(), url });
    console.log(`🚀 API Request Started [${id}]: ${url} (${this.activeRequests.size} active)`);
    this.logActiveRequests();
    return id;
  }

  endRequest(id: string, success: boolean) {
    const req = this.activeRequests.get(id);
    if (req) {
      const duration = Date.now() - req.start;
      console.log(`${success ? '✅' : '❌'} API Request Ended [${id}]: ${req.url} (${duration}ms)`);
      this.activeRequests.delete(id);
      this.logActiveRequests();
    }
  }

  cancelRequest(id: string) {
    const req = this.activeRequests.get(id);
    if (req) {
      console.log(`🛑 API Request Cancelled [${id}]: ${req.url}`);
      this.activeRequests.delete(id);
      this.logActiveRequests();
    }
  }

  private logActiveRequests() {
    if (this.activeRequests.size > 0) {
      console.log('📊 Active Requests:', Array.from(this.activeRequests.entries()).map(([id, req]) => ({
        id,
        url: req.url,
        duration: `${Date.now() - req.start}ms`
      })));
    }
  }

  getActiveRequestCount(): number {
    return this.activeRequests.size;
  }
}

export const apiDebugger = new ApiDebugger();