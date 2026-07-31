from decimal import Decimal
from pathlib import Path

from recipeflow.api import compile_document, parse_yaml
from recipeflow.layout import (
    LayoutOptions,
    create_tabular_layout,
    validate_tabular_layout,
)
from recipeflow.models.common import NormalizedQuantity, Provenance, Quantity
from recipeflow.models.graph import Edge, MaterialNode, OperationNode, RecipeGraph
from recipeflow.typography import (
    DeterministicTextMeasurer,
    default_text_measurer,
)


def _compiled_fixture(name: str) -> RecipeGraph:
    source = Path(f"examples/golden/{name}.recipe.yaml").read_text(encoding="utf-8")
    parsed = parse_yaml(source)
    assert parsed.document is not None
    compiled = compile_document(parsed.document, strict=True)
    assert compiled.graph is not None
    return compiled.graph


def _graph() -> RecipeGraph:
    return RecipeGraph(
        recipe_id="layout-stress",
        title="Unicode crêpes with a deliberately long descriptive title",
        nodes=[
            MaterialNode(
                id="flour",
                label="stone-ground whole-grain flour with exceptionally long wording",
                role="ingredient",
                quantity="1 cup · 125 g",
            ),
            MaterialNode(
                id="milk",
                label="whole milk or unsweetened plant-based alternative",
                role="ingredient",
                quantity="250 mL",
            ),
            OperationNode(
                id="op:preheat",
                label="preheat the wide cast-iron pan thoroughly",
                operation_kind="setup",
                action="preheat",
                temperature="200 °C",
                duration="10 min",
            ),
            OperationNode(
                id="op:whisk",
                label="whisk until perfectly smooth",
                operation_kind="transform",
                action="whisk vigorously",
                until="no visible dry pockets remain and the batter is perfectly smooth",
            ),
            MaterialNode(
                id="batter",
                label="silky crêpe batter with café-style consistency",
                role="intermediate",
            ),
            OperationNode(
                id="op:cook",
                label="cook",
                operation_kind="transform",
                action="cook",
                temperature="200 °C",
                duration="2..3 min",
            ),
            MaterialNode(
                id="crepes",
                label="finished crème brûlée crêpes",
                role="final",
            ),
        ],
        edges=[
            Edge(id="e2", kind="consumes", source="flour", target="op:whisk"),
            Edge(id="e3", kind="consumes", source="milk", target="op:whisk"),
            Edge(id="e4", kind="produces", source="op:whisk", target="batter"),
            Edge(id="e5", kind="consumes", source="batter", target="op:cook"),
            Edge(id="e6", kind="requires", source="op:preheat", target="op:cook"),
            Edge(id="e7", kind="produces", source="op:cook", target="crepes"),
        ],
        final_material_ids=["crepes"],
    )


def test_layout_contains_measured_complete_text_and_no_collisions() -> None:
    layout = create_tabular_layout(
        _graph(),
        LayoutOptions(preferred_width=920, theme="modern"),
        text_measurer=DeterministicTextMeasurer(),
    )

    assert not layout.diagnostics
    assert layout.text_blocks
    assert all(not block.overflow for block in layout.text_blocks)
    assert any(len(block.lines) > 1 for block in layout.text_blocks)
    assert any(path.kind == "setup-dependency" for path in layout.paths)
    assert "finished crème brûlée crêpes" in {
        block.source_text for block in layout.text_blocks
    }
    assert validate_tabular_layout(layout) == ()


def test_horizontal_and_vertical_operation_orientations_are_resolved_in_layout() -> None:
    horizontal = create_tabular_layout(
        _graph(),
        LayoutOptions(operation_label_orientation="horizontal"),
        text_measurer=DeterministicTextMeasurer(),
    )
    vertical = create_tabular_layout(
        _graph(),
        LayoutOptions(operation_label_orientation="vertical"),
        text_measurer=DeterministicTextMeasurer(),
    )

    assert {operation.orientation for operation in horizontal.operations} == {"horizontal"}
    assert {operation.orientation for operation in vertical.operations} == {"vertical"}
    assert any(block.rotation == -90 for block in vertical.text_blocks)


def test_duration_ranges_use_unambiguous_visual_typography() -> None:
    layout = create_tabular_layout(
        _graph(),
        text_measurer=DeterministicTextMeasurer(),
    )
    cook = next(
        operation
        for operation in layout.operations
        if operation.operation_id == "op:cook"
    )
    detail = next(
        block
        for block in layout.text_blocks
        if block.id == "text:operation:op:cook:detail"
    )

    assert cook.duration == "2..3 min"
    assert detail.source_text == "Temperature: 200 °C · Time: 2 to 3 min"


