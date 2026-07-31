from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from recipeflow.analysis import analyze
from recipeflow.compatibility import format_document, migrate, semantic_diff
from recipeflow.compilation import compile_document, compile_recipe
from recipeflow.layout import (
    LayoutStrategy,
    create_tabular_layout,
    get_layout_strategy,
    list_layout_strategies,
    register_layout_strategy,
    validate_tabular_layout,
)
from recipeflow.models import (
    BuildResult,
    RecipeDocument,
    ValidationResult,
)
from recipeflow.parsing import (
    SourceFormat,
    parse,
    parse_document,
    parse_json,
    parse_yaml,
)
from recipeflow.planning import (
    plan_recipes,
    project_mise_en_place,
    project_shopping_list,
)
from recipeflow.renderers import RenderOptions
from recipeflow.rendering import render, render_check
from recipeflow.schema import export_schema
from recipeflow.validation import ValidationOptions, validate

DocumentSource = str | Mapping[str, Any] | RecipeDocument

__all__ = [
    "DocumentSource",
    "LayoutStrategy",
    "RenderOptions",
    "ValidationOptions",
    "analyze",
    "build",
    "compile_document",
    "compile_recipe",
    "create_tabular_layout",
    "export_schema",
    "format_document",
    "get_layout_strategy",
    "incremental_validate",
    "list_layout_strategies",
    "migrate",
    "parse",
    "parse_document",
    "parse_json",
    "parse_yaml",
    "plan_recipes",
    "project_mise_en_place",
    "project_shopping_list",
    "register_layout_strategy",
    "render",
    "render_check",
    "semantic_diff",
    "validate",
    "validate_source",
    "validate_tabular_layout",
]


def validate_source(
    source: DocumentSource,
    source_format: SourceFormat = "yaml",
    *,
    strict: bool = False,
) -> ValidationResult:
    """Parse and validate text or an in-memory document in one service call."""

    parsed = parse_document(source, source_format)
    if parsed.document is None:
        return ValidationResult(diagnostics=parsed.diagnostics)
    validated = validate(parsed.document, strict=strict)
    return ValidationResult(
        diagnostics=(*parsed.diagnostics, *validated.diagnostics),
    )


def incremental_validate(
    source: DocumentSource,
    source_format: SourceFormat = "yaml",
    *,
    strict: bool = False,
) -> ValidationResult:
    """Editor-friendly alias for stateless incremental validation."""

    return validate_source(source, source_format, strict=strict)


def build(
    source: DocumentSource,
    source_format: SourceFormat = "yaml",
    *,
    strict: bool = False,
) -> BuildResult:
    """Run parse, validation, deterministic compilation, and analysis."""

    parsed = parse_document(source, source_format)
    if parsed.document is None:
        return BuildResult(diagnostics=parsed.diagnostics)
    compiled = compile_document(parsed.document, strict=strict)
    diagnostics = (*parsed.diagnostics, *compiled.diagnostics)
    if compiled.graph is None:
        return BuildResult(
            document=parsed.document,
            diagnostics=diagnostics,
        )
    return BuildResult(
        document=parsed.document,
        graph=compiled.graph,
        analysis=analyze(compiled.graph),
        diagnostics=diagnostics,
    )
