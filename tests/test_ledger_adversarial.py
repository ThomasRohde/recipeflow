from __future__ import annotations

from recipeflow.layout import LayoutOptions, create_tabular_layout
from recipeflow.models import Edge, MaterialNode, OperationNode, RecipeGraph
from recipeflow.typography import DeterministicTextMeasurer


def _layout(
    graph: RecipeGraph,
    *,
    page_height: float | None = None,
    safe_margin: float = 24,
):
    return create_tabular_layout(
        graph,
        LayoutOptions(
            notation="ledger",
            page_height=page_height,
            print_mode=page_height is not None,
            safe_margin=safe_margin,
        ),
        text_measurer=DeterministicTextMeasurer(),
    )


def _material(identifier: str, *, role: str = "ingredient", quantity: str | None = None):
    return MaterialNode(
        id=identifier,
        label=identifier.replace("-", " "),
        role=role,
        quantity=quantity,
    )


def _operation(identifier: str, action: str, *, kind: str = "transform"):
    return OperationNode(
        id=identifier,
        label=action,
        operation_kind=kind,
        action=action,
    )


def test_intermediate_and_six_direct_inputs_all_survive_in_join_entry() -> None:
    direct_ids = tuple(f"direct-{index}" for index in range(1, 7))
    graph = RecipeGraph(
        recipe_id="ledger-many-direct-inputs",
        title="Intermediate with direct additions",
        nodes=(
            _material("starter"),
            _operation("op:prepare", "prepare starter"),
            _material("prepared-starter", role="intermediate"),
            *(_material(identifier) for identifier in direct_ids),
            _operation("op:join", "join everything"),
            _material("finished-dish", role="final"),
        ),
        edges=(
            Edge(id="starter-in", kind="consumes", source="starter", target="op:prepare"),
            Edge(
                id="starter-out",
                kind="produces",
                source="op:prepare",
                target="prepared-starter",
            ),
            Edge(
                id="prepared-in",
                kind="consumes",
                source="prepared-starter",
                target="op:join",
            ),
            *(
                Edge(
                    id=f"{identifier}-in",
                    kind="consumes",
                    source=identifier,
                    target="op:join",
                )
                for identifier in direct_ids
            ),
            Edge(
                id="finished-out",
                kind="produces",
                source="op:join",
                target="finished-dish",
            ),
        ),
        final_material_ids=("finished-dish",),
    )

    layout = _layout(graph)
    join = next(item for item in layout.operations if item.operation_id == "op:join")
    consumed_on_join = {
        item.material_id
        for item in layout.materials
        if item.lane == 1 and item.show_left_label
    }
    join_text = {
        block.source_text
        for block in layout.text_blocks
        if block.id in join.text_block_ids
    }

    expected = {"prepared-starter", *direct_ids}
    assert set(join.input_material_ids) == expected
    assert consumed_on_join == expected
    assert {identifier.replace("-", " ") for identifier in direct_ids} <= join_text


def test_multiple_non_final_outputs_from_one_entry_receive_suffix_folios() -> None:
    graph = RecipeGraph(
        recipe_id="ledger-output-folios",
        title="Multiple output folios",
        nodes=(
            _material("raw"),
            _operation("op:separate", "separate"),
            _material("first-portion", role="intermediate"),
            _material("second-portion", role="intermediate"),
            _operation("op:finish", "finish"),
            _material("result", role="final"),
        ),
        edges=(
            Edge(id="raw-in", kind="consumes", source="raw", target="op:separate"),
            Edge(
                id="first-out",
                kind="produces",
                source="op:separate",
                target="first-portion",
            ),
            Edge(
                id="second-out",
                kind="produces",
                source="op:separate",
                target="second-portion",
            ),
            Edge(
                id="first-in",
                kind="consumes",
                source="first-portion",
                target="op:finish",
            ),
            Edge(
                id="second-in",
                kind="consumes",
                source="second-portion",
                target="op:finish",
            ),
            Edge(id="result-out", kind="produces", source="op:finish", target="result"),
        ),
        final_material_ids=("result",),
    )

    layout = _layout(graph)
    first_entry = next(item for item in layout.operations if item.operation_id == "op:separate")
    entry_text = {
        block.source_text
        for block in layout.text_blocks
        if block.id in first_entry.text_block_ids
    }

    assert {"M1a", "M1b"} <= entry_text
    assert len({text for text in entry_text if text.startswith("M1")}) == 2


