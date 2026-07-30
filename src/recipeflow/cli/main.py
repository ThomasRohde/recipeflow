import json
from pathlib import Path
from typing import Annotated, Literal

import typer
from rich.console import Console
from rich.table import Table

from recipeflow import analyze, compile_recipe, parse
from recipeflow import render as render_graph
from recipeflow import validate as validate_document
from recipeflow.models import Diagnostic, RecipeDocument
from recipeflow.schema import schema_json

app = typer.Typer(
    help="Compile and inspect recipes as transformation graphs.",
    no_args_is_help=True,
)
console = Console()


def read_document(path: Path) -> RecipeDocument:
    source_format: Literal["yaml", "json"] = (
        "json" if path.suffix.lower() == ".json" else "yaml"
    )
    result = parse(path.read_text(encoding="utf-8"), source_format)
    if not result.ok or result.document is None:
        emit_diagnostics(result.diagnostics, False)
        raise typer.Exit(1)
    return result.document


def emit_diagnostics(
    diagnostics: tuple[Diagnostic, ...],
    json_output: bool,
) -> None:
    if json_output:
        typer.echo(
            json.dumps(
                {
                    "valid": not any(
                        diagnostic.severity.value == "error"
                        for diagnostic in diagnostics
                    ),
                    "diagnostics": [
                        diagnostic.model_dump(mode="json")
                        for diagnostic in diagnostics
                    ],
                },
                indent=2,
            )
        )
        return

    if not diagnostics:
        console.print("[green]Valid RecipeFlow document.[/green]")
        return

    for diagnostic in diagnostics:
        console.print(
            f"[{diagnostic.severity.value.upper()}] "
            f"{diagnostic.code} {diagnostic.path}: {diagnostic.message}"
        )


@app.command()
def validate(
    path: Path,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    document = read_document(path)
    result = validate_document(document)
    emit_diagnostics(result.diagnostics, json_output)
    if not result.ok:
        raise typer.Exit(1)


@app.command(name="compile")
def compile_command(
    path: Path,
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
) -> None:
    document = read_document(path)
    result = validate_document(document)
    if not result.ok:
        emit_diagnostics(result.diagnostics, False)
        raise typer.Exit(1)

    content = compile_recipe(document).model_dump_json(indent=2) + "\n"
    if output:
        output.write_text(content, encoding="utf-8")
    else:
        typer.echo(content, nl=False)


@app.command()
def inspect(
    path: Path,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    document = read_document(path)
    result = validate_document(document)
    if not result.ok:
        emit_diagnostics(result.diagnostics, json_output)
        raise typer.Exit(1)

    report = analyze(compile_recipe(document))
    if json_output:
        typer.echo(report.model_dump_json(indent=2))
        return

    table = Table(title=document.recipe.title)
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("Ingredients", str(report.ingredient_count))
    table.add_row("Setup actions", str(report.setup_count))
    table.add_row("Transformations", str(report.operation_count))
    table.add_row("Intermediates", ", ".join(report.intermediate_ids) or "none")
    table.add_row("Final outputs", ", ".join(report.final_ids) or "none")
    table.add_row(
        "Unused ingredients",
        ", ".join(report.unused_ingredient_ids) or "none",
    )
    table.add_row("Operation order", " → ".join(report.topological_operation_ids))
    console.print(table)


@app.command(name="render")
def render_command(
    path: Path,
    format: Annotated[
        Literal["text", "mermaid", "json", "tabular-svg", "tabular-html", "tabular-layout"],
        typer.Option("--format", "-f"),
    ] = "text",
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
) -> None:
    document = read_document(path)
    result = validate_document(document)
    if not result.ok:
        emit_diagnostics(result.diagnostics, False)
        raise typer.Exit(1)

    artifact = render_graph(compile_recipe(document), format)
    if output:
        output.write_text(artifact.content, encoding="utf-8")
    else:
        typer.echo(artifact.content, nl=False)


@app.command()
def schema(
    contract: Annotated[
        Literal["document", "graph", "diagnostic"],
        typer.Option("--contract"),
    ] = "document",
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
) -> None:
    content = schema_json(contract)
    if output:
        output.write_text(content, encoding="utf-8")
    else:
        typer.echo(content, nl=False)


if __name__ == "__main__":
    app()
