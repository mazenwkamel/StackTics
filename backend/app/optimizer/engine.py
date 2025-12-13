"""Packing optimization engine.

This module contains the core algorithm for optimizing box placement under a bed.
Implements a 3D bin packing heuristic with support for:
- Layer-by-layer placement
- Weight and fragility constraints
- Box rotations
- Multiple placement strategies
- Rounded corner containers
"""

import math
from dataclasses import dataclass
from typing import Optional

from app.models import (
    Bed,
    Box,
    Settings,
    Placement,
    Orientation,
    Priority,
    Fragility,
    AccessFrequency,
    Strategy,
)


@dataclass
class PlacedBox:
    """A box with its placement information for internal tracking."""
    box: Box
    placement: Placement
    # Actual dimensions after rotation
    placed_length: float
    placed_width: float
    placed_height: float

    @property
    def x_end(self) -> float:
        return self.placement.x + self.placed_length

    @property
    def y_end(self) -> float:
        return self.placement.y + self.placed_width

    @property
    def z_end(self) -> float:
        return self.placement.z + self.placed_height


@dataclass
class FreeSpace:
    """Represents a free rectangular region in 3D space."""
    x: float
    y: float
    z: float
    length: float  # extent in x direction
    width: float   # extent in y direction
    height: float  # extent in z direction

    @property
    def volume(self) -> float:
        return self.length * self.width * self.height

    @property
    def x_end(self) -> float:
        return self.x + self.length

    @property
    def y_end(self) -> float:
        return self.y + self.width

    @property
    def z_end(self) -> float:
        return self.z + self.height

    def contains_point(self, x: float, y: float, z: float) -> bool:
        return (self.x <= x < self.x_end and
                self.y <= y < self.y_end and
                self.z <= z < self.z_end)

    def intersects(self, other: "FreeSpace") -> bool:
        """Check if two spaces overlap."""
        return not (
            self.x_end <= other.x or other.x_end <= self.x or
            self.y_end <= other.y or other.y_end <= self.y or
            self.z_end <= other.z or other.z_end <= self.z
        )


def point_in_corner_exclusion(
    px: float, py: float,
    corner_x: float, corner_y: float,
    radius: float,
    corner_type: str,
) -> bool:
    """Check if a point falls within a corner exclusion zone.

    The exclusion zone is the area between the square corner and the arc.

    Args:
        px, py: Point coordinates
        corner_x, corner_y: Center of the corner arc
        radius: Corner radius
        corner_type: One of 'bottom_left', 'bottom_right', 'top_left', 'top_right'

    Returns:
        True if the point is in the exclusion zone (outside the arc but inside the square).
    """
    if radius <= 0:
        return False

    # Calculate distance from the arc center
    dx = px - corner_x
    dy = py - corner_y
    distance = math.sqrt(dx * dx + dy * dy)

    # Check based on corner type if point is in the corner square region
    if corner_type == 'bottom_left':
        in_square = px < corner_x and py < corner_y
    elif corner_type == 'bottom_right':
        in_square = px > corner_x and py < corner_y
    elif corner_type == 'top_left':
        in_square = px < corner_x and py > corner_y
    elif corner_type == 'top_right':
        in_square = px > corner_x and py > corner_y
    else:
        return False

    # Point is excluded if it's in the square region AND outside the arc
    return in_square and distance > radius