def test_long_entry_heading_gives_material_branch_marker_its_own_row() -> None:
    graph = RecipeGraph(
        recipe_id="ledger-long-branch-heading",
        title="Long branch heading",
        nodes=(
            _material("first-input"),
            _operation("op:first", "prepare the first independent material branch"),
            _material("first-result", role="intermediate"),
            _material("second-input"),
            _operation(
                "op:second",
                "wash, trim, divide most into large pieces, and reserve an "
                "unquantified portion as thin garnish slices",
            ),
            _material("second-result", role="intermediate"),
            _operation("op:join", "combine both prepared branches"),
            _material("finished-dish", role="final"),
        ),
        edges=(
            Edge(
                id="first-input-edge",
                kind="consumes",
                source="first-input",
                target="op:first",
            ),
            Edge(
                id="first-output-edge",
                kind="produces",
                source="op:first",
                target="first-result",
            ),
            Edge(
                id="second-input-edge",
                kind="consumes",
                source="second-input",
                target="op:second",
            ),
            Edge(
                id="second-output-edge",
                kind="produces",
                source="op:second",
                target="second-result",
            ),
            Edge(
                id="first-join-edge",
                kind="consumes",
                source="first-result",
                target="op:join",
            ),
            Edge(
                id="second-join-edge",
                kind="consumes",
                source="second-result",
                target="op:join",
            ),
            Edge(
                id="final-edge",
                kind="produces",
                source="op:join",
                target="finished-dish",
            ),
        ),
        final_material_ids=("finished-dish",),
    )

    layout = _layout(graph)
    action = next(
        block
        for block in layout.text_blocks
        if block.id == "text:ledger:entry:op:second:action"
    )
    marker = next(
        block
        for block in layout.text_blocks
        if block.id == "text:ledger:entry:op:second:marker"
    )

    assert marker.source_text == "SEPARATE MATERIAL BRANCH"
    assert action.rect.y - (marker.rect.y + marker.rect.height) >= 2
    assert action.rect.x >= 12
    assert action.rect.x + action.rect.width <= layout.width - 12
    assert not action.overflow
    assert not marker.overflow


def test_independent_operations_use_authored_source_order_as_tie_break() -> None:
    graph = RecipeGraph(
        recipe_id="ledger-authored-order",
        title="Authored order",
        nodes=(
            _material("oil"),
            OperationNode(
                id="op:heat-oil",
                label="heat the oil",
                operation_kind="transform",
                action="heat the oil",
                source_path="/operations/1",
            ),
            _material("hot-oil", role="final"),
            _material("potatoes"),
            OperationNode(
                id="op:soak-potatoes",
                label="soak the potatoes",
                operation_kind="transform",
                action="soak the potatoes",
                source_path="/operations/0",
            ),
            _material("soaked-potatoes", role="final"),
        ),
        edges=(
            Edge(id="oil-in", kind="consumes", source="oil", target="op:heat-oil"),
            Edge(id="oil-out", kind="produces", source="op:heat-oil", target="hot-oil"),
            Edge(
                id="potatoes-in",
                kind="consumes",
                source="potatoes",
                target="op:soak-potatoes",
            ),
            Edge(
                id="potatoes-out",
                kind="produces",
                source="op:soak-potatoes",
                target="soaked-potatoes",
            ),
        ),
        final_material_ids=("hot-oil", "soaked-potatoes"),
    )

    layout = _layout(graph)

    assert [item.operation_id for item in layout.operations] == [
        "op:soak-potatoes",
        "op:heat-oil",
    ]


def test_explicit_precedes_is_rendered_as_after_entry_condition() -> None:
    graph = RecipeGraph(
        recipe_id="ledger-precedes",
        title="Explicit sequence",
        nodes=(
            _material("first-input"),
            _operation("op:first", "complete first task"),
            _material("first-result", role="final"),
            _material("second-input"),
            _operation("op:second", "complete second task"),
            _material("second-result", role="final"),
        ),
        edges=(
            Edge(
                id="first-input-edge",
                kind="consumes",
                source="first-input",
                target="op:first",
            ),
            Edge(
                id="first-output-edge",
                kind="produces",
                source="op:first",
                target="first-result",
            ),
            Edge(
                id="second-input-edge",
                kind="consumes",
                source="second-input",
                target="op:second",
            ),
            Edge(
                id="second-output-edge",
                kind="produces",
                source="op:second",
                target="second-result",
            ),
            Edge(id="sequence", kind="precedes", source="op:first", target="op:second"),
        ),
        final_material_ids=("first-result", "second-result"),
    )

    layout = _layout(graph)
    second = next(item for item in layout.operations if item.operation_id == "op:second")
    second_text = {
        block.source_text
        for block in layout.text_blocks
        if block.id in second.text_block_ids
    }

    assert "After entry 1" in second_text


