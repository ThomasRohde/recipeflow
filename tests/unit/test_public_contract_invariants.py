from __future__ import annotations

from types import MappingProxyType

import pytest
from pydantic import ValidationError

import recipeflow
from recipeflow.graph_index import GraphIndex
from recipeflow.models.common import (
    DurationSpec,
    NormalizedQuantity,
    TemperatureSpec,
)
from recipeflow.models.graph import RecipeGraph
from recipeflow.parsing import parse_document
from recipeflow.validation import ValidationOptions, validate


@pytest.mark.parametrize(
    "factory",
    [
        lambda: NormalizedQuantity(minimum=10, maximum=5),
        lambda: DurationSpec(
            source_text="5-10 minutes",
            minimum_minutes=10,
            maximum_minutes=5,
        ),
        lambda: TemperatureSpec(
            source_text="100-200 C",
            minimum=200,
            maximum=100,
            unit="C",
        ),
    ],
)
def test_public_range_contracts_reject_inverted_bounds(factory: object) -> None:
    assert callable(factory)
    with pytest.raises(ValidationError, match="minimum"):
        factory()


def _minimal_document(
    *,
    duration: str = "PT5M",
    source: object = "omitted",
) -> dict[str, object]:
    recipe: dict[str, object] = {"id": "contract", "title": "Contract"}
    if source != "omitted":
        recipe["source"] = source
    return {
        "recipeflow": 1,
        "recipe": recipe,
        "ingredients": {
            "base": {
                "label": "Base",
                "source_text": "1 base",
            }
        },
        "operations": [
            {
                "id": "finish",
                "action": "finish",
                "duration": duration,
                "inputs": ["base"],
                "outputs": {
                    "result": {
                        "label": "Result",
                        "role": "final",
                    }
                },
            }
        ],
    }


def test_iso_durations_are_parsed_conservatively() -> None:
    valid = parse_document(_minimal_document(duration="P1DT2H30M"))
    invalid = parse_document(
        _minimal_document(duration="PTdefinitely-not-a-duration")
    )
    assert valid.document is not None
    assert invalid.document is not None

    assert not any(item.code == "RF401" for item in validate(valid.document).diagnostics)
    assert any(item.code == "RF401" for item in validate(invalid.document).diagnostics)


def test_strict_provenance_rejects_an_empty_source_object() -> None:
    parsed = parse_document(
        _minimal_document(source={"url": None, "title": None})
    )
    assert parsed.document is not None

    result = validate(
        parsed.document,
        options=ValidationOptions(strict=True),
    )

    assert any(item.code == "RF390" for item in result.diagnostics)


def test_canonical_graph_and_indexes_are_deeply_read_only() -> None:
    graph = RecipeGraph(
        recipe_id="immutable",
        title="Immutable",
        nodes=[],
        edges=[],
        final_material_ids=[],
        subrecipes={},
    )
    index = GraphIndex(graph)

    assert isinstance(graph.nodes, tuple)
    assert isinstance(graph.edges, tuple)
    assert isinstance(graph.final_material_ids, tuple)
    assert isinstance(graph.subrecipes, MappingProxyType)
    with pytest.raises(AttributeError):
        graph.nodes.clear()  # type: ignore[attr-defined]
    with pytest.raises(TypeError):
        graph.subrecipes["new"] = object()  # type: ignore[index]
    with pytest.raises(TypeError):
        index.materials["new"] = object()  # type: ignore[index]
    with pytest.raises(AttributeError):
        index.materials = {}  # type: ignore[assignment]


def test_package_exposes_its_distribution_version() -> None:
    assert recipeflow.__version__ == "1.0.0"