def box_intersects_corner(
    box_x: float, box_y: float,
    box_length: float, box_width: float,
    bed_length: float, bed_width: float,
    corner_radius: float,
    total_margin: float,
) -> bool:
    """Check if a box placement intersects with any rounded corner exclusion zone.

    Uses a conservative approach: checks if any corner of the box falls within
    an exclusion zone, plus checks a grid of points along the edges.

    Args:
        box_x, box_y: Box position (already includes margin offset)
        box_length, box_width: Box dimensions
        bed_length, bed_width: Full bed dimensions
        corner_radius: Radius of rounded corners
        total_margin: Total margin from bed edges

    Returns:
        True if the box intersects any corner exclusion zone.
    """
    if corner_radius <= 0:
        return False

    # Define the four corner arc centers (in bed coordinates)
    # The arc centers are at (margin + radius, margin + radius) from each corner
    corners = [
        # (arc_center_x, arc_center_y, corner_type)
        (total_margin + corner_radius, total_margin + corner_radius, 'bottom_left'),
        (bed_length - total_margin - corner_radius, total_margin + corner_radius, 'bottom_right'),
        (total_margin + corner_radius, bed_width - total_margin - corner_radius, 'top_left'),
        (bed_length - total_margin - corner_radius, bed_width - total_margin - corner_radius, 'top_right'),
    ]

    # Points to check: corners of the box and points along edges
    check_points = [
        (box_x, box_y),
        (box_x + box_length, box_y),
        (box_x, box_y + box_width),
        (box_x + box_length, box_y + box_width),
    ]

    # Add edge midpoints for better coverage
    check_points.extend([
        (box_x + box_length / 2, box_y),
        (box_x + box_length / 2, box_y + box_width),
        (box_x, box_y + box_width / 2),
        (box_x + box_length, box_y + box_width / 2),
    ])

    # Check each point against each corner
    for px, py in check_points:
        for cx, cy, corner_type in corners:
            if point_in_corner_exclusion(px, py, cx, cy, corner_radius, corner_type):
                return True

    return False


def get_box_orientations(box: Box) -> list[tuple[float, float, float, Orientation]]:
    """Get all valid orientations for a box based on rotation flags.

    Returns list of (length, width, height, orientation) tuples.
    """
    orientations = []
    dims = {"length": box.length, "width": box.width, "height": box.height}

    # All possible permutations of dimensions
    permutations = [
        ("length", "width", "height"),   # Original
        ("length", "height", "width"),   # Rotate around X (swap height/width)
        ("width", "length", "height"),   # Rotate around Z (swap length/width)
        ("width", "height", "length"),   # Rotate around Y then Z
        ("height", "length", "width"),   # Rotate around Y (swap height/length)
        ("height", "width", "length"),   # Rotate around X then Y
    ]

    for l_axis, w_axis, h_axis in permutations:
        # Determine which rotations are needed for this permutation
        needs_x = (h_axis != "height" and w_axis != "width") or (h_axis == "width" and w_axis == "height")
        needs_y = (h_axis != "height" and l_axis != "length") or (h_axis == "length" and l_axis == "height")
        needs_z = (l_axis != "length" and w_axis != "width") or (l_axis == "width" and w_axis == "length")

        # Check if this orientation is allowed
        # Original orientation is always allowed
        is_original = (l_axis == "length" and w_axis == "width" and h_axis == "height")

        if is_original:
            allowed = True
        else:
            # Simplified: allow if any required rotation is permitted
            # This is a heuristic - full rotation constraint checking is complex
            allowed = True
            if l_axis != "length" or w_axis != "width":
                allowed = allowed and box.can_rotate_z
            if h_axis != "height":
                if w_axis == "height" or h_axis == "width":
                    allowed = allowed and box.can_rotate_x
                if l_axis == "height" or h_axis == "length":
                    allowed = allowed and box.can_rotate_y

        if allowed:
            orientation = Orientation(
                length_axis=l_axis,
                width_axis=w_axis,
                height_axis=h_axis,
            )
            placed_dims = (dims[l_axis], dims[w_axis], dims[h_axis])

            # Avoid duplicates (same dimensions can result from different rotations)
            if not any(
                abs(placed_dims[0] - o[0]) < 0.001 and
                abs(placed_dims[1] - o[1]) < 0.001 and
                abs(placed_dims[2] - o[2]) < 0.001
                for o in orientations
            ):
                orientations.append((placed_dims[0], placed_dims[1], placed_dims[2], orientation))

    return orientations


