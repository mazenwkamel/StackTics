"""API routes for StackTics."""

from fastapi import APIRouter

from app.schemas import (
    OptimizeRequest,
    OptimizeResponse,
    PlacementSchema,
    OrientationSchema,
    MetricsSchema,
)
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


router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "app": "StackTics"}


@router.post("/optimize", response_model=OptimizeResponse)
async def optimize(request: OptimizeRequest) -> OptimizeResponse:
    """Run the packing optimization algorithm.

    Takes bed dimensions, a list of boxes, and settings.
    Returns optimized placements, unplaced boxes, and metrics.
    """
    # Convert schema to domain models
    bed = Bed(
        length=request.bed.length,
        width=request.bed.width,
        height=request.bed.height,
        margin=request.bed.margin,
        corner_radius=request.bed.corner_radius,
    )

    boxes = [
        Box(
            id=box.id,
            name=box.name,
            length=box.length,
            width=box.width,
            height=box.height,
            weight=box.weight,
            fragility=Fragility(box.fragility.value),
            access_frequency=AccessFrequency(box.access_frequency.value),
            priority=Priority(box.priority.value),
            can_rotate_x=box.can_rotate_x,
            can_rotate_y=box.can_rotate_y,
            can_rotate_z=box.can_rotate_z,
            max_supported_load=box.max_supported_load,
        )
        for box in request.boxes
    ]

    settings = Settings(
        strategy=Strategy(request.settings.strategy.value),
        accessibility_preference=request.settings.accessibility_preference,
        padding=request.settings.padding,
        margin=request.settings.margin,
    )

    # Run optimization
    placements, unplaced_box_ids, metrics = optimize_packing(bed, boxes, settings)

    # Convert domain models back to schema
    placement_schemas = [
        PlacementSchema(
            box_id=p.box_id,
            x=p.x,
            y=p.y,
            z=p.z,
            orientation=OrientationSchema(
                length_axis=p.orientation.length_axis,
                width_axis=p.orientation.width_axis,
                height_axis=p.orientation.height_axis,
            ),
        )
        for p in placements
    ]

    return OptimizeResponse(
        placements=placement_schemas,
        unplaced_box_ids=unplaced_box_ids,
        metrics=MetricsSchema(**metrics),
    )
