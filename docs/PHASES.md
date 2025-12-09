# StackTics Development Phases

This document outlines the planned development phases for StackTics.

## Phase 0: Environment and Scaffolding (Current)

**Goal**: Establish the foundation for development.

### Completed
- [x] Set up Python FastAPI backend with project structure
- [x] Set up React TypeScript frontend with Vite
- [x] Implement health check endpoint
- [x] Wire up basic request from frontend to backend `/optimize`
- [x] Implement dummy optimizer that returns fixed positions
- [x] Create basic 2D visualization
- [x] Add summary panel with metrics display

### Deliverables
- Working frontend-to-backend communication
- Runnable development environment
- Basic documentation

---

## Phase 1: Domain Modeling and Validation

**Goal**: Solidify data structures and add robust validation.

### Tasks
- [ ] Refine Bed, Box, Settings, Placement models with complete field documentation
- [ ] Add comprehensive input validation for:
  - Dimensions (positive, reasonable ranges)
  - Weights (positive, reasonable ranges)
  - Rotation flags (valid combinations)
  - Priorities (enum validation)
- [ ] Ensure serialization/deserialization works cleanly between backend and frontend
- [ ] Add meaningful error messages that help users fix invalid inputs
- [ ] Implement frontend form validation matching backend rules
- [ ] Add API error response handling in frontend

### Deliverables
- Validated input on both frontend and backend
- Helpful error messages
- Complete type safety

---

## Phase 2: Basic 3D Grid Heuristic

**Goal**: Implement a working packing algorithm.

### Tasks
- [ ] Implement a simple representation of the bed interior:
  - Option A: 3D grid of cells
  - Option B: Free-space list (list of unoccupied rectangular regions)
- [ ] Implement box sorting by composite score:
  - Priority (must_fit first)
  - Access frequency (often-used have slight preference)
  - Volume (larger boxes first for better space utilization)
- [ ] Implement layer-by-layer placement from the floor upward
- [ ] Enforce weight constraints:
  - Heavy boxes below lighter boxes
  - Fragile boxes on top
- [ ] Enforce max_supported_load for boxes in lower layers
- [ ] Ensure placements respect:
  - Margins from bed walls
  - Padding between boxes
  - No overlapping

### Deliverables
- Working packing algorithm
- Correct placement respecting all constraints
- Improved placement vs. simple line-up

---

## Phase 3: Strategy Options

**Goal**: Implement different optimization strategies.

### Maximize Volume Strategy
- [ ] Pack as many boxes as possible
- [ ] Prioritize filling available space completely
- [ ] Accept small gaps if it allows fitting more boxes

### Minimize Holes Strategy
- [ ] Penalize small isolated free pockets
- [ ] Encourage larger contiguous regions of free space
- [ ] May place fewer boxes but with cleaner layout

### Implementation
- [ ] Add fragmentation_score calculation:
  - Count isolated free regions
  - Measure average free region size
  - Weight by region accessibility
- [ ] Integrate strategy selection into placement scoring
- [ ] Reflect strategy effects in metrics

### Deliverables
- User can choose between strategies
- Metrics show strategy impact
- Visible difference in layouts between strategies

---

## Phase 4: Accessibility and Priority Refinement

**Goal**: Make high-priority and frequently used boxes easier to reach.

### Bed Zone Model
- [ ] Define zones based on position:
  - **Foot zone**: Near the foot of the bed (easiest access)
  - **Edge zone**: Along the sides
  - **Center zone**: Deep in the middle (hard to reach)
  - **Head zone**: Near the headboard (hardest)
- [ ] Assign accessibility scores to each zone

### Placement Rules
- [ ] High priority + often used: Place in foot/edge zones
- [ ] High priority + rarely used: Any zone, but prefer stable positions
- [ ] Optional + often used: Edges if space allows
- [ ] Optional + rarely used: Center/head zones

### Implementation
- [ ] Modify placement scoring to include zone accessibility
- [ ] Weight accessibility by `accessibility_preference` setting
- [ ] Show placement reasoning in summary panel

### Deliverables
- Frequently used boxes are accessible
- Summary explains why boxes were placed where they are
- Users can tune accessibility vs. space trade-off

---

## Phase 5: Visualization Improvements

**Goal**: Make the layout easier to understand.

### Layout2DView Enhancements
- [ ] Correct scaling based on bed dimensions
- [ ] Fit viewport with proper aspect ratio
- [ ] Show layer information:
  - Label showing "Layer 1", "Layer 2"
  - Visual differentiation (opacity or pattern)
- [ ] Color coding:
  - By fragility (green/yellow/red)
  - By access frequency (bright to dim)
  - By priority (solid vs. dashed border)
- [ ] Hover tooltips showing box details

### Packing Guide
- [ ] Generate step-by-step instructions:
  ```
  1. Place "Winter Clothes" (60x40x25) at floor, position (5, 5)
  2. Place "Photo Albums" (35x30x20) at floor, position (66, 5)
  3. Place "Shoes Box" (40x30x15) on top of "Winter Clothes"
  ```
- [ ] Include orientation if box was rotated
- [ ] Add warnings for weight/fragility concerns

### Deliverables
- Clear, informative visualization
- Printable packing instructions
- At-a-glance understanding of layout

---

## Phase 6: Refinement and Packaging

**Goal**: Polish the application for regular use.

### Configuration
- [ ] Add settings page for defaults:
  - Default padding between boxes
  - Default margin from bed edges
  - Default max_supported_load per fragility category
- [ ] Persist settings to localStorage or JSON file

### Error Handling
- [ ] Graceful handling of backend errors
- [ ] Retry logic for transient failures
- [ ] Clear error messages in UI

### Running the Application
- [ ] Update documentation with complete setup instructions
- [ ] Create `start.sh` / `start.bat` script to launch both services
- [ ] Add production build instructions

### Polish
- [ ] Responsive design improvements
- [ ] Keyboard navigation
- [ ] Loading states and animations
- [ ] Save/load configurations

### Deliverables
- Production-ready application
- Easy to start and use
- Complete documentation

---

## Future Phases (Ideas)

### Phase 7: 3D Visualization
- Interactive 3D view with Three.js or similar
- Rotate and zoom the layout
- Click boxes to see details

### Phase 8: Export and Sharing
- Export configurations as JSON
- Import saved configurations
- Share configurations via URL

### Phase 9: Machine Learning Enhancement
- Learn from user adjustments
- Suggest improvements
- Personalized preferences

### Phase 10: Multi-Storage Support
- Multiple storage areas (closet, garage)
- Move boxes between areas
- Global inventory management
