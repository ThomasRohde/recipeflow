from __future__ import annotations

import json

import pytest

from recipeflow.compatibility import format_document, migrate, semantic_diff
from recipeflow.compilation import compile_document, compile_recipe
from recipeflow.exceptions import RecipeCompilationError
from recipeflow.models.graph import (
    Edge,
    EdgeKind,
    MaterialNode,
    OperationNode,
    RecipeGraph,
)
from recipeflow.parsing import parse_document


def _rich_document() -> dict[str, object]:
    return {
        "recipeflow": 1,
        "recipe": {"title": "Rich compilation"},
        "ingredients": {
            "base": {
                "label": "Base",
                "quantity": {
                    "source_text": "100 g",
                    "normalized": {"value": "100", "unit": "g"},
                },
            },
            "seasoning": {"label": "Seasoning", "optional": True},
            "reserved-input": {
                "label": "Reserved input",
                "role": "reserved",
            },
        },
        "setup": [
            {
                "id": "heat",
                "action": "heat",
                "target": "oven",
                "produces": "hot",
                "duration": {
                    "source_text": "10 min",
                    "minimum_minutes": "10",
                },
                "temperature": {
                    "source_text": "180 C",
                    "value": "180",
                    "unit": "C",
                },
            },
            {
                "id": "prepare",
                "action": "prepare",
                "produces": "ready",
                "requires": ["hot"],
            },
        ],
        "operations": [
            {
                "id": "transform",
                "action": "transform",
                "inputs": [
                    {"material": "base", "quantity": "100 g"},
                    {"material": "seasoning", "optional": True},
                    {
                        "material": "reserved-input",
                        "reserve": True,
                        "from_reserve": True,
                    },
                ],
                "requires": ["ready"],
                "precedes": ["finish"],
                "outputs": {
                    "kept": {"label": "Kept", "role": "reserved"},
                    "scraps": {"label": "Scraps", "role": "waste"},
                    "mixture": {"label": "Mixture"},
                },
            },
            {
                "id": "finish",
                "action": "finish",
                "inputs": [
                    {"material": "kept", "from_reserve": True},
                    "mixture",
                ],
                "outputs": {
                    "result": {"label": "Result", "role": "final"},
                },
            },
        ],
    }


def test_compilation_preserves_structured_values_and_edge_semantics() -> None:
    parsed = parse_document(_rich_document())
    assert parsed.document is not None

    result = compile_document(parsed.document)

    assert result.graph is not None
    graph = result.graph
    assert graph.recipe_id.startswith("recipe:auto-")
    kinds = {edge.kind for edge in graph.edges}
    assert {
        EdgeKind.REQUIRES,
        EdgeKind.PRECEDES,
        EdgeKind.RESERVES,
        EdgeKind.DISCARDS,
        EdgeKind.OPTIONALLY_APPLIES,
    } <= kinds
    setup = next(node for node in graph.nodes if node.id == "op:heat")
    assert isinstance(setup, OperationNode)
    assert setup.duration_value is not None
    assert setup.temperature_value is not None
    base = next(node for node in graph.nodes if node.id == "base")
    assert isinstance(base, MaterialNode)
    assert base.normalized_quantity is not None


def test_compile_recipe_raises_structured_error_for_invalid_document() -> None:
    parsed = parse_document(
        {
            "recipeflow": 1,
            "recipe": {"id": "invalid", "title": "Invalid"},
            "ingredients": {"unused": {"label": "Unused"}},
            "operations": [],
        }
    )
    assert parsed.document is not None

    with pytest.raises(RecipeCompilationError) as captured:
        compile_recipe(parsed.document)

    assert captured.value.diagnostics
    assert captured.value.diagnostics[0].code.startswith("RF")


def test_format_and_migrate_return_diagnostics_for_invalid_sources() -> None:
    formatted = format_document("recipe: [")
    unsupported = migrate("{}", target_version="recipeflow.document/v99")
    invalid = migrate("recipe: [")

    assert not formatted.ok
    assert formatted.diagnostics[0].code == "RF101"
    assert not unsupported.ok
    assert unsupported.diagnostics[0].code == "RF601"
    assert not invalid.ok
    assert invalid.diagnostics[0].code == "RF101"


