"""Resolve hot-plan material identity without falling back to another segment."""
from independent_hybrid_material import MaterialIdentity

def identity_for_plan(stage,layer,plan):
    catalog=getattr(stage,"catalog",None)
    if catalog is None:return stage.identity(layer,plan.rank)
    if catalog.boundary!=stage.boundary:raise ValueError("catalog seam identity mismatch")
    tokens=catalog.tokens(plan.tokens_sha256)
    return MaterialIdentity(stage.model,stage.code,layer,plan.rank,
                            plan.tokens_sha256,len(tokens),stage.boundary)
