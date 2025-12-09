import type { Settings, Strategy } from '../api/types';

interface PackingSettingsFormProps {
  settings: Settings;
  onChange: (settings: Settings) => void;
}

export function PackingSettingsForm({ settings, onChange }: PackingSettingsFormProps) {
  const handleChange = <K extends keyof Settings>(field: K, value: Settings[K]) => {
    onChange({ ...settings, [field]: value });
  };

  return (
    <div className="form-section">
      <h3>Packing Settings</h3>
      <div className="form-grid">
        <label>
          Strategy:
          <select
            value={settings.strategy}
            onChange={(e) => handleChange('strategy', e.target.value as Strategy)}
          >
            <option value="maximize_volume">Maximize Volume</option>
            <option value="minimize_holes">Minimize Holes</option>
          </select>
        </label>

        <label>
          Accessibility Preference:
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={settings.accessibility_preference}
            onChange={(e) =>
              handleChange('accessibility_preference', parseFloat(e.target.value))
            }
          />
          <span className="range-value">
            {settings.accessibility_preference < 0.3
              ? 'Compact'
              : settings.accessibility_preference > 0.7
                ? 'Accessible'
                : 'Balanced'}
          </span>
        </label>

        <label>
          Padding (cm):
          <input
            type="number"
            min="0"
            step="0.5"
            value={settings.padding}
            onChange={(e) => handleChange('padding', parseFloat(e.target.value) || 0)}
          />
        </label>

        <label>
          Additional Margin (cm):
          <input
            type="number"
            min="0"
            step="0.5"
            value={settings.margin}
            onChange={(e) => handleChange('margin', parseFloat(e.target.value) || 0)}
          />
        </label>
      </div>
    </div>
  );
}