def test_layout_validator_reports_overlapping_opaque_boxes() -> None:
    layout = create_tabular_layout(
        _graph(),
        text_measurer=DeterministicTextMeasurer(),
    )
    opaque = [box for box in layout.boxes if box.opaque]
    first, second = opaque[:2]
    moved = second.model_copy(update={"rect": first.rect})
    invalid_boxes = tuple(moved if box.id == second.id else box for box in layout.boxes)
    invalid = layout.model_copy(update={"boxes": invalid_boxes})

    assert "RF505" in {item.code for item in validate_tabular_layout(invalid)}


def test_many_narrow_operations_auto_vertical_actions_do_not_overflow() -> None:
    layout = create_tabular_layout(
        _compiled_fixture("many-narrow-operations"),
        LayoutOptions(theme="classic"),
    )

    action_blocks = {
        block.id: block
        for block in layout.text_blocks
        if block.role == "operation-action"
    }
    expected_vertical = {
        "text:operation:op:fill:action",
        "text:operation:op:moisten:action",
        "text:operation:op:boil:action",
        "text:operation:op:toss:action",
    }
    assert expected_vertical <= action_blocks.keys()
    assert all(
        action_blocks[identifier].rotation == -90
        and not action_blocks[identifier].overflow
        for identifier in expected_vertical
    )
    assert "RF501" not in {item.code for item in layout.diagnostics}


def test_long_text_layout_recovers_ingredient_detail_and_setup_notes() -> None:
    layout = create_tabular_layout(
        _compiled_fixture("long-text"),
        LayoutOptions(theme="classic"),
    )
    blocks = {block.source_text: block for block in layout.text_blocks}

    pastry_source = (
        "one 28 cm all-butter sweet pastry shell, blind-baked until deeply "
        "golden at the edges and completely cooled in its fluted tart pan"
    )
    pastry_preparation = "completely cooled in its fluted tart pan"
    setup_note = (
        "Allow at least twenty minutes after the thermostat first signals "
        "readiness so the baking stone and oven walls reach an even temperature."
    )
    assert blocks[pastry_source].role == "ingredient-source"
    assert blocks[pastry_preparation].role == "ingredient-preparation"
    assert blocks[setup_note].role == "setup-note"
    assert all(not block.overflow for block in layout.text_blocks)
    assert "RF501" not in {item.code for item in layout.diagnostics}


def test_ingredient_visibility_options_control_quantities_and_provenance() -> None:
    ingredient = MaterialNode(
        id="flour",
        label="stone-ground flour",
        role="ingredient",
        quantity="1 cup",
        normalized_quantity=Quantity(
            source_text="1 cup",
            normalized=NormalizedQuantity(value=Decimal("250"), unit="g"),
        ),
        source_text="1 cup stone-ground flour from the source",
        preparation_state="sifted twice",
        annotations=("keep the bran",),
        provenance=(Provenance(source_text="ingredient line 4"),),
    )
    graph = RecipeGraph(
        recipe_id="visibility",
        title="Visibility options",
        nodes=[
            ingredient,
            OperationNode(
                id="op:mix",
                label="mix",
                operation_kind="transform",
                action="mix",
            ),
            MaterialNode(id="dough", label="dough", role="final"),
        ],
        edges=[
            Edge(id="e1", kind="consumes", source="flour", target="op:mix"),
            Edge(id="e2", kind="produces", source="op:mix", target="dough"),
        ],
        final_material_ids=["dough"],
    )

    normalized_only = create_tabular_layout(
        graph,
        LayoutOptions(
            show_source_quantities=False,
            show_normalized_quantities=True,
            show_provenance=False,
        ),
        text_measurer=DeterministicTextMeasurer(),
    )
    normalized_text = {block.source_text for block in normalized_only.text_blocks}
    assert "250 g" in normalized_text
    assert "1 cup" not in normalized_text
    assert "1 cup stone-ground flour from the source" not in normalized_text
    assert "sifted twice" in normalized_text
    assert "keep the bran" in normalized_text
    assert "ingredient line 4" not in normalized_text

    with_evidence = create_tabular_layout(
        graph,
        LayoutOptions(show_provenance=True),
        text_measurer=DeterministicTextMeasurer(),
    )
    evidence_blocks = {
        block.source_text: block.role for block in with_evidence.text_blocks
    }
    assert evidence_blocks["1 cup"] == "ingredient-quantity"
    assert (
        evidence_blocks["1 cup stone-ground flour from the source"]
        == "ingredient-source"
    )
    assert evidence_blocks["ingredient line 4"] == "ingredient-provenance"


