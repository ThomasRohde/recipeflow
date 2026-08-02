from __future__ import annotations

import pytest

from recipeflow.layout import (
    LayoutOptions,
    create_tabular_layout,
    validate_tabular_layout,
)
from recipeflow.models import Edge, MaterialNode, OperationNode, RecipeGraph
from recipeflow.typography import DeterministicTextMeasurer


def _graph_with_unused_optional_water() -> RecipeGraph:
    return RecipeGraph(
        recipe_id="unused-source-material",
        title="Unused source material",
        nodes=(
            MaterialNode(
                id="potatoes",
                label="potatoes",
                role="ingredient",
                quantity="500 g",
            ),
            MaterialNode(
                id="water",
                label="water listed without a method use",
                role="optional",
                quantity="as needed",
                optional=True,
                source_text="Water - as needed",
            ),
            OperationNode(
                id="op:cook",
                label="cook potatoes",
                operation_kind="transform",
                action="cook the potatoes",
            ),
            MaterialNode(
                id="finished-potatoes",
                label="finished potatoes",
                role="final",
            ),
        ),
        edges=(
            Edge(
                id="potatoes-in",
                kind="consumes",
                source="potatoes",
                target="op:cook",
            ),
            Edge(
                id="finished-out",
                kind="produces",
                source="op:cook",
                target="finished-potatoes",
            ),
        ),
        final_material_ids=("finished-potatoes",),
    )


@pytest.mark.parametrize("notation", ["flow", "ledger"])
def test_unused_source_material_is_explicit_without_false_membership(
    notation: str,
) -> None:
    graph = _graph_with_unused_optional_water()
    layout = create_tabular_layout(
        graph,
        LayoutOptions(notation=notation, preferred_width=900),
        text_measurer=DeterministicTextMeasurer(),
    )

    unresolved = [
        block
        for block in layout.text_blocks
        if block.id.endswith("unresolved-source:water")
        or block.id.endswith("unresolved-source-material:water")
    ]

    assert len(unresolved) == 1
    assert unresolved[0].source_text == (
        "as needed · water listed without a method use · optional · "
        "UNRESOLVED · NO METHOD USE"
    )
    assert unresolved[0].role == "ingredient-annotation"
    assert any(
        block.source_text == "SOURCE MATERIALS WITH NO METHOD USE"
        for block in layout.text_blocks
    )
    assert "water" not in {material.material_id for material in layout.materials}
    assert all(path.source_id != "water" for path in layout.paths)
    assert all(
        "water" not in (*operation.input_material_ids, *operation.output_material_ids)
        for operation in layout.operations
    )
    assert graph.edges == _graph_with_unused_optional_water().edges
    assert not layout.diagnostics
    assert validate_tabular_layout(layout) == ()


def test_compact_table_keeps_its_existing_unused_material_treatment() -> None:
    layout = create_tabular_layout(
        _graph_with_unused_optional_water(),
        LayoutOptions(notation="compact-table", preferred_width=900),
        text_measurer=DeterministicTextMeasurer(),
    )

    assert "Water - as needed (optional)" in {
        block.source_text for block in layout.text_blocks
    }
    assert not any("unresolved-source" in block.id for block in layout.text_blocks)
    assert not any("unresolved-source" in box.id for box in layout.boxes)
    assert not layout.diagnostics
