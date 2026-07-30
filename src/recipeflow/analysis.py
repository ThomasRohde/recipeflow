from collections import defaultdict, deque
from recipeflow.models import GraphAnalysis, RecipeGraph
from recipeflow.models.graph import MaterialNode, OperationNode

def analyze(graph: RecipeGraph) -> GraphAnalysis:
    materials={n.id:n for n in graph.nodes if isinstance(n,MaterialNode)}
    operations={n.id:n for n in graph.nodes if isinstance(n,OperationNode)}
    consumed={e.source for e in graph.edges if e.kind=="consumes"}
    producer={e.target:e.source for e in graph.edges if e.kind=="produces"}
    adjacency: dict[str,set[str]]=defaultdict(set); indegree={oid:0 for oid,o in operations.items() if o.operation_kind=="transform"}
    for e in graph.edges:
        if e.kind=="consumes" and e.source in producer:
            p=producer[e.source]; c=e.target
            if p in indegree and c in indegree and c not in adjacency[p]:
                adjacency[p].add(c); indegree[c]+=1
    q=deque(sorted(k for k,v in indegree.items() if v==0)); order=[]
    while q:
        n=q.popleft(); order.append(n.removeprefix('op:'))
        for nxt in sorted(adjacency[n]):
            indegree[nxt]-=1
            if indegree[nxt]==0:q.append(nxt)
    return GraphAnalysis(
        ingredient_count=sum(1 for m in materials.values() if m.role=="ingredient"),
        setup_count=sum(1 for o in operations.values() if o.operation_kind=="setup"),
        operation_count=sum(1 for o in operations.values() if o.operation_kind=="transform"),
        intermediate_ids=tuple(sorted(m.id for m in materials.values() if m.role=="intermediate" and not m.id.startswith('req:'))),
        final_ids=tuple(graph.final_material_ids),
        unused_ingredient_ids=tuple(sorted(m.id for m in materials.values() if m.role=="ingredient" and m.id not in consumed)),
        topological_operation_ids=tuple(order),
    )
