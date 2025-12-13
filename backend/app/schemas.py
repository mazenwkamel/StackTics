"""Pydantic schemas for API request and response types.

These schemas are used by FastAPI for request validation and response serialization.
They mirror the domain models but are designed for network transport.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


# ============================================================================
# Constants for validation
# ============================================================================

# Reasonable dimension limits (in cm)
MIN_DIMENSION = 1.0        # Minimum 1cm
MAX_BED_DIMENSION = 500.0  # Max 5 meters for bed
MAX_BOX_DIMENSION = 200.0  # Max 2 meters for a box

# Weight limits (in kg)
MAX_WEIGHT = 100.0  # Max 100kg per box

# Margin/padding limits (in cm)
MAX_MARGIN = 50.0   # Max 50cm margin
MAX_PADDING = 20.0  # Max 20cm padding between boxes


# ============================================================================
# Enums
# ============================================================================

class FragilityEnum(str, Enum):
    """Fragility level of a box."""
    ROBUST = "robust"
    NORMAL = "normal"
    FRAGILE = "fragile"


class AccessFrequencyEnum(str, Enum):
    """How often a box needs to be accessed."""
    RARE = "rare"
    SOMETIMES = "sometimes"
    OFTEN = "often"


class PriorityEnum(str, Enum):
    """Priority level for box placement."""
    MUST_FIT = "must_fit"
    OPTIONAL = "optional"


class StrategyEnum(str, Enum):
    """Packing strategy options."""
    MAXIMIZE_VOLUME = "maximize_volume"
    MINIMIZE_HOLES = "minimize_holes"


# ============================================================================
# Schemas
# ============================================================================

class BedSchema(BaseModel):
    """Schema for bed/container dimensions."""
    length: float = Field(
        ...,
        gt=0,
        le=MAX_BED_DIMENSION,
        description="Length in cm (head to foot). Must be between 1 and 500 cm."
    )
    width: float = Field(
        ...,
        gt=0,
        le=MAX_BED_DIMENSION,
        description="Width in cm (across the bed). Must be between 1 and 500 cm."
    )
    height: float = Field(
        ...,
        gt=0,
        le=MAX_BED_DIMENSION,
        description="Height in cm (vertical clearance). Must be between 1 and 500 cm."
    )
    margin: float = Field(
        default=0,
        ge=0,
        le=MAX_MARGIN,
        description="Margin from edges in cm. Must be between 0 and 50 cm."
    )
    corner_radius: float = Field(
        default=0,
        ge=0,
        le=100,
        description="Corner radius in cm for rounded corners. Must be between 0 and 100 cm."
    )

    @model_validator(mode='after')
    def validate_usable_space(self) -> 'BedSchema':
        """Ensure the margin and corner radius don't consume all the space."""
        usable_length = self.length - 2 * self.margin
        usable_width = self.width - 2 * self.margin

        if usable_length <= 0:
            raise ValueError(
                f"Margin ({self.margin} cm) is too large for bed length ({self.length} cm). "
                f"Usable length would be {usable_length} cm. Reduce margin or increase length."
            )
        if usable_width <= 0:
            raise ValueError(
                f"Margin ({self.margin} cm) is too large for bed width ({self.width} cm). "
                f"Usable width would be {usable_width} cm. Reduce margin or increase width."
            )

        # Validate corner radius doesn't exceed half the smallest dimension
        max_radius = min(self.length, self.width) / 2
        if self.corner_radius > max_radius:
            raise ValueError(
                f"Corner radius ({self.corner_radius} cm) is too large. "
                f"Maximum allowed is {max_radius:.1f} cm (half of the smallest dimension)."
            )
        return self


class BoxSchema(BaseModel):
    """Schema for a box to be packed."""
    id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique identifier for the box"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Display name for the box"
    )
    length: float = Field(
        ...,
        gt=0,
        le=MAX_BOX_DIMENSION,
        description="Length in cm. Must be between 1 and 200 cm."
    )
    width: float = Field(
        ...,
        gt=0,
        le=MAX_BOX_DIMENSION,
        description="Width in cm. Must be between 1 and 200 cm."
    )
    height: float = Field(
        ...,
        gt=0,
        le=MAX_BOX_DIMENSION,
        description="Height in cm. Must be between 1 and 200 cm."
    )
    weight: float = Field(
        ...,
        ge=0,
        le=MAX_WEIGHT,
        description="Weight in kg. Must be between 0 and 100 kg."
    )
    fragility: FragilityEnum = Field(
        default=FragilityEnum.NORMAL,
        description="How fragile the box contents are"
    )
    access_frequency: AccessFrequencyEnum = Field(
        default=AccessFrequencyEnum.SOMETIMES,
        description="How often you need to access this box"
    )
    priority: PriorityEnum = Field(
        default=PriorityEnum.OPTIONAL,
        description="Whether this box must fit or is optional"
    )
    can_rotate_x: bool = Field(
        default=True,
        description="Can rotate around X axis (tips box forward/back)"
    )
    can_rotate_y: bool = Field(
        default=True,
        description="Can rotate around Y axis (tips box left/right)"
    )
    can_rotate_z: bool = Field(
        default=True,
        description="Can rotate around Z axis (spins box horizontally)"
    )
    max_supported_load: Optional[float] = Field(
        default=None,
        ge=0,
        le=MAX_WEIGHT * 2,
        description="Maximum weight that can be placed on top (kg). If not set, defaults based on fragility."
    )

    @field_validator('name')
    @classmethod
    def name_not_empty_whitespace(cls, v: str) -> str:
        """Ensure name is not just whitespace."""
        if not v.strip():
            raise ValueError("Box name cannot be empty or just whitespace")
        return v.strip()


