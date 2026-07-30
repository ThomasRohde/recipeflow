from enum import StrEnum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class Diagnostic(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: str = "recipeflow.diagnostic/v1"
    code: str
    severity: Severity
    path: str = ""
    message: str
    suggestions: tuple[str, ...] = ()
    related_paths: tuple[str, ...] = ()
    context: dict[str, Any] = Field(default_factory=dict)