def calculate_box_score(box: Box, accessibility_preference: float) -> float:
    """Calculate a sorting score for a box. Lower score = place first.

    Considers:
    - Priority (must_fit boxes first)
    - Weight (heavier boxes first for stability)
    - Fragility (robust boxes first, they go on bottom)
    - Access frequency (with accessibility_preference weighting)
    - Volume (larger boxes first for better space utilization)
    """
    score = 0.0

    # Priority: must_fit = 0, optional = 1000
    if box.priority == Priority.MUST_FIT:
        score += 0
    else:
        score += 1000

    # Weight: heavier boxes first (negative weight contribution)
    # Normalize to reasonable range
    score -= box.weight * 10

    # Fragility: robust first, then normal, then fragile
    fragility_scores = {
        Fragility.ROBUST: 0,
        Fragility.NORMAL: 50,
        Fragility.FRAGILE: 100,
    }
    score += fragility_scores.get(box.fragility, 50)

    # Access frequency: with high accessibility_preference, place often-used boxes later
    # (so they end up in more accessible positions at edges)
    # With low accessibility_preference, ignore this
    frequency_scores = {
        AccessFrequency.OFTEN: 200,
        AccessFrequency.SOMETIMES: 100,
        AccessFrequency.RARE: 0,
    }
    score += frequency_scores.get(box.access_frequency, 100) * accessibility_preference

    # Volume: larger boxes first (negative contribution)
    volume = box.length * box.width * box.height
    score -= volume * 0.01

    return score


def get_support_at_position(
    x: float, y: float, z: float,
    length: float, width: float,
    placed_boxes: list[PlacedBox],
    bed_floor_z: float,
    padding: float = 0,
) -> tuple[float, list[PlacedBox]]:
    """Calculate support level and supporting boxes at a position.

    Returns:
        (support_ratio, supporting_boxes) where support_ratio is 0-1
        indicating how much of the box's base is supported.
    """
    if z <= bed_floor_z + 0.001:
        # On the floor - fully supported
        return 1.0, []

    box_area = length * width
    if box_area <= 0:
        return 0.0, []

    supported_area = 0.0
    supporting = []

    for placed in placed_boxes:
        # Check if this placed box is directly below (z positions match with padding)
        # Box at z is supported by placed box at z_end + padding
        if abs(placed.z_end + padding - z) > 0.1:  # Small tolerance
            continue

        # Calculate overlap area
        overlap_x_start = max(x, placed.placement.x)
        overlap_x_end = min(x + length, placed.x_end)
        overlap_y_start = max(y, placed.placement.y)
        overlap_y_end = min(y + width, placed.y_end)

        if overlap_x_end > overlap_x_start and overlap_y_end > overlap_y_start:
            overlap_area = (overlap_x_end - overlap_x_start) * (overlap_y_end - overlap_y_start)
            supported_area += overlap_area
            supporting.append(placed)

    support_ratio = min(supported_area / box_area, 1.0)
    return support_ratio, supporting


def check_load_constraint(
    box: Box,
    supporting_boxes: list[PlacedBox],
    placed_boxes: list[PlacedBox],
    boxes_by_id: dict[str, Box],
) -> bool:
    """Check if placing this box would exceed max_supported_load of boxes below."""
    if not supporting_boxes:
        return True

    # Calculate total weight that would be on each supporting box
    for support in supporting_boxes:
        support_box = boxes_by_id.get(support.box.id)
        if not support_box or support_box.max_supported_load is None:
            continue

        # Calculate current load on this supporting box
        current_load = 0.0
        for placed in placed_boxes:
            if placed.placement.z > support.z_end - 0.1:  # Above the support
                # Check if it's actually on top of support
                _, supporters = get_support_at_position(
                    placed.placement.x, placed.placement.y, placed.placement.z,
                    placed.placed_length, placed.placed_width,
                    [support], support.placement.z
                )
                if supporters:
                    current_load += boxes_by_id[placed.box.id].weight

        # Check if adding new box exceeds limit
        if current_load + box.weight > support_box.max_supported_load:
            return False

    return True


def check_fragility_constraint(
    box: Box,
    supporting_boxes: list[PlacedBox],
) -> bool:
    """Check fragility rules: fragile boxes should not support heavy boxes."""
    for support in supporting_boxes:
        # Don't place heavy boxes on fragile ones
        if support.box.fragility == Fragility.FRAGILE and box.weight > 5:
            return False
        # Don't place robust/heavy boxes on normal boxes if weight is excessive
        if support.box.fragility == Fragility.NORMAL and box.weight > 15:
            return False
    return True


