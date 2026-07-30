from typing import Literal
from recipeflow.analysis import analyze
from recipeflow.compilation import compile_recipe
from recipeflow.models import BuildResult, RecipeDocument, RecipeGraph, RenderArtifact, ValidationResult
from recipeflow.parsing import parse
from recipeflow.rendering import render
from recipeflow.validation import validate
from recipeflow.layout import create_tabular_layout

__all__=["analyze","build","compile_recipe","create_tabular_layout","parse","render","validate"]

def build(source: str, source_format: Literal["yaml","json"]="yaml") -> BuildResult:
    parsed=parse(source,source_format)
    if not parsed.ok or parsed.document is None:
        return BuildResult(diagnostics=parsed.diagnostics)
    validation=validate(parsed.document)
    if not validation.ok:
        return BuildResult(document=parsed.document,diagnostics=validation.diagnostics)
    graph=compile_recipe(parsed.document)
    return BuildResult(document=parsed.document,graph=graph,analysis=analyze(graph),diagnostics=validation.diagnostics)