class SettingsSchema(BaseModel):
    """Schema for packing settings."""
    strategy: StrategyEnum = Field(
        default=StrategyEnum.MAXIMIZE_VOLUME,
        description="Packing strategy: 'maximize_volume' fills space efficiently, 'minimize_holes' reduces fragmentation"
    )
    accessibility_preference: float = Field(
        default=0.5,
        ge=0,
        le=1,
        description="Balance between compact packing (0.0) and accessibility (1.0)"
    )
    padding: float = Field(
        default=1.0,
        ge=0,
        le=MAX_PADDING,
        description="Space between boxes in cm. Must be between 0 and 20 cm."
    )
    margin: float = Field(
        default=0.0,
        ge=0,
        le=MAX_MARGIN,
        description="Additional margin from bed edges in cm. Must be between 0 and 50 cm."
    )


class OrientationSchema(BaseModel):
    """Schema for box orientation.

    Maps the box's original dimensions to the placed dimensions.
    Valid values for each axis are: 'length', 'width', 'height'.
    Each value must be used exactly once across all three axes.
    """
    length_axis: Literal['length', 'width', 'height'] = Field(
        ...,
        description="Which box dimension aligns with bed length"
    )
    width_axis: Literal['length', 'width', 'height'] = Field(
        ...,
        description="Which box dimension aligns with bed width"
    )
    height_axis: Literal['length', 'width', 'height'] = Field(
        ...,
        description="Which box dimension aligns with vertical"
    )

    @model_validator(mode='after')
    def validate_axes(self) -> 'OrientationSchema':
        """Ensure each axis maps to a unique dimension."""
        axes = [self.length_axis, self.width_axis, self.height_axis]
        if len(set(axes)) != 3:
            raise ValueError(
                f"Each axis must map to a unique dimension. "
                f"Got: length_axis={self.length_axis}, width_axis={self.width_axis}, height_axis={self.height_axis}"
            )
        return self


class PlacementSchema(BaseModel):
    """Schema for a box placement result."""
    box_id: str = Field(..., description="ID of the placed box")
    x: float = Field(..., description="X position in cm (along bed length)")
    y: float = Field(..., description="Y position in cm (across bed width)")
    z: float = Field(..., description="Z position in cm (vertical, 0 = floor)")
    orientation: OrientationSchema = Field(..., description="Box orientation")


class MetricsSchema(BaseModel):
    """Schema for packing metrics."""
    total_boxes: int = Field(..., ge=0, description="Total number of boxes in request")
    placed_boxes: int = Field(..., ge=0, description="Number of boxes successfully placed")
    used_volume_ratio: float = Field(
        ...,
        ge=0,
        le=1,
        description="Ratio of bed volume used by placed boxes"
    )
    free_volume_ratio: float = Field(
        ...,
        ge=0,
        le=1,
        description="Ratio of bed volume that is free"
    )
    fragmentation_score: float = Field(
        ...,
        ge=0,
        description="Score indicating how fragmented the free space is (lower is better)"
    )


class OptimizeRequest(BaseModel):
    """Request schema for the /optimize endpoint."""
    bed: BedSchema
    boxes: list[BoxSchema] = Field(
        ...,
        max_length=100,
        description="List of boxes to pack. Maximum 100 boxes."
    )
    settings: SettingsSchema = Field(default_factory=SettingsSchema)

    @model_validator(mode='after')
    def validate_request(self) -> 'OptimizeRequest':
        """Cross-field validation for the entire request."""
        errors = []

        # Check for duplicate box IDs
        box_ids = [box.id for box in self.boxes]
        duplicates = [id for id in box_ids if box_ids.count(id) > 1]
        if duplicates:
            unique_duplicates = list(set(duplicates))
            errors.append(
                f"Duplicate box IDs found: {', '.join(unique_duplicates)}. Each box must have a unique ID."
            )

        # Calculate usable space (bed dimensions minus margins)
        total_margin = self.bed.margin + self.settings.margin
        usable_length = self.bed.length - 2 * total_margin
        usable_width = self.bed.width - 2 * total_margin
        usable_height = self.bed.height

        if usable_length <= 0 or usable_width <= 0:
            errors.append(
                f"Combined margins ({total_margin} cm) leave no usable space. "
                f"Bed margin: {self.bed.margin} cm, Settings margin: {self.settings.margin} cm."
            )
        else:
            # Check each box can fit in the bed (in at least one orientation)
            for box in self.boxes:
                dims = sorted([box.length, box.width, box.height])
                bed_dims = sorted([usable_length, usable_width, usable_height])

                # Check if box fits in any orientation
                can_fit = all(d <= b for d, b in zip(dims, bed_dims))

                if not can_fit:
                    errors.append(
                        f"Box '{box.name}' ({box.length}×{box.width}×{box.height} cm) "
                        f"cannot fit in the bed's usable space ({usable_length:.1f}×{usable_width:.1f}×{usable_height:.1f} cm) "
                        f"in any orientation."
                    )

        if errors:
            raise ValueError(" | ".join(errors))

        return self


class OptimizeResponse(BaseModel):
    """Response schema for the /optimize endpoint."""
    placements: list[PlacementSchema]
    unplaced_box_ids: list[str]
    metrics: MetricsSchema


# ============================================================================
# Error Response Schemas
# ============================================================================

class ValidationErrorDetail(BaseModel):
    """Details about a single validation error."""
    field: str = Field(..., description="The field that failed validation (dot-notation path)")
    message: str = Field(..., description="Human-readable error message")
    type: str = Field(..., description="Error type code")


class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: str = Field(..., description="Error category")
    message: str = Field(..., description="Human-readable summary of the error")
    details: list[ValidationErrorDetail] = Field(
        default=[],
        description="List of specific validation errors"
    )
