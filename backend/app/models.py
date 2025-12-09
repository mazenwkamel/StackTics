"""Domain models for StackTics.

These are internal domain types used by the optimizer and other business logic.
They are not directly exposed to the network layer.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Fragility(Enum):
    """Fragility level of a box."""
    ROBUST = "robust"
    NORMAL = "normal"
    FRAGILE = "fragile"


class AccessFrequency(Enum):
    """How often a box needs to be accessed."""
    RARE = "rare"
    SOMETIMES = "sometimes"
    OFTEN = "often"


class Priority(Enum):
    """Priority level for box placement."""
    MUST_FIT = "must_fit"
    OPTIONAL = "optional"


class Strategy(Enum):
    """Packing strategy options."""
    MAXIMIZE_VOLUME = "maximize_volume"
    MINIMIZE_HOLES = "minimize_holes"


@dataclass
class Bed:
    """Represents the space under the bed where boxes will be packed."""
    length: float  # cm, along the length of the bed (head to foot)
    width: float   # cm, across the bed
    height: float  # cm, vertical clearance
    margin: float  # cm, margin from all edges


@dataclass
class Box:
    """Represents a box to be packed."""
    id: str
    name: str
    length: float  # cm
    width: float   # cm
    height: float  # cm
    weight: float  # kg
    fragility: Fragility
    access_frequency: AccessFrequency
    priority: Priority
    can_rotate_x: bool = True  # Can rotate around X axis (swap height/width)
    can_rotate_y: bool = True  # Can rotate around Y axis (swap height/length)
    can_rotate_z: bool = True  # Can rotate around Z axis (swap length/width)
    max_supported_load: Optional[float] = None  # kg, max weight that can be placed on top

    def __post_init__(self):
        # Default max_supported_load based on fragility if not set
        if self.max_supported_load is None:
            defaults = {
                Fragility.ROBUST: 50.0,
                Fragility.NORMAL: 20.0,
                Fragility.FRAGILE: 5.0,
            }
            self.max_supported_load = defaults.get(self.fragility, 20.0)


@dataclass
class Settings:
    """Packing settings and preferences."""
    strategy: Strategy
    accessibility_preference: float = 0.5  # 0.0 = compact, 1.0 = accessible
    padding: float = 1.0  # cm, space between boxes
    margin: float = 0.0   # cm, additional margin (can override bed margin)


@dataclass
class Orientation:
    """Describes how a box is oriented in space.

    Maps the box's original dimensions to the placed dimensions.
    For example, if length_axis='width', the box's length dimension
    is aligned with the width direction of the bed.
    """
    length_axis: str  # 'length', 'width', or 'height'
    width_axis: str
    height_axis: str

    @classmethod
    def default(cls) -> "Orientation":
        """Return the default orientation (no rotation)."""
        return cls(length_axis="length", width_axis="width", height_axis="height")


@dataclass
class Placement:
    """Represents where and how a box is placed."""
    box_id: str
    x: float  # cm, position along bed length (0 = foot of bed)
    y: float  # cm, position across bed width (0 = left edge)
    z: float  # cm, vertical position (0 = floor)
    orientation: Orientation = field(default_factory=Orientation.default)

    @property
    def orientation_str(self) -> str:
        """Return a simple string representation of orientation."""
        return f"{self.orientation.length_axis[0]}{self.orientation.width_axis[0]}{self.orientation.height_axis[0]}"
