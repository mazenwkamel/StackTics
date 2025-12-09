import type { Bed, Box, Placement } from '../api/types';

interface Layout2DViewProps {
  bed: Bed;
  boxes: Box[];
  placements: Placement[];
}

// Color palette for boxes
const BOX_COLORS = [
  '#4CAF50', '#2196F3', '#FF9800', '#E91E63', '#9C27B0',
  '#00BCD4', '#FFEB3B', '#795548', '#607D8B', '#F44336',
];

export function Layout2DView({ bed, boxes, placements }: Layout2DViewProps) {
  const boxesById = new Map(boxes.map((box) => [box.id, box]));
  const padding = 20;
  const scale = Math.min(
    (400 - 2 * padding) / bed.length,
    (300 - 2 * padding) / bed.width
  );

  const svgWidth = bed.length * scale + 2 * padding;
  const svgHeight = bed.width * scale + 2 * padding;

  // Transform coordinates: origin at top-left of SVG, y increases downward
  const toSvgX = (x: number) => padding + x * scale;
  const toSvgY = (y: number) => padding + y * scale;

  return (
    <div className="layout-view">
      <h3>Top-Down View</h3>
      <svg
        width={svgWidth}
        height={svgHeight}
        viewBox={`0 0 ${svgWidth} ${svgHeight}`}
        className="layout-svg"
      >
        {/* Bed outline */}
        <rect
          x={padding}
          y={padding}
          width={bed.length * scale}
          height={bed.width * scale}
          fill="#f5f5f5"
          stroke="#333"
          strokeWidth="2"
        />

        {/* Margin indicator */}
        {bed.margin > 0 && (
          <rect
            x={padding + bed.margin * scale}
            y={padding + bed.margin * scale}
            width={(bed.length - 2 * bed.margin) * scale}
            height={(bed.width - 2 * bed.margin) * scale}
            fill="none"
            stroke="#999"
            strokeWidth="1"
            strokeDasharray="4"
          />
        )}

        {/* Placed boxes */}
        {placements.map((placement, index) => {
          const box = boxesById.get(placement.box_id);
          if (!box) return null;

          const color = BOX_COLORS[index % BOX_COLORS.length];

          return (
            <g key={placement.box_id}>
              <rect
                x={toSvgX(placement.x)}
                y={toSvgY(placement.y)}
                width={box.length * scale}
                height={box.width * scale}
                fill={color}
                fillOpacity="0.7"
                stroke={color}
                strokeWidth="2"
              />
              <text
                x={toSvgX(placement.x) + (box.length * scale) / 2}
                y={toSvgY(placement.y) + (box.width * scale) / 2}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize="10"
                fill="#000"
              >
                {box.name.length > 8 ? box.name.slice(0, 8) + '...' : box.name}
              </text>
            </g>
          );
        })}

        {/* Axis labels */}
        <text x={padding + (bed.length * scale) / 2} y={svgHeight - 4} textAnchor="middle" fontSize="10" fill="#666">
          Length (foot of bed →)
        </text>
        <text
          x={8}
          y={padding + (bed.width * scale) / 2}
          textAnchor="middle"
          fontSize="10"
          fill="#666"
          transform={`rotate(-90, 8, ${padding + (bed.width * scale) / 2})`}
        >
          Width
        </text>
      </svg>

      {placements.length === 0 && (
        <p className="no-placements">No boxes placed yet. Run optimization to see the layout.</p>
      )}
    </div>
  );
}
