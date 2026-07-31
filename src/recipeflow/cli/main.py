from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Annotated, Any, Literal

import typer
from typer._click.exceptions import Abort, ClickException, Exit
from typer._click.globals import get_current_context
from typer.core import TyperGroup

from recipeflow import (
    CliResult,
    Diagnostic,
    RenderOptions,
    Severity,
    analyze,
    compile_document,
    format_document,
    migrate,
    parse_document,
    render,
    render_check,
    semantic_diff,
)
from recipeflow.models import RecipeDocument
from recipeflow.renderers import PngDependencyError
from recipeflow.schema import schema_json

SUCCESS = 0
VALIDATION_FAILURE = 2
PARSE_FAILURE = 3
UNSUPPORTED_VERSION = 4
IO_FAILURE = 5
INTERNAL_FAILURE = 70


class RecipeFlowGroup(TyperGroup):
    """Map unexpected adapter failures to the documented stable exit code."""

    def invoke(self, ctx: Any) -> Any:
        raw_args = (
            *getattr(ctx, "_protected_args", ()),
            *getattr(ctx, "args", ()),
        )
        requested_json = "--json" in raw_args
        requested_quiet = "--quiet" in raw_args
        try:
            return super().invoke(ctx)
        except (Exit, Abort, ClickException):
            raise
        except Exception as exc:
            current = get_current_context(silent=True)
            params = current.params if current is not None else {}
            command = (
                current.info_name
                if current is not None and current.info_name
                else ctx.invoked_subcommand or "recipeflow"
            )
            _emit(
                command,
                ok=False,
                diagnostics=(
                    _diagnostic(
                        "RF900",
                        f"Unexpected internal failure: {type(exc).__name__}: {exc}",
                        path=f"/{command}",
                        context={"category": "internal"},
                    ),
                ),
                json_output=bool(params.get("json_output", requested_json)),
                quiet=bool(params.get("quiet", requested_quiet)),
            )
            raise typer.Exit(INTERNAL_FAILURE) from exc