def find_placement_position(
    box: Box,
    orientation: tuple[float, float, float, Orientation],
    placed_boxes: list[PlacedBox],
    boxes_by_id: dict[str, Box],
    usable_space: FreeSpace,
    padding: float,
    strategy: Strategy,
    bed: Bed,
    total_margin: float,
) -> Optional[tuple[float, float, float]]:
    """Find the best position for a box with given orientation.

    Uses a corner-point heuristic: tries placing at corners of existing boxes
    and at the origin, choosing the position that best fits the strategy.
    Excludes positions that would intersect with rounded corners.
    """
    length, width, height, _ = orientation

    # Generate candidate positions (corner points)
    candidates: list[tuple[float, float, float]] = []

    # Start with origin of usable space
    candidates.append((usable_space.x, usable_space.y, usable_space.z))

    # Add corners from placed boxes
    for placed in placed_boxes:
        # Right of placed box
        candidates.append((placed.x_end + padding, placed.placement.y, placed.placement.z))
        # Behind placed box
        candidates.append((placed.placement.x, placed.y_end + padding, placed.placement.z))
        # On top of placed box (with padding for cardboard thickness)
        candidates.append((placed.placement.x, placed.placement.y, placed.z_end + padding))

    # Filter and score valid positions
    valid_positions: list[tuple[float, float, float, float]] = []

    for x, y, z in candidates:
        # Check bounds
        if x < usable_space.x or x + length > usable_space.x_end:
            continue
        if y < usable_space.y or y + width > usable_space.y_end:
            continue
        if z < usable_space.z or z + height > usable_space.z_end:
            continue

        # Check if box intersects with any rounded corner
        if box_intersects_corner(
            x, y, length, width,
            bed.length, bed.width,
            bed.corner_radius, total_margin
        ):
            continue

        # Check collision with placed boxes
        collision = False
        for placed in placed_boxes:
            # Check if boxes would overlap (with padding in all directions)
            if not (
                x + length + padding <= placed.placement.x or
                placed.x_end + padding <= x or
                y + width + padding <= placed.placement.y or
                placed.y_end + padding <= y or
                z + height + padding <= placed.placement.z or
                placed.z_end + padding <= z
            ):
                collision = True
                break

        if collision:
            continue

        # Check support (boxes above floor need support)
        support_ratio, supporting = get_support_at_position(
            x, y, z, length, width, placed_boxes, usable_space.z, padding
        )

        # Require at least 50% support for stability
        if z > usable_space.z + 0.1 and support_ratio < 0.5:
            continue

        # Check load and fragility constraints
        if not check_load_constraint(box, supporting, placed_boxes, boxes_by_id):
            continue
        if not check_fragility_constraint(box, supporting):
            continue

        # Calculate position score based on strategy
        if strategy == Strategy.MAXIMIZE_VOLUME:
            # Prefer positions that pack tightly (low x, low y, low z)
            score = x + y * 0.1 + z * 0.01
        else:  # MINIMIZE_HOLES
            # Prefer positions adjacent to existing boxes
            adjacency_score = 0
            for placed in placed_boxes:
                if abs(x - placed.x_end - padding) < 0.1:
                    adjacency_score -= 10
                if abs(y - placed.y_end - padding) < 0.1:
                    adjacency_score -= 10
                if abs(z - placed.z_end) < 0.1:
                    adjacency_score -= 5
            score = x + y * 0.1 + z * 0.01 + adjacency_score

        valid_positions.append((x, y, z, score))

    if not valid_positions:
        return None

    # Return position with best (lowest) score
    valid_positions.sort(key=lambda p: p[3])
    best = valid_positions[0]
    return (best[0], best[1], best[2])


