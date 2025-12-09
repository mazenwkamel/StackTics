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

  // Result state - store both placements and the boxes snapshot used
  const [placements, setPlacements] = useState<Placement[]>([]);
  const [unplacedBoxIds, setUnplacedBoxIds] = useState<string[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [resultBoxes, setResultBoxes] = useState<Box[]>([]); // Boxes at time of optimization

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
      // Store a snapshot of boxes used for this optimization
      setResultBoxes(boxes.map(b => ({ ...b })));
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
        {/* Left sidebar - Boxes */}
        <div className="left-sidebar">
          <div className="sidebar-header">
            <h3>Boxes ({boxes.length})</h3>
            <button type="button" onClick={() => {
              const newBox: Box = {
                id: `box-${Date.now()}`,
                name: `Box ${boxes.length + 1}`,
                length: 30,
                width: 20,
                height: 15,
                weight: 1,
                fragility: 'normal',
                access_frequency: 'sometimes',
                priority: 'optional',
                can_rotate_x: true,
                can_rotate_y: true,
                can_rotate_z: true,
              };
              setBoxes([...boxes, newBox]);
            }} className="add-button">
              + Add Box
            </button>
          </div>
          <div className="sidebar-content">
            <BoxListEditor boxes={boxes} onChange={setBoxes} />
          </div>
        </div>

        {/* Center - Main view */}
        <div className="center-column">
          <Layout2DView bed={bed} boxes={resultBoxes} placements={placements} />
          <SummaryPanel
            metrics={metrics}
            unplacedBoxIds={unplacedBoxIds}
            boxNames={boxNames}
          />
        </div>

        {/* Right sidebar - Settings */}
        <div className="right-sidebar">
          <BedConfigForm bed={bed} onChange={setBed} />
          <PackingSettingsForm settings={settings} onChange={setSettings} />
          <div className="form-section">
            <button
              className="optimize-button"
              onClick={handleOptimize}
              disabled={isLoading || boxes.length === 0}
            >
              {isLoading ? 'Optimizing...' : 'Optimize Packing'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
