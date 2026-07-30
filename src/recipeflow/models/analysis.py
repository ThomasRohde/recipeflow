from pydantic import BaseModel, ConfigDict

class GraphAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: str = "recipeflow.analysis/v1"
    ingredient_count: int
    setup_count: int
    operation_count: int
    intermediate_ids: tuple[str, ...]
    final_ids: tuple[str, ...]
    unused_ingredient_ids: tuple[str, ...]
    topological_operation_ids: tuple[str, ...]
