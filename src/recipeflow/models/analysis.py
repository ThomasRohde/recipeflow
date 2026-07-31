from typing import Literal

from recipeflow.models.common import ANALYSIS_SCHEMA_VERSION, PublicModel


class MaterialUsage(PublicModel):
    material_id: str
    producer_operation_id: str | None = None
    consumer_operation_ids: tuple[str, ...] = ()


class FlowFeature(PublicModel):
    id: str
    related_ids: tuple[str, ...] = ()


class SetupPrerequisite(PublicModel):
    operation_id: str
    required_by_operation_ids: tuple[str, ...] = ()


class GraphAnalysis(PublicModel):
    schema_version: Literal["recipeflow.analysis/v1"] = ANALYSIS_SCHEMA_VERSION
    ingredient_count: int
    material_count: int
    setup_count: int
    operation_count: int
    intermediate_ids: tuple[str, ...]
    final_ids: tuple[str, ...]
    waste_ids: tuple[str, ...] = ()
    garnish_ids: tuple[str, ...] = ()
    reserved_ids: tuple[str, ...] = ()
    unused_ingredient_ids: tuple[str, ...]
    material_usage: tuple[MaterialUsage, ...] = ()
    branches: tuple[FlowFeature, ...] = ()
    joins: tuple[FlowFeature, ...] = ()
    splits: tuple[FlowFeature, ...] = ()
    disconnected_components: tuple[tuple[str, ...], ...] = ()
    topological_operation_ids: tuple[str, ...]
    critical_path_operation_ids: tuple[str, ...] = ()
    critical_path_minutes: float | None = None
    parallel_operation_groups: tuple[tuple[str, ...], ...] = ()
    setup_prerequisites: tuple[SetupPrerequisite, ...] = ()
