import type { Box, Fragility, AccessFrequency, Priority } from '../api/types';
import { defaultBox } from '../api/types';

interface BoxListEditorProps {
  boxes: Box[];
  onChange: (boxes: Box[]) => void;
}

export function BoxListEditor({ boxes, onChange }: BoxListEditorProps) {
  const addBox = () => {
    const newBox: Box = {
      ...defaultBox,
      id: `box-${Date.now()}`,
      name: `Box ${boxes.length + 1}`,
    };
    onChange([...boxes, newBox]);
  };

  const removeBox = (id: string) => {
    onChange(boxes.filter((box) => box.id !== id));
  };

  const updateBox = (id: string, updates: Partial<Box>) => {
    onChange(
      boxes.map((box) => (box.id === id ? { ...box, ...updates } : box))
    );
  };

  return (
    <div className="form-section">
      <h3>Boxes</h3>
      <button type="button" onClick={addBox} className="add-button">
        + Add Box
      </button>

      {boxes.length === 0 ? (
        <p className="empty-message">No boxes added yet. Click "Add Box" to start.</p>
      ) : (
        <div className="box-list">
          {boxes.map((box) => (
            <div key={box.id} className="box-item">
              <div className="box-header">
                <input
                  type="text"
                  value={box.name}
                  onChange={(e) => updateBox(box.id, { name: e.target.value })}
                  placeholder="Box name"
                  className="box-name-input"
                />
                <button
                  type="button"
                  onClick={() => removeBox(box.id)}
                  className="remove-button"
                >
                  Remove
                </button>
              </div>

              <div className="box-fields">
                <div className="field-group">
                  <label>
                    L:
                    <input
                      type="number"
                      min="1"
                      value={box.length}
                      onChange={(e) =>
                        updateBox(box.id, { length: parseFloat(e.target.value) || 1 })
                      }
                    />
                  </label>
                  <label>
                    W:
                    <input
                      type="number"
                      min="1"
                      value={box.width}
                      onChange={(e) =>
                        updateBox(box.id, { width: parseFloat(e.target.value) || 1 })
                      }
                    />
                  </label>
                  <label>
                    H:
                    <input
                      type="number"
                      min="1"
                      value={box.height}
                      onChange={(e) =>
                        updateBox(box.id, { height: parseFloat(e.target.value) || 1 })
                      }
                    />
                  </label>
                  <label>
                    Weight:
                    <input
                      type="number"
                      min="0"
                      step="0.1"
                      value={box.weight}
                      onChange={(e) =>
                        updateBox(box.id, { weight: parseFloat(e.target.value) || 0 })
                      }
                    />
                  </label>
                </div>

                <div className="field-group">
                  <label>
                    Fragility:
                    <select
                      value={box.fragility}
                      onChange={(e) =>
                        updateBox(box.id, { fragility: e.target.value as Fragility })
                      }
                    >
                      <option value="robust">Robust</option>
                      <option value="normal">Normal</option>
                      <option value="fragile">Fragile</option>
                    </select>
                  </label>
                  <label>
                    Access:
                    <select
                      value={box.access_frequency}
                      onChange={(e) =>
                        updateBox(box.id, {
                          access_frequency: e.target.value as AccessFrequency,
                        })
                      }
                    >
                      <option value="rare">Rare</option>
                      <option value="sometimes">Sometimes</option>
                      <option value="often">Often</option>
                    </select>
                  </label>
                  <label>
                    Priority:
                    <select
                      value={box.priority}
                      onChange={(e) =>
                        updateBox(box.id, { priority: e.target.value as Priority })
                      }
                    >
                      <option value="must_fit">Must Fit</option>
                      <option value="optional">Optional</option>
                    </select>
                  </label>
                </div>

                <div className="field-group rotation-flags">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={box.can_rotate_x}
                      onChange={(e) =>
                        updateBox(box.id, { can_rotate_x: e.target.checked })
                      }
                    />
                    Rotate X
                  </label>
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={box.can_rotate_y}
                      onChange={(e) =>
                        updateBox(box.id, { can_rotate_y: e.target.checked })
                      }
                    />
                    Rotate Y
                  </label>
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={box.can_rotate_z}
                      onChange={(e) =>
                        updateBox(box.id, { can_rotate_z: e.target.checked })
                      }
                    />
                    Rotate Z
                  </label>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
