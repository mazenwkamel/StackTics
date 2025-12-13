import type { Bed, Box, Placement } from '../api/types';

interface Layout2DViewProps {
  bed: Bed;
  boxes: Box[];
  placements: Placement[];
}

// Color palette for layers (z levels)
const LAYER_COLORS = [
  { fill: '#4CAF50', stroke: '#388E3C' },  // Green - floor
  { fill: '#2196F3', stroke: '#1976D2' },  // Blue - layer 1
  { fill: '#FF9800', stroke: '#F57C00' },  // Orange - layer 2
  { fill: '#E91E63', stroke: '#C2185B' },  // Pink - layer 3
  { fill: '#9C27B0', stroke: '#7B1FA2' },  // Purple - layer 4
];

interface PlacedBoxInfo {
  placement: Placement;
  box: Box;
  // Actual placed dimensions based on orientation
  placedLength: number;
  placedWidth: number;
  placedHeight: number;
  layer: number;
  isRotated: boolean;
  rotationType: string;
}

function getRotationInfo(_box: Box, orientation: Placement['orientation']): { isRotated: boolean; rotationType: string } {
  const { length_axis, width_axis, height_axis } = orientation;

  // No rotation: length→length, width→width, height→height
  if (length_axis === 'length' && width_axis === 'width' && height_axis === 'height') {
    return { isRotated: false, rotationType: '' };
  }

  // Describe the rotation based on what changed
  const changes: string[] = [];

  if (height_axis !== 'height') {
    // Box was tipped - height is now along a different axis
    if (height_axis === 'length') {
      changes.push('tipped forward');
    } else if (height_axis === 'width') {
      changes.push('tipped sideways');
    }
  }

  if (length_axis === 'width' && width_axis === 'length') {
    changes.push('rotated 90°');
  } else if (length_axis !== 'length' || width_axis !== 'width') {
    if (height_axis === 'height') {
      changes.push('rotated 90°');
    }
  }

  // Simplify common rotations
  if (length_axis === 'width' && width_axis === 'length' && height_axis === 'height') {
    return { isRotated: true, rotationType: 'Z 90°' };
  }
  if (length_axis === 'height' && width_axis === 'width' && height_axis === 'length') {
    return { isRotated: true, rotationType: 'Y 90°' };
  }
  if (length_axis === 'length' && width_axis === 'height' && height_axis === 'width') {
    return { isRotated: true, rotationType: 'X 90°' };
  }

  // For more complex rotations, show axis mapping
  return {
    isRotated: true,
    rotationType: `L→${length_axis[0].toUpperCase()}, W→${width_axis[0].toUpperCase()}, H→${height_axis[0].toUpperCase()}`
  };
}

function getPlacedDimensions(box: Box, orientation: Placement['orientation']): [number, number, number] {
  // The orientation tells us which original dimension is aligned with each placed axis
  // e.g., length_axis: "width" means the box's width is now along the bed's length direction
  const dims: Record<string, number> = {
    length: box.length,
    width: box.width,
    height: box.height,
  };

  // Return [placedLength, placedWidth, placedHeight]
  // Each axis tells us which original dimension occupies that placed direction
  return [
    dims[orientation.length_axis],  // What original dim is along placed length?
    dims[orientation.width_axis],   // What original dim is along placed width?
    dims[orientation.height_axis],  // What original dim is along placed height?
  ];
}

function assignLayers(placements: Placement[], boxes: Map<string, Box>): PlacedBoxInfo[] {
  // Sort by z position to assign layers
  const placedInfos: PlacedBoxInfo[] = [];
  const zLevels = new Set<number>();

  for (const placement of placements) {
    const box = boxes.get(placement.box_id);
    if (!box) {
      console.warn(`Layout2DView: No box found for placement box_id="${placement.box_id}"`);
      continue;
    }

    const [placedLength, placedWidth, placedHeight] = getPlacedDimensions(box, placement.orientation);
    const { isRotated, rotationType } = getRotationInfo(box, placement.orientation);
    zLevels.add(Math.round(placement.z * 10) / 10); // Round to avoid floating point issues

    placedInfos.push({
      placement,
      box,
      placedLength,
      placedWidth,
      placedHeight,
      layer: 0, // Will be assigned below
      isRotated,
      rotationType,
    });
  }

  // Assign layer numbers based on z position
  const sortedZLevels = Array.from(zLevels).sort((a, b) => a - b);
  const zToLayer = new Map(sortedZLevels.map((z, i) => [Math.round(z * 10) / 10, i]));

  for (const info of placedInfos) {
    info.layer = zToLayer.get(Math.round(info.placement.z * 10) / 10) || 0;
  }

  // Sort by layer (lower layers first, so higher layers render on top)
  return placedInfos.sort((a, b) => a.layer - b.layer);
}

