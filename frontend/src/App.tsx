import { useState, useEffect } from 'react';
import './App.css';

import type { Bed, Box, Settings, Placement, Metrics } from './api/types';
import { defaultBed, defaultSettings } from './api/types';
import { checkHealth, optimize } from './api/client';

import { BedConfigForm } from './components/BedConfigForm';
import { BoxListEditor } from './components/BoxListEditor';
import { PackingSettingsForm } from './components/PackingSettingsForm';
import { Layout2DView } from './components/Layout2DView';
import { SummaryPanel } from './components/SummaryPanel';

function App() {
  // Form state
  const [bed, setBed] = useState<Bed>(defaultBed);
  const [boxes, setBoxes] = useState<Box[]>([]);
  const [settings, setSettings] = useState<Settings>(defaultSettings);

  // Result state
  const [placements, setPlacements] = useState<Placement[]>([]);
  const [unplacedBoxIds, setUnplacedBoxIds] = useState<string[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);

  // UI state
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState<boolean | null>(null);

  // Check backend health on mount
  useEffect(() => {
    checkHealth()
      .then(() => setIsConnected(true))
      .catch(() => setIsConnected(false));
  }, []);

  const boxNames = new Map(boxes.map((b) => [b.id, b.name]));

  const handleOptimize = async () => {
    if (boxes.length === 0) {
      setError('Please add at least one box before optimizing.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await optimize({ bed, boxes, settings });
      setPlacements(response.placements);
      setUnplacedBoxIds(response.unplaced_box_ids);
      setMetrics(response.metrics);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setPlacements([]);
      setUnplacedBoxIds([]);
      setMetrics(null);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>StackTics</h1>
        <p>Optimize how to pack boxes under your bed</p>
      </header>

      {isConnected !== null && (
        <div className={`health-status ${isConnected ? 'connected' : 'disconnected'}`}>
          {isConnected ? 'Backend connected' : 'Backend not reachable - start the server'}
        </div>
      )}

      {error && <div className="error-message">{error}</div>}

      <div className="main-content">
        <div className="left-column">
          <BedConfigForm bed={bed} onChange={setBed} />
          <PackingSettingsForm settings={settings} onChange={setSettings} />
          <BoxListEditor boxes={boxes} onChange={setBoxes} />

          <button
            className="optimize-button"
            onClick={handleOptimize}
            disabled={isLoading || boxes.length === 0}
          >
            {isLoading ? 'Optimizing...' : 'Optimize Packing'}
          </button>
        </div>

        <div className="right-column">
          <Layout2DView bed={bed} boxes={boxes} placements={placements} />
          <SummaryPanel
            metrics={metrics}
            unplacedBoxIds={unplacedBoxIds}
            boxNames={boxNames}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
