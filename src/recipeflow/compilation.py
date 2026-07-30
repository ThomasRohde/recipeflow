from recipeflow.models import RecipeDocument, RecipeGraph
from recipeflow.models.graph import Edge, MaterialNode, OperationNode

def compile_recipe(document: RecipeDocument) -> RecipeGraph:
    nodes=[]; edges=[]; edge_no=1
    for iid, ingredient in document.ingredients.items():
        nodes.append(MaterialNode(id=iid,label=ingredient.label,role="ingredient",quantity=ingredient.quantity))
    for setup in document.setup:
        op_id=f"op:{setup.id}"
        nodes.append(OperationNode(id=op_id,label=f"{setup.action} {setup.target or ''}".strip(),operation_kind="setup",action=setup.action,duration=setup.duration,temperature=setup.temperature))
        prereq_id=f"req:{setup.produces}"
        nodes.append(MaterialNode(id=prereq_id,label=setup.produces.replace('-', ' '),role="intermediate"))
        edges.append(Edge(id=f"edge:{edge_no}",kind="produces",source=op_id,target=prereq_id)); edge_no+=1
    final_ids=[]
    for op in document.operations:
        op_id=f"op:{op.id}"
        nodes.append(OperationNode(id=op_id,label=op.action,operation_kind="transform",action=op.action,duration=op.duration,temperature=op.temperature,until=op.until))
        for inp in op.inputs:
            edges.append(Edge(id=f"edge:{edge_no}",kind="consumes",source=inp,target=op_id)); edge_no+=1
        for req in op.requires:
            edges.append(Edge(id=f"edge:{edge_no}",kind="requires",source=f"req:{req}",target=op_id)); edge_no+=1
        for oid,out in op.outputs.items():
            role="final" if out.final else out.role
            nodes.append(MaterialNode(id=oid,label=out.label,role=role))
            edges.append(Edge(id=f"edge:{edge_no}",kind="produces",source=op_id,target=oid)); edge_no+=1
            if role=="final": final_ids.append(oid)
    return RecipeGraph(recipe_id=document.recipe.id,title=document.recipe.title,nodes=nodes,edges=edges,final_material_ids=final_ids)
