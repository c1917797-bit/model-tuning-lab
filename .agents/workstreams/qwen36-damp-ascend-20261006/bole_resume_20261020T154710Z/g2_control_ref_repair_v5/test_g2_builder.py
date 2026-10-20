"""Pure parent/model qualification and exact host derive controls."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import sourceio as C
import g2_validate as V
import g2_host_adapter as HA
P=Path(__file__).resolve().parent


def safe_declared_refs(text):
 """Read only literal BASE/REFS; never execute/import the donor substrate."""
 tree=ast.parse(text)
 def assignment(name):
  values=[n.value for n in tree.body if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id==name]
  if len(values)!=1:raise ValueError('exact unique '+name+' assignment')
  return values[0]
 base_node=assignment('BASE')
 if not isinstance(base_node,ast.Constant)or type(base_node.value)is not str or not Path(base_node.value).is_absolute():raise ValueError('unique BASE absolute string literal')
 base=base_node.value
 def value(node):
  if isinstance(node,ast.Dict):
   keys=[]
   for k in node.keys:
    if not isinstance(k,ast.Constant)or type(k.value)is not str:raise ValueError('literal string keys; no dictionary unpack')
    keys.append(k.value)
   if len(set(keys))!=len(keys):raise ValueError('no repeated literal keys')
   return{k:value(v)for k,v in zip(keys,node.values)}
  if isinstance(node,ast.Call):
   if not isinstance(node.func,ast.Name)or node.func.id!='dict'or node.args or any(k.arg is None for k in node.keywords):raise ValueError('only dict keyword literals; no positional/star/executable calls')
   keys=[k.arg for k in node.keywords]
   if len(set(keys))!=len(keys):raise ValueError('no repeated dict keywords')
   return{k.arg:value(k.value)for k in node.keywords}
  if isinstance(node,ast.BinOp):
   if not(isinstance(node.op,ast.Add)and isinstance(node.left,ast.Name)and node.left.id=='BASE'and isinstance(node.right,ast.Constant)and type(node.right.value)is str):raise ValueError('only literal BASE plus literal filename')
   return base+node.right.value
  return ast.literal_eval(node)
 root=assignment('REFS')
 if not isinstance(root,(ast.Dict,ast.Call)):raise ValueError('REFS must be literal dict or safe keyword dict')
 refs=value(root);names={'model_contract','safety_host','host_once'}
 if type(refs)is not dict or set(refs)!=names:raise ValueError('exact three genuine025 source Refs')
 for name,r in refs.items():
  if not(type(r)is dict and set(r)=={'path','bytes','sha256'}and r['path']==base+'/'+name+'.py'and
   type(r['bytes'])is int and r['bytes']>0 and type(r['sha256'])is str and len(r['sha256'])==64 and
   all(c in '0123456789abcdef'for c in r['sha256'])):raise ValueError('exact typed declared Ref3')
 return refs


class BuilderTests(unittest.TestCase):
 def qualified(self):
  td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);root=Path(td.name)
  sr={'source':1}
  ranks=[]
  for i in range(4):ranks.append(C.write(root/('rank%d.json'%i),dict(requests=[dict(actual_final_retirement_observed=True)]*2)))
  report=dict(source=sr,service_complete=True,completed_request_count=2,
    component_checks_pass=True,scheduler_committed_independently=True,model_ready=False,
    slot_reuse_observed=False,actual_all4_retirement=True,ranks=ranks)
  rr=C.write(root/'ATTRIBUTION.json',report)
  owner=dict(source=sr,primary=None,secondary=[],source_before={'actual':1},source_after={'actual':1},
    cpu_only=False,summary=dict(independent=rr))
  ownerref=C.write(root/'RESULT.json',owner)
  m=dict(service_experiment=dict(schema='bole.c1-two-request-service/v1',prefix=131,request_count=2,max_steps_per_request=1,max_output_tokens=2),
    prepared_only=False,default_enabled=False,g1_repair_v2={},files={})
  return root,sr,m,ownerref,rr,owner,report
 def test_parent_requires_actual_independent_model_not_CPU_only_or_source(self):
  root,sr,m,ownerref,rr,owner,report=self.qualified()
  self.assertTrue(V.parent_qualified(sr,m,ownerref,rr))
  for key,value in(('primary','failed'),('secondary',['cleanup']),('cpu_only',True),('source_after',{'changed':1})):
   x=dict(owner);x[key]=value;r=C.write(root/(key+'.json'),x)
   with self.subTest(key=key),self.assertRaises(ValueError):V.parent_qualified(sr,m,r,rr)
 def test_parent_independent_gate_cannot_skip_retirement_or_math(self):
  root,sr,m,oref,rr,owner,report=self.qualified()
  for key in('service_complete','component_checks_pass','scheduler_committed_independently','actual_all4_retirement'):
   x=dict(report);x[key]=False;r=C.write(root/('bad-'+key+'.json'),x)
   own=dict(owner,summary=dict(independent=r));o=C.write(root/('owner-'+key+'.json'),own)
   with self.subTest(key=key),self.assertRaises(ValueError):V.parent_qualified(sr,m,o,r)
 def test_slot_reuse_false_remains_truthful_observation(self):
  _,sr,m,oref,rr,owner,report=self.qualified()
  self.assertFalse(report['slot_reuse_observed']);self.assertTrue(V.parent_qualified(sr,m,oref,rr))
 def test_fresh_builder_is_cold_and_does_not_mutate_without_explicit_execute(self):
  for mode in([],['--help']):
   q=subprocess.run([sys.executable,'-I','-B',str(P/'prepare_g2.py'),*mode],capture_output=True,text=True,timeout=10)
   self.assertEqual(q.returncode,0,q.stderr)
   if not mode:self.assertEqual(json.loads(q.stdout),dict(enabled=False,NPU=False))
 def test_declared_REFS_literal_and_safe_dict_constructor_match_exact_original_values(self):
  source=(P/'owned_substrate.py').read_text()
  refs=safe_declared_refs(source)
  self.assertEqual(refs['safety_host']['bytes'],22338)
  self.assertEqual(refs['safety_host']['sha256'],'20bda52a1c3fbc75db47104cbd4759faf91da1f39032d4730160983f7b9c0c30')
  declared="BASE='/reference'\nREFS="+repr({k:dict(r,path='/reference/'+k+'.py')for k,r in refs.items()})
  self.assertEqual(safe_declared_refs(declared),{k:dict(r,path='/reference/'+k+'.py')for k,r in refs.items()})
 def test_declared_REFS_rejects_arbitrary_execution_unpack_reassignment_or_bad_values(self):
  source=(P/'owned_substrate.py').read_text()
  refs=safe_declared_refs(source);base=str(Path(refs['safety_host']['path']).parent)
  cases=["BASE="+repr(base)+"\nREFS=dict(**"+repr(refs)+")",source.replace("dict(path=BASE+", "__import__(path=BASE+",1),source.replace("dict(path=BASE+", "dict(**dict(path=BASE+",1),
   source+"\nBASE='/foreign'\n",source.replace("BASE+'/safety_host.py'","str(BASE)+'/safety_host.py'"),
   source.replace('bytes=22338','bytes=True'),source.replace("BASE+'/safety_host.py'","BASE+'/../safety_host.py'"),
   source.replace('dict(path=BASE+', 'dict({},path=BASE+',1)]
  for candidate in cases:
   with self.subTest(candidate=candidate[:120]),self.assertRaises((ValueError,SyntaxError)):safe_declared_refs(candidate)
 def test_CPU3_derivation_retains_complete_original_create_inspect_resource_checks(self):
  local=P.parents[1]/'g1_review_v2'
  if(local/'external025.py').is_file():external_path=local/'external025.py';original=local/'safety_host.py'
  else:
   m=C.obj(C.ref(P/'SOURCE_TEMPLATE.json'));external_path=C.checked(m['files']['external025.py'])
   pins=safe_declared_refs(C.checked(m['files']['owned_substrate.py']).read_text())
   original=C.checked(pins['safety_host'])
  spec=importlib.util.spec_from_file_location('_g2_test_external',external_path);E=importlib.util.module_from_spec(spec);spec.loader.exec_module(E)
  before,prior=E.derive(original.read_bytes());after,pairs=HA.derive(original.read_bytes(),E)
  restored=after
  for old,new in reversed(pairs):self.assertEqual(restored.count(new),2);restored=restored.replace(new,old)
  self.assertEqual(restored,before)
  self.assertIn('h["Memory"]==h["MemorySwap"]==mem',after)
  self.assertIn('len(dev)==(0 if cpu else 7)',after)
  self.assertIn('full exact immutable inputs/owned output mounts',after)


if __name__=='__main__':unittest.main()
