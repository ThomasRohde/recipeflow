from __future__ import annotations

from typing import Any, cast

from recipeflow.models.common import Severity
from recipeflow.parsing import parse, parse_document, parse_json, parse_yaml
from recipeflow.validation import ValidationOptions, validate


def _document(
    *,
    ingredients: dict[str, object] | None = None,
    setup: list[dict[str, object]] | None = None,
    operations: list[dict[str, object]] | None = None,
    recipe: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "recipeflow": 1,
        "recipe": recipe or {"id": "edge-cases", "title": "Edge cases"},
        "ingredients": ingredients or {"base": {"label": "Base"}},
        "setup": setup or [],
        "operations": operations
        or [
            {
                "id": "finish",
                "action": "finish",
                "inputs": ["base"],
                "outputs": {"result": {"label": "Result", "role": "final"}},
            }
        ],
    }


def test_parse_accepts_mapping_model_and_alias_entrypoint() -> None:
    mapping_result = parse_document(_document())
    assert mapping_result.document is not None

    model_result = parse(mapping_result.document)

    assert model_result.ok
    assert model_result.document is mapping_result.document
    assert model_result.source_version == "recipeflow.document/v1"


def test_parse_reports_non_mapping_wrong_type_and_escaped_model_path() -> None:
    sequence = parse_yaml("- one\n- two\n")
    wrong_type = parse_document(cast(Any, 42))
    invalid_model = parse_document(
        {
            **_document(),
            "ingredients": {"bad/key~part": {}},
        }
    )

    assert sequence.diagnostics[0].code == "RF102"
    assert "mapping object" in sequence.diagnostics[0].message
    assert wrong_type.diagnostics[0].code == "RF102"
    assert invalid_model.diagnostics[0].path == "/ingredients/bad~1key~0part/label"
    assert all(
        result.diagnostics[0].context["category"] == "parse"
        for result in (sequence, wrong_type, invalid_model)
    )


def test_parse_rejects_unhashable_yaml_key_and_legacy_version() -> None:
    unhashable = parse_yaml("? [one, two]\n: value\n")
    legacy = parse_document({**_document(), "recipeflow": 2})

    assert unhashable.diagnostics[0].code == "RF101"
    assert legacy.diagnostics[0].code == "RF601"
    assert legacy.source_version == "recipeflow.legacy/2"


def test_validation_reports_reference_shape_and_identifier_failures() -> None:
    parsed = parse_document(
        _document(
            ingredients={
                "op:base": {"label": "Reserved namespace"},
                "shared": {"label": "Shared"},
            },
            setup=[
                {
                    "id": "duplicate",
                    "action": "preheat",
                    "produces": "ready",
                    "duration": "eventually",
                    "temperature": "scorching",
                },
                {
                    "id": "second",
                    "action": "prepare",
                    "produces": "ready",
                },
            ],
            operations=[
                {
                    "id": "duplicate",
                    "action": "first",
                    "inputs": ["shared", "shared", "ghost"],
                    "requires": ["missing-prerequisite"],
                    "precedes": ["missing-successor"],
                    "outputs": {
                        "shared": {"label": "Duplicate material"},
                        "bad-role": {
                            "label": "Bad role",
                            "role": "ingredient",
                        },
                        "bad-final": {
                            "label": "Bad final",
                            "role": "waste",
                            "final": True,
                        },
                    },
                    "subrecipe": {"id": "missing-subrecipe"},
                },
                {
                    "id": "empty",
                    "action": "empty",
                    "inputs": [],
                    "outputs": {},
                },
            ],
        )
    )
    assert parsed.document is not None

    result = validate(parsed.document)
    codes = {diagnostic.code for diagnostic in result.diagnostics}

    assert codes >= {
        "RF101",
        "RF102",
        "RF103",
        "RF104",
        "RF105",
        "RF201",
        "RF202",
        "RF203",
        "RF205",
        "RF206",
        "RF301",
        "RF302",
        "RF303",
        "RF401",
        "RF402",
    }


