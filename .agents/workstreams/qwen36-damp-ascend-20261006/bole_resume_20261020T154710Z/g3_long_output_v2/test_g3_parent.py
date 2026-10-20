"""A prepared source or first-frame success never qualifies the long successor."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import sourceio as C
import g3_parent as G

class ParentTests(unittest.TestCase):
 def fixture(self):
  td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);p=Path(td.name)
  scope=dict(schema='bole.c1-two-request-stream-service/v2',profile='smoke4',prefix=131,request_count=2,max_steps_per_request=3,
   max_output_tokens=4,capture_protocol='every-frame-independent-CPU-ACK/v1')
  m=dict(service_experiment=scope,prepared_only=False,default_enabled=False,files={},service_required_sameimage_software_cases=258);sr=C.write(p/'SOURCE.json',m)
  audit=dict(schema='bole.G2-readonly-source-preparation-audit-supplement/v6',source=sr,missing=[],original_contract_unmodified=True,actual_software_cases=258,
   original_source_and_COMMANDS_unmodified=True,source_preparation_supplement_only=True,directory_mounts_added=False)
  ar=C.write(p/'AUDIT.json',audit)
  report=dict(source=sr,scope=scope,service_complete=True,completed_request_count=2,component_checks_pass=True,
   scheduler_committed_independently=True,all4_worker_retirement_verified=True,every_frame_independently_consumed=True,
   model_ready=False,successful_raw_replay_available=False,ranks=[dict(rank=rank,all_frames_consumed=True,coverage_proof=dict(all_coverage=True),
    requests=[dict(steps=2,processed_tokens=3,output_token_ids=[7,11,13,17],next_counter_ACKs=1,component_checks_pass=True)for _ in range(2)])for rank in range(4)])
  rr=C.write(p/'REPORT.json',report)
  owner=dict(source=sr,primary=None,secondary=[],source_before={'a':'same'},source_after={'a':'same'},cpu_only=False,summary=dict(independent=rr))
  own=C.write(p/'OWNER.json',owner);return p,sr,m,own,rr,ar
 def test_only_actual_complete_parent_plus_independent_corrected_source_audit_admits(self):
  p,sr,m,own,rr,ar=self.fixture();self.assertTrue(G.qualified(sr,m,own,rr,source_audit_ref=ar))
 def test_pending_source_only_CPU_only_or_first_frame_parent_never_admits(self):
  p,sr,m,own,rr,ar=self.fixture()
  with self.assertRaises((ValueError,TypeError)):G.qualified(sr,m,None,None,source_audit_ref=ar)
  for field,value in(('prepared_only',True),('service_experiment',dict(m['service_experiment'],max_output_tokens=1024))):
   with self.subTest(field=field),self.assertRaises(ValueError):G.qualified(sr,dict(m,**{field:value}),own,rr,source_audit_ref=ar)
  o=C.obj(own);o['cpu_only']=True;own2=C.write(p/'CPU.json',o)
  with self.assertRaises(ValueError):G.qualified(sr,m,own2,rr,source_audit_ref=ar)
 def test_missing_late_coverage_retirement_or_source_audit_failure_remains_blocking(self):
  for field in('coverage','retirement','component','audit'):
   p,sr,m,own,rr,ar=self.fixture();r=C.obj(rr);o=C.obj(own)
   if field=='coverage':r['ranks'][3]['coverage_proof']['all_coverage']=False
   elif field=='retirement':r['all4_worker_retirement_verified']=False
   elif field=='component':r['ranks'][2]['requests'][1]['component_checks_pass']=False
   else:
    a=C.obj(ar);a['missing']=[{'missing':True}];ar=C.write(p/'AUDIT-FAILED.json',a)
   rr=C.write(p/'REPORT-ALTERED.json',r);o['summary']['independent']=rr;own=C.write(p/'OWNER-ALTERED.json',o)
   with self.subTest(field=field),self.assertRaises(ValueError):G.qualified(sr,m,own,rr,source_audit_ref=ar)

if __name__=='__main__':unittest.main()