def optimize_packing(
    bed: Bed,
    boxes: list[Box],
    settings: Settings,
) -> tuple[list[Placement], list[str], dict]:
    """Optimize the packing of boxes under a bed.

    Args:
        bed: The bed/container dimensions and margins.
        boxes: List of boxes to pack.
        settings: Packing settings including strategy and preferences.

    Returns:
        A tuple of:
        - placements: List of Placement objects for boxes that fit.
        - unplaced_box_ids: List of box IDs that could not be placed.
        - metrics: Dictionary with packing metrics.
    """
    placements: list[Placement] = []
    placed_boxes: list[PlacedBox] = []
    unplaced_box_ids: list[str] = []

    # Calculate usable space after margins
    total_margin = bed.margin + settings.margin
    usable_length = bed.length - (2 * total_margin)
    usable_width = bed.width - (2 * total_margin)
    usable_height = bed.height

    if usable_length <= 0 or usable_width <= 0 or usable_height <= 0:
        return [], [box.id for box in boxes], _calculate_metrics(
            boxes, [], usable_length, usable_width, usable_height
        )

    usable_space = FreeSpace(
        x=total_margin,
        y=total_margin,
        z=0,
        length=usable_length,
        width=usable_width,
        height=usable_height,
    )

    # Create lookup
    boxes_by_id = {box.id: box for box in boxes}

    # Sort boxes by score
    sorted_boxes = sorted(
        boxes,
        key=lambda b: calculate_box_score(b, settings.accessibility_preference),
    )

    # Place each box
    for box in sorted_boxes:
        best_placement: Optional[tuple[float, float, float, Orientation, float, float, float]] = None
        best_score = float("inf")

        # Try all valid orientations
        for length, width, height, orientation in get_box_orientations(box):
            # Skip if box doesn't fit in usable space at all
            if length > usable_length or width > usable_width or height > usable_height:
                continue

            position = find_placement_position(
                box, (length, width, height, orientation),
                placed_boxes, boxes_by_id, usable_space,
                settings.padding, settings.strategy,
                bed, total_margin,
            )

            if position:
                x, y, z = position
                # Score: prefer lower positions and positions closer to origin
                score = z * 1000 + x + y * 0.1
                if score < best_score:
                    best_score = score
                    best_placement = (x, y, z, orientation, length, width, height)

        if best_placement:
            x, y, z, orientation, length, width, height = best_placement
            placement = Placement(
                box_id=box.id,
                x=x,
                y=y,
                z=z,
                orientation=orientation,
            )
            placements.append(placement)
            placed_boxes.append(PlacedBox(
                box=box,
                placement=placement,
                placed_length=length,
                placed_width=width,
                placed_height=height,
            ))
        else:
            unplaced_box_ids.append(box.id)

    metrics = _calculate_metrics(
        boxes, placed_boxes, usable_length, usable_width, usable_height
    )

    return placements, unplaced_box_ids, metrics


def _calculate_metrics(
    boxes: list[Box],
    placed_boxes: list[PlacedBox],
    usable_length: float,
    usable_width: float,
    usable_height: float,
) -> dict:
    """Calculate packing metrics."""
    total_bed_volume = usable_length * usable_width * usable_height
    if total_bed_volume <= 0:
        total_bed_volume = 1

    # Calculate used volume
    used_volume = sum(
        pb.placed_length * pb.placed_width * pb.placed_height
        for pb in placed_boxes
    )

    used_volume_ratio = min(used_volume / total_bed_volume, 1.0)
    free_volume_ratio = 1.0 - used_volume_ratio

    # Calculate fragmentation score
    # Based on how scattered the placements are
    total_boxes = len(boxes)
    placed_count = len(placed_boxes)

    if placed_count == 0:
        fragmentation_score = 1.0
    else:
        # Calculate bounding box of all placed boxes
        min_x = min(pb.placement.x for pb in placed_boxes)
        max_x = max(pb.x_end for pb in placed_boxes)
        min_y = min(pb.placement.y for pb in placed_boxes)
        max_y = max(pb.y_end for pb in placed_boxes)
        min_z = min(pb.placement.z for pb in placed_boxes)
        max_z = max(pb.z_end for pb in placed_boxes)

        bounding_volume = (max_x - min_x) * (max_y - min_y) * (max_z - min_z)
        if bounding_volume > 0:
            # Fragmentation = 1 - (used volume / bounding volume)
            # Lower is better (more tightly packed)
            fragmentation_score = 1.0 - (used_volume / bounding_volume)
        else:
            fragmentation_score = 0.0

    return {
        "total_boxes": total_boxes,
        "placed_boxes": placed_count,
        "used_volume_ratio": round(used_volume_ratio, 4),
        "free_volume_ratio": round(free_volume_ratio, 4),
        "fragmentation_score": round(fragmentation_score, 4),
    }
