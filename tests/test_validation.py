from recipeflow import build


def test_unused_ingredient_is_error() -> None:
    source = """
recipeflow: 1
recipe: {id: test, title: Test}
ingredients:
  flour: {label: flour}
  salt: {label: salt}
operations:
  - id: mix
    action: mix
    inputs: [flour]
    outputs:
      dough: {label: dough, final: true, role: final}
"""
    result = build(source)
    assert not result.ok
    assert any(diagnostic.code == "RF211" for diagnostic in result.diagnostics)


def test_unknown_material_is_error() -> None:
    source = """
recipeflow: 1
recipe: {id: test, title: Test}
ingredients: {}
operations:
  - id: mix
    action: mix
    inputs: [ghost]
    outputs:
      result: {label: result, final: true, role: final}
"""
    result = build(source)
    assert any(diagnostic.code == "RF104" for diagnostic in result.diagnostics)
