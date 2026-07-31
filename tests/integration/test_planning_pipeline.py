import json
from datetime import UTC, datetime

from recipeflow.compilation import compile_document
from recipeflow.parsing import parse_json
from recipeflow.planning import (
    PlanningRequest,
    RecipeInstance,
    ResourceCapacity,
    plan_recipes,
)


def _oven_graph(recipe_id: str, ingredient: str):
    parsed = parse_json(
        json.dumps(
            {
                "recipeflow": 1,
                "recipe": {"id": recipe_id, "title": recipe_id},
                "ingredients": {ingredient: {"label": ingredient}},
                "operations": [
                    {
                        "id": "bake",
                        "action": "bake",
                        "inputs": [ingredient],
                        "duration": "30 min",
                        "resources": [{"id": "oven"}],
                        "outputs": {
                            f"{recipe_id}-result": {
                                "label": f"{recipe_id} result",
                                "role": "final",
                            }
                        },
                    }
                ],
            }
        )
    )
    assert parsed.document is not None
    compiled = compile_document(parsed.document)
    assert compiled.graph is not None
    return compiled.graph


def test_planner_serializes_shared_resource_use_and_builds_projections() -> None:
    target = datetime(2026, 7, 30, 18, 0, tzinfo=UTC)
    request = PlanningRequest(
        recipes=(
            RecipeInstance(id="bread", graph=_oven_graph("bread", "flour")),
            RecipeInstance(id="pie", graph=_oven_graph("pie", "apples")),
        ),
        target_time=target,
        resources=(ResourceCapacity(id="oven", capacity=1),),
    )

    result = plan_recipes(request)

    assert result.ok
    assert result.plan is not None
    assert result.plan.critical_path_minutes == 60
    assert result.plan.operations[0].end <= result.plan.operations[1].start
    assert result.plan.operations[-1].end == target
    assert {item.label for item in result.plan.shopping_list} == {
        "apples",
        "flour",
    }