def test_setup_produced_token_resolves_to_setup_folio_not_food() -> None:
    graph = RecipeGraph(
        recipe_id="ledger-setup-token",
        title="Setup token",
        nodes=(
            _operation("op:preheat", "preheat oven", kind="setup"),
            _material("oven-ready", role="intermediate"),
            _material("batter"),
            _operation("op:bake", "bake"),
            _material("cake", role="final"),
        ),
        edges=(
            Edge(
                id="oven-ready-out",
                kind="produces",
                source="op:preheat",
                target="oven-ready",
            ),
            Edge(id="batter-in", kind="consumes", source="batter", target="op:bake"),
            Edge(id="oven-required", kind="requires", source="oven-ready", target="op:bake"),
            Edge(id="cake-out", kind="produces", source="op:bake", target="cake"),
        ),
        final_material_ids=("cake",),
    )

    layout = _layout(graph)
    bake = next(item for item in layout.operations if item.operation_id == "op:bake")
    bake_text = {
        block.source_text
        for block in layout.text_blocks
        if block.id in bake.text_block_ids
    }

    assert "S1" in bake_text
    assert bake.input_material_ids == ("batter",)
    assert all(item.material_id != "oven-ready" for item in layout.materials)
    assert [item.operation_id for item in layout.setup] == ["op:preheat"]


def test_oversized_entry_splits_only_between_leaf_cells() -> None:
    input_ids = tuple(f"input-{index:02d}" for index in range(18))
    graph = RecipeGraph(
        recipe_id="ledger-safe-split",
        title="Safely split entry",
        nodes=(
            *(_material(identifier) for identifier in input_ids),
            _operation("op:combine", "combine all inputs"),
            _material("combined", role="final"),
        ),
        edges=(
            *(
                Edge(
                    id=f"{identifier}-edge",
                    kind="consumes",
                    source=identifier,
                    target="op:combine",
                )
                for identifier in input_ids
            ),
            Edge(
                id="combined-out",
                kind="produces",
                source="op:combine",
                target="combined",
            ),
        ),
        final_material_ids=("combined",),
    )

    layout = _layout(graph, page_height=400, safe_margin=20)
    operation = layout.operations[0]
    box_ids = {box.id for box in layout.boxes}
    consumed_boxes = [
        box
        for box in layout.boxes
        if box.id.startswith("box:ledger:consumed:op:combine:")
    ]

    assert len(operation.box_ids) > 1
    assert set(operation.box_ids) <= box_ids
    assert len(consumed_boxes) == len(input_ids)
    assert len({box.id for box in consumed_boxes}) == len(input_ids)
    assert any(path.style_class == "sheet-break" for path in layout.paths)
    assert layout.height % 400 == 0


def test_unsplittable_semantic_leaf_reports_rf508() -> None:
    long_label = " ".join("exceptionally-long-description" for _ in range(160))
    graph = RecipeGraph(
        recipe_id="ledger-unsplittable-leaf",
        title="Unsplittable leaf",
        nodes=(
            MaterialNode(
                id="huge-input",
                label=long_label,
                role="ingredient",
                quantity="1 portion",
            ),
            _operation("op:use", "use input"),
            _material("result", role="final"),
        ),
        edges=(
            Edge(id="huge-in", kind="consumes", source="huge-input", target="op:use"),
            Edge(id="result-out", kind="produces", source="op:use", target="result"),
        ),
        final_material_ids=("result",),
    )

    layout = _layout(graph, page_height=260, safe_margin=20)

    assert "RF508" in {item.code for item in layout.diagnostics}


def test_missing_partial_allocation_reports_rf506() -> None:
    graph = RecipeGraph(
        recipe_id="ledger-missing-allocation",
        title="Missing allocation",
        nodes=(
            _material("shared", quantity="100 g"),
            _operation("op:first", "use first portion"),
            _material("first-result", role="final"),
            _operation("op:second", "use second portion"),
            _material("second-result", role="final"),
        ),
        edges=(
            Edge(
                id="first-draw",
                kind="consumes",
                source="shared",
                target="op:first",
                quantity="40 g",
            ),
            Edge(
                id="first-result-out",
                kind="produces",
                source="op:first",
                target="first-result",
            ),
            Edge(id="second-draw", kind="consumes", source="shared", target="op:second"),
            Edge(
                id="second-result-out",
                kind="produces",
                source="op:second",
                target="second-result",
            ),
        ),
        final_material_ids=("first-result", "second-result"),
    )

    layout = _layout(graph)
    failures = [item for item in layout.diagnostics if item.code == "RF506"]

    assert len(failures) == 1
    assert failures[0].path == "/operations/op:second/inputs/shared"


def test_unconsumed_reserved_output_reports_rf507() -> None:
    graph = RecipeGraph(
        recipe_id="ledger-open-reserve",
        title="Open reserve",
        nodes=(
            _material("mixture", quantity="300 g"),
            _operation("op:divide", "divide mixture"),
            _material("served", role="final", quantity="250 g"),
            _material("held", role="reserved", quantity="50 g"),
        ),
        edges=(
            Edge(id="mixture-in", kind="consumes", source="mixture", target="op:divide"),
            Edge(id="served-out", kind="produces", source="op:divide", target="served"),
            Edge(id="held-out", kind="reserves", source="op:divide", target="held"),
        ),
        final_material_ids=("served",),
    )

    layout = _layout(graph)
    failures = [item for item in layout.diagnostics if item.code == "RF507"]

    assert len(failures) == 1
    assert failures[0].path == "/materials/held"
