from __future__ import annotations

from recipeflow.models.common import Diagnostic


class RecipeFlowError(Exception):
    """Base exception for unexpected or explicitly requested failing operations."""


class RecipeCompilationError(RecipeFlowError):
    def __init__(self, diagnostics: tuple[Diagnostic, ...]) -> None:
        self.diagnostics = diagnostics
        super().__init__("Recipe compilation failed validation")


class GraphInvariantError(RecipeFlowError):
    pass


class UnsupportedSchemaVersionError(RecipeFlowError):
    def __init__(self, version: str) -> None:
        self.version = version
        super().__init__(f"Unsupported schema version: {version}")
