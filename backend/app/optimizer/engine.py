"""Packing optimization engine.

This module contains the core algorithm for optimizing box placement under a bed.
Currently implements a simple stub that places boxes in a line along the x-axis.
"""

from app.models import (
    Bed,
    Box,
    Settings,
    Placement,
    Orientation,
    Priority,
)


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
    unplaced_box_ids: list[str] = []

    # Calculate usable space after margins
    total_margin = bed.margin + settings.margin
    usable_length = bed.length - (2 * total_margin)
    usable_width = bed.width - (2 * total_margin)
    usable_height = bed.height

    if usable_length <= 0 or usable_width <= 0 or usable_height <= 0:
        # No usable space, all boxes are unplaced
        return [], [box.id for box in boxes], _calculate_metrics(
            boxes, [], bed, usable_length, usable_width, usable_height
        )

    # Sort boxes: must_fit first, then by volume (largest first)
    sorted_boxes = sorted(
        boxes,
        key=lambda b: (
            0 if b.priority == Priority.MUST_FIT else 1,
            -(b.length * b.width * b.height),
        ),
    )

    # Simple placement: line up boxes along x-axis
    current_x = total_margin
    padding = settings.padding

    for box in sorted_boxes:
        # Check if box fits in remaining x space
        # For this stub, we don't rotate - just use original dimensions
        box_length = box.length
        box_width = box.width
        box_height = box.height

        # Check if box fits in the usable space
        fits_length = (current_x + box_length + total_margin) <= bed.length
        fits_width = box_width <= usable_width
        fits_height = box_height <= usable_height

        if fits_length and fits_width and fits_height:
            placement = Placement(
                box_id=box.id,
                x=current_x,
                y=total_margin,
                z=0,
                orientation=Orientation.default(),
            )
            placements.append(placement)
            current_x += box_length + padding
        else:
            unplaced_box_ids.append(box.id)

    metrics = _calculate_metrics(
        boxes, placements, bed, usable_length, usable_width, usable_height
    )

    return placements, unplaced_box_ids, metrics


def _calculate_metrics(
    boxes: list[Box],
    placements: list[Placement],
    bed: Bed,
    usable_length: float,
    usable_width: float,
    usable_height: float,
) -> dict:
    """Calculate packing metrics.

    Args:
        boxes: All boxes in the request.
        placements: Successfully placed boxes.
        bed: Bed dimensions.
        usable_length: Available length after margins.
        usable_width: Available width after margins.
        usable_height: Available height.

    Returns:
        Dictionary of metrics.
    """
    total_bed_volume = usable_length * usable_width * usable_height
    if total_bed_volume <= 0:
        total_bed_volume = 1  # Avoid division by zero

    # Create a lookup for placed boxes
    placed_box_ids = {p.box_id for p in placements}
    boxes_by_id = {box.id: box for box in boxes}

    # Calculate used volume
    used_volume = sum(
        boxes_by_id[box_id].length * boxes_by_id[box_id].width * boxes_by_id[box_id].height
        for box_id in placed_box_ids
        if box_id in boxes_by_id
    )

    used_volume_ratio = min(used_volume / total_bed_volume, 1.0)
    free_volume_ratio = 1.0 - used_volume_ratio

    # Fragmentation score: placeholder calculation
    # Lower is better. For now, just use the ratio of unplaced to total boxes.
    total_boxes = len(boxes)
    placed_boxes = len(placements)
    fragmentation_score = (total_boxes - placed_boxes) / max(total_boxes, 1)

    return {
        "total_boxes": total_boxes,
        "placed_boxes": placed_boxes,
        "used_volume_ratio": round(used_volume_ratio, 4),
        "free_volume_ratio": round(free_volume_ratio, 4),
        "fragmentation_score": round(fragmentation_score, 4),
    }
