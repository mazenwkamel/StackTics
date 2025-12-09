# StackTics API Contract

This document defines the JSON structures used by the StackTics API.

## Base URL

```
http://localhost:8000
```

## Endpoints

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "app": "StackTics"
}
```

### POST /optimize

Run the packing optimization algorithm.

## Request Structure

```json
{
  "bed": { ... },
  "boxes": [ ... ],
  "settings": { ... }
}
```

### Bed Object

Defines the container (space under the bed) dimensions.

| Field   | Type   | Required | Description |
|---------|--------|----------|-------------|
| length  | number | Yes      | Length in cm (head to foot direction) |
| width   | number | Yes      | Width in cm (across the bed) |
| height  | number | Yes      | Height in cm (vertical clearance) |
| margin  | number | No       | Margin from all edges in cm (default: 0) |

**Example:**
```json
{
  "length": 200,
  "width": 150,
  "height": 30,
  "margin": 5
}
```

### Box Object

Defines a box to be packed.

| Field              | Type    | Required | Description |
|--------------------|---------|----------|-------------|
| id                 | string  | Yes      | Unique identifier |
| name               | string  | Yes      | Display name |
| length             | number  | Yes      | Length in cm |
| width              | number  | Yes      | Width in cm |
| height             | number  | Yes      | Height in cm |
| weight             | number  | Yes      | Weight in kg |
| fragility          | string  | No       | "robust", "normal", "fragile" (default: "normal") |
| access_frequency   | string  | No       | "rare", "sometimes", "often" (default: "sometimes") |
| priority           | string  | No       | "must_fit", "optional" (default: "optional") |
| can_rotate_x       | boolean | No       | Can rotate around X axis (default: true) |
| can_rotate_y       | boolean | No       | Can rotate around Y axis (default: true) |
| can_rotate_z       | boolean | No       | Can rotate around Z axis (default: true) |
| max_supported_load | number  | No       | Maximum weight on top in kg (auto-derived from fragility if not set) |

**Fragility Values:**
- `robust`: Can support up to 50 kg on top
- `normal`: Can support up to 20 kg on top
- `fragile`: Can support up to 5 kg on top

**Access Frequency Values:**
- `rare`: Accessed less than once a month
- `sometimes`: Accessed a few times a month
- `often`: Accessed weekly or more

**Priority Values:**
- `must_fit`: Must be placed, algorithm prioritizes these
- `optional`: Place if space allows

**Example:**
```json
{
  "id": "box-winter-clothes",
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
  "can_rotate_z": true,
  "max_supported_load": 50
}
```

### Settings Object

Configuration for the optimization algorithm.

| Field                    | Type   | Required | Description |
|--------------------------|--------|----------|-------------|
| strategy                 | string | No       | "maximize_volume" or "minimize_holes" (default: "maximize_volume") |
| accessibility_preference | number | No       | 0.0 (compact) to 1.0 (accessible) (default: 0.5) |
| padding                  | number | No       | Space between boxes in cm (default: 1) |
| margin                   | number | No       | Additional margin from bed edges in cm (default: 0) |

**Strategy Values:**
- `maximize_volume`: Pack as many boxes as possible, use maximum space
- `minimize_holes`: Prefer layouts with fewer fragmented gaps

**Example:**
```json
{
  "strategy": "maximize_volume",
  "accessibility_preference": 0.7,
  "padding": 1,
  "margin": 0
}
```

## Response Structure

```json
{
  "placements": [ ... ],
  "unplaced_box_ids": [ ... ],
  "metrics": { ... }
}
```

### Placement Object

Describes where and how a box was placed.

| Field       | Type   | Description |
|-------------|--------|-------------|
| box_id      | string | ID of the placed box |
| x           | number | X position in cm (along bed length, 0 = foot of bed) |
| y           | number | Y position in cm (across bed width, 0 = left edge) |
| z           | number | Z position in cm (vertical, 0 = floor) |
| orientation | object | How the box is oriented |

### Orientation Object

Describes how the box's dimensions are mapped to the bed's coordinate system.

| Field       | Type   | Description |
|-------------|--------|-------------|
| length_axis | string | Which box dimension aligns with bed length ("length", "width", or "height") |
| width_axis  | string | Which box dimension aligns with bed width |
| height_axis | string | Which box dimension aligns with vertical |

**Example Placement:**
```json
{
  "box_id": "box-winter-clothes",
  "x": 5,
  "y": 5,
  "z": 0,
  "orientation": {
    "length_axis": "length",
    "width_axis": "width",
    "height_axis": "height"
  }
}
```

### Metrics Object

Statistics about the packing result.

| Field               | Type   | Description |
|---------------------|--------|-------------|
| total_boxes         | number | Total number of boxes in the request |
| placed_boxes        | number | Number of boxes successfully placed |
| used_volume_ratio   | number | Ratio of bed volume occupied by boxes (0.0 to 1.0) |
| free_volume_ratio   | number | Ratio of bed volume that is free (0.0 to 1.0) |
| fragmentation_score | number | How fragmented the free space is (lower is better) |

**Example:**
```json
{
  "total_boxes": 5,
  "placed_boxes": 4,
  "used_volume_ratio": 0.45,
  "free_volume_ratio": 0.55,
  "fragmentation_score": 0.2
}
```

## Complete Example

### Request

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
      "name": "Books",
      "length": 35,
      "width": 25,
      "height": 30,
      "weight": 12,
      "fragility": "robust",
      "access_frequency": "sometimes",
      "priority": "must_fit",
      "can_rotate_x": true,
      "can_rotate_y": true,
      "can_rotate_z": false
    },
    {
      "id": "box3",
      "name": "Decorations",
      "length": 50,
      "width": 40,
      "height": 35,
      "weight": 3,
      "fragility": "fragile",
      "access_frequency": "rare",
      "priority": "optional",
      "can_rotate_x": false,
      "can_rotate_y": false,
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

### Response

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
  "unplaced_box_ids": ["box3"],
  "metrics": {
    "total_boxes": 3,
    "placed_boxes": 2,
    "used_volume_ratio": 0.15,
    "free_volume_ratio": 0.85,
    "fragmentation_score": 0.33
  }
}
```

## Error Responses

### Validation Error (422)

When request data is invalid:

```json
{
  "detail": [
    {
      "loc": ["body", "boxes", 0, "length"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt"
    }
  ]
}
```

### Server Error (500)

When an unexpected error occurs:

```json
{
  "detail": "Internal server error"
}
```
