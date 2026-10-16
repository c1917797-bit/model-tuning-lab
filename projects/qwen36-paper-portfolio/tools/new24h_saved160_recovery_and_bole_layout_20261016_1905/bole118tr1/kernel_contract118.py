"""Exact reviewed installed kernel sources; source proof is not calibration."""
ROOT='/cache/cch/qwen36-paper-preparation-20261007/lowbit/bole-installed-conv660-kernel-MAIN-20261016-001'
FILES={
'op_host/causal_conv1d_def.cpp':(3493,'8bb47bb6be57184a94d2d220194e96aad8d9b6e5c43ee531d94d24ebfe6b90b7'),
'op_kernel/causal_conv1d.h':(46361,'83af972763a708fce1b723106dcd243260fb3302c947d3a59ed34a868c6e0bf3'),
'op_kernel/causal_conv1d_update.h':(4418,'1678810248bb470ac87769804ee8bd2b8682010184ae05b02d89b74f11e3f2ac'),
'op_kernel/causal_conv1d.cpp':(2742,'3001e398478b3f532510b1b130e9ab2a97d9c12ec367437e49ed8f97fb7afb7b')}
def readset():return [dict(path=ROOT+'/'+n,bytes=size,sha256=digest)for n,(size,digest)in FILES.items()]
def verify(C):
 for r in readset():C.checked(r)
 return dict(schema='bole.native-conv-source-contract/v118',refs=readset(),layout='SD slot,width-1,channel',run_mode=1,num_accepted_tokens=None,initial_state_read=True,accumulation='FP32 Mul/MulAddDst',output_cast='BF16 CAST_RINT',selected_cache_write='last width-1 raw T projections, oldest-to-newest',NPU=False,qualified=False)
