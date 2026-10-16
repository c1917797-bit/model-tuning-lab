"""New-library intake. Old022 proves only an unchanged predecessor ABI, not051 math."""
ARMS=('split_scale_v051','split_scale_sidecar_v051')
def admit(m,obj,ref):
 r=m['split_build_ref']
 if r is None:raise ValueError('actual051 build missing; no future artifact acceptance')
 if r!=m['reviewed_split_build_ref']:raise ValueError('exact actually reviewed051 build Ref3')
 v=obj(r)
 if not(v['schema']=='deltalog-split-scale-actual-build/v051'and v['primary']is None and v['source_manifest']==m['split_kernel_source_ref']and v['Devices']==[]and v['NPU']is False and v['numeric_qualified']is False and v['model_ready']is False):raise ValueError('actual051 exact source-bound build result')
 if [x['arm']for x in v['artifacts']]!=list(ARMS)or not v['commands']or not all(x['exit_code']==0 and x['error']is None for x in v['commands']):raise ValueError('both completed051 build arms')
 libs=[x['library']for x in v['artifacts']]
 if libs!=[m['library_ref'],m['debug_library']]or libs[0]==libs[1]:raise ValueError('exact distinct new production/debug artifacts')
 for lib in libs:
  if ref(lib['path'])!=lib:raise ValueError('new artifact bytes/hash drift')
 if m['debug_build_ref']!=r:raise ValueError('same actual dual build receipt')
 return v
