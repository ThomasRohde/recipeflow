from __future__ import annotations

import pytest
from test_tabular_layout_engine import _compiled_fixture

from recipeflow.exceptions import (
    LayoutStrategyRegistrationError,
    UnknownLayoutStrategyError,
)
from recipeflow.layout import (
    LayoutOptions,
    create_tabular_layout,
    get_layout_strategy,
    list_layout_strategies,
    register_layout_strategy,
    validate_tabular_layout,
)
from recipeflow.models import Edge, MaterialNode, OperationNode, RecipeGraph, TabularLayout
from recipeflow.typography import TextMeasurer


class _DelegatingStrategy:
    def __init__(self, notation: str) -> None:
        self.notation = notation

    def create_layout(
        self,
        graph: RecipeGraph,
        options: LayoutOptions,
        *,
        text_measurer: TextMeasurer | None = None,
    ) -> TabularLayout:
        flow_options = LayoutOptions(**{**vars(options), "notation": "flow"})
        layout = get_layout_strategy("flow").create_layout(
            graph,
            flow_options,
            text_measurer=text_measurer,
        )
        return layout.model_copy(update={"notation": self.notation})


def test_builtin_layout_strategies_are_public_and_flow_remains_default() -> None:
    assert list_layout_strategies() == ("compact-table", "flow", "ledger")

    layout = create_tabular_layout(_compiled_fixture("espresso-brownies"))

    assert layout.notation == "flow"


def test_ledger_is_deterministic_and_does_not_change_the_default_strategy() -> None:
    graph = _compiled_fixture("split-and-reserve")
    options = LayoutOptions(
        notation="ledger",
        preferred_width=794,
        page_height=1123,
        print_mode=True,
        safe_margin=40,
    )

    first = create_tabular_layout(graph, options)
    second = create_tabular_layout(graph, options)

    assert first.notation == "ledger"
    assert first.model_dump_json(by_alias=True) == second.model_dump_json(by_alias=True)
    assert create_tabular_layout(graph).notation == "flow"


@pytest.mark.parametrize(
    "fixture",
    [
        "espresso-brownies",
        "long-text",
        "measurement-systems",
        "branch-and-join",
        "split-and-reserve",
        "multiple-outputs",
        "setup-heavy",
        "many-narrow-operations",
        "long-completion-criteria",
        "unicode",
        "compact",
        "large",
    ],
)
def test_compact_table_creates_complete_valid_layouts(fixture: str) -> None:
    layout = create_tabular_layout(
        _compiled_fixture(fixture),
        LayoutOptions(notation="compact-table"),
    )

    assert layout.notation == "compact-table"
    assert layout.operations
    assert all(operation.box_ids for operation in layout.operations)
    assert validate_tabular_layout(layout) == ()
    assert layout.diagnostics == ()
    assert all(not block.overflow for block in layout.text_blocks)


def test_compact_table_links_noncontiguous_operation_spans() -> None:
    graph = RecipeGraph(
        recipe_id="nonconsecutive-spans",
        title="Nonconsecutive spans",
        nodes=(
            MaterialNode(id="a", label="a", role="ingredient"),
            MaterialNode(id="b", label="b", role="ingredient"),
            MaterialNode(id="c", label="c", role="ingredient"),
            OperationNode(
                id="op:ab",
                label="combine a b",
                operation_kind="transform",
                action="combine a b",
            ),
            OperationNode(
                id="op:bc",
                label="combine b c",
                operation_kind="transform",
                action="combine b c",
            ),
            OperationNode(
                id="op:ac",
                label="combine a c",
                operation_kind="transform",
                action="combine a c",
            ),
            MaterialNode(id="ab", label="ab", role="intermediate"),
            MaterialNode(id="bc", label="bc", role="intermediate"),
            MaterialNode(id="ac", label="ac", role="intermediate"),
            OperationNode(
                id="op:join",
                label="join",
                operation_kind="transform",
                action="join",
            ),
            MaterialNode(id="final", label="final", role="final"),
        ),
        edges=(
            Edge(id="a-ab", kind="consumes", source="a", target="op:ab"),
            Edge(id="b-ab", kind="consumes", source="b", target="op:ab"),
            Edge(id="ab-out", kind="produces", source="op:ab", target="ab"),
            Edge(id="b-bc", kind="consumes", source="b", target="op:bc"),
            Edge(id="c-bc", kind="consumes", source="c", target="op:bc"),
            Edge(id="bc-out", kind="produces", source="op:bc", target="bc"),
            Edge(id="a-ac", kind="consumes", source="a", target="op:ac"),
            Edge(id="c-ac", kind="consumes", source="c", target="op:ac"),
            Edge(id="ac-out", kind="produces", source="op:ac", target="ac"),
            Edge(id="ab-join", kind="consumes", source="ab", target="op:join"),
            Edge(id="bc-join", kind="consumes", source="bc", target="op:join"),
            Edge(id="ac-join", kind="consumes", source="ac", target="op:join"),
            Edge(id="final-out", kind="produces", source="op:join", target="final"),
        ),
        final_material_ids=("final",),
    )
    layout = create_tabular_layout(
        graph,
        LayoutOptions(notation="compact-table"),
    )
    operation = next(operation for operation in layout.operations if len(operation.box_ids) > 1)

    assert len(operation.box_ids) == 2
    assert any(
        path.id == f"path:table:segments:{operation.operation_id}"
        for path in layout.paths
    )


def test_compact_table_names_direct_source_inputs_inside_operation_cells() -> None:
    layout = create_tabular_layout(
        _compiled_fixture("setup-heavy"),
        LayoutOptions(notation="compact-table"),
    )
    fold = next(operation for operation in layout.operations if operation.action == "fold gently")
    visible = {
        block.source_text
        for block in layout.text_blocks
        if block.id in fold.text_block_ids
    }

    assert "Uses: 30 g softened unsalted butter" in visible


def test_unknown_and_invalid_strategy_names_are_structured() -> None:
    with pytest.raises(UnknownLayoutStrategyError):
        get_layout_strategy("missing.vendor")
    with pytest.raises(LayoutStrategyRegistrationError):
        register_layout_strategy("unnamespaced", _DelegatingStrategy("unnamespaced"))


def test_third_party_strategies_are_explicit_namespaced_and_non_overwriting() -> None:
    name = "tests:delegating"
    register_layout_strategy(name, _DelegatingStrategy(name))
    with pytest.raises(LayoutStrategyRegistrationError):
        register_layout_strategy(name, _DelegatingStrategy(name))

    layout = create_tabular_layout(
        _compiled_fixture("compact"),
        LayoutOptions(notation=name),
    )

    assert layout.notation == name


def test_strategy_must_report_the_selected_notation() -> None:
    name = "tests:mismatched"
    register_layout_strategy(name, _DelegatingStrategy("tests:other"))

    with pytest.raises(LayoutStrategyRegistrationError):
        create_tabular_layout(
            _compiled_fixture("compact"),
            LayoutOptions(notation=name),
        )
