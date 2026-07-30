from collections import defaultdict, deque

from recipeflow.models.graph import MaterialNode, OperationNode, RecipeGraph
from recipeflow.models.layout import Lane, MaterialSegment, OperationCell, SetupCard, TabularLayout


def create_tabular_layout(graph: RecipeGraph) -> TabularLayout:
    materials = {n.id: n for n in graph.nodes if isinstance(n, MaterialNode)}
    operations = {n.id: n for n in graph.nodes if isinstance(n, OperationNode)}
    consumes: dict[str, list[str]] = defaultdict(list)
    produces: dict[str, list[str]] = defaultdict(list)
    requires: dict[str, list[str]] = defaultdict(list)
    producer: dict[str, str] = {}
    for e in graph.edges:
        if e.kind == 'consumes': consumes[e.target].append(e.source)
        elif e.kind == 'produces':
            produces[e.source].append(e.target); producer[e.target] = e.source
        else: requires[e.target].append(e.source)

    transform_ids = [n.id for n in graph.nodes if isinstance(n, OperationNode) and n.operation_kind == 'transform']
    indegree = {oid: 0 for oid in transform_ids}; adj: dict[str, set[str]] = defaultdict(set)
    for oid in transform_ids:
        for mid in consumes.get(oid, []):
            src = producer.get(mid)
            if src in indegree and oid not in adj[src]: adj[src].add(oid); indegree[oid] += 1
    q = deque([oid for oid in transform_ids if indegree[oid] == 0]); order=[]
    while q:
        oid=q.popleft(); order.append(oid)
        for nxt in adj[oid]:
            indegree[nxt]-=1
            if indegree[nxt]==0:q.append(nxt)
    if len(order) != len(transform_ids): order = transform_ids

    ingredient_ids=[n.id for n in graph.nodes if isinstance(n, MaterialNode) and n.role=='ingredient']
    lane_of={mid:i for i,mid in enumerate(ingredient_ids)}; next_lane=len(ingredient_ids)
    for oid in order:
        ins=consumes.get(oid,[]); lanes=[lane_of[m] for m in ins if m in lane_of]
        primary=min(lanes) if lanes else next_lane
        if not lanes: next_lane += 1
        outs=produces.get(oid,[])
        for j,mid in enumerate(outs):
            if j==0: lane_of[mid]=primary
            else: lane_of[mid]=next_lane; next_lane += 1

    label_width=270; col_width=150; header_height=74; setup_height=78; row_height=54
    left=label_width+26; op_x={oid:left+i*col_width+col_width/2 for i,oid in enumerate(order)}
    width=max(760,left+max(1,len(order))*col_width+180); height=header_height+setup_height+max(1,next_lane)*row_height+62
    y_for=lambda lane: header_height+setup_height+lane*row_height+row_height/2

    consumers: dict[str,list[str]]=defaultdict(list)
    for oid in order:
        for mid in consumes.get(oid,[]): consumers[mid].append(oid)
    segs=[]
    for mid,node in materials.items():
        if mid.startswith('req:') or mid not in lane_of: continue
        lane=lane_of[mid]; prod=producer.get(mid)
        x1=left-8 if node.role=='ingredient' else (op_x.get(prod,left)-18)
        cs=consumers.get(mid,[])
        x2=max((op_x[c]+18 for c in cs), default=width-85)
        segs.append(MaterialSegment(material_id=mid,label=node.label,quantity=node.quantity,role=node.role,lane=lane,x1=x1,x2=x2,y=y_for(lane),show_left_label=node.role=='ingredient',show_inline_label=node.role!='ingredient'))

    cells=[]
    for oid in order:
        node=operations[oid]; ins=consumes.get(oid,[]); outs=produces.get(oid,[])
        lanes=[lane_of[m] for m in ins if m in lane_of] + [lane_of[m] for m in outs if m in lane_of]
        lo=min(lanes) if lanes else 0; hi=max(lanes) if lanes else lo
        cells.append(OperationCell(operation_id=oid,label=node.label,action=node.action,x=op_x[oid],y1=y_for(lo)-18,y2=y_for(hi)+18,input_material_ids=tuple(ins),output_material_ids=tuple(outs),duration=node.duration,temperature=node.temperature,until=node.until))

    setup_nodes=[n for n in graph.nodes if isinstance(n,OperationNode) and n.operation_kind=='setup']
    cards=[]
    if setup_nodes:
        card_w=(width-left-60)/len(setup_nodes)
        for i,n in enumerate(setup_nodes):
            detail=' · '.join(x for x in [n.temperature,n.duration] if x) or None
            cards.append(SetupCard(operation_id=n.id,label=n.label,detail=detail,x=left+i*card_w,width=card_w-12))
    return TabularLayout(title=graph.title,width=width,height=height,label_width=label_width,header_height=header_height,setup_height=setup_height,row_height=row_height,lanes=tuple(Lane(index=i,y=y_for(i),initial_material_id=ingredient_ids[i] if i<len(ingredient_ids) else None) for i in range(next_lane)),materials=tuple(segs),operations=tuple(cells),setup=tuple(cards),final_material_ids=tuple(graph.final_material_ids))