def test_intermediate_label_visibility_option_preserves_final_label() -> None:
    visible = create_tabular_layout(
        _graph(),
        LayoutOptions(show_intermediate_labels=True),
        text_measurer=DeterministicTextMeasurer(),
    )
    hidden = create_tabular_layout(
        _graph(),
        LayoutOptions(show_intermediate_labels=False),
        text_measurer=DeterministicTextMeasurer(),
    )
    visible_ids = {block.id for block in visible.text_blocks}
    hidden_ids = {block.id for block in hidden.text_blocks}

    assert "text:material:batter" in visible_ids
    assert "text:material:batter" not in hidden_ids
    assert "text:material:crepes" in hidden_ids
    batter = next(
        material for material in hidden.materials if material.material_id == "batter"
    )
    assert not batter.show_inline_label
    assert batter.label_box_id is None


def test_unicode_layout_uses_conservative_widths_inside_final_card() -> None:
    layout = create_tabular_layout(_compiled_fixture("unicode"))
    final = next(
        block
        for block in layout.text_blocks
        if block.id == "text:material:creme-brulee"
    )
    measurer = default_text_measurer()
    available_width = final.rect.width - final.padding.left - final.padding.right

    assert final.source_text == "crème brûlée au café · καραμέλα · コーヒー"
    assert len(final.lines) > 1
    assert not final.overflow
    assert all(
        measurer.measure(line.text, final.style).width <= available_width + 0.01
        for line in final.lines
    )
    assert "RF501" not in {item.code for item in layout.diagnostics}


def test_layout_exposes_recipe_yield_and_material_portion_quantities() -> None:
    caramel = create_tabular_layout(_compiled_fixture("long-completion-criteria"))
    split = create_tabular_layout(_compiled_fixture("split-and-reserve"))

    yield_block = next(block for block in caramel.text_blocks if block.id == "text:yield")
    split_text = {block.source_text for block in split.text_blocks}

    assert yield_block.role == "recipe-yield"
    assert yield_block.source_text == "Yield: 450 mL sauce"
    assert "250 mL · cream for the mousse base" in split_text
    assert "50 mL · reserved cream for the final rosette" in split_text


def test_layout_exposes_per_operation_input_quantities() -> None:
    layout = create_tabular_layout(_compiled_fixture("many-narrow-operations"))
    quantities = {
        block.id: block.source_text
        for block in layout.text_blocks
        if block.role == "operation-input-quantity"
    }

    assert quantities["text:operation:op:moisten:input-quantities"] == (
        "Uses: 30 mL water for sealing and boiling"
    )
    assert quantities["text:operation:op:boil:input-quantities"] == (
        "Uses: 2970 mL water for sealing and boiling"
    )

    large = create_tabular_layout(_compiled_fixture("large"))
    large_quantities = {
        block.id: block.source_text
        for block in large.text_blocks
        if block.role == "operation-input-quantity"
    }
    assert large_quantities["text:operation:op:build-sauce:input-quantities"] == (
        "Uses: 500 mL unsalted chicken stock · 800 g peeled plum tomatoes"
    )
    assert "text:operation:op:braise:input-quantities" not in (
        large_quantities
    )


def test_setup_targets_and_dependency_routes_remain_individually_traceable() -> None:
    graph = _compiled_fixture("setup-heavy")
    layout = create_tabular_layout(graph)
    setup_nodes = {
        node.id: node
        for node in graph.nodes
        if isinstance(node, OperationNode) and node.operation_kind == "setup"
    }
    dependency_paths = [
        path for path in layout.paths if path.kind == "setup-dependency"
    ]
    portion_paths = [
        path
        for path in dependency_paths
        if path.target_ids == ("op:portion",)
    ]

    assert setup_nodes["op:prepare-ramekins"].target == "six 180 mL ramekins"
    assert "Target: six 180 mL ramekins" in {
        block.source_text for block in layout.text_blocks
    }
    required_by = {
        block.id: block.source_text
        for block in layout.text_blocks
        if block.role == "setup-required-by"
    }
    assert required_by["text:setup:op:organize-station:required-by"] == (
        "Required by: fill and level"
    )
    assert required_by["text:setup:op:clear-door:required-by"] == (
        "Required by: transfer and bake"
    )
    assert len({path.points[1].y for path in dependency_paths}) == len(
        dependency_paths
    )
    assert len(portion_paths) == 2
    assert portion_paths[0].points[-1].x != portion_paths[1].points[-1].x
    assert not layout.diagnostics
