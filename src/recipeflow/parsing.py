import json
from typing import Any, Literal
import yaml
from pydantic import ValidationError
from recipeflow.models import Diagnostic, ParseResult, RecipeDocument, Severity

def _validation_diagnostics(exc: ValidationError) -> tuple[Diagnostic, ...]:
    items=[]
    for error in exc.errors():
        path="/" + "/".join(str(p) for p in error["loc"])
        items.append(Diagnostic(code="RF001", severity=Severity.ERROR, path=path, message=error["msg"]))
    return tuple(items)

def parse(source: str, source_format: Literal["yaml", "json"] = "yaml") -> ParseResult:
    try:
        data: Any = yaml.safe_load(source) if source_format == "yaml" else json.loads(source)
    except (yaml.YAMLError, json.JSONDecodeError) as exc:
        return ParseResult(diagnostics=(Diagnostic(code="RF000", severity=Severity.ERROR, message=f"Syntax error: {exc}"),))
    try:
        return ParseResult(document=RecipeDocument.model_validate(data))
    except ValidationError as exc:
        return ParseResult(diagnostics=_validation_diagnostics(exc))
