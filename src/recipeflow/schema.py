from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel

from recipeflow.models import (
    CliResult,
    Diagnostic,
    GraphAnalysis,
    RecipeDocument,
    RecipeGraph,
    RenderArtifact,
    TabularLayout,
)

type ContractName = Literal[
    "document",
    "graph",
    "diagnostic",
    "analysis",
    "tabular-layout",
    "render-result",
    "cli-result",
]

SCHEMA_MODELS: dict[ContractName, type[BaseModel]] = {
    "document": RecipeDocument,
    "graph": RecipeGraph,
    "diagnostic": Diagnostic,
    "analysis": GraphAnalysis,
    "tabular-layout": TabularLayout,
    "render-result": RenderArtifact,
    "cli-result": CliResult,
}

SCHEMA_FILENAMES: dict[ContractName, str] = {
    "document": "recipeflow-document-v1.schema.json",
    "graph": "recipeflow-graph-v1.schema.json",
    "diagnostic": "recipeflow-diagnostic-v1.schema.json",
    "analysis": "recipeflow-analysis-v1.schema.json",
    "tabular-layout": "recipeflow-tabular-layout-v1.schema.json",
    "render-result": "recipeflow-render-result-v1.schema.json",
    "cli-result": "recipeflow-cli-result-v1.schema.json",
}


def export_schema(contract: ContractName = "document") -> dict[str, object]:
    """Return a deterministic, language-neutral public JSON Schema."""

    schema = SCHEMA_MODELS[contract].model_json_schema(mode="serialization")
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = f"https://recipeflow.dev/schemas/{SCHEMA_FILENAMES[contract]}"
    return dict(sorted(schema.items()))


def schema_json(contract: ContractName = "document") -> str:
    return (
        json.dumps(
            export_schema(contract),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
