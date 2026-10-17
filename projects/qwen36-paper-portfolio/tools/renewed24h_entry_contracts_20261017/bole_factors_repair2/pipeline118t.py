"""Profile-only extension of existing physical4 118t ARM/controller."""
def modules(C,m):
 import factor,run_factor,consume_factor,diagnose,decision_gate,root_pair,root_pair_stage
 for module in(factor,run_factor,consume_factor,diagnose,decision_gate,root_pair,root_pair_stage):
  C.need(C.ref(module.__file__)==m['files'][module.__name__+'.py'],'exact source-bound own module, no ambient imports')
def run(t,C,m,out,deadline):
 import run_factor,torch_npu
 modules(C,m)
 return run_factor.run(t,torch_npu,C,m,out,deadline)
def consume(t,C,m,sr,outer):
 import consume_factor
 modules(C,m)
 C.need(outer['schema']=='bole.tree-stage/vFAfactor'and outer['source']==sr and outer['primary']is None and outer['NPU']is True,'actual released same-source factor outer stage')
 return consume_factor.consume(t,C,m,sr,outer['result'])
