"""Validate successive editor buffers without using the filesystem."""

from recipeflow import incremental_validate

INCOMPLETE = """
recipeflow: 1
recipe: {id: salad, title: Salad}
ingredients:
  leaves: {label: salad leaves}
operations: []
"""

COMPLETE = """
recipeflow: 1
recipe: {id: salad, title: Salad}
ingredients:
  leaves: {label: salad leaves}
operations:
  - id: serve
    action: arrange
    inputs: [leaves]
    outputs:
      salad: {label: arranged salad, role: final, final: true}
"""


def diagnostic_codes(buffer: str) -> tuple[str, ...]:
    return tuple(item.code for item in incremental_validate(buffer).diagnostics)


def main() -> None:
    before = diagnostic_codes(INCOMPLETE)
    after = diagnostic_codes(COMPLETE)
    assert before
    assert not after
    print("before", before, "after", after)


if __name__ == "__main__":
    main()
