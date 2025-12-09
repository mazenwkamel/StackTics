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

## Installation

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Frontend

```bash
cd frontend
npm install
```

## Running the Application

### Start the Backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

The API will be available at http://localhost:8000

### Start the Frontend

```bash
cd frontend
npm run dev
```

The UI will be available at http://localhost:5173

## Quick Start

1. Start both backend and frontend servers
2. Open http://localhost:5173 in your browser
3. Configure your bed dimensions (length, width, height, margin)
4. Add boxes with their properties (dimensions, weight, fragility, etc.)
5. Choose a packing strategy
6. Click "Optimize Packing" to see the results

## Example API Request

```json
{
  "bed": {
    "length": 200,
    "width": 150,
    "height": 30,
    "margin": 5
  },
  "boxes": [
    {
      "id": "box1",
      "name": "Winter Clothes",
      "length": 60,
      "width": 40,
      "height": 25,
      "weight": 8,
      "fragility": "robust",
      "access_frequency": "rare",
      "priority": "must_fit",
      "can_rotate_x": true,
      "can_rotate_y": true,
      "can_rotate_z": true
    },
    {
      "id": "box2",
      "name": "Photo Albums",
      "length": 35,
      "width": 30,
      "height": 20,
      "weight": 3,
      "fragility": "fragile",
      "access_frequency": "sometimes",
      "priority": "optional",
      "can_rotate_x": true,
      "can_rotate_y": true,
      "can_rotate_z": true
    }
  ],
  "settings": {
    "strategy": "maximize_volume",
    "accessibility_preference": 0.5,
    "padding": 1,
    "margin": 0
  }
}
```

## Example API Response

```json
{
  "placements": [
    {
      "box_id": "box1",
      "x": 5,
      "y": 5,
      "z": 0,
      "orientation": {
        "length_axis": "length",
        "width_axis": "width",
        "height_axis": "height"
      }
    },
    {
      "box_id": "box2",
      "x": 66,
      "y": 5,
      "z": 0,
      "orientation": {
        "length_axis": "length",
        "width_axis": "width",
        "height_axis": "height"
      }
    }
  ],
  "unplaced_box_ids": [],
  "metrics": {
    "total_boxes": 2,
    "placed_boxes": 2,
    "used_volume_ratio": 0.1234,
    "free_volume_ratio": 0.8766,
    "fragmentation_score": 0
  }
}
```

## Project Structure

```
StackTics/
├── backend/               # Python FastAPI backend
│   ├── app/
│   │   ├── main.py       # App entry point
│   │   ├── models.py     # Domain models
│   │   ├── schemas.py    # API schemas
│   │   ├── api/          # Route handlers
│   │   └── optimizer/    # Packing algorithm
│   └── tests/
├── frontend/             # React TypeScript frontend
│   └── src/
│       ├── api/          # API client
│       └── components/   # React components
└── docs/                 # Documentation
```

## Documentation

- [Architecture](ARCHITECTURE.md) - System design and data flow
- [API Contract](API_CONTRACT.md) - Complete API specification
- [Development Phases](PHASES.md) - Roadmap for future development

## License

MIT
