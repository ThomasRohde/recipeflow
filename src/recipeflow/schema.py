import json
from typing import Literal

from recipeflow.models import Diagnostic, RecipeDocument, RecipeGraph


def schema_json(
    contract: Literal["document", "graph", "diagnostic"] = "document",
) -> str:
    model = {
        "document": RecipeDocument,
        "graph": RecipeGraph,
        "diagnostic": Diagnostic,
    }[contract]
    return json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n"
