"""StackTics FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router


app = FastAPI(
    title="StackTics",
    description="API for optimizing box packing under a bed",
    version="0.1.0",
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API router
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint with basic info."""
    return {
        "app": "StackTics",
        "version": "0.1.0",
        "docs": "/docs",
    }
