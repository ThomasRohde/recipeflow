from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, Literal

import yaml
from pydantic import ValidationError
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode

from recipeflow.models.common import (
    DOCUMENT_SCHEMA_VERSION,
    Diagnostic,
    Severity,
)
from recipeflow.models.document import RecipeDocument
from recipeflow.models.results import ParseResult

SourceFormat = Literal["yaml", "json"]


class DuplicateKeyError(ValueError):
    def __init__(self, key: object, location: str | None = None) -> None:
        self.key = key
        self.location = location
        message = f"Duplicate mapping key {key!r}"
        if location:
            message += f" at {location}"
        super().__init__(message)


class _UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(
    loader: _UniqueKeyLoader,
    node: MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as exc:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found an unhashable key",
                key_node.start_mark,
            ) from exc
        if duplicate:
            location = (
                f"line {key_node.start_mark.line + 1}, "
                f"column {key_node.start_mark.column + 1}"
            )
            raise DuplicateKeyError(key, location)
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(key)
        result[key] = value
    return result


def _pointer(parts: tuple[Any, ...]) -> str:
    escaped = (
        str(part).replace("~", "~0").replace("/", "~1")
        for part in parts
    )
    return "/" + "/".join(escaped)


def _validation_diagnostics(exc: ValidationError) -> tuple[Diagnostic, ...]:
    diagnostics = []
    for error in exc.errors():
        diagnostics.append(
            Diagnostic(
                code="RF102",
                severity=Severity.ERROR,
                path=_pointer(error["loc"]),
                message=error["msg"],
                context={"category": "parse", "type": error["type"]},
            )
        )
    return tuple(diagnostics)


def _source_version(data: Mapping[str, Any]) -> str:
    version = data.get("schema_version")
    if isinstance(version, str):
        return version
    legacy = data.get("recipeflow")
    return f"recipeflow.legacy/{legacy}" if legacy is not None else DOCUMENT_SCHEMA_VERSION


def _version_diagnostic(data: Mapping[str, Any]) -> Diagnostic | None:
    version = data.get("schema_version")
    if version is not None and version != DOCUMENT_SCHEMA_VERSION:
        return Diagnostic(
            code="RF601",
            severity=Severity.ERROR,
            path="/schema_version",
            message=f"Unsupported RecipeFlow document schema version {version!r}.",
            suggestions=(DOCUMENT_SCHEMA_VERSION,),
            context={"supported_versions": [DOCUMENT_SCHEMA_VERSION, "recipeflow.legacy/1"]},
        )
    legacy = data.get("recipeflow")
    if version is None and legacy not in (None, 1):
        return Diagnostic(
            code="RF601",
            severity=Severity.ERROR,
            path="/recipeflow",
            message=f"Unsupported legacy RecipeFlow document version {legacy!r}.",
            suggestions=("1", DOCUMENT_SCHEMA_VERSION),
        )
    return None


def parse_document(
    source: str | Mapping[str, Any] | RecipeDocument,
    source_format: SourceFormat = "yaml",
) -> ParseResult:
    if isinstance(source, RecipeDocument):
        return ParseResult(
            document=source,
            source_version=source.schema_version,
        )

    data: Any
    if isinstance(source, Mapping):
        data = dict(source)
    elif isinstance(source, str):
        try:
            if source_format == "yaml":
                data = yaml.load(source, Loader=_UniqueKeyLoader)
            else:
                data = json.loads(source, object_pairs_hook=_json_object)
        except DuplicateKeyError as exc:
            return ParseResult(
                diagnostics=(
                    Diagnostic(
                        code="RF103",
                        severity=Severity.ERROR,
                        message=str(exc),
                        context={
                            "category": "parse",
                            "duplicate_key": str(exc.key),
                        },
                    ),
                )
            )
        except (yaml.YAMLError, json.JSONDecodeError) as exc:
            return ParseResult(
                diagnostics=(
                    Diagnostic(
                        code="RF101",
                        severity=Severity.ERROR,
                        message=f"Syntax error: {exc}",
                        context={"category": "parse"},
                    ),
                )
            )
    else:
        return ParseResult(
            diagnostics=(
                Diagnostic(
                    code="RF102",
                    severity=Severity.ERROR,
                    message=(
                        "Recipe input must be YAML/JSON text, a mapping, "
                        "or a RecipeDocument."
                    ),
                    context={"category": "parse"},
                ),
            )
        )

    if not isinstance(data, Mapping):
        return ParseResult(
            diagnostics=(
                Diagnostic(
                    code="RF102",
                    severity=Severity.ERROR,
                    path="",
                    message="A RecipeFlow document must be a mapping object.",
                    context={"category": "parse"},
                ),
            )
        )

    version_diagnostic = _version_diagnostic(data)
    if version_diagnostic:
        return ParseResult(
            diagnostics=(version_diagnostic,),
            source_version=_source_version(data),
        )

    try:
        document = RecipeDocument.model_validate(data)
    except ValidationError as exc:
        return ParseResult(
            diagnostics=_validation_diagnostics(exc),
            source_version=_source_version(data),
        )
    return ParseResult(
        document=document,
        source_version=_source_version(data),
    )


def parse(
    source: str | Mapping[str, Any] | RecipeDocument,
    source_format: SourceFormat = "yaml",
) -> ParseResult:
    return parse_document(source, source_format)


def parse_yaml(source: str | Mapping[str, Any] | RecipeDocument) -> ParseResult:
    return parse_document(source, "yaml")


def parse_json(source: str | Mapping[str, Any] | RecipeDocument) -> ParseResult:
    return parse_document(source, "json")
