"""Nine source-owned cases, three actual outputs each; never model permission."""
FRAMES=9
REPEATS=1
def ready(v,sr):
 return v['schema']=='mxr.block-refinement-owned-probe/v044'and v['source']==sr and v['primary']is None and len(v['raws'])==9 and len({r['path']for r in v['raws']})==9 and v['outputs_per_case']==3 and v['NPU']is True and v['pool_released']is True and bool(v['mapped_library'])and type(v['actual_algorithm_identity'])is dict and v['model_ready']is False
def consumer_ready(v,sr):
 return v['schema']=='mxr.block-refinement-owned-consumer/v044'and v['source']==sr and v['complete']is True and len(v['rows'])==9 and v['case_outputs']==[3]*9 and v['numerical_qualification_granted']is False and v['model_ready']is False and v['performance_ready']is False
