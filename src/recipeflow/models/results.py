from __future__ import annotations

from typing import Any, Literal

from recipeflow.models.analysis import GraphAnalysis
from recipeflow.models.common import Diagnostic, PublicModel, Severity
from recipeflow.models.document import RecipeDocument
from recipeflow.models.graph import RecipeGraph


class ResultModel(PublicModel):
    @staticmethod
    def diagnostics_ok(diagnostics: tuple[Diagnostic, ...]) -> bool:
        return not any(item.severity == Severity.ERROR for item in diagnostics)


class ParseResult(ResultModel):
    schema_version: Literal["recipeflow.parse-result/v1"] = "recipeflow.parse-result/v1"
    document: RecipeDocument | None = None
    diagnostics: tuple[Diagnostic, ...] = ()
    source_version: str | None = None

    @property
    def ok(self) -> bool:
        return self.document is not None and self.diagnostics_ok(self.diagnostics)


class ValidationResult(ResultModel):
    schema_version: Literal["recipeflow.validation-result/v1"] = (
        "recipeflow.validation-result/v1"
    )
    diagnostics: tuple[Diagnostic, ...] = ()

    @property
    def ok(self) -> bool:
        return self.diagnostics_ok(self.diagnostics)


class CompileResult(ResultModel):
    schema_version: Literal["recipeflow.compile-result/v1"] = "recipeflow.compile-result/v1"
    document: RecipeDocument | None = None
    graph: RecipeGraph | None = None
    diagnostics: tuple[Diagnostic, ...] = ()

    @property
    def ok(self) -> bool:
        return self.graph is not None and self.diagnostics_ok(self.diagnostics)


class RenderArtifact(ResultModel):
    schema_version: Literal["recipeflow.render-result/v1"] = "recipeflow.render-result/v1"
    format: str
    media_type: str
    content: str | bytes
    width: int | None = None
    height: int | None = None


class BuildResult(ResultModel):
    schema_version: Literal["recipeflow.build-result/v1"] = "recipeflow.build-result/v1"
    document: RecipeDocument | None = None
    graph: RecipeGraph | None = None
    analysis: GraphAnalysis | None = None
    diagnostics: tuple[Diagnostic, ...] = ()

    @property
    def ok(self) -> bool:
        return self.graph is not None and self.diagnostics_ok(self.diagnostics)


class FormatResult(ResultModel):
    schema_version: Literal["recipeflow.format-result/v1"] = "recipeflow.format-result/v1"
    document: RecipeDocument | None = None
    content: str | None = None
    format: Literal["yaml", "json"] = "yaml"
    diagnostics: tuple[Diagnostic, ...] = ()

    @property
    def ok(self) -> bool:
        return self.content is not None and self.diagnostics_ok(self.diagnostics)


class MigrationStep(ResultModel):
    source_version: str
    target_version: str
    description: str


class MigrationResult(ResultModel):
    schema_version: Literal["recipeflow.migration-result/v1"] = (
        "recipeflow.migration-result/v1"
    )
    document: RecipeDocument | None = None
    content: str | None = None
    changed: bool = False
    dry_run: bool = False
    steps: tuple[MigrationStep, ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()

    @property
    def ok(self) -> bool:
        return self.document is not None and self.diagnostics_ok(self.diagnostics)


class DiffChange(ResultModel):
    kind: str
    path: str
    before: Any | None = None
    after: Any | None = None
    related_paths: tuple[str, ...] = ()


class DiffResult(ResultModel):
    schema_version: Literal["recipeflow.diff-result/v1"] = "recipeflow.diff-result/v1"
    changes: tuple[DiffChange, ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()

    @property
    def ok(self) -> bool:
        return self.diagnostics_ok(self.diagnostics)


class CliResult(ResultModel):
    schema_version: Literal["recipeflow.cli-result/v1"] = "recipeflow.cli-result/v1"
    command: str
    ok: bool
    data: Any | None = None
    diagnostics: tuple[Diagnostic, ...] = ()
