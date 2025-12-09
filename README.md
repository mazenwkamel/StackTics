# StackTics

A local application that helps you optimally organize boxes under a bed based on size, weight, fragility, and how often you need to access them.

## Overview

StackTics solves the common problem of organizing under-bed storage efficiently. Instead of randomly shoving boxes under your bed, StackTics calculates the optimal arrangement considering:

- **Physical constraints**: Box dimensions, weight limits, and available space
- **Fragility**: Heavy boxes go on the bottom; fragile items are protected
- **Accessibility**: Frequently used items are placed near the edges for easy access
- **Space optimization**: Minimize wasted space or fragmented gaps

## Prerequisites

- **Python 3.11+** for the backend
- **Node.js 18+** for the frontend

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

## Project Structure

```
StackTics/
├── backend/          # Python FastAPI backend
├── frontend/         # React TypeScript frontend
└── docs/             # Documentation
    ├── README.md
    ├── ARCHITECTURE.md
    ├── API_CONTRACT.md
    └── PHASES.md
```

## Documentation

See the [docs](docs/) folder for complete documentation:

- [Project Overview](docs/README.md)
- [Architecture](docs/ARCHITECTURE.md)
- [API Contract](docs/API_CONTRACT.md)
- [Development Phases](docs/PHASES.md)

## License

MIT
