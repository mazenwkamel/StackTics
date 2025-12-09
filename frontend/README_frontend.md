# StackTics Frontend

React TypeScript frontend for the StackTics box packing optimization tool.

## Requirements

- Node.js 18 or later
- npm or yarn

## Setup

1. Install dependencies:

```bash
cd frontend
npm install
```

## Running the Development Server

```bash
npm run dev
```

The app will be available at http://localhost:5173

Make sure the backend is running at http://localhost:8000 before using the app.

## Building for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

## Project Structure

```
frontend/
├── src/
│   ├── main.tsx           # React entry point
│   ├── App.tsx            # Main app component
│   ├── App.css            # Global styles
│   ├── api/
│   │   ├── types.ts       # TypeScript interfaces
│   │   └── client.ts      # HTTP client for backend
│   └── components/
│       ├── BedConfigForm.tsx       # Bed dimension input
│       ├── BoxListEditor.tsx       # Box list management
│       ├── PackingSettingsForm.tsx # Strategy settings
│       ├── Layout2DView.tsx        # 2D visualization
│       └── SummaryPanel.tsx        # Results display
├── index.html
├── package.json
├── tsconfig.json
├── tsconfig.node.json
├── vite.config.ts
└── README_frontend.md
```

## Components

### BedConfigForm
Input form for bed dimensions (length, width, height) and margin from edges.

### BoxListEditor
Table/list interface for adding and editing boxes with all their properties:
- Name and dimensions
- Weight and fragility
- Access frequency and priority
- Rotation flags

### PackingSettingsForm
Settings for the optimization:
- Strategy selection (maximize volume or minimize holes)
- Accessibility preference slider
- Padding between boxes

### Layout2DView
SVG-based top-down visualization of the bed and placed boxes. Each box is shown as a colored rectangle with its name.

### SummaryPanel
Displays optimization results:
- Total, placed, and unplaced box counts
- Volume utilization metrics
- List of boxes that couldn't be placed
