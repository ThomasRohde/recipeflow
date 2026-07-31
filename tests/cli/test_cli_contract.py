import json
from pathlib import Path
from typing import Any, NoReturn

import pytest
from typer.testing import CliRunner

from recipeflow.cli.main import app

runner = CliRunner()
EXAMPLE = Path(__file__).parents[2] / "examples" / "espresso-brownies.recipe.yaml"


def _json(result: Any) -> dict[str, object]:
    value = json.loads(result.stdout)
    assert isinstance(value, dict)
    assert value["schema_version"] == "recipeflow.cli-result/v1"
    return value


def test_machine_validation_is_one_stable_envelope() -> None:
    result = runner.invoke(app, ["validate", str(EXAMPLE), "--json"])

    assert result.exit_code == 0
    envelope = _json(result)
    assert envelope["command"] == "validate"
    assert envelope["ok"] is True
    assert result.stderr == ""


def test_parse_version_validation_and_io_exit_codes(tmp_path: Path) -> None:
    syntax = tmp_path / "syntax.recipe.yaml"
    syntax.write_text("recipe: [", encoding="utf-8")
    unsupported = tmp_path / "unsupported.recipe.yaml"
    unsupported.write_text(
        "schema_version: recipeflow.document/v99\nrecipe: {}\n",
        encoding="utf-8",
    )
    invalid = tmp_path / "invalid.recipe.yaml"
    invalid.write_text(
        """\
recipeflow: 1
recipe: {id: invalid, title: Invalid}
ingredients:
  unused: {label: unused}
operations:
  - id: finish
    action: finish
    outputs:
      result: {label: result, role: final}
""",
        encoding="utf-8",
    )

    syntax_result = runner.invoke(app, ["validate", str(syntax), "--json"])
    version_result = runner.invoke(app, ["validate", str(unsupported), "--json"])
    invalid_result = runner.invoke(app, ["validate", str(invalid), "--json"])
    missing_result = runner.invoke(
        app,
        ["validate", str(tmp_path / "missing.recipe.yaml"), "--json"],
    )
    missing_outputs = tmp_path / "missing-outputs.recipe.yaml"
    missing_outputs.write_text(
        """\
recipeflow: 1
recipe: {id: shape, title: Shape}
ingredients:
  base: {label: Base}
operations:
  - {id: broken, action: transform, inputs: [base], outputs: {}}
""",
        encoding="utf-8",
    )
    shape_result = runner.invoke(
        app,
        ["validate", str(missing_outputs), "--json"],
    )

    assert syntax_result.exit_code == 3
    assert version_result.exit_code == 4
    assert invalid_result.exit_code == 2
    assert missing_result.exit_code == 5
    assert shape_result.exit_code == 2
    assert _json(syntax_result)["ok"] is False
    assert _json(version_result)["ok"] is False
    assert _json(invalid_result)["ok"] is False
    assert _json(missing_result)["ok"] is False
    assert _json(shape_result)["diagnostics"][0]["code"] == "RF103"


def test_authoring_commands_round_trip_through_public_services(tmp_path: Path) -> None:
    initialized = tmp_path / "new.recipe.yaml"
    formatted = tmp_path / "formatted.recipe.yaml"
    migrated = tmp_path / "migrated.recipe.yaml"

    init_result = runner.invoke(app, ["init", str(initialized), "--json"])
    format_result = runner.invoke(
        app,
        [
            "format",
            str(EXAMPLE),
            "--output",
            str(formatted),
            "--json",
        ],
    )
    migrate_result = runner.invoke(
        app,
        [
            "migrate",
            str(EXAMPLE),
            "--output",
            str(migrated),
            "--json",
        ],
    )
    diff_result = runner.invoke(
        app,
        ["diff", str(formatted), str(migrated), "--json"],
    )

    assert init_result.exit_code == 0
    assert format_result.exit_code == 0
    assert migrate_result.exit_code == 0
    assert diff_result.exit_code == 0
    assert initialized.is_file()
    assert formatted.is_file()
    assert migrated.is_file()
    assert _json(diff_result)["command"] == "diff"


