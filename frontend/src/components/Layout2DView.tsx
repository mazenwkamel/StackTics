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
  const svgPadding = 24;
  const maxWidth = 450;
  const maxHeight = 280;

  const scale = Math.min(
    (maxWidth - 2 * svgPadding) / bed.length,
    (maxHeight - 2 * svgPadding) / bed.width
  );

  const svgWidth = bed.length * scale + 2 * svgPadding;
  const svgHeight = bed.width * scale + 2 * svgPadding + 28; // Extra space for legend

  const toSvgX = (x: number) => svgPadding + x * scale;
  const toSvgY = (y: number) => svgPadding + y * scale;

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
        {/* Bed outline */}
        <rect
          x={svgPadding}
          y={svgPadding}
          width={bed.length * scale}
          height={bed.width * scale}
          fill="#fafafa"
          stroke="#333"
          strokeWidth="2"
        />

        {/* Margin indicator */}
        {bed.margin > 0 && (
          <rect
            x={svgPadding + bed.margin * scale}
            y={svgPadding + bed.margin * scale}
            width={(bed.length - 2 * bed.margin) * scale}
            height={(bed.width - 2 * bed.margin) * scale}
            fill="none"
            stroke="#aaa"
            strokeWidth="1"
            strokeDasharray="4 2"
          />
        )}

        {/* Grid lines for reference */}
        {Array.from({ length: Math.floor(bed.length / 50) }).map((_, i) => (
          <line
            key={`vgrid-${i}`}
            x1={toSvgX((i + 1) * 50)}
            y1={svgPadding}
            x2={toSvgX((i + 1) * 50)}
            y2={svgPadding + bed.width * scale}
            stroke="#eee"
            strokeWidth="1"
          />
        ))}
        {Array.from({ length: Math.floor(bed.width / 50) }).map((_, i) => (
          <line
            key={`hgrid-${i}`}
            x1={svgPadding}
            y1={toSvgY((i + 1) * 50)}
            x2={svgPadding + bed.length * scale}
            y2={toSvgY((i + 1) * 50)}
            stroke="#eee"
            strokeWidth="1"
          />
        ))}

        {/* Placed boxes */}
        {placedBoxes.map((info) => {
          const { placement, box, placedLength, placedWidth, layer, isRotated } = info;
          const colors = LAYER_COLORS[layer % LAYER_COLORS.length];
          const boxWidth = placedLength * scale;
          const boxHeight = placedWidth * scale;

          // Offset for stacked boxes to show depth
          const stackOffset = layer * 3;

          return (
            <g key={placement.box_id}>
              {/* Shadow for depth effect on stacked boxes */}
              {layer > 0 && (
                <rect
                  x={toSvgX(placement.x) + stackOffset + 2}
                  y={toSvgY(placement.y) + stackOffset + 2}
                  width={boxWidth}
                  height={boxHeight}
                  fill="rgba(0,0,0,0.2)"
                  rx="0"
                />
              )}
              {/* Box rectangle */}
              <rect
                x={toSvgX(placement.x) + stackOffset}
                y={toSvgY(placement.y) + stackOffset}
                width={boxWidth}
                height={boxHeight}
                fill={colors.fill}
                fillOpacity={0.85}
                stroke={colors.stroke}
                strokeWidth="2"
                rx="0"
              />
              {/* Box label */}
              <text
                x={toSvgX(placement.x) + stackOffset + boxWidth / 2}
                y={toSvgY(placement.y) + stackOffset + boxHeight / 2 - 6}
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
                x={toSvgX(placement.x) + stackOffset + boxWidth / 2}
                y={toSvgY(placement.y) + stackOffset + boxHeight / 2 + 8}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize="9"
                fill="rgba(255,255,255,0.9)"
              >
                z={placement.z}cm
              </text>
              {/* Rotation indicator badge */}
              {isRotated && boxWidth > 30 && boxHeight > 25 && (
                <g>
                  <rect
                    x={toSvgX(placement.x) + stackOffset + boxWidth - 22}
                    y={toSvgY(placement.y) + stackOffset + 2}
                    width="20"
                    height="12"
                    fill="rgba(255,255,255,0.9)"
                    rx="0"
                  />
                  <text
                    x={toSvgX(placement.x) + stackOffset + boxWidth - 12}
                    y={toSvgY(placement.y) + stackOffset + 10}
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

        {/* Dimension labels */}
        <text
          x={svgPadding + (bed.length * scale) / 2}
          y={svgPadding - 8}
          textAnchor="middle"
          fontSize="11"
          fill="#666"
        >
          {bed.length}cm
        </text>
        <text
          x={svgPadding - 8}
          y={svgPadding + (bed.width * scale) / 2}
          textAnchor="middle"
          fontSize="11"
          fill="#666"
          transform={`rotate(-90, ${svgPadding - 8}, ${svgPadding + (bed.width * scale) / 2})`}
        >
          {bed.width}cm
        </text>

        {/* Layer legend */}
        {numLayers > 0 && (
          <g transform={`translate(${svgPadding}, ${svgHeight - 30})`}>
            <text x="0" y="0" fontSize="10" fill="#666">Layers:</text>
            {Array.from({ length: numLayers }).map((_, i) => {
              const colors = LAYER_COLORS[i % LAYER_COLORS.length];
              return (
                <g key={i} transform={`translate(${50 + i * 70}, -5)`}>
                  <rect
                    width="16"
                    height="16"
                    fill={colors.fill}
                    stroke={colors.stroke}
                    strokeWidth="1"
                    rx="0"
                  />
                  <text x="20" y="12" fontSize="10" fill="#666">
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
