import type { Bed } from '../api/types';

interface BedConfigFormProps {
  bed: Bed;
  onChange: (bed: Bed) => void;
}

export function BedConfigForm({ bed, onChange }: BedConfigFormProps) {
  const handleChange = (field: keyof Bed, value: string) => {
    const numValue = parseFloat(value) || 0;
    onChange({ ...bed, [field]: numValue });
  };

  return (
    <div className="form-section">
      <h3>Bed Configuration</h3>
      <div className="form-grid">
        <label>
          Length (cm):
          <input
            type="number"
            min="0"
            step="1"
            value={bed.length}
            onChange={(e) => handleChange('length', e.target.value)}
          />
        </label>
        <label>
          Width (cm):
          <input
            type="number"
            min="0"
            step="1"
            value={bed.width}
            onChange={(e) => handleChange('width', e.target.value)}
          />
        </label>
        <label>
          Height (cm):
          <input
            type="number"
            min="0"
            step="1"
            value={bed.height}
            onChange={(e) => handleChange('height', e.target.value)}
          />
        </label>
        <label>
          Margin (cm):
          <input
            type="number"
            min="0"
            step="0.5"
            value={bed.margin}
            onChange={(e) => handleChange('margin', e.target.value)}
          />
        </label>
      </div>
    </div>
  );
}
