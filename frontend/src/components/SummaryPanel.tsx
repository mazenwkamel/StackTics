import type { Metrics } from '../api/types';

interface SummaryPanelProps {
  metrics: Metrics | null;
  unplacedBoxIds: string[];
  boxNames: Map<string, string>;
}

export function SummaryPanel({ metrics, unplacedBoxIds, boxNames }: SummaryPanelProps) {
  if (!metrics) {
    return (
      <div className="summary-panel">
        <h3>Summary</h3>
        <p className="no-results">Run optimization to see results.</p>
      </div>
    );
  }

  const volumePercent = (metrics.used_volume_ratio * 100).toFixed(1);
  const freePercent = (metrics.free_volume_ratio * 100).toFixed(1);

  return (
    <div className="summary-panel">
      <h3>Summary</h3>
      <div className="summary-content">
        <div className="metrics-grid">
          <div className="metric">
            <span className="metric-label">Total</span>
            <span className="metric-value">{metrics.total_boxes}</span>
          </div>
          <div className="metric">
            <span className="metric-label">Placed</span>
            <span className="metric-value success">{metrics.placed_boxes}</span>
          </div>
          <div className="metric">
            <span className="metric-label">Unplaced</span>
            <span className={`metric-value ${metrics.total_boxes - metrics.placed_boxes > 0 ? 'warning' : ''}`}>
              {metrics.total_boxes - metrics.placed_boxes}
            </span>
          </div>
          <div className="metric">
            <span className="metric-label">Used</span>
            <span className="metric-value">{volumePercent}%</span>
          </div>
          <div className="metric">
            <span className="metric-label">Free</span>
            <span className="metric-value">{freePercent}%</span>
          </div>
        </div>

        {unplacedBoxIds.length > 0 && (
          <div className="unplaced-boxes">
            <h4>Unplaced Boxes</h4>
            <ul>
              {unplacedBoxIds.map((id) => (
                <li key={id}>{boxNames.get(id) || id}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
