from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from recipeflow.models.common import (
    DurationSpec,
    NormalizedQuantity,
    Quantity,
    ResourceRequirement,
)
from recipeflow.models.document import RepeatSpec
from recipeflow.models.graph import Edge, MaterialNode, OperationNode, RecipeGraph
from recipeflow.planning import (
    PlanningRequest,
    RecipeInstance,
    ResourceCapacity,
    plan_recipes,
    project_mise_en_place,
    project_shopping_list,
)

TARGET = datetime(2026, 7, 30, 18, 0, tzinfo=UTC)


def _graph(
    nodes: list[MaterialNode | OperationNode],
    edges: list[Edge] | None = None,
) -> RecipeGraph:
    return RecipeGraph(
        recipe_id="planning",
        title="Planning",
        nodes=nodes,
        edges=edges or [],
        final_material_ids=[],
    )


def test_planner_converts_supported_duration_units_and_repeat_counts() -> None:
    graph = _graph(
        [
            OperationNode(
                id="op:milliseconds",
                label="Milliseconds",
                operation_kind="transform",
                action="wait",
                duration="60000 ms",
            ),
            OperationNode(
                id="op:seconds",
                label="Seconds",
                operation_kind="transform",
                action="wait",
                duration="120 seconds",
            ),
            OperationNode(
                id="op:hours",
                label="Hours",
                operation_kind="transform",
                action="wait",
                duration="1.5 hours",
                repeat=RepeatSpec(count=2),
            ),
            OperationNode(
                id="op:days",
                label="Days",
                operation_kind="transform",
                action="wait",
                duration="1 day",
            ),
            OperationNode(
                id="op:structured",
                label="Structured",
                operation_kind="transform",
                action="wait",
                duration_value=DurationSpec(
                    source_text="4..6 min",
                    minimum_minutes=Decimal(4),
                    maximum_minutes=Decimal(6),
                ),
            ),
        ]
    )

    result = plan_recipes(
        PlanningRequest(
            recipes=(RecipeInstance(id="durations", graph=graph),),
            target_time=TARGET,
        )
    )

    assert result.plan is not None
    durations = {
        operation.operation_id: operation.duration_minutes
        for operation in result.plan.operations
    }
    assert durations == {
        "milliseconds": Decimal(1),
        "seconds": Decimal(2),
        "hours": Decimal(180),
        "days": Decimal(1440),
        "structured": Decimal(6),
    }


def test_planner_reports_capacity_cycles_and_fallback_duration() -> None:
    over_capacity = _graph(
        [
            OperationNode(
                id="op:busy",
                label="Busy",
                operation_kind="transform",
                action="work",
                duration="5 min",
                resources=(
                    ResourceRequirement(id="hands", quantity=2),
                ),
            )
        ]
    )
    capacity_result = plan_recipes(
        PlanningRequest(
            recipes=(RecipeInstance(id="busy", graph=over_capacity),),
            target_time=TARGET,
            resources=(ResourceCapacity(id="hands", capacity=1),),
        )
    )
    assert not capacity_result.ok
    assert capacity_result.diagnostics[0].code == "RF702"

    cycle = _graph(
        [
            MaterialNode(id="a", label="A", role="intermediate"),
            MaterialNode(id="b", label="B", role="intermediate"),
            OperationNode(
                id="op:first",
                label="First",
                operation_kind="transform",
                action="first",
            ),
            OperationNode(
                id="op:second",
                label="Second",
                operation_kind="transform",
                action="second",
            ),
        ],
        [
            Edge(id="e1", kind="produces", source="op:first", target="a"),
            Edge(id="e2", kind="consumes", source="a", target="op:second"),
            Edge(id="e3", kind="produces", source="op:second", target="b"),
            Edge(id="e4", kind="consumes", source="b", target="op:first"),
        ],
    )
    cycle_result = plan_recipes(
        PlanningRequest(
            recipes=(RecipeInstance(id="cycle", graph=cycle),),
            target_time=TARGET,
        )
    )
    assert not cycle_result.ok
    assert cycle_result.diagnostics[0].code == "RF701"

    fallback = _graph(
        [
            OperationNode(
                id="op:unknown",
                label="Unknown",
                operation_kind="transform",
                action="wait",
                equipment=("oven",),
            )
        ]
    )
    fallback_result = plan_recipes(
        PlanningRequest(
            recipes=(RecipeInstance(id="fallback", graph=fallback),),
            target_time=TARGET,
            default_operation_minutes=Decimal(7),
        )
    )
    assert fallback_result.plan is not None
    assert fallback_result.plan.operations[0].duration_minutes == 7
    assert fallback_result.plan.operations[0].resource_ids == ("oven",)
    assert fallback_result.diagnostics[0].code == "RF710"


def test_shopping_and_mise_projections_preserve_normalized_and_source_values() -> None:
    graph = _graph(
        [
            MaterialNode(
                id="flour",
                label="Flour",
                role="ingredient",
                normalized_quantity=Quantity(
                    source_text="100 g",
                    normalized=NormalizedQuantity(
                        minimum=Decimal(100),
                        maximum=Decimal(100),
                        unit="g",
                    ),
                ),
                preparation_state="sifted",
                temperature_state="room temperature",
                annotations=("fine",),
            ),
            MaterialNode(
                id="salt",
                label="Salt",
                role="optional",
                quantity="1 pinch",
                optional=True,
            ),
            MaterialNode(
                id="water",
                label="Water",
                role="ingredient",
            ),
            MaterialNode(
                id="produced",
                label="Produced",
                role="ingredient",
            ),
            OperationNode(
                id="op:setup",
                label="Preheat oven",
                operation_kind="setup",
                action="preheat",
                duration="10 min",
                temperature="180 C",
            ),
            OperationNode(
                id="op:make",
                label="Make",
                operation_kind="transform",
                action="make",
            ),
        ],
        [
            Edge(
                id="produced-edge",
                kind="produces",
                source="op:make",
                target="produced",
            )
        ],
    )
    recipes = (
        RecipeInstance(id="one", graph=graph, scale=Decimal(2)),
        RecipeInstance(id="two", graph=graph, scale=Decimal("0.5")),
    )

    shopping = project_shopping_list(recipes)
    mise = project_mise_en_place(recipes)

    by_label = {item.label: item for item in shopping}
    assert by_label["Flour"].normalized_quantity == 250
    assert by_label["Flour"].unit == "g"
    assert by_label["Flour"].quantity_texts == ("100 g",)
    assert by_label["Salt"].quantity_texts == (
        "1 pinch x 0.5",
        "1 pinch x 2",
    )
    assert by_label["Salt"].optional
    assert by_label["Water"].normalized_quantity is None
    assert "Produced" not in by_label
    assert {item.kind for item in mise} == {"material", "setup"}
    assert any(item.detail == "sifted · room temperature · fine" for item in mise)
    assert any(item.detail == "180 C · 10 min" for item in mise)
