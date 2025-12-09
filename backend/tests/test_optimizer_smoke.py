"""Smoke tests for the optimizer engine."""

import pytest

from app.models import (
    Bed,
    Box,
    Settings,
    Fragility,
    AccessFrequency,
    Priority,
    Strategy,
)
from app.optimizer.engine import optimize_packing


def test_optimize_packing_empty_boxes():
    """Test optimization with no boxes."""
    bed = Bed(length=200, width=150, height=30, margin=5)
    boxes = []
    settings = Settings(strategy=Strategy.MAXIMIZE_VOLUME)

    placements, unplaced, metrics = optimize_packing(bed, boxes, settings)

    assert placements == []
    assert unplaced == []
    assert metrics["total_boxes"] == 0
    assert metrics["placed_boxes"] == 0


def test_optimize_packing_single_box_fits():
    """Test optimization with a single box that fits."""
    bed = Bed(length=200, width=150, height=30, margin=5)
    box = Box(
        id="box1",
        name="Test Box",
        length=50,
        width=40,
        height=20,
        weight=5,
        fragility=Fragility.NORMAL,
        access_frequency=AccessFrequency.SOMETIMES,
        priority=Priority.MUST_FIT,
    )
    settings = Settings(strategy=Strategy.MAXIMIZE_VOLUME)

    placements, unplaced, metrics = optimize_packing(bed, [box], settings)

    assert len(placements) == 1
    assert placements[0].box_id == "box1"
    assert unplaced == []
    assert metrics["total_boxes"] == 1
    assert metrics["placed_boxes"] == 1


def test_optimize_packing_box_too_large():
    """Test optimization with a box that is too large."""
    bed = Bed(length=100, width=80, height=20, margin=5)
    box = Box(
        id="bigbox",
        name="Big Box",
        length=150,  # Too long
        width=40,
        height=15,
        weight=10,
        fragility=Fragility.ROBUST,
        access_frequency=AccessFrequency.RARE,
        priority=Priority.OPTIONAL,
    )
    settings = Settings(strategy=Strategy.MAXIMIZE_VOLUME)

    placements, unplaced, metrics = optimize_packing(bed, [box], settings)

    assert len(placements) == 0
    assert unplaced == ["bigbox"]
    assert metrics["total_boxes"] == 1
    assert metrics["placed_boxes"] == 0


def test_optimize_packing_multiple_boxes():
    """Test optimization with multiple boxes, some fitting."""
    bed = Bed(length=200, width=150, height=30, margin=5)
    boxes = [
        Box(
            id="box1",
            name="Box 1",
            length=40,
            width=30,
            height=20,
            weight=3,
            fragility=Fragility.NORMAL,
            access_frequency=AccessFrequency.OFTEN,
            priority=Priority.MUST_FIT,
        ),
        Box(
            id="box2",
            name="Box 2",
            length=50,
            width=35,
            height=25,
            weight=5,
            fragility=Fragility.FRAGILE,
            access_frequency=AccessFrequency.SOMETIMES,
            priority=Priority.OPTIONAL,
        ),
        Box(
            id="box3",
            name="Box 3",
            length=60,
            width=40,
            height=20,
            weight=8,
            fragility=Fragility.ROBUST,
            access_frequency=AccessFrequency.RARE,
            priority=Priority.OPTIONAL,
        ),
    ]
    settings = Settings(strategy=Strategy.MAXIMIZE_VOLUME, padding=2)

    placements, unplaced, metrics = optimize_packing(bed, boxes, settings)

    # All boxes should fit in a 200cm bed with these sizes
    assert len(placements) == 3
    assert unplaced == []
    assert metrics["total_boxes"] == 3
    assert metrics["placed_boxes"] == 3
    assert metrics["used_volume_ratio"] > 0


def test_optimize_packing_must_fit_priority():
    """Test that must_fit boxes are placed before optional ones."""
    bed = Bed(length=100, width=80, height=30, margin=5)
    boxes = [
        Box(
            id="optional1",
            name="Optional 1",
            length=40,
            width=30,
            height=20,
            weight=3,
            fragility=Fragility.NORMAL,
            access_frequency=AccessFrequency.RARE,
            priority=Priority.OPTIONAL,
        ),
        Box(
            id="must1",
            name="Must Fit 1",
            length=45,
            width=30,
            height=20,
            weight=5,
            fragility=Fragility.NORMAL,
            access_frequency=AccessFrequency.OFTEN,
            priority=Priority.MUST_FIT,
        ),
    ]
    settings = Settings(strategy=Strategy.MAXIMIZE_VOLUME, padding=2)

    placements, unplaced, metrics = optimize_packing(bed, boxes, settings)

    # must1 should be placed first (lower x position)
    placed_ids = [p.box_id for p in placements]
    if "must1" in placed_ids and "optional1" in placed_ids:
        must1_placement = next(p for p in placements if p.box_id == "must1")
        optional1_placement = next(p for p in placements if p.box_id == "optional1")
        assert must1_placement.x < optional1_placement.x


def test_optimize_packing_returns_metrics():
    """Test that metrics are calculated correctly."""
    bed = Bed(length=100, width=100, height=50, margin=0)
    box = Box(
        id="box1",
        name="Box 1",
        length=50,
        width=50,
        height=25,
        weight=10,
        fragility=Fragility.ROBUST,
        access_frequency=AccessFrequency.SOMETIMES,
        priority=Priority.MUST_FIT,
    )
    settings = Settings(strategy=Strategy.MAXIMIZE_VOLUME, margin=0, padding=0)

    placements, unplaced, metrics = optimize_packing(bed, [box], settings)

    assert "total_boxes" in metrics
    assert "placed_boxes" in metrics
    assert "used_volume_ratio" in metrics
    assert "free_volume_ratio" in metrics
    assert "fragmentation_score" in metrics

    # Box volume: 50*50*25 = 62500
    # Bed volume: 100*100*50 = 500000
    # Used ratio should be 62500/500000 = 0.125
    assert metrics["used_volume_ratio"] == pytest.approx(0.125, rel=0.01)
    assert metrics["free_volume_ratio"] == pytest.approx(0.875, rel=0.01)
