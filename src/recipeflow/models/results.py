from pydantic import BaseModel, ConfigDict
from recipeflow.models.analysis import GraphAnalysis
from recipeflow.models.common import Diagnostic, Severity
from recipeflow.models.document import RecipeDocument
from recipeflow.models.graph import RecipeGraph

class ResultModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

class ParseResult(ResultModel):
    document: RecipeDocument | None = None
    diagnostics: tuple[Diagnostic, ...] = ()
    @property
    def ok(self) -> bool:
        return self.document is not None and not any(d.severity == Severity.ERROR for d in self.diagnostics)

class ValidationResult(ResultModel):
    diagnostics: tuple[Diagnostic, ...] = ()
    @property
    def ok(self) -> bool:
        return not any(d.severity == Severity.ERROR for d in self.diagnostics)

class RenderArtifact(ResultModel):
    format: str
    media_type: str
    content: str

class BuildResult(ResultModel):
    document: RecipeDocument | None = None
    graph: RecipeGraph | None = None
    analysis: GraphAnalysis | None = None
    diagnostics: tuple[Diagnostic, ...] = ()
    @property
    def ok(self) -> bool:
        return self.graph is not None and not any(d.severity == Severity.ERROR for d in self.diagnostics)
