import json

from recipeflow.analysis import analyze
from recipeflow.compatibility import format_document, migrate, semantic_diff
from recipeflow.compilation import compile_document
from recipeflow.parsing import parse_json


def _flow(quantity: str = "100 g") -> dict[str, object]:
    return {
        "recipeflow": 1,
        "recipe": {"id": "flow", "title": "Flow", "yield": "2 portions"},
        "ingredients": {
            "flour": {"label": "Flour", "quantity": quantity},
        },
        "operations": [
            {
                "id": "split",
                "action": "split",
                "inputs": ["flour"],
                "duration": "5 min",
                "outputs": {
                    "left": {"label": "Left"},
                    "right": {"label": "Right"},
                },
            },
            {
                "id": "join",
                "action": "combine",
                "inputs": ["left", "right"],
                "duration": "10 min",
                "outputs": {"result": {"label": "Result", "role": "final"}},
            },
        ],
    }


def _compiled_flow(quantity: str = "100 g"):
    parsed = parse_json(json.dumps(_flow(quantity)))
    assert parsed.document is not None
    compiled = compile_document(parsed.document)
    assert compiled.graph is not None
    return compiled.graph


def test_analysis_reports_splits_joins_parallelism_and_critical_path() -> None:
    report = analyze(_compiled_flow())

    assert report.operation_count == 2
    assert [item.id for item in report.splits] == ["split"]
    assert [item.id for item in report.joins] == ["join"]
    assert report.critical_path_operation_ids == ("split", "join")
    assert report.critical_path_minutes == 15


def test_format_is_deterministic_and_migration_is_explicit() -> None:
    source = json.dumps(_flow())
    first = format_document(source, source_format="json", output_format="yaml")
    second = format_document(source, source_format="json", output_format="yaml")
    migrated = migrate(source, source_format="json", output_format="json")

    assert first.ok
    assert first.content == second.content
    assert migrated.ok
    assert migrated.changed
    assert migrated.steps[0].target_version == "recipeflow.document/v1"
    assert migrated.content is not None
    assert '"schema_version": "recipeflow.document/v1"' in migrated.content
    assert '"recipeflow"' not in migrated.content


def test_semantic_diff_classifies_quantity_changes() -> None:
    result = semantic_diff(
        json.dumps(_flow("100 g")),
        json.dumps(_flow("125 g")),
        source_format="json",
    )

    assert result.ok
    assert any(item.kind == "quantity-changed" for item in result.changes)