app = typer.Typer(
    cls=RecipeFlowGroup,
    help="Validate, compile, inspect, and render RecipeFlow documents.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)

_INITIAL_DOCUMENT = """\
schema_version: recipeflow.document/v1
recipe:
  id: replace-me
  title: Replace me
ingredients: {}
setup: []
operations: []
"""


def _diagnostic(
    code: str,
    message: str,
    *,
    path: str = "",
    suggestions: tuple[str, ...] = (),
    context: dict[str, Any] | None = None,
) -> Diagnostic:
    return Diagnostic(
        code=code,
        severity=Severity.ERROR,
        path=path,
        message=message,
        suggestions=suggestions,
        context=context or {},
    )


def _exit_code(diagnostics: tuple[Diagnostic, ...]) -> int:
    errors = tuple(item for item in diagnostics if item.severity == Severity.ERROR)
    if not errors:
        return SUCCESS
    if any(item.context.get("category") == "io" for item in errors):
        return IO_FAILURE
    if any(item.code.startswith("RF6") for item in errors):
        return UNSUPPORTED_VERSION
    if any(item.context.get("category") == "parse" for item in errors):
        return PARSE_FAILURE
    return VALIDATION_FAILURE


def _emit(
    command: str,
    *,
    ok: bool,
    data: Any = None,
    diagnostics: tuple[Diagnostic, ...] = (),
    json_output: bool = False,
    quiet: bool = False,
) -> None:
    if json_output:
        envelope = CliResult(
            command=command,
            ok=ok,
            data=data,
            diagnostics=diagnostics,
        )
        typer.echo(envelope.model_dump_json(indent=2, by_alias=True))
        return
    for diagnostic in diagnostics:
        typer.echo(
            (
                f"{diagnostic.severity.value.upper()} {diagnostic.code} "
                f"{diagnostic.path}: {diagnostic.message}"
            ),
            err=True,
        )
        for suggestion in diagnostic.suggestions:
            typer.echo(f"  suggestion: {suggestion}", err=True)
    if data is not None and not quiet:
        if isinstance(data, str):
            typer.echo(data, nl=not data.endswith("\n"))
        else:
            typer.echo(json.dumps(data, ensure_ascii=False, indent=2))


def _read(path: Path) -> tuple[str | None, tuple[Diagnostic, ...]]:
    try:
        return path.read_text(encoding="utf-8"), ()
    except OSError as exc:
        return None, (
            _diagnostic(
                "RF190",
                f"Unable to read '{path}': {exc}",
                path=str(path),
                context={"category": "io"},
            ),
        )


def _write(
    path: Path,
    content: str | bytes,
) -> tuple[Diagnostic, ...]:
    try:
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
    except OSError as exc:
        return (
            _diagnostic(
                "RF190",
                f"Unable to write '{path}': {exc}",
                path=str(path),
                context={"category": "io"},
            ),
        )
    return ()


def _source_format(path: Path) -> Literal["yaml", "json"]:
    return "json" if path.suffix.lower() == ".json" else "yaml"


def _load_document(path: Path) -> tuple[RecipeDocument | None, tuple[Diagnostic, ...]]:
    source, diagnostics = _read(path)
    if source is None:
        return None, diagnostics
    parsed = parse_document(source, _source_format(path))
    return parsed.document, parsed.diagnostics


def _finish(
    command: str,
    *,
    data: Any = None,
    diagnostics: tuple[Diagnostic, ...] = (),
    json_output: bool = False,
    quiet: bool = False,
    success_message: str | None = None,
) -> None:
    code = _exit_code(diagnostics)
    payload = data if data is not None else success_message
    _emit(
        command,
        ok=code == SUCCESS,
        data=payload,
        diagnostics=diagnostics,
        json_output=json_output,
        quiet=quiet,
    )
    if code:
        raise typer.Exit(code)


@app.command(name="init")
def init_command(
    path: Annotated[Path, typer.Argument()] = Path("recipe.flow.yaml"),
    force: Annotated[bool, typer.Option("--force")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    quiet: Annotated[bool, typer.Option("--quiet")] = False,
) -> None:
    if path.exists() and not force:
        _finish(
            "init",
            diagnostics=(
                _diagnostic(
                    "RF191",
                    f"Refusing to overwrite existing file '{path}'.",
                    path=str(path),
                    suggestions=("Pass --force to overwrite it.",),
                    context={"category": "io"},
                ),
            ),
            json_output=json_output,
            quiet=quiet,
        )
    diagnostics = _write(path, _INITIAL_DOCUMENT)
    _finish(
        "init",
        data={"path": str(path)},
        diagnostics=diagnostics,
        json_output=json_output,
        quiet=quiet,
        success_message=f"Created {path}",
    )


@app.command()
def validate(
    path: Path,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    strict: Annotated[bool, typer.Option("--strict")] = False,
    quiet: Annotated[bool, typer.Option("--quiet")] = False,
    no_color: Annotated[bool, typer.Option("--no-color")] = False,
) -> None:
    del no_color
    document, diagnostics = _load_document(path)
    if document is not None:
        from recipeflow import validate as validate_document

        result = validate_document(document, strict=strict)
        diagnostics = (*diagnostics, *result.diagnostics)
    _finish(
        "validate",
        data={"valid": _exit_code(diagnostics) == SUCCESS},
        diagnostics=diagnostics,
        json_output=json_output,
        quiet=quiet,
        success_message="Valid RecipeFlow document.",
    )


@app.command(name="compile")
def compile_command(
    path: Path,
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    strict: Annotated[bool, typer.Option("--strict")] = False,
    quiet: Annotated[bool, typer.Option("--quiet")] = False,
) -> None:
    document, diagnostics = _load_document(path)
    graph = None
    if document is not None:
        compiled = compile_document(document, strict=strict)
        graph = compiled.graph
        diagnostics = (*diagnostics, *compiled.diagnostics)
    if graph is None:
        _finish(
            "compile",
            diagnostics=diagnostics,
            json_output=json_output,
            quiet=quiet,
        )
        return
    content = graph.model_dump_json(indent=2, by_alias=True) + "\n"
    if output:
        diagnostics = (*diagnostics, *_write(output, content))
        data: Any = {"path": str(output), "graph": graph.model_dump(mode="json")}
    else:
        data = graph.model_dump(mode="json") if json_output else content
    _finish(
        "compile",
        data=data,
        diagnostics=diagnostics,
        json_output=json_output,
        quiet=quiet,
    )


@app.command()
def inspect(
    path: Path,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    strict: Annotated[bool, typer.Option("--strict")] = False,
    quiet: Annotated[bool, typer.Option("--quiet")] = False,
) -> None:
    document, diagnostics = _load_document(path)
    graph = None
    if document is not None:
        compiled = compile_document(document, strict=strict)
        graph = compiled.graph
        diagnostics = (*diagnostics, *compiled.diagnostics)
    if graph is None:
        _finish(
            "inspect",
            diagnostics=diagnostics,
            json_output=json_output,
            quiet=quiet,
        )
        return
    report = analyze(graph)
    if json_output:
        data: Any = report.model_dump(mode="json", by_alias=True)
    else:
        data = "\n".join(
            (
                graph.title,
                f"Ingredients: {report.ingredient_count}",
                f"Materials: {report.material_count}",
                f"Setup actions: {report.setup_count}",
                f"Transformations: {report.operation_count}",
                f"Final outputs: {', '.join(report.final_ids) or 'none'}",
                (
                    "Operation order: "
                    + (" → ".join(report.topological_operation_ids) or "none")
                ),
            )
        )
    _finish(
        "inspect",
        data=data,
        diagnostics=diagnostics,
        json_output=json_output,
        quiet=quiet,
    )


@app.command(name="render")
def render_command(
    path: Path,
    format: Annotated[
        Literal[
            "text",
            "mermaid",
            "json",
            "canonical-json",
            "tabular-layout",
            "tabular-svg",
            "tabular-html",
            "tabular-png",
        ],
        typer.Option("--format", "-f"),
    ] = "text",
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    strict: Annotated[bool, typer.Option("--strict")] = False,
    quiet: Annotated[bool, typer.Option("--quiet")] = False,
    theme: Annotated[Literal["classic", "modern"], typer.Option("--theme")] = "classic",
    operation_label_orientation: Annotated[
        Literal["auto", "horizontal", "vertical"],
        typer.Option("--operation-label-orientation"),
    ] = "auto",
    width: Annotated[float | None, typer.Option("--width")] = None,
    scale: Annotated[float, typer.Option("--scale")] = 2.0,
    dpi: Annotated[int, typer.Option("--dpi")] = 144,
    background: Annotated[str | None, typer.Option("--background")] = None,
    minimum_font_size: Annotated[
        float, typer.Option("--minimum-font-size")
    ] = 10,
    base_font_size: Annotated[float, typer.Option("--base-font-size")] = 14,
    line_height: Annotated[float, typer.Option("--line-height")] = 1.3,
    outer_margin: Annotated[float | None, typer.Option("--outer-margin")] = None,
    ingredient_label_width: Annotated[
        float | None, typer.Option("--ingredient-label-width")
    ] = None,
    operation_column_minimum_width: Annotated[
        float, typer.Option("--operation-column-minimum-width")
    ] = 82,
    operation_column_maximum_width: Annotated[
        float, typer.Option("--operation-column-maximum-width")
    ] = 176,
    setup_card_minimum_width: Annotated[
        float, typer.Option("--setup-card-minimum-width")
    ] = 176,
    orientation: Annotated[
        Literal["auto", "landscape", "portrait"],
        typer.Option("--orientation"),
    ] = "auto",
    show_intermediate_labels: Annotated[
        bool,
        typer.Option(
            "--show-intermediate-labels/--hide-intermediate-labels"
        ),
    ] = True,
    show_source_quantities: Annotated[
        bool,
        typer.Option("--show-source-quantities/--hide-source-quantities"),
    ] = True,
    show_normalized_quantities: Annotated[
        bool,
        typer.Option(
            "--show-normalized-quantities/--hide-normalized-quantities"
        ),
    ] = False,
    show_provenance: Annotated[
        bool,
        typer.Option("--show-provenance/--hide-provenance"),
    ] = False,
    wrap_mode: Annotated[
        Literal["word", "grapheme"],
        typer.Option("--wrap-mode"),
    ] = "word",
    allow_ellipsis: Annotated[
        bool,
        typer.Option("--allow-ellipsis/--preserve-complete-text"),
    ] = False,
    page_size: Annotated[
        Literal["auto", "A4", "letter"],
        typer.Option("--page-size"),
    ] = "auto",
    print_mode: Annotated[
        bool,
        typer.Option("--print-mode/--screen-mode"),
    ] = False,
) -> None:
    document, diagnostics = _load_document(path)
    graph = None
    if document is not None:
        compiled = compile_document(document, strict=strict)
        graph = compiled.graph
        diagnostics = (*diagnostics, *compiled.diagnostics)
    if graph is None:
        _finish(
            "render",
            diagnostics=diagnostics,
            json_output=json_output,
            quiet=quiet,
        )
        return
    if format == "tabular-png" and output is None:
        _finish(
            "render",
            diagnostics=(
                *diagnostics,
                _diagnostic(
                    "RF511",
                    "PNG rendering requires --output to keep binary data off stdout.",
                    path="/render/output",
                ),
            ),
            json_output=json_output,
            quiet=quiet,
        )
        return
    try:
        options = RenderOptions(
            theme=theme,
            operation_label_orientation=operation_label_orientation,
            width=width,
            scale=scale,
            dpi=dpi,
            background=background,
            minimum_font_size=minimum_font_size,
            base_font_size=base_font_size,
            line_height=line_height,
            outer_margin=outer_margin,
            ingredient_label_width=ingredient_label_width,
            operation_column_minimum_width=operation_column_minimum_width,
            operation_column_maximum_width=operation_column_maximum_width,
            setup_card_minimum_width=setup_card_minimum_width,
            orientation=orientation,
            show_intermediate_labels=show_intermediate_labels,
            show_source_quantities=show_source_quantities,
            show_normalized_quantities=show_normalized_quantities,
            show_provenance=show_provenance,
            wrap_mode=wrap_mode,
            allow_ellipsis=allow_ellipsis,
            page_size=page_size,
            print_mode=print_mode,
        )
    except ValueError as exc:
        _finish(
            "render",
            diagnostics=(
                *diagnostics,
                _diagnostic(
                    "RF512",
                    f"Invalid render options: {exc}",
                    path="/render/options",
                ),
            ),
            json_output=json_output,
            quiet=quiet,
        )
        return
    try:
        artifact = render(graph, format, options)
    except PngDependencyError as exc:
        _finish(
            "render",
            diagnostics=(*diagnostics, exc.diagnostic),
            json_output=json_output,
            quiet=quiet,
        )
        return
    except (RuntimeError, ValueError) as exc:
        _finish(
            "render",
            diagnostics=(
                *diagnostics,
                _diagnostic("RF599", f"Rendering failed: {exc}", path="/render"),
            ),
            json_output=json_output,
            quiet=quiet,
        )
        return
    if output:
        diagnostics = (*diagnostics, *_write(output, artifact.content))
        data: Any = {
            "path": str(output),
            "format": artifact.format,
            "media_type": artifact.media_type,
            "width": artifact.width,
            "height": artifact.height,
        }
    else:
        data = (
            {
                "format": artifact.format,
                "media_type": artifact.media_type,
                "content": artifact.content,
                "width": artifact.width,
                "height": artifact.height,
            }
            if json_output
            else artifact.content
        )
    _finish(
        "render",
        data=data,
        diagnostics=diagnostics,
        json_output=json_output,
        quiet=quiet,
    )


@app.command(name="render-check")
def render_check_command(
    path: Path,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    strict: Annotated[bool, typer.Option("--strict")] = False,
    quiet: Annotated[bool, typer.Option("--quiet")] = False,
    theme: Annotated[Literal["classic", "modern"], typer.Option("--theme")] = "classic",
    operation_label_orientation: Annotated[
        Literal["auto", "horizontal", "vertical"],
        typer.Option("--operation-label-orientation"),
    ] = "auto",
    width: Annotated[float | None, typer.Option("--width")] = None,
) -> None:
    document, diagnostics = _load_document(path)
    graph = None
    if document is not None:
        compiled = compile_document(document, strict=strict)
        graph = compiled.graph
        diagnostics = (*diagnostics, *compiled.diagnostics)
    if graph is not None:
        try:
            options = RenderOptions(
                theme=theme,
                operation_label_orientation=operation_label_orientation,
                width=width,
            )
        except ValueError as exc:
            diagnostics = (
                *diagnostics,
                _diagnostic(
                    "RF512",
                    f"Invalid render options: {exc}",
                    path="/render/options",
                ),
            )
        else:
            checked = render_check(graph, options)
            diagnostics = (*diagnostics, *checked.diagnostics)
    _finish(
        "render-check",
        data={"valid": _exit_code(diagnostics) == SUCCESS},
        diagnostics=diagnostics,
        json_output=json_output,
        quiet=quiet,
        success_message="Layout passed all RF5xx checks.",
    )


@app.command(name="format")
def format_command(
    path: Path,
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
    output_format: Annotated[
        Literal["yaml", "json"], typer.Option("--format", "-f")
    ] = "yaml",
    in_place: Annotated[bool, typer.Option("--in-place")] = False,
    check: Annotated[bool, typer.Option("--check")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    quiet: Annotated[bool, typer.Option("--quiet")] = False,
) -> None:
    source, diagnostics = _read(path)
    result = None
    if source is not None:
        result = format_document(
            source,
            source_format=_source_format(path),
            output_format=output_format,
        )
        diagnostics = (*diagnostics, *result.diagnostics)
    if result is None or result.content is None:
        _finish(
            "format",
            diagnostics=diagnostics,
            json_output=json_output,
            quiet=quiet,
        )
        return
    changed = source != result.content
    target = path if in_place else output
    if target is not None and not check:
        diagnostics = (*diagnostics, *_write(target, result.content))
    data: Any
    if json_output:
        data = {
            "changed": changed,
            "path": str(target) if target else None,
            "content": None if target else result.content,
        }
    else:
        data = None if target or check else result.content
    if check and changed:
        diagnostics = (
            *diagnostics,
            _diagnostic(
                "RF620",
                f"'{path}' is not deterministically formatted.",
                path=str(path),
            ),
        )
    _finish(
        "format",
        data=data,
        diagnostics=diagnostics,
        json_output=json_output,
        quiet=quiet,
    )


@app.command(name="migrate")
def migrate_command(
    path: Path,
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
    target_version: Annotated[
        str, typer.Option("--target-version")
    ] = "recipeflow.document/v1",
    output_format: Annotated[
        Literal["yaml", "json"], typer.Option("--format", "-f")
    ] = "yaml",
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    quiet: Annotated[bool, typer.Option("--quiet")] = False,
) -> None:
    source, diagnostics = _read(path)
    result = None
    if source is not None:
        result = migrate(
            source,
            target_version=target_version,
            source_format=_source_format(path),
            output_format=output_format,
            dry_run=dry_run,
        )
        diagnostics = (*diagnostics, *result.diagnostics)
    if result is None or result.content is None:
        _finish(
            "migrate",
            diagnostics=diagnostics,
            json_output=json_output,
            quiet=quiet,
        )
        return
    if output and not dry_run:
        diagnostics = (*diagnostics, *_write(output, result.content))
    data: Any = {
        "changed": result.changed,
        "dry_run": result.dry_run,
        "steps": [step.model_dump(mode="json") for step in result.steps],
        "path": str(output) if output and not dry_run else None,
        "content": None if output and not dry_run else result.content,
    }
    _finish(
        "migrate",
        data=data if json_output else result.content,
        diagnostics=diagnostics,
        json_output=json_output,
        quiet=quiet,
    )


@app.command(name="diff")
def diff_command(
    before: Path,
    after: Path,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    quiet: Annotated[bool, typer.Option("--quiet")] = False,
) -> None:
    before_source, before_diagnostics = _read(before)
    after_source, after_diagnostics = _read(after)
    diagnostics = (*before_diagnostics, *after_diagnostics)
    if before_source is None or after_source is None:
        _finish(
            "diff",
            diagnostics=diagnostics,
            json_output=json_output,
            quiet=quiet,
        )
        return
    result = semantic_diff(
        before_source,
        after_source,
        source_format=(
            "json"
            if _source_format(before) == _source_format(after) == "json"
            else "yaml"
        ),
    )
    diagnostics = (*diagnostics, *result.diagnostics)
    data = [change.model_dump(mode="json") for change in result.changes]
    _finish(
        "diff",
        data=data,
        diagnostics=diagnostics,
        json_output=json_output,
        quiet=quiet,
    )


@app.command()
def schema(
    contract: Annotated[
        Literal[
            "document",
            "graph",
            "diagnostic",
            "analysis",
            "tabular-layout",
            "render-result",
            "cli-result",
        ],
        typer.Option("--contract"),
    ] = "document",
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
) -> None:
    content = schema_json(contract)
    diagnostics = _write(output, content) if output else ()
    if diagnostics:
        _finish("schema", diagnostics=diagnostics)
    elif output is None:
        typer.echo(content, nl=False)


def _example_directory() -> Path:
    source_tree = Path(__file__).resolve().parents[3] / "examples"
    if source_tree.is_dir():
        return source_tree
    packaged = resources.files("recipeflow").joinpath("examples")
    return Path(str(packaged))


@app.command()
def examples(
    name: Annotated[str | None, typer.Argument()] = None,
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    quiet: Annotated[bool, typer.Option("--quiet")] = False,
) -> None:
    directory = _example_directory()
    choices = tuple(sorted(path.name for path in directory.glob("*.recipe.yaml")))
    if name is None:
        _finish(
            "examples",
            data=list(choices),
            json_output=json_output,
            quiet=quiet,
        )
        return
    source = directory / name
    if source.suffixes[-2:] != [".recipe", ".yaml"]:
        source = directory / f"{name}.recipe.yaml"
    if not source.is_file():
        _finish(
            "examples",
            diagnostics=(
                _diagnostic(
                    "RF192",
                    f"Unknown bundled example '{name}'.",
                    suggestions=choices,
                    context={"category": "io"},
                ),
            ),
            json_output=json_output,
            quiet=quiet,
        )
        return
    content, diagnostics = _read(source)
    if content is not None and output:
        diagnostics = (*diagnostics, *_write(output, content))
    _finish(
        "examples",
        data=(
            {"path": str(output), "name": source.name}
            if output
            else content
        ),
        diagnostics=diagnostics,
        json_output=json_output,
        quiet=quiet,
    )


if __name__ == "__main__":
    app()
