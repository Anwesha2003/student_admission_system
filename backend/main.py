from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Dict, Any
import uvicorn
import os

# Import routers
from routers import admission ,document ,loan ,student

# Import database client
from database.chroma_client import initialize_chroma_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database on startup
    initialize_chroma_db()
    yield
    # Cleanup on shutdown

# Create FastAPI app
app = FastAPI(
    title="Student Admission System API",
    description="API for automating the student admission process",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(admission.router, prefix="/api/admissions", tags=["admissions"])
app.include_router(document.router, prefix="/api/documents", tags=["documents"])
app.include_router(loan.router, prefix="/api/loans", tags=["loans"])
app.include_router(student.router, prefix="/api/students", tags=["students"])

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Student Admission System API"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)