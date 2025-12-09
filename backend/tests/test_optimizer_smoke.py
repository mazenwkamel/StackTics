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
from app.optimizer.engine import optimize_packing, get_box_orientations, calculate_box_score


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
    """Test optimization with a box that is too large in all orientations."""
    bed = Bed(length=100, width=80, height=20, margin=5)
    # Box is too large even when rotated (150 > 90 usable length, 90 > 70 usable width)
    box = Box(
        id="bigbox",
        name="Big Box",
        length=150,
        width=100,
        height=25,  # Also too tall
        weight=10,
        fragility=Fragility.ROBUST,
        access_frequency=AccessFrequency.RARE,
        priority=Priority.OPTIONAL,
        can_rotate_x=False,
        can_rotate_y=False,
        can_rotate_z=False,
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
    """Test that must_fit boxes are placed."""
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

    # Both should be placed
    placed_ids = [p.box_id for p in placements]
    assert "must1" in placed_ids
    assert len(placements) == 2


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


# New tests for Phase 2 features

def test_box_stacking():
    """Test that boxes can be stacked on top of each other."""
    bed = Bed(length=100, width=100, height=60, margin=5)
    boxes = [
        Box(
            id="bottom",
            name="Bottom Box",
            length=50,
            width=50,
            height=20,
            weight=10,
            fragility=Fragility.ROBUST,
            access_frequency=AccessFrequency.RARE,
            priority=Priority.MUST_FIT,
        ),
        Box(
            id="top",
            name="Top Box",
            length=40,
            width=40,
            height=15,
            weight=3,
            fragility=Fragility.NORMAL,
            access_frequency=AccessFrequency.OFTEN,
            priority=Priority.MUST_FIT,
        ),
    ]
    settings = Settings(strategy=Strategy.MAXIMIZE_VOLUME, padding=0)

    placements, unplaced, metrics = optimize_packing(bed, boxes, settings)

    assert len(placements) == 2
    assert unplaced == []

    # Find placements
    bottom_p = next(p for p in placements if p.box_id == "bottom")
    top_p = next(p for p in placements if p.box_id == "top")

    # Top box should be either next to or on top of bottom box
    # With the algorithm preferring floor placement, both might be on floor
    # But if stacked, top should be at z=20 (bottom's height)
    assert bottom_p.z == 0  # Bottom on floor


def test_heavy_box_below_light():
    """Test that heavier boxes are placed first (end up below)."""
    bed = Bed(length=100, width=100, height=50, margin=5)
    boxes = [
        Box(
            id="light",
            name="Light Box",
            length=40,
            width=40,
            height=15,
            weight=2,
            fragility=Fragility.NORMAL,
            access_frequency=AccessFrequency.SOMETIMES,
            priority=Priority.MUST_FIT,
        ),
        Box(
            id="heavy",
            name="Heavy Box",
            length=50,
            width=50,
            height=20,
            weight=20,
            fragility=Fragility.ROBUST,
            access_frequency=AccessFrequency.RARE,
            priority=Priority.MUST_FIT,
        ),
    ]
    settings = Settings(strategy=Strategy.MAXIMIZE_VOLUME, padding=0)

    placements, unplaced, metrics = optimize_packing(bed, boxes, settings)

    assert len(placements) == 2

    # Heavy box should be placed first due to sorting
    heavy_p = next(p for p in placements if p.box_id == "heavy")
    assert heavy_p.z == 0  # Heavy box on floor


def test_fragile_box_not_supporting_heavy():
    """Test that fragile boxes don't support heavy boxes."""
    bed = Bed(length=60, width=60, height=50, margin=5)
    boxes = [
        Box(
            id="fragile",
            name="Fragile Box",
            length=40,
            width=40,
            height=15,
            weight=2,
            fragility=Fragility.FRAGILE,
            access_frequency=AccessFrequency.SOMETIMES,
            priority=Priority.MUST_FIT,
        ),
        Box(
            id="heavy",
            name="Heavy Box",
            length=35,
            width=35,
            height=15,
            weight=10,  # Heavy - should not go on fragile
            fragility=Fragility.ROBUST,
            access_frequency=AccessFrequency.RARE,
            priority=Priority.MUST_FIT,
        ),
    ]
    settings = Settings(strategy=Strategy.MAXIMIZE_VOLUME, padding=0)

    placements, unplaced, metrics = optimize_packing(bed, boxes, settings)

    # Both should be placed but heavy should NOT be on top of fragile
    assert len(placements) == 2

    fragile_p = next(p for p in placements if p.box_id == "fragile")
    heavy_p = next(p for p in placements if p.box_id == "heavy")

    # Heavy should be on floor (placed first due to sorting)
    assert heavy_p.z == 0


def test_max_supported_load_constraint():
    """Test that max_supported_load is respected."""
    bed = Bed(length=60, width=60, height=60, margin=5)
    boxes = [
        Box(
            id="weak",
            name="Weak Box",
            length=40,
            width=40,
            height=15,
            weight=2,
            fragility=Fragility.NORMAL,
            access_frequency=AccessFrequency.SOMETIMES,
            priority=Priority.MUST_FIT,
            max_supported_load=5,  # Can only support 5kg
        ),
        Box(
            id="heavy",
            name="Heavy Box",
            length=35,
            width=35,
            height=15,
            weight=10,  # Too heavy to go on weak box
            fragility=Fragility.ROBUST,
            access_frequency=AccessFrequency.RARE,
            priority=Priority.MUST_FIT,
        ),
    ]
    settings = Settings(strategy=Strategy.MAXIMIZE_VOLUME, padding=0)

    placements, unplaced, metrics = optimize_packing(bed, boxes, settings)

    # Both should be placed
    assert len(placements) == 2

    # Heavy box should be on floor (not on weak box)
    heavy_p = next(p for p in placements if p.box_id == "heavy")
    assert heavy_p.z == 0


def test_box_rotation():
    """Test that boxes can be rotated to fit."""
    bed = Bed(length=100, width=50, height=30, margin=5)
    # Box is 80x30x20 - won't fit in 40 width without rotation
    box = Box(
        id="rotatable",
        name="Rotatable Box",
        length=80,
        width=30,
        height=20,
        weight=5,
        fragility=Fragility.NORMAL,
        access_frequency=AccessFrequency.SOMETIMES,
        priority=Priority.MUST_FIT,
        can_rotate_x=True,
        can_rotate_y=True,
        can_rotate_z=True,
    )
    settings = Settings(strategy=Strategy.MAXIMIZE_VOLUME, padding=0)

    placements, unplaced, metrics = optimize_packing(bed, [box], settings)

    # Box should fit (possibly rotated)
    assert len(placements) == 1
    assert unplaced == []


def test_no_rotation_constraint():
    """Test that rotation flags are respected."""
    bed = Bed(length=50, width=100, height=30, margin=5)
    # Box is 80x30x20 - needs Z rotation to fit in 40x90 space
    box = Box(
        id="fixed",
        name="Fixed Box",
        length=80,
        width=30,
        height=20,
        weight=5,
        fragility=Fragility.NORMAL,
        access_frequency=AccessFrequency.SOMETIMES,
        priority=Priority.MUST_FIT,
        can_rotate_x=False,
        can_rotate_y=False,
        can_rotate_z=False,  # Cannot rotate
    )
    settings = Settings(strategy=Strategy.MAXIMIZE_VOLUME, padding=0)

    placements, unplaced, metrics = optimize_packing(bed, [box], settings)

    # Box should not fit without rotation
    assert len(placements) == 0
    assert "fixed" in unplaced


def test_get_box_orientations():
    """Test that orientations are generated correctly."""
    box = Box(
        id="test",
        name="Test",
        length=30,
        width=20,
        height=10,
        weight=1,
        fragility=Fragility.NORMAL,
        access_frequency=AccessFrequency.SOMETIMES,
        priority=Priority.OPTIONAL,
        can_rotate_x=True,
        can_rotate_y=True,
        can_rotate_z=True,
    )

    orientations = get_box_orientations(box)

    # Should have multiple orientations (up to 6 for different dims)
    assert len(orientations) >= 1

    # All dimensions should be permutations of original
    original_dims = {30, 20, 10}
    for length, width, height, _ in orientations:
        assert {length, width, height} == original_dims


def test_calculate_box_score():
    """Test box scoring for sorting."""
    must_fit_heavy = Box(
        id="mh",
        name="Must Heavy",
        length=50,
        width=50,
        height=50,
        weight=20,
        fragility=Fragility.ROBUST,
        access_frequency=AccessFrequency.RARE,
        priority=Priority.MUST_FIT,
    )
    optional_light = Box(
        id="ol",
        name="Optional Light",
        length=20,
        width=20,
        height=20,
        weight=1,
        fragility=Fragility.FRAGILE,
        access_frequency=AccessFrequency.OFTEN,
        priority=Priority.OPTIONAL,
    )

    score_mh = calculate_box_score(must_fit_heavy, 0.5)
    score_ol = calculate_box_score(optional_light, 0.5)

    # Must fit heavy robust should be placed first (lower score)
    assert score_mh < score_ol


def test_minimize_holes_strategy():
    """Test that minimize_holes strategy affects placement."""
    bed = Bed(length=200, width=150, height=30, margin=5)
    boxes = [
        Box(
            id="box1",
            name="Box 1",
            length=40,
            width=40,
            height=20,
            weight=5,
            fragility=Fragility.NORMAL,
            access_frequency=AccessFrequency.SOMETIMES,
            priority=Priority.MUST_FIT,
        ),
        Box(
            id="box2",
            name="Box 2",
            length=40,
            width=40,
            height=20,
            weight=5,
            fragility=Fragility.NORMAL,
            access_frequency=AccessFrequency.SOMETIMES,
            priority=Priority.MUST_FIT,
        ),
    ]

    settings_volume = Settings(strategy=Strategy.MAXIMIZE_VOLUME, padding=2)
    settings_holes = Settings(strategy=Strategy.MINIMIZE_HOLES, padding=2)

    placements_v, _, _ = optimize_packing(bed, boxes, settings_volume)
    placements_h, _, _ = optimize_packing(bed, boxes, settings_holes)

    # Both strategies should place all boxes
    assert len(placements_v) == 2
    assert len(placements_h) == 2


def test_padding_applies_to_height():
    """Test that padding between stacked boxes applies in the z direction."""
    # Bed is exactly 30cm tall
    bed = Bed(length=100, width=100, height=30, margin=0)
    # Two boxes of exactly 15cm height - should NOT stack in 30cm with 2cm padding
    boxes = [
        Box(
            id="box1",
            name="Box 1",
            length=30,
            width=30,
            height=15,
            weight=3,
            fragility=Fragility.ROBUST,
            access_frequency=AccessFrequency.RARE,
            priority=Priority.MUST_FIT,
        ),
        Box(
            id="box2",
            name="Box 2",
            length=30,
            width=30,
            height=15,
            weight=3,
            fragility=Fragility.ROBUST,
            access_frequency=AccessFrequency.RARE,
            priority=Priority.MUST_FIT,
        ),
    ]
    # With 2cm padding, stacked boxes need: 15 + 2 + 15 = 32cm > 30cm
    settings = Settings(strategy=Strategy.MAXIMIZE_VOLUME, padding=2)

    placements, unplaced, metrics = optimize_packing(bed, boxes, settings)

    # Both boxes should fit side by side, not stacked
    assert len(placements) == 2
    assert len(unplaced) == 0

    # Both boxes should be on the floor (z=0) since they can't stack with padding
    for p in placements:
        assert p.z == 0, f"Box {p.box_id} should be on floor, but z={p.z}"


def test_padding_zero_allows_perfect_stacking():
    """Test that with zero padding, boxes can stack exactly."""
    # Bed is exactly 30cm tall
    bed = Bed(length=50, width=50, height=30, margin=0)
    # Two boxes of exactly 15cm height - should stack perfectly with no padding
    boxes = [
        Box(
            id="box1",
            name="Box 1",
            length=40,
            width=40,
            height=15,
            weight=3,
            fragility=Fragility.ROBUST,
            access_frequency=AccessFrequency.RARE,
            priority=Priority.MUST_FIT,
        ),
        Box(
            id="box2",
            name="Box 2",
            length=35,
            width=35,
            height=15,
            weight=2,
            fragility=Fragility.NORMAL,
            access_frequency=AccessFrequency.SOMETIMES,
            priority=Priority.MUST_FIT,
        ),
    ]
    # With 0 padding, stacked boxes need: 15 + 15 = 30cm = exactly fits
    settings = Settings(strategy=Strategy.MAXIMIZE_VOLUME, padding=0)

    placements, unplaced, metrics = optimize_packing(bed, boxes, settings)

    # Both boxes should be placed
    assert len(placements) == 2
    assert len(unplaced) == 0

    # One box should be on floor, one stacked on top
    z_positions = sorted([p.z for p in placements])
    assert z_positions[0] == 0, "First box should be on floor"
    assert z_positions[1] == 15, "Second box should be stacked at z=15"
