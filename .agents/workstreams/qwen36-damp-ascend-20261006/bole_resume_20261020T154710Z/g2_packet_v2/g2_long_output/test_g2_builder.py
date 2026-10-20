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
 def test_CPU3_derivation_retains_complete_original_create_inspect_resource_checks(self):
  local=P.parents[1]/'g1_review_v2'
  if(local/'external025.py').is_file():external_path=local/'external025.py';original=local/'safety_host.py'
  else:
   m=C.obj(C.ref(P/'SOURCE_TEMPLATE.json'));external_path=C.checked(m['files']['external025.py'])
   tree=ast.parse(C.checked(m['files']['owned_substrate.py']).read_bytes());pins=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='REFS'for t in n.targets)))
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
