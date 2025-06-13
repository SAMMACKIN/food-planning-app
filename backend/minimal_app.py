from fastapi import FastAPI
import os
import uvicorn

app = FastAPI(title="Food Planning API - Minimal")

@app.get("/")
async def root():
    return {"message": "Food Planning App API - Minimal Version", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "Minimal app is working"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting minimal app on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)