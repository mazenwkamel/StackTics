"""Pydantic schemas for API request and response types.

These schemas are used by FastAPI for request validation and response serialization.
They mirror the domain models but are designed for network transport.
"""

from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


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


class BedSchema(BaseModel):
    """Schema for bed/container dimensions."""
    length: float = Field(..., gt=0, description="Length in cm (head to foot)")
    width: float = Field(..., gt=0, description="Width in cm (across the bed)")
    height: float = Field(..., gt=0, description="Height in cm (vertical clearance)")
    margin: float = Field(default=0, ge=0, description="Margin from edges in cm")


class BoxSchema(BaseModel):
    """Schema for a box to be packed."""
    id: str = Field(..., min_length=1, description="Unique identifier for the box")
    name: str = Field(..., min_length=1, description="Display name for the box")
    length: float = Field(..., gt=0, description="Length in cm")
    width: float = Field(..., gt=0, description="Width in cm")
    height: float = Field(..., gt=0, description="Height in cm")
    weight: float = Field(..., ge=0, description="Weight in kg")
    fragility: FragilityEnum = Field(default=FragilityEnum.NORMAL)
    access_frequency: AccessFrequencyEnum = Field(default=AccessFrequencyEnum.SOMETIMES)
    priority: PriorityEnum = Field(default=PriorityEnum.OPTIONAL)
    can_rotate_x: bool = Field(default=True, description="Can rotate around X axis")
    can_rotate_y: bool = Field(default=True, description="Can rotate around Y axis")
    can_rotate_z: bool = Field(default=True, description="Can rotate around Z axis")
    max_supported_load: Optional[float] = Field(
        default=None,
        ge=0,
        description="Maximum weight that can be placed on top (kg)"
    )


class SettingsSchema(BaseModel):
    """Schema for packing settings."""
    strategy: StrategyEnum = Field(
        default=StrategyEnum.MAXIMIZE_VOLUME,
        description="Packing strategy to use"
    )
    accessibility_preference: float = Field(
        default=0.5,
        ge=0,
        le=1,
        description="0.0 = compact packing, 1.0 = prioritize accessibility"
    )
    padding: float = Field(
        default=1.0,
        ge=0,
        description="Space between boxes in cm"
    )
    margin: float = Field(
        default=0.0,
        ge=0,
        description="Additional margin from bed edges in cm"
    )


class OrientationSchema(BaseModel):
    """Schema for box orientation."""
    length_axis: str = Field(..., description="Which box dimension aligns with bed length")
    width_axis: str = Field(..., description="Which box dimension aligns with bed width")
    height_axis: str = Field(..., description="Which box dimension aligns with vertical")


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
    boxes: list[BoxSchema]
    settings: SettingsSchema = Field(default_factory=SettingsSchema)


class OptimizeResponse(BaseModel):
    """Response schema for the /optimize endpoint."""
    placements: list[PlacementSchema]
    unplaced_box_ids: list[str]
    metrics: MetricsSchema
