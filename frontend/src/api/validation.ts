/**
 * Frontend validation utilities matching backend validation rules.
 */

import { VALIDATION, Bed, Box, Settings } from './types';

// ============================================================================
// Validation Result Types
// ============================================================================

export interface ValidationError {
  field: string;
  message: string;
}

export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
}

// ============================================================================
// Individual Field Validators
// ============================================================================

export function validateBedLength(value: number): string | null {
  if (value <= 0) return 'Length must be greater than 0';
  if (value > VALIDATION.MAX_BED_DIMENSION) return `Length cannot exceed ${VALIDATION.MAX_BED_DIMENSION} cm`;
  return null;
}

export function validateBedWidth(value: number): string | null {
  if (value <= 0) return 'Width must be greater than 0';
  if (value > VALIDATION.MAX_BED_DIMENSION) return `Width cannot exceed ${VALIDATION.MAX_BED_DIMENSION} cm`;
  return null;
}

export function validateBedHeight(value: number): string | null {
  if (value <= 0) return 'Height must be greater than 0';
  if (value > VALIDATION.MAX_BED_DIMENSION) return `Height cannot exceed ${VALIDATION.MAX_BED_DIMENSION} cm`;
  return null;
}

export function validateMargin(value: number): string | null {
  if (value < 0) return 'Margin cannot be negative';
  if (value > VALIDATION.MAX_MARGIN) return `Margin cannot exceed ${VALIDATION.MAX_MARGIN} cm`;
  return null;
}

export function validateBoxDimension(value: number, dimension: string): string | null {
  if (value <= 0) return `${dimension} must be greater than 0`;
  if (value > VALIDATION.MAX_BOX_DIMENSION) return `${dimension} cannot exceed ${VALIDATION.MAX_BOX_DIMENSION} cm`;
  return null;
}

export function validateWeight(value: number): string | null {
  if (value < 0) return 'Weight cannot be negative';
  if (value > VALIDATION.MAX_WEIGHT) return `Weight cannot exceed ${VALIDATION.MAX_WEIGHT} kg`;
  return null;
}

export function validateBoxName(value: string): string | null {
  const trimmed = value.trim();
  if (!trimmed) return 'Name cannot be empty';
  if (trimmed.length > VALIDATION.MAX_NAME_LENGTH) return `Name cannot exceed ${VALIDATION.MAX_NAME_LENGTH} characters`;
  return null;
}

export function validatePadding(value: number): string | null {
  if (value < 0) return 'Padding cannot be negative';
  if (value > VALIDATION.MAX_PADDING) return `Padding cannot exceed ${VALIDATION.MAX_PADDING} cm`;
  return null;
}

export function validateAccessibilityPreference(value: number): string | null {
  if (value < 0 || value > 1) return 'Accessibility preference must be between 0 and 1';
  return null;
}

// ============================================================================
// Object Validators
// ============================================================================

export function validateBed(bed: Bed): ValidationResult {
  const errors: ValidationError[] = [];

  const lengthError = validateBedLength(bed.length);
  if (lengthError) errors.push({ field: 'bed.length', message: lengthError });

  const widthError = validateBedWidth(bed.width);
  if (widthError) errors.push({ field: 'bed.width', message: widthError });

  const heightError = validateBedHeight(bed.height);
  if (heightError) errors.push({ field: 'bed.height', message: heightError });

  const marginError = validateMargin(bed.margin);
  if (marginError) errors.push({ field: 'bed.margin', message: marginError });

  // Cross-field validation: margin vs dimensions
  if (errors.length === 0) {
    const usableLength = bed.length - 2 * bed.margin;
    const usableWidth = bed.width - 2 * bed.margin;

    if (usableLength <= 0) {
      errors.push({
        field: 'bed.margin',
        message: `Margin (${bed.margin} cm) is too large for bed length (${bed.length} cm)`,
      });
    }
    if (usableWidth <= 0) {
      errors.push({
        field: 'bed.margin',
        message: `Margin (${bed.margin} cm) is too large for bed width (${bed.width} cm)`,
      });
    }
  }

  return { valid: errors.length === 0, errors };
}