def test_migrating_current_document_is_an_unchanged_dry_run() -> None:
    current = {
        **_rich_document(),
        "schema_version": "recipeflow.document/v1",
    }
    current.pop("recipeflow")

    result = migrate(current, output_format="json", dry_run=True)

    assert result.ok
    assert not result.changed
    assert result.dry_run
    assert result.steps == ()
    assert result.content is not None
    assert json.loads(result.content)["schema_version"] == "recipeflow.document/v1"


def _graph(
    *,
    materials: list[MaterialNode],
    operations: list[OperationNode],
    edges: list[Edge],
    finals: list[str],
) -> RecipeGraph:
    return RecipeGraph(
        recipe_id="diff",
        title="Diff",
        nodes=[*materials, *operations],
        edges=edges,
        final_material_ids=finals,
    )


def test_semantic_diff_classifies_graph_shape_and_edge_changes() -> None:
    before = _graph(
        materials=[
            MaterialNode(
                id="ingredient",
                label="Old ingredient",
                role="ingredient",
                quantity="1",
            ),
            MaterialNode(id="removed", label="Removed", role="intermediate"),
            MaterialNode(id="final-old", label="Old final", role="final"),
        ],
        operations=[
            OperationNode(
                id="op:removed",
                label="Removed",
                operation_kind="transform",
                action="remove",
            ),
            OperationNode(
                id="op:shared",
                label="Shared",
                operation_kind="transform",
                action="old action",
            ),
        ],
        edges=[
            Edge(
                id="old-reserve",
                kind="reserves",
                source="ingredient",
                target="op:shared",
            ),
            Edge(
                id="old-require",
                kind="requires",
                source="op:removed",
                target="op:shared",
            ),
            Edge(
                id="old-dependency",
                kind="produces",
                source="op:shared",
                target="final-old",
            ),
        ],
        finals=["final-old"],
    )
    after = _graph(
        materials=[
            MaterialNode(
                id="ingredient",
                label="New ingredient",
                role="optional",
                quantity="2",
            ),
            MaterialNode(id="added", label="Added", role="ingredient"),
            MaterialNode(id="final-new", label="New final", role="final"),
        ],
        operations=[
            OperationNode(
                id="op:shared",
                label="Shared",
                operation_kind="transform",
                action="new action",
            ),
            OperationNode(
                id="op:added",
                label="Added",
                operation_kind="transform",
                action="add",
            ),
        ],
        edges=[
            Edge(
                id="new-reserve",
                kind="reserves",
                source="ingredient",
                target="op:added",
            ),
            Edge(
                id="new-require",
                kind="requires",
                source="op:added",
                target="op:shared",
            ),
            Edge(
                id="new-dependency",
                kind="produces",
                source="op:shared",
                target="final-new",
            ),
        ],
        finals=["final-new"],
    )

    result = semantic_diff(before, after)
    kinds = {change.kind for change in result.changes}

    assert kinds >= {
        "ingredient-added",
        "material-removed",
        "ingredient-renamed",
        "quantity-changed",
        "material-role-changed",
        "operation-added",
        "operation-removed",
        "operation-changed",
        "final-output-changed",
        "reservation-altered",
        "setup-requirement-changed",
        "dependency-changed",
    }


def test_semantic_diff_propagates_parse_diagnostics() -> None:
    valid = json.dumps(
        {
            "recipeflow": 1,
            "recipe": {"id": "valid", "title": "Valid"},
            "ingredients": {"base": {"label": "Base"}},
            "operations": [
                {
                    "id": "finish",
                    "action": "finish",
                    "inputs": ["base"],
                    "outputs": {
                        "result": {"label": "Result", "role": "final"}
                    },
                }
            ],
        }
    )

    result = semantic_diff("recipe: [", valid)

    assert not result.ok
    assert result.diagnostics[0].code == "RF101"
