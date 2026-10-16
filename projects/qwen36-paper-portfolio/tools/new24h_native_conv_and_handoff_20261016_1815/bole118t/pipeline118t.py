"""Thin actual118c-owner hooks: new eight-row TND domain, no resource changes."""
from pathlib import Path

def modules(C,m):
 import adapter,reference,run_component,consume
 for module in(adapter,reference,run_component,consume):
  C.need(C.ref(module.__file__)==m['files'][module.__name__+'.py'],'exact own component import, no ambient sibling')

def run(t,C,m,out,deadline):
 import predecessor118t as P,run_component as K,torch_npu
 modules(C,m)
 P.join(C,m)
 return K.run(t,torch_npu,m,out,deadline,actual_arm_verified=True)

def consume(t,C,m,sr,outer):
 import consume as K,predecessor118t as P
 modules(C,m)
 proof=P.join(C,m)
 C.need(outer['schema']=='bole.tree-stage/v118t'and outer['source']==sr and outer['primary']is None and outer['NPU']is True,'actual TND complete outer')
 # A temporary report is not needed: receiver returns a dict when out=None.
 value=K.run(t,sr,outer['result'],None)
 return dict(value,schema='bole.paged-tree-independent/v118t',pass_gate=value['component_pass'],
             actual_capture=outer['result'],actual118c=proof,qualified=False,model_ready=False)
