# StackTics Architecture

## Overview

StackTics is a local application with a client-server architecture:

- **Frontend**: React TypeScript single-page application
- **Backend**: Python FastAPI REST API

Both run locally on the user's machine. The frontend communicates with the backend via HTTP requests.

## System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         User's Browser                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    React Frontend                          │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐    │  │
│  │  │ BedConfig   │  │ BoxList     │  │ PackingSettings │    │  │
│  │  │ Form        │  │ Editor      │  │ Form            │    │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘    │  │
│  │                         │                                  │  │
│  │                         ▼                                  │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │                   App.tsx (State)                    │  │  │
│  │  │  bed, boxes, settings, placements, metrics          │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │                         │                                  │  │
│  │         ┌───────────────┴───────────────┐                 │  │
│  │         ▼                               ▼                 │  │
│  │  ┌─────────────┐                 ┌─────────────┐          │  │
│  │  │ Layout2D    │                 │ Summary     │          │  │
│  │  │ View        │                 │ Panel       │          │  │
│  │  └─────────────┘                 └─────────────┘          │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP (POST /optimize)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    API Layer (routes.py)                   │  │
│  │  POST /optimize  ──────────────────────────────────────►  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Schema Validation (schemas.py)                │  │
│  │  OptimizeRequest → Domain Models                          │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                 Optimizer (engine.py)                      │  │
│  │  optimize_packing(bed, boxes, settings)                   │  │
│  │     → placements, unplaced_box_ids, metrics               │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. User Input

The user interacts with three main forms:

- **BedConfigForm**: Defines the container (bed) dimensions
- **BoxListEditor**: Adds/edits boxes with all their properties
- **PackingSettingsForm**: Chooses strategy and preferences

All form data is managed in `App.tsx` state.

### 2. Optimization Request

When the user clicks "Optimize Packing":

1. Frontend collects `bed`, `boxes`, and `settings` from state
2. Constructs an `OptimizeRequest` object
3. Sends POST request to `http://localhost:8000/optimize`

### 3. Backend Processing

1. **routes.py**: Receives request, validates with Pydantic schemas
2. **schemas.py → models.py**: Converts API schemas to domain models
3. **engine.py**: Runs `optimize_packing()` algorithm
4. Returns domain models converted back to response schemas

### 4. Response Display

1. Frontend receives `OptimizeResponse`
2. Updates state with `placements`, `unplaced_box_ids`, `metrics`
3. **Layout2DView**: Renders SVG visualization of placements
4. **SummaryPanel**: Shows metrics and lists unplaced boxes

## Code Separation

### Domain Models (models.py)

Internal Python dataclasses representing the core domain:

- `Bed`: Container dimensions
- `Box`: Item to pack with all properties
- `Settings`: Algorithm configuration
- `Placement`: Where a box was placed
- `Orientation`: How a box is rotated

These are used by the optimizer and can evolve independently of the API.

### API Schemas (schemas.py)

Pydantic models for request/response serialization:

- `BedSchema`, `BoxSchema`, `SettingsSchema`
- `PlacementSchema`, `OrientationSchema`, `MetricsSchema`
- `OptimizeRequest`, `OptimizeResponse`

These define the API contract and handle validation.

### TypeScript Interfaces (types.ts)

Frontend types that mirror the API schemas:

- `Bed`, `Box`, `Settings`
- `Placement`, `Orientation`, `Metrics`
- `OptimizeRequest`, `OptimizeResponse`

Must stay synchronized with backend schemas.

### Optimization Engine (engine.py)

The core algorithm, currently a simple stub:

```python
def optimize_packing(
    bed: Bed,
    boxes: list[Box],
    settings: Settings,
) -> tuple[list[Placement], list[str], dict]:
```

Returns:
- `placements`: List of where each box goes
- `unplaced_box_ids`: Boxes that couldn't fit
- `metrics`: Statistics about the packing

## Key Design Decisions

### Monorepo Structure

Backend and frontend in the same repo allows:
- Coordinated versioning
- Shared documentation
- Easier development workflow

### REST API

Simple REST over HTTP chosen for:
- Easy debugging (curl, browser tools)
- No need for real-time updates
- Familiar patterns

### State Management

React useState for simplicity:
- No external state library needed yet
- All state in App.tsx
- Easy to reason about

### SVG Visualization

SVG chosen for Layout2DView:
- Vector graphics scale cleanly
- Easy to add interactivity later
- No canvas complexity

## Future Considerations

### Planned Extensions

- 3D visualization (Three.js or similar)
- Multiple layers display
- Export/import configurations
- Undo/redo support

### Scalability

Current design handles typical home use (10-50 boxes). For larger scale:
- Consider WebWorkers for heavy computation
- Implement pagination for box lists
- Add caching for repeated calculations