export function validateBox(box: Box): ValidationResult {
  const errors: ValidationError[] = [];

  const nameError = validateBoxName(box.name);
  if (nameError) errors.push({ field: `box.${box.id}.name`, message: nameError });

  const lengthError = validateBoxDimension(box.length, 'Length');
  if (lengthError) errors.push({ field: `box.${box.id}.length`, message: lengthError });

  const widthError = validateBoxDimension(box.width, 'Width');
  if (widthError) errors.push({ field: `box.${box.id}.width`, message: widthError });

  const heightError = validateBoxDimension(box.height, 'Height');
  if (heightError) errors.push({ field: `box.${box.id}.height`, message: heightError });

  const weightError = validateWeight(box.weight);
  if (weightError) errors.push({ field: `box.${box.id}.weight`, message: weightError });

  return { valid: errors.length === 0, errors };
}

export function validateSettings(settings: Settings): ValidationResult {
  const errors: ValidationError[] = [];

  const paddingError = validatePadding(settings.padding);
  if (paddingError) errors.push({ field: 'settings.padding', message: paddingError });

  const marginError = validateMargin(settings.margin);
  if (marginError) errors.push({ field: 'settings.margin', message: marginError });

  const accessError = validateAccessibilityPreference(settings.accessibility_preference);
  if (accessError) errors.push({ field: 'settings.accessibility_preference', message: accessError });

  return { valid: errors.length === 0, errors };
}

// ============================================================================
// Full Request Validation
// ============================================================================

export function validateOptimizeRequest(
  bed: Bed,
  boxes: Box[],
  settings: Settings
): ValidationResult {
  const errors: ValidationError[] = [];

  // Validate bed
  const bedResult = validateBed(bed);
  errors.push(...bedResult.errors);

  // Validate settings
  const settingsResult = validateSettings(settings);
  errors.push(...settingsResult.errors);

  // Validate each box
  for (const box of boxes) {
    const boxResult = validateBox(box);
    errors.push(...boxResult.errors);
  }

  // Check for duplicate box IDs
  const boxIds = boxes.map((b) => b.id);
  const duplicates = boxIds.filter((id, index) => boxIds.indexOf(id) !== index);
  if (duplicates.length > 0) {
    errors.push({
      field: 'boxes',
      message: `Duplicate box IDs found: ${[...new Set(duplicates)].join(', ')}`,
    });
  }

  // Check max boxes
  if (boxes.length > VALIDATION.MAX_BOXES) {
    errors.push({
      field: 'boxes',
      message: `Too many boxes. Maximum is ${VALIDATION.MAX_BOXES}`,
    });
  }

  // Cross-validation: check if boxes can fit in bed
  if (bedResult.valid && settingsResult.valid) {
    const totalMargin = bed.margin + settings.margin;
    const usableLength = bed.length - 2 * totalMargin;
    const usableWidth = bed.width - 2 * totalMargin;
    const usableHeight = bed.height;

    if (usableLength <= 0 || usableWidth <= 0) {
      errors.push({
        field: 'settings.margin',
        message: `Combined margins (${totalMargin} cm) leave no usable space`,
      });
    } else {
      for (const box of boxes) {
        // Sort dimensions to check if box fits in any orientation
        const boxDims = [box.length, box.width, box.height].sort((a, b) => a - b);
        const bedDims = [usableLength, usableWidth, usableHeight].sort((a, b) => a - b);

        const canFit = boxDims.every((d, i) => d <= bedDims[i]);

        if (!canFit) {
          errors.push({
            field: `box.${box.id}`,
            message: `Box "${box.name}" (${box.length}x${box.width}x${box.height} cm) cannot fit in the bed's usable space (${usableLength.toFixed(0)}x${usableWidth.toFixed(0)}x${usableHeight.toFixed(0)} cm)`,
          });
        }
      }
    }
  }

  return { valid: errors.length === 0, errors };
}

// ============================================================================
// Utility: Format errors for display
// ============================================================================

export function formatValidationErrors(result: ValidationResult): string {
  if (result.valid) return '';
  return result.errors.map((e) => e.message).join('\n');
}
