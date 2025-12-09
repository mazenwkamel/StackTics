/**
 * TypeScript interfaces matching the StackTics API contract.
 */

export type Fragility = 'robust' | 'normal' | 'fragile';
export type AccessFrequency = 'rare' | 'sometimes' | 'often';
export type Priority = 'must_fit' | 'optional';
export type Strategy = 'maximize_volume' | 'minimize_holes';

export interface Bed {
  length: number;
  width: number;
  height: number;
  margin: number;
}

export interface Box {
  id: string;
  name: string;
  length: number;
  width: number;
  height: number;
  weight: number;
  fragility: Fragility;
  access_frequency: AccessFrequency;
  priority: Priority;
  can_rotate_x: boolean;
  can_rotate_y: boolean;
  can_rotate_z: boolean;
  max_supported_load?: number;
}

export interface Settings {
  strategy: Strategy;
  accessibility_preference: number;
  padding: number;
  margin: number;
}

export interface Orientation {
  length_axis: string;
  width_axis: string;
  height_axis: string;
}

export interface Placement {
  box_id: string;
  x: number;
  y: number;
  z: number;
  orientation: Orientation;
}

export interface Metrics {
  total_boxes: number;
  placed_boxes: number;
  used_volume_ratio: number;
  free_volume_ratio: number;
  fragmentation_score: number;
}

export interface OptimizeRequest {
  bed: Bed;
  boxes: Box[];
  settings: Settings;
}

export interface OptimizeResponse {
  placements: Placement[];
  unplaced_box_ids: string[];
  metrics: Metrics;
}

export interface HealthResponse {
  status: string;
  app: string;
}

/**
 * Default values for creating new boxes.
 */
export const defaultBox: Omit<Box, 'id'> = {
  name: '',
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

/**
 * Default bed configuration.
 */
export const defaultBed: Bed = {
  length: 200,
  width: 150,
  height: 30,
  margin: 5,
};

/**
 * Default packing settings.
 */
export const defaultSettings: Settings = {
  strategy: 'maximize_volume',
  accessibility_preference: 0.5,
  padding: 1,
  margin: 0,
};
