import json

from recipeflow.compilation import compile_document
from recipeflow.models.results import CliResult
from recipeflow.parsing import parse_json


def test_document_json_round_trip_uses_portable_aliases() -> None:
    source = {
        "recipeflow": 1,
        "recipe": {"id": "round-trip", "title": "Round trip", "yield": "4"},
        "ingredients": {"x": {"label": "X"}},
        "operations": [
            {
                "id": "finish",
                "action": "finish",
                "inputs": ["x"],
                "outputs": {"result": {"label": "Result", "role": "final"}},
            }
        ],
    }
    parsed = parse_json(json.dumps(source))
    assert parsed.document is not None

    serialized = parsed.document.model_dump_json()
    reparsed = parse_json(serialized)

    assert '"yield":' in serialized
    assert "yield_text" not in serialized
    assert reparsed.ok
    assert reparsed.document == parsed.document


def test_graph_and_result_contracts_are_versioned_and_serializable() -> None:
    parsed = parse_json(
        json.dumps(
            {
                "schema_version": "recipeflow.document/v1",
                "recipe": {"id": "contract", "title": "Contract"},
                "ingredients": {"x": {"label": "X"}},
                "operations": [
                    {
                        "id": "finish",
                        "action": "finish",
                        "inputs": ["x"],
                        "outputs": {
                            "result": {"label": "Result", "role": "final"}
                        },
                    }
                ],
            }
        )
    )
    assert parsed.document is not None
    compiled = compile_document(parsed.document)
    assert compiled.graph is not None

    graph_data = json.loads(compiled.graph.model_dump_json())
    envelope = CliResult(
        command="compile",
        ok=True,
        data=graph_data,
    )
    envelope_data = json.loads(envelope.model_dump_json())

    assert graph_data["schema_version"] == "recipeflow.graph/v1"
    assert envelope_data["schema_version"] == "recipeflow.cli-result/v1"
    assert envelope_data["ok"] is True