def test_validation_reports_material_lifecycle_failures() -> None:
    parsed = parse_json(
        """
{
  "recipeflow": 1,
  "recipe": {"id": "lifecycle", "title": "Lifecycle"},
  "ingredients": {
    "base": {"label": "Base"},
    "reserved": {"label": "Reserved", "role": "reserved"}
  },
  "operations": [
    {
      "id": "prepare",
      "action": "prepare",
      "inputs": ["base", "reserved"],
      "outputs": {
        "shared": {"label": "Shared"},
        "orphan": {"label": "Orphan"},
        "final-a": {"label": "Final A", "role": "final"},
        "final-b": {"label": "Final B", "final": true}
      }
    },
    {
      "id": "use-one",
      "action": "use",
      "inputs": ["shared"],
      "outputs": {"one": {"label": "One", "role": "waste"}}
    },
    {
      "id": "use-two",
      "action": "use",
      "inputs": ["shared"],
      "outputs": {"two": {"label": "Two", "role": "waste"}}
    }
  ]
}
"""
    )
    assert parsed.document is not None

    result = validate(parsed.document)
    codes = {diagnostic.code for diagnostic in result.diagnostics}

    assert codes >= {"RF304", "RF305", "RF306", "RF307"}


def test_shareable_terminal_cooutput_is_intentionally_retained() -> None:
    parsed = parse_document(
        _document(
            operations=[
                {
                    "id": "finish",
                    "action": "finish",
                    "inputs": ["base"],
                    "outputs": {
                        "retained": {
                            "label": "Retained useful co-output",
                            "shareable": True,
                        },
                        "result": {"label": "Result", "role": "final"},
                    },
                }
            ]
        )
    )
    assert parsed.document is not None

    result = validate(parsed.document)

    assert "RF304" not in {item.code for item in result.diagnostics}


def test_empty_repeat_split_mismatch_connectivity_and_warning_promotion() -> None:
    parsed = parse_document(
        _document(
            ingredients={
                "base": {"label": "Base"},
                "isolated": {"label": "Isolated", "optional": True},
            },
            operations=[
                {
                    "id": "split",
                    "action": "split",
                    "operation_type": "split",
                    "inputs": [
                        {"material": "base", "quantity": "100 g"},
                    ],
                    "repeat": {},
                    "outputs": {
                        "left": {"label": "Left", "quantity": "40 g"},
                        "right": {
                            "label": "Right",
                            "quantity": "50 g",
                            "role": "final",
                        },
                    },
                },
            ],
        )
    )
    assert parsed.document is not None

    result = validate(
        parsed.document,
        options=ValidationOptions(warnings_as_errors=True),
    )
    by_code = {diagnostic.code: diagnostic for diagnostic in result.diagnostics}

    assert {"RF405", "RF406", "RF308"} <= by_code.keys()
    assert by_code["RF308"].severity == Severity.ERROR


def test_split_quantity_uses_declared_material_amount_when_input_is_implicit() -> None:
    parsed = parse_document(
        _document(
            ingredients={
                "cream": {
                    "label": "Cream",
                    "quantity": "300 mL",
                },
            },
            operations=[
                {
                    "id": "divide",
                    "action": "divide",
                    "inputs": ["cream"],
                    "outputs": {
                        "base": {
                            "label": "Base cream",
                            "quantity": "250 mL",
                        },
                        "reserve": {
                            "label": "Reserved cream",
                            "quantity": "100 mL",
                            "role": "final",
                        },
                    },
                },
            ],
        )
    )
    assert parsed.document is not None

    result = validate(parsed.document)

    mismatch = next(item for item in result.diagnostics if item.code == "RF406")
    assert mismatch.path == "/operations/0/outputs"
    assert "350 mL" in mismatch.message
    assert "300 mL" in mismatch.message


def test_strict_validation_requires_recipe_and_ingredient_provenance() -> None:
    parsed = parse_document(_document())
    assert parsed.document is not None

    result = validate(parsed.document, strict=True)

    assert {diagnostic.code for diagnostic in result.diagnostics} >= {
        "RF390",
        "RF391",
    }