def test_compile_inspect_render_check_schema_and_examples(tmp_path: Path) -> None:
    graph = tmp_path / "recipe.graph.json"
    svg = tmp_path / "recipe.svg"
    schema = tmp_path / "layout.schema.json"

    compile_result = runner.invoke(
        app,
        ["compile", str(EXAMPLE), "--output", str(graph), "--json"],
    )
    inspect_result = runner.invoke(app, ["inspect", str(EXAMPLE), "--json"])
    render_result = runner.invoke(
        app,
        [
            "render",
            str(EXAMPLE),
            "--format",
            "tabular-svg",
            "--output",
            str(svg),
            "--json",
        ],
    )
    check_result = runner.invoke(
        app,
        ["render-check", str(EXAMPLE), "--json"],
    )
    schema_result = runner.invoke(
        app,
        [
            "schema",
            "--contract",
            "tabular-layout",
            "--output",
            str(schema),
        ],
    )
    examples_result = runner.invoke(app, ["examples", "--json"])

    assert compile_result.exit_code == 0
    assert inspect_result.exit_code == 0
    assert render_result.exit_code == 0
    assert check_result.exit_code == 0
    assert schema_result.exit_code == 0
    assert examples_result.exit_code == 0
    assert graph.is_file()
    assert svg.read_text(encoding="utf-8").startswith("<svg")
    assert schema.is_file()
    assert _json(check_result)["data"] == {"valid": True}


def test_png_requires_an_output_path() -> None:
    result = runner.invoke(
        app,
        [
            "render",
            str(EXAMPLE),
            "--format",
            "tabular-png",
            "--json",
        ],
    )

    assert result.exit_code == 2
    envelope = _json(result)
    diagnostics = envelope["diagnostics"]
    assert isinstance(diagnostics, list)
    assert diagnostics[0]["code"] == "RF511"


@pytest.mark.parametrize("command", ["render", "render-check"])
def test_invalid_render_options_are_structured_authoring_diagnostics(
    command: str,
) -> None:
    result = runner.invoke(
        app,
        [command, str(EXAMPLE), "--width", "-1", "--json"],
    )

    assert result.exit_code == 2
    envelope = _json(result)
    diagnostics = envelope["diagnostics"]
    assert isinstance(diagnostics, list)
    assert diagnostics[-1]["code"] == "RF512"
    assert diagnostics[-1]["path"] == "/render/options"


@pytest.mark.parametrize("command", ["render", "render-check"])
def test_unknown_render_notation_is_a_structured_authoring_diagnostic(
    command: str,
) -> None:
    result = runner.invoke(
        app,
        [
            command,
            str(EXAMPLE),
            *(["--format", "tabular-layout"] if command == "render" else []),
            "--notation",
            "unknown",
            "--json",
        ],
    )

    assert result.exit_code == 2
    diagnostics = _json(result)["diagnostics"]
    assert diagnostics[-1]["code"] == "RF512"
    assert diagnostics[-1]["path"] == "/render/notation"


def test_render_exposes_the_complete_typed_option_surface(tmp_path: Path) -> None:
    layout_path = tmp_path / "configured.layout.json"
    result = runner.invoke(
        app,
        [
            "render",
            str(EXAMPLE),
            "--format",
            "tabular-layout",
            "--output",
            str(layout_path),
            "--theme",
            "modern",
            "--minimum-font-size",
            "11",
            "--base-font-size",
            "15",
            "--line-height",
            "1.4",
            "--outer-margin",
            "28",
            "--ingredient-label-width",
            "260",
            "--operation-column-minimum-width",
            "90",
            "--operation-column-maximum-width",
            "190",
            "--setup-card-minimum-width",
            "190",
            "--orientation",
            "landscape",
            "--operation-label-orientation",
            "horizontal",
            "--hide-intermediate-labels",
            "--show-source-quantities",
            "--show-normalized-quantities",
            "--show-provenance",
            "--wrap-mode",
            "grapheme",
            "--allow-ellipsis",
            "--background",
            "#ffffff",
            "--page-size",
            "letter",
            "--print-mode",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    assert layout_path.is_file()
    envelope = _json(result)
    assert envelope["ok"] is True


def test_unexpected_internal_failure_uses_exit_70_and_json_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(_graph: object) -> NoReturn:
        raise RuntimeError("simulated adapter defect")

    monkeypatch.setattr("recipeflow.cli.main.analyze", fail)
    result = runner.invoke(app, ["inspect", str(EXAMPLE), "--json"])

    assert result.exit_code == 70
    envelope = _json(result)
    assert envelope["ok"] is False
    diagnostics = envelope["diagnostics"]
    assert isinstance(diagnostics, list)
    assert diagnostics[0]["code"] == "RF900"
