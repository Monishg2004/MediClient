
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
import os
from app import router as api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Ensure storage directories exist
os.makedirs("storage", exist_ok=True)
os.makedirs("storage/conversations", exist_ok=True)

# Initialize FastAPI app
app = FastAPI(title="MediCompanion API")

# Configure CORS - FIXED VERSION
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or more specifically ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Include API routes
app.include_router(api_router, prefix="/api")

# Root endpoint
@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {"message": "MediCompanion API is running"}

# Health check endpoint
@app.get("/health")
async def health_check():
    logger.info("Health check endpoint called")
    return {"status": "healthy"}

if __name__ == "__main__":
    logger.info("Starting MediCompanion API server on port 5000")
    uvicorn.run(app, host="0.0.0.0", port=5000)
