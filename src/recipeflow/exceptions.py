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


class LayoutStrategyError(RecipeFlowError):
    """Base error for layout-strategy selection and execution."""


class UnknownLayoutStrategyError(LayoutStrategyError):
    def __init__(self, name: str, available: tuple[str, ...]) -> None:
        self.name = name
        self.available = available
        choices = ", ".join(available) or "none"
        super().__init__(f"Unknown layout notation '{name}'. Available: {choices}")


class LayoutStrategyRegistrationError(LayoutStrategyError):
    pass
