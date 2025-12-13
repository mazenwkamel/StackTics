"""StackTics FastAPI application entry point."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.api.routes import router
from app.schemas import ErrorResponse, ValidationErrorDetail


app = FastAPI(
    title="StackTics",
    description="API for optimizing box packing under a bed",
    version="0.1.0",
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def format_validation_errors(errors: list) -> ErrorResponse:
    """Convert Pydantic validation errors to our standard format."""
    details = []
    for error in errors:
        # Build field path from location
        loc = error.get("loc", [])
        # Skip 'body' prefix if present
        if loc and loc[0] == "body":
            loc = loc[1:]
        field = ".".join(str(part) for part in loc) if loc else "request"

        # Get a clean error message
        msg = error.get("msg", "Invalid value")

        # Get error type
        error_type = error.get("type", "value_error")

        details.append(ValidationErrorDetail(
            field=field,
            message=msg,
            type=error_type,
        ))

    # Create summary message
    if len(details) == 1:
        summary = details[0].message
    else:
        summary = f"{len(details)} validation errors found"

    return ErrorResponse(
        error="validation_error",
        message=summary,
        details=details,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with user-friendly messages."""
    error_response = format_validation_errors(exc.errors())
    return JSONResponse(
        status_code=422,
        content=error_response.model_dump(),
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions (usually from model validators)."""
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error="validation_error",
            message=str(exc),
            details=[],
        ).model_dump(),
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