export function Layout2DView({ bed, boxes, placements }: Layout2DViewProps) {
  const boxesById = new Map(boxes.map((box) => [box.id, box]));
  const svgPadding = 40; // Extra padding for labels
  const maxWidth = 400;
  const maxHeight = 350;

  // Rotated view: bed.width is horizontal (X), bed.length is vertical (Y)
  // Head of bed at top (y=0), foot at bottom (y=length)
  const scale = Math.min(
    (maxWidth - 2 * svgPadding) / bed.width,
    (maxHeight - 2 * svgPadding) / bed.length
  );

  const bedVisualWidth = bed.width * scale;   // Horizontal extent
  const bedVisualHeight = bed.length * scale; // Vertical extent

  const svgWidth = bedVisualWidth + 2 * svgPadding;
  const svgHeight = bedVisualHeight + 2 * svgPadding + 32; // Extra space for legend

  // Transform coordinates: original (x along length, y along width)
  // becomes (x along width = horizontal, y along length = vertical)
  const toSvgX = (origY: number) => svgPadding + origY * scale;  // Original Y -> SVG X
  const toSvgY = (origX: number) => svgPadding + origX * scale;  // Original X -> SVG Y

  const placedBoxes = assignLayers(placements, boxesById);
  const numLayers = Math.max(0, ...placedBoxes.map(p => p.layer)) + 1;

  return (
    <div className="layout-view">
      <h3>Top-Down View</h3>
      <div className="layout-svg-container">
        <svg
          width={svgWidth}
          height={svgHeight}
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="layout-svg"
        >
        {/* Head of bed indicator (top) */}
        <g transform={`translate(${svgPadding + bedVisualWidth / 2}, ${svgPadding - 8})`}>
          <rect
            x="-28"
            y="-14"
            width="56"
            height="18"
            fill="#1f2937"
            rx="4"
          />
          <text
            x="0"
            y="-2"
            textAnchor="middle"
            fontSize="10"
            fontWeight="600"
            fill="white"
            letterSpacing="0.5"
          >
            HEAD
          </text>
        </g>

        {/* Bed outline with corner radius */}
        <rect
          x={svgPadding}
          y={svgPadding}
          width={bedVisualWidth}
          height={bedVisualHeight}
          fill="#fafafa"
          stroke="#374151"
          strokeWidth="2"
          rx={bed.corner_radius * scale}
        />

        {/* Corner exclusion zones - show where boxes can't be placed */}
        {bed.corner_radius > 0 && (
          <>
            {/* Top-left corner */}
            <path
              d={`M ${svgPadding} ${svgPadding + bed.corner_radius * scale}
                  L ${svgPadding} ${svgPadding}
                  L ${svgPadding + bed.corner_radius * scale} ${svgPadding}
                  A ${bed.corner_radius * scale} ${bed.corner_radius * scale} 0 0 0
                    ${svgPadding} ${svgPadding + bed.corner_radius * scale}
                  Z`}
              fill="rgba(239, 68, 68, 0.15)"
              stroke="rgba(239, 68, 68, 0.4)"
              strokeWidth="1"
              strokeDasharray="2 2"
            />
            {/* Top-right corner */}
            <path
              d={`M ${svgPadding + bedVisualWidth - bed.corner_radius * scale} ${svgPadding}
                  L ${svgPadding + bedVisualWidth} ${svgPadding}
                  L ${svgPadding + bedVisualWidth} ${svgPadding + bed.corner_radius * scale}
                  A ${bed.corner_radius * scale} ${bed.corner_radius * scale} 0 0 0
                    ${svgPadding + bedVisualWidth - bed.corner_radius * scale} ${svgPadding}
                  Z`}
              fill="rgba(239, 68, 68, 0.15)"
              stroke="rgba(239, 68, 68, 0.4)"
              strokeWidth="1"
              strokeDasharray="2 2"
            />
            {/* Bottom-left corner */}
            <path
              d={`M ${svgPadding} ${svgPadding + bedVisualHeight - bed.corner_radius * scale}
                  L ${svgPadding} ${svgPadding + bedVisualHeight}
                  L ${svgPadding + bed.corner_radius * scale} ${svgPadding + bedVisualHeight}
                  A ${bed.corner_radius * scale} ${bed.corner_radius * scale} 0 0 0
                    ${svgPadding} ${svgPadding + bedVisualHeight - bed.corner_radius * scale}
                  Z`}
              fill="rgba(239, 68, 68, 0.15)"
              stroke="rgba(239, 68, 68, 0.4)"
              strokeWidth="1"
              strokeDasharray="2 2"
            />
            {/* Bottom-right corner */}
            <path
              d={`M ${svgPadding + bedVisualWidth} ${svgPadding + bedVisualHeight - bed.corner_radius * scale}
                  L ${svgPadding + bedVisualWidth} ${svgPadding + bedVisualHeight}
                  L ${svgPadding + bedVisualWidth - bed.corner_radius * scale} ${svgPadding + bedVisualHeight}
                  A ${bed.corner_radius * scale} ${bed.corner_radius * scale} 0 0 0
                    ${svgPadding + bedVisualWidth} ${svgPadding + bedVisualHeight - bed.corner_radius * scale}
                  Z`}
              fill="rgba(239, 68, 68, 0.15)"
              stroke="rgba(239, 68, 68, 0.4)"
              strokeWidth="1"
              strokeDasharray="2 2"
            />
          </>
        )}

        {/* Margin indicator */}
        {bed.margin > 0 && (
          <rect
            x={svgPadding + bed.margin * scale}
            y={svgPadding + bed.margin * scale}
            width={(bed.width - 2 * bed.margin) * scale}
            height={(bed.length - 2 * bed.margin) * scale}
            fill="none"
            stroke="#aaa"
            strokeWidth="1"
            strokeDasharray="4 2"
          />
        )}

        {/* Grid lines for reference - vertical lines (along width) */}
        {Array.from({ length: Math.floor(bed.width / 50) }).map((_, i) => (
          <line
            key={`vgrid-${i}`}
            x1={svgPadding + (i + 1) * 50 * scale}
            y1={svgPadding}
            x2={svgPadding + (i + 1) * 50 * scale}
            y2={svgPadding + bedVisualHeight}
            stroke="#eee"
            strokeWidth="1"
          />
        ))}
        {/* Horizontal grid lines (along length) */}
        {Array.from({ length: Math.floor(bed.length / 50) }).map((_, i) => (
          <line
            key={`hgrid-${i}`}
            x1={svgPadding}
            y1={svgPadding + (i + 1) * 50 * scale}
            x2={svgPadding + bedVisualWidth}
            y2={svgPadding + (i + 1) * 50 * scale}
            stroke="#eee"
            strokeWidth="1"
          />
        ))}

        {/* Foot of bed indicator (bottom) */}
        <g transform={`translate(${svgPadding + bedVisualWidth / 2}, ${svgPadding + bedVisualHeight + 8})`}>
          <rect
            x="-28"
            y="-4"
            width="56"
            height="18"
            fill="#6b7280"
            rx="4"
          />
          <text
            x="0"
            y="9"
            textAnchor="middle"
            fontSize="10"
            fontWeight="600"
            fill="white"
            letterSpacing="0.5"
          >
            FOOT
          </text>
        </g>

        {/* Placed boxes */}
        {placedBoxes.map((info) => {
          const { placement, box, placedLength, placedWidth, layer, isRotated } = info;
          const colors = LAYER_COLORS[layer % LAYER_COLORS.length];
          // Rotated: placedWidth becomes visual width (horizontal), placedLength becomes visual height (vertical)
          const boxVisualWidth = placedWidth * scale;
          const boxVisualHeight = placedLength * scale;

          // Offset for stacked boxes to show depth
          const stackOffset = layer * 3;

          // Rotated coordinates: placement.y -> SVG X, placement.x -> SVG Y
          const svgX = toSvgX(placement.y) + stackOffset;
          const svgY = toSvgY(placement.x) + stackOffset;

          return (
            <g key={placement.box_id}>
              {/* Shadow for depth effect on stacked boxes */}
              {layer > 0 && (
                <rect
                  x={svgX + 2}
                  y={svgY + 2}
                  width={boxVisualWidth}
                  height={boxVisualHeight}
                  fill="rgba(0,0,0,0.2)"
                  rx="2"
                />
              )}
              {/* Box rectangle */}
              <rect
                x={svgX}
                y={svgY}
                width={boxVisualWidth}
                height={boxVisualHeight}
                fill={colors.fill}
                fillOpacity={0.85}
                stroke={colors.stroke}
                strokeWidth="2"
                rx="2"
              />
              {/* Box label */}
              <text
                x={svgX + boxVisualWidth / 2}
                y={svgY + boxVisualHeight / 2 - 6}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize="11"
                fontWeight="500"
                fill="#fff"
                style={{ textShadow: '0 1px 2px rgba(0,0,0,0.5)' }}
              >
                {box.name.length > 10 ? box.name.slice(0, 10) + '…' : box.name}
              </text>
              {/* Z position label */}
              <text
                x={svgX + boxVisualWidth / 2}
                y={svgY + boxVisualHeight / 2 + 8}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize="9"
                fill="rgba(255,255,255,0.9)"
              >
                z={placement.z}cm
              </text>
              {/* Rotation indicator badge */}
              {isRotated && boxVisualWidth > 30 && boxVisualHeight > 25 && (
                <g>
                  <rect
                    x={svgX + boxVisualWidth - 22}
                    y={svgY + 2}
                    width="20"
                    height="12"
                    fill="rgba(255,255,255,0.9)"
                    rx="2"
                  />
                  <text
                    x={svgX + boxVisualWidth - 12}
                    y={svgY + 10}
                    textAnchor="middle"
                    fontSize="7"
                    fontWeight="600"
                    fill="#1565c0"
                  >
                    ↻
                  </text>
                </g>
              )}
            </g>
          );
        })}

        {/* Dimension labels - Width on top (horizontal), Length on side (vertical) */}
        <text
          x={svgPadding + bedVisualWidth / 2}
          y={svgPadding - 24}
          textAnchor="middle"
          fontSize="11"
          fill="#999"
        >
          {bed.width}cm (width)
        </text>
        <text
          x={svgPadding - 12}
          y={svgPadding + bedVisualHeight / 2}
          textAnchor="middle"
          fontSize="11"
          fill="#999"
          transform={`rotate(-90, ${svgPadding - 12}, ${svgPadding + bedVisualHeight / 2})`}
        >
          {bed.length}cm (length)
        </text>

        {/* Layer legend */}
        {numLayers > 0 && (
          <g transform={`translate(${svgPadding}, ${svgHeight - 28})`}>
            <text x="0" y="0" fontSize="10" fill="#666" fontWeight="500">Layers:</text>
            {Array.from({ length: numLayers }).map((_, i) => {
              const colors = LAYER_COLORS[i % LAYER_COLORS.length];
              return (
                <g key={i} transform={`translate(${50 + i * 70}, -5)`}>
                  <rect
                    width="14"
                    height="14"
                    fill={colors.fill}
                    stroke={colors.stroke}
                    strokeWidth="1"
                    rx="3"
                  />
                  <text x="18" y="11" fontSize="10" fill="#666">
                    {i === 0 ? 'Floor' : `Layer ${i}`}
                  </text>
                </g>
              );
            })}
          </g>
        )}
      </svg>
      </div>

      {placements.length === 0 && (
        <p className="no-placements">No boxes placed yet. Run optimization to see the layout.</p>
      )}

      {placements.length > 0 && (
        <div className="placement-list">
          <h4>Placement Details</h4>
          <table className="placement-table">
            <thead>
              <tr>
                <th>Box</th>
                <th>Position (x, y, z)</th>
                <th>Placed Size (L×W×H)</th>
                <th>Rotation</th>
              </tr>
            </thead>
            <tbody>
              {placedBoxes.map((info) => (
                <tr key={info.placement.box_id}>
                  <td>
                    <span
                      className="layer-dot"
                      style={{ backgroundColor: LAYER_COLORS[info.layer % LAYER_COLORS.length].fill }}
                    />
                    {info.box.name}
                  </td>
                  <td>({info.placement.x}, {info.placement.y}, {info.placement.z})</td>
                  <td>
                    {info.placedLength}×{info.placedWidth}×{info.placedHeight}
                    {info.isRotated && (
                      <span className="original-dims">
                        orig: {info.box.length}×{info.box.width}×{info.box.height}
                      </span>
                    )}
                  </td>
                  <td>
                    <span className={`rotation-badge ${info.isRotated ? '' : 'no-rotation'}`}>
                      {info.isRotated ? info.rotationType : 'None'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
