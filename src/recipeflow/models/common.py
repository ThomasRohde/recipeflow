from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

DOCUMENT_SCHEMA_VERSION: Literal["recipeflow.document/v1"] = (
    "recipeflow.document/v1"
)
GRAPH_SCHEMA_VERSION: Literal["recipeflow.graph/v1"] = "recipeflow.graph/v1"
DIAGNOSTIC_SCHEMA_VERSION: Literal["recipeflow.diagnostic/v1"] = (
    "recipeflow.diagnostic/v1"
)
ANALYSIS_SCHEMA_VERSION: Literal["recipeflow.analysis/v1"] = (
    "recipeflow.analysis/v1"
)


class PublicModel(BaseModel):
    """Shared behavior for language-neutral public contracts."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        populate_by_name=True,
        serialize_by_alias=True,
        validate_by_alias=True,
        validate_by_name=True,
    )


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class DiagnosticFix(PublicModel):
    operation: Literal["add", "remove", "replace"]
    path: str
    value: Any | None = None
    description: str | None = None


class Diagnostic(PublicModel):
    schema_version: Literal["recipeflow.diagnostic/v1"] = DIAGNOSTIC_SCHEMA_VERSION
    code: str = Field(pattern=r"^RF\d{3}$")
    severity: Severity
    path: str = ""
    message: str
    suggestions: tuple[str, ...] = ()
    related_paths: tuple[str, ...] = ()
    fix: DiagnosticFix | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class Provenance(PublicModel):
    """Evidence connecting an authored fact to its source."""

    source_id: str | None = None
    path: str | None = None
    source_text: str | None = None
    note: str | None = None
    confidence: Decimal | None = Field(default=None, ge=0, le=1)


class Ambiguity(PublicModel):
    description: str
    alternatives: tuple[str, ...] = ()
    resolution: str | None = None
    explicit: bool = True


class NormalizedQuantity(PublicModel):
    value: Decimal | None = None
    minimum: Decimal | None = None
    maximum: Decimal | None = None
    unit: str | None = None

    @model_validator(mode="after")
    def _ordered_range(self) -> Self:
        if (
            self.minimum is not None
            and self.maximum is not None
            and self.minimum > self.maximum
        ):
            raise ValueError("minimum cannot exceed maximum")
        return self


class Quantity(PublicModel):
    source_text: str
    normalized: NormalizedQuantity | None = None


class DurationSpec(PublicModel):
    source_text: str
    minimum_minutes: Decimal | None = Field(default=None, ge=0)
    maximum_minutes: Decimal | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _ordered_range(self) -> Self:
        if (
            self.minimum_minutes is not None
            and self.maximum_minutes is not None
            and self.minimum_minutes > self.maximum_minutes
        ):
            raise ValueError("minimum_minutes cannot exceed maximum_minutes")
        return self


class TemperatureSpec(PublicModel):
    source_text: str
    value: Decimal | None = None
    minimum: Decimal | None = None
    maximum: Decimal | None = None
    unit: Literal["C", "F", "K"] | None = None

    @model_validator(mode="after")
    def _ordered_range(self) -> Self:
        if (
            self.minimum is not None
            and self.maximum is not None
            and self.minimum > self.maximum
        ):
            raise ValueError("minimum cannot exceed maximum")
        return self


class ResourceRequirement(PublicModel):
    id: str
    label: str | None = None
    quantity: int = Field(default=1, ge=1)
    exclusive: bool = True
