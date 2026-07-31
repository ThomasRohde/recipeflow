"""A framework-neutral service function suitable for a FastAPI endpoint."""

from typing import Any

from recipeflow import build

SOURCE = """
recipeflow: 1
recipe: {id: toast, title: Toast}
ingredients:
  bread: {label: bread, quantity: 1 slice}
operations:
  - id: toast
    action: toast
    inputs: [bread]
    outputs:
      toast: {label: toast, role: final, final: true}
"""


def compile_request(body: str) -> tuple[int, dict[str, Any]]:
    """Return an HTTP-like status and JSON-compatible public result."""
    result = build(body)
    status = 200 if result.ok else 422
    return status, result.model_dump(mode="json")


def main() -> None:
    status, payload = compile_request(SOURCE)
    assert status == 200
    assert payload["graph"]["recipe_id"] == "toast"
    print(status, payload["graph"]["schema_version"])


if __name__ == "__main__":
    main()
