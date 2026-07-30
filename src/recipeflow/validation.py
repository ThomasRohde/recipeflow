from collections import Counter, defaultdict, deque
from recipeflow.models import Diagnostic, RecipeDocument, Severity, ValidationResult

def validate(document: RecipeDocument) -> ValidationResult:
    diagnostics: list[Diagnostic] = []
    ingredient_ids=set(document.ingredients)
    setup_outputs={item.produces for item in document.setup}
    output_ids=[oid for operation in document.operations for oid in operation.outputs]
    material_counts=Counter([*ingredient_ids, *output_ids])
    for material_id, count in sorted(material_counts.items()):
        if count > 1:
            diagnostics.append(Diagnostic(code="RF101", severity=Severity.ERROR, path=f"/materials/{material_id}", message=f"Material id '{material_id}' is declared more than once."))
    operation_ids=[item.id for item in document.setup] + [item.id for item in document.operations]
    for operation_id, count in Counter(operation_ids).items():
        if count > 1:
            diagnostics.append(Diagnostic(code="RF102", severity=Severity.ERROR, path=f"/operations/{operation_id}", message=f"Operation id '{operation_id}' is declared more than once."))
    known_materials=ingredient_ids | set(output_ids)
    consumed: set[str]=set()
    producer: dict[str,str]={}
    for op in document.operations:
        for oid in op.outputs: producer[oid]=op.id
    adjacency: dict[str,set[str]]=defaultdict(set)
    indegree={op.id:0 for op in document.operations}
    for idx, op in enumerate(document.operations):
        if not op.outputs:
            diagnostics.append(Diagnostic(code="RF103", severity=Severity.ERROR, path=f"/operations/{idx}/outputs", message="A transformation must produce at least one material."))
        for input_id in op.inputs:
            if input_id not in known_materials:
                diagnostics.append(Diagnostic(code="RF104", severity=Severity.ERROR, path=f"/operations/{idx}/inputs", message=f"Unknown material '{input_id}'.", suggestions=tuple(sorted(known_materials))))
            else:
                consumed.add(input_id)
                source_op=producer.get(input_id)
                if source_op and source_op != op.id and op.id not in adjacency[source_op]:
                    adjacency[source_op].add(op.id); indegree[op.id]+=1
        for req in op.requires:
            if req not in setup_outputs:
                diagnostics.append(Diagnostic(code="RF105", severity=Severity.ERROR, path=f"/operations/{idx}/requires", message=f"Unknown prerequisite '{req}'.", suggestions=tuple(sorted(setup_outputs))))
    for iid, ingredient in document.ingredients.items():
        if iid not in consumed and not ingredient.optional:
            diagnostics.append(Diagnostic(code="RF211", severity=Severity.ERROR, path=f"/ingredients/{iid}", message=f"Ingredient '{iid}' is never consumed or marked optional."))
    final_ids=[oid for op in document.operations for oid,out in op.outputs.items() if out.final or out.role=="final"]
    if not final_ids:
        diagnostics.append(Diagnostic(code="RF212", severity=Severity.ERROR, path="/operations", message="At least one final output is required."))
    queue=deque(sorted(k for k,v in indegree.items() if v==0)); visited=[]
    while queue:
        n=queue.popleft(); visited.append(n)
        for nxt in sorted(adjacency[n]):
            indegree[nxt]-=1
            if indegree[nxt]==0: queue.append(nxt)
    if len(visited) != len(indegree):
        diagnostics.append(Diagnostic(code="RF213", severity=Severity.ERROR, path="/operations", message="Material dependencies contain a cycle."))
    return ValidationResult(diagnostics=tuple(diagnostics))
