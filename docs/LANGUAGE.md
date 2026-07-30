# RecipeFlow authoring language v1

A document contains metadata, ingredients, setup actions and material-transforming operations.

```yaml
recipeflow: 1
recipe:
  id: example
  title: Example
  source:
    url: https://example.test/recipe

ingredients:
  flour:
    label: flour
    quantity: 100 g

operations:
  - id: make-dough
    action: mix
    inputs: [flour]
    outputs:
      dough:
        label: dough
  - id: bake
    action: bake
    inputs: [dough]
    outputs:
      loaf:
        label: loaf
        final: true
```

Material identifiers are unique across ingredients and operation outputs. `inputs` consume material. `requires` refer to setup outputs or other non-material prerequisites. Every non-setup operation must produce at least one output.
