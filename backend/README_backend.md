# StackTics Backend

Python FastAPI backend for the StackTics box packing optimization tool.

## Requirements

- Python 3.11 or later
- pip or uv for package management

## Setup

1. Create a virtual environment:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -e ".[dev]"
```

Or using uv:

```bash
uv pip install -e ".[dev]"
```

## Running the Server

Start the development server:

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at:
- http://localhost:8000 - Root endpoint
- http://localhost:8000/health - Health check
- http://localhost:8000/docs - Interactive API documentation (Swagger UI)
- http://localhost:8000/redoc - Alternative API documentation

## API Endpoints

### GET /health
Returns the health status of the application.

```json
{
  "status": "ok",
  "app": "StackTics"
}
```

### POST /optimize
Runs the packing optimization algorithm.

See `docs/API_CONTRACT.md` for the full request and response schema.

## Running Tests

```bash
pytest
```

Or with verbose output:

```bash
pytest -v
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app entry point
│   ├── models.py        # Domain models (dataclasses)
│   ├── schemas.py       # Pydantic schemas for API
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py    # API route handlers
│   └── optimizer/
│       ├── __init__.py
│       └── engine.py    # Packing algorithm
├── tests/
│   ├── __init__.py
│   └── test_optimizer_smoke.py
├── pyproject.toml
└── README_backend.md
```
