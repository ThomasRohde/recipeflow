from __future__ import annotations

from recipeflow.compilation import compile_document
from recipeflow.models.graph import CompiledSubrecipe
from recipeflow.parsing import parse_document
from recipeflow.validation import validate


def _document_with_subrecipes(
    subrecipes: dict[str, object],
    *,
    reference: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "recipeflow": 1,
        "recipe": {"id": "composed", "title": "Composed recipe"},
        "ingredients": {"parent-base": {"label": "Parent base"}},
        "subrecipes": subrecipes,
        "operations": [
            {
                "id": "assemble",
                "action": "assemble",
                "inputs": ["parent-base"],
                "subrecipe": reference
                or {
                    "id": "sauce",
                    "output": "prepared",
                    "inputs": {"base": "parent-base"},
                },
                "outputs": {
                    "served": {
                        "label": "Served",
                        "role": "final",
                    }
                },
            }
        ],
    }


def _sauce() -> dict[str, object]:
    return {
        "id": "sauce",
        "title": "Sauce",
        "ingredients": {"base": {"label": "Base"}},
        "operations": [
            {
                "id": "blend",
                "action": "blend",
                "inputs": ["base"],
                "outputs": {"prepared": {"label": "Prepared sauce"}},
            }
        ],
        "output_ids": ["prepared"],
    }


def test_compilation_preserves_a_valid_compiled_subrecipe_boundary() -> None:
    parsed = parse_document(_document_with_subrecipes({"sauce": _sauce()}))
    assert parsed.document is not None

    validated = validate(parsed.document)
    compiled = compile_document(parsed.document)

    assert validated.ok
    assert compiled.ok
    assert compiled.graph is not None
    boundary = compiled.graph.subrecipes["sauce"]
    assert isinstance(boundary, CompiledSubrecipe)
    assert boundary.final_material_ids == ("prepared",)
    assert {node.id for node in boundary.nodes} >= {"base", "prepared", "op:blend"}
    assert boundary.edges
    assert all(
        item.source_path is not None
        and item.source_path.startswith("/subrecipes/sauce/")
        for item in (*boundary.nodes, *boundary.edges)
    )


def test_invalid_nested_graph_is_reported_before_compilation() -> None:
    invalid = _sauce()
    invalid["operations"] = [
        {
            "id": "blend",
            "action": "blend",
            "inputs": ["not-declared"],
            "outputs": {"prepared": {"label": "Prepared sauce"}},
        }
    ]
    parsed = parse_document(_document_with_subrecipes({"sauce": invalid}))
    assert parsed.document is not None

    validated = validate(parsed.document)
    compiled = compile_document(parsed.document)

    assert not validated.ok
    assert compiled.graph is None
    assert any(
        diagnostic.code == "RF104"
        and diagnostic.path.startswith("/subrecipes/sauce/")
        for diagnostic in validated.diagnostics
    )
    assert all(diagnostic.code != "RF900" for diagnostic in compiled.diagnostics)


def test_subrecipe_outputs_are_explicit_and_parent_selection_is_checked() -> None:
    invalid = _sauce()
    invalid["output_ids"] = ["not-produced"]
    parsed = parse_document(
        _document_with_subrecipes(
            {"sauce": invalid},
            reference={
                "id": "sauce",
                "output": "prepared",
                "inputs": {"base": "parent-base"},
            },
        )
    )
    assert parsed.document is not None

    result = validate(parsed.document)

    assert not result.ok
    assert {item.code for item in result.diagnostics} >= {"RF207", "RF215"}


def test_subrecipe_inputs_require_explicit_boundary_bindings() -> None:
    parsed = parse_document(
        _document_with_subrecipes(
            {"sauce": _sauce()},
            reference={"id": "sauce", "output": "prepared"},
        )
    )
    assert parsed.document is not None

    result = validate(parsed.document)

    missing = [item for item in result.diagnostics if item.code == "RF216"]
    assert len(missing) == 1
    assert missing[0].path == "/operations/0/subrecipe/inputs"


def test_recursive_subrecipe_dependencies_are_rejected() -> None:
    def component(identifier: str, dependency: str) -> dict[str, object]:
        return {
            "id": identifier,
            "title": identifier.upper(),
            "operations": [
                {
                    "id": f"use-{dependency}",
                    "action": f"use {dependency}",
                    "subrecipe": {"id": dependency, "output": f"{dependency}-out"},
                    "outputs": {
                        f"{identifier}-out": {"label": f"{identifier} output"}
                    },
                }
            ],
            "output_ids": [f"{identifier}-out"],
        }

    parsed = parse_document(
        _document_with_subrecipes(
            {
                "alpha": component("alpha", "beta"),
                "beta": component("beta", "alpha"),
            },
            reference={"id": "alpha", "output": "alpha-out"},
        )
    )
    assert parsed.document is not None

    result = validate(parsed.document)

    cycles = [item for item in result.diagnostics if item.code == "RF309"]
    assert len(cycles) == 1
    assert len(cycles[0].related_paths) == 2
