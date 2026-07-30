from recipeflow import build

def test_unused_ingredient_is_error():
    source="""
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
    result=build(source)
    assert not result.ok
    assert any(d.code=="RF211" for d in result.diagnostics)

def test_unknown_material_is_error():
    source="""
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
    result=build(source)
    assert any(d.code=="RF104" for d in result.diagnostics)
