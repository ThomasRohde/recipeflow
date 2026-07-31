import json

from recipeflow.compilation import compile_document
from recipeflow.parsing import parse_json, parse_yaml
from recipeflow.validation import validate


def _document(
    *,
    ingredients: dict[str, object] | None = None,
    operations: list[dict[str, object]] | None = None,
    setup: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "recipeflow": 1,
        "recipe": {"id": "test", "title": "Test"},
        "ingredients": ingredients or {"flour": {"label": "Flour"}},
        "setup": setup or [],
        "operations": operations
        or [
            {
                "id": "mix",
                "action": "mix",
                "inputs": ["flour"],
                "outputs": {"result": {"label": "Result", "role": "final"}},
            }
        ],
    }


def test_parsers_reject_duplicate_mapping_keys() -> None:
    yaml_result = parse_yaml(
        """
recipeflow: 1
recipe: {id: duplicate, title: Duplicate}
ingredients:
  flour: {label: First}
  flour: {label: Second}
operations: []
"""
    )
    json_result = parse_json(
        '{"recipeflow":1,"recipe":{"id":"x","id":"y","title":"T"},'
        '"ingredients":{},"operations":[]}'
    )

    assert not yaml_result.ok
    assert yaml_result.diagnostics[0].code == "RF103"
    assert not json_result.ok
    assert json_result.diagnostics[0].code == "RF103"


def test_self_consumption_is_reported_as_a_cycle() -> None:
    parsed = parse_json(
        json.dumps(
            _document(
                ingredients={},
                operations=[
                    {
                        "id": "mix",
                        "action": "mix",
                        "inputs": ["result"],
                        "outputs": {
                            "result": {"label": "Result", "role": "final"}
                        },
                    }
                ],
            )
        )
    )

    assert parsed.document is not None
    result = validate(parsed.document)
    assert not result.ok
    assert any(item.code == "RF213" for item in result.diagnostics)


def test_reserved_graph_namespaces_and_duplicate_setup_tokens_are_rejected() -> None:
    parsed = parse_json(
        json.dumps(
            _document(
                ingredients={"op:mix": {"label": "Collision"}},
                setup=[
                    {"id": "heat", "action": "heat", "produces": "ready"},
                    {"id": "warm", "action": "warm", "produces": "ready"},
                ],
                operations=[
                    {
                        "id": "mix",
                        "action": "mix",
                        "inputs": ["op:mix"],
                        "requires": ["ready"],
                        "outputs": {
                            "result": {"label": "Result", "role": "final"}
                        },
                    }
                ],
            )
        )
    )

    assert parsed.document is not None
    result = validate(parsed.document)
    assert {item.code for item in result.diagnostics} >= {"RF201", "RF202"}


def test_temporal_and_repetition_rules_are_structured() -> None:
    parsed = parse_json(
        json.dumps(
            _document(
                operations=[
                    {
                        "id": "mix",
                        "action": "mix",
                        "inputs": ["flour"],
                        "duration": "whenever",
                        "temperature": "very hot indeed",
                        "repeat": {"count": -3, "interval": "sometimes"},
                        "outputs": {
                            "result": {"label": "Result", "role": "final"}
                        },
                    }
                ]
            )
        )
    )

    assert parsed.document is not None
    result = validate(parsed.document)
    assert {item.code for item in result.diagnostics} >= {
        "RF401",
        "RF402",
        "RF403",
        "RF404",
    }


def test_compilation_is_canonical_across_mapping_order() -> None:
    first = _document(
        ingredients={
            "a": {"label": "A"},
            "b": {"label": "B"},
        },
        operations=[
            {
                "id": "mix",
                "action": "mix",
                "inputs": ["a", "b"],
                "repeat": {"count": 2},
                "outputs": {"result": {"label": "Result", "role": "final"}},
            }
        ],
    )
    second = {
        **first,
        "ingredients": {
            "b": {"label": "B"},
            "a": {"label": "A"},
        },
    }
    first_parsed = parse_json(json.dumps(first))
    second_parsed = parse_json(json.dumps(second))
    assert first_parsed.document is not None
    assert second_parsed.document is not None

    first_compiled = compile_document(first_parsed.document)
    second_compiled = compile_document(second_parsed.document)

    assert first_compiled.graph == second_compiled.graph
    assert first_compiled.graph is not None
    operation = next(
        node
        for node in first_compiled.graph.nodes
        if node.kind == "operation" and node.operation_kind == "transform"
    )
    assert operation.repeat is not None
    assert operation.repeat.count == 2
