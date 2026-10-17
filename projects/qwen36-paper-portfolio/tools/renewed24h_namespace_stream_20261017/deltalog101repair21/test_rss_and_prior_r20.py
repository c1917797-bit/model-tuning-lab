"""Narrow resource-failure recording and preserved-failure prior contract."""
import importlib.util,json,sys,types,unittest,copy
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent
class Resources(unittest.TestCase):
 def test_original_rss_exception_first_and_record_failure_does_not_mask(self):
  fake=types.SimpleNamespace(RUSAGE_SELF=0,RUSAGE_CHILDREN=1,getrusage=lambda n:types.SimpleNamespace(ru_maxrss=(500000,30000)[n]))
  with patch.dict(sys.modules,{'resource':fake}):
   spec=importlib.util.spec_from_file_location('_rss_r20_test',P/'rss_failure_record.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
  error=ValueError('source-original host plus CLI cumulative512MiB');events=[]
  class Owned:
   cid=None;out=P
   def rss(self):events.append('original');raise error
  def write(path,value):events.append(value);raise OSError('recording denied')
  r.install(Owned,types.SimpleNamespace(write=write))
  with self.assertRaises(ValueError)as caught:Owned().rss()
  self.assertIs(caught.exception,error);self.assertEqual(events[0],'original');self.assertEqual(events[1]['aggregate_peak_rss_kib'],530000);self.assertEqual(events[1]['original_limit_kib'],524288)
 def test_prior_wrong_failure_and_created_cid_rejected_before_filesystem(self):
  import prior_empty_r19 as R
  def need(v,m):
   if not v:raise ValueError(m)
  base=dict(schema='deltalog.actual-owned-dispatch-smoke/v025',source=R.SOURCE,status='failed',primary=R.PRIMARY,secondary=[],all_created_containers_release_verified=True,owned_containers=[dict(stage=str(R.OPT/'cpu-preflight'),cid=None,exact_owned_release_verified=None)])
  source=dict(prepared_template=R.TEMPLATE,prepared_only=False,output_root=str(R.OPT))
  for mutate in('primary','created','pending','secondary'):
   o=copy.deepcopy(base)
   if mutate=='primary':o['primary']='different failure'
   if mutate=='created':o['owned_containers'][0]['cid']='a'*64
   if mutate=='pending':o['all_created_containers_release_verified']=False
   if mutate=='secondary':o['secondary']=['unreleased']
   documents={R.OWNER['path']:o,R.SOURCE['path']:source,R.JOURNAL['path']:{}}
   with self.assertRaises(ValueError):R.validate(types.SimpleNamespace(obj=lambda r:documents[r['path']],need=need),None)
 def test_no_large_index_dict_retained_and_atomic_baseline_precedes_validate(self):
  text=(P/'model_snapshot_budget.py').read_text(encoding='utf8')
  self.assertLess(text.index('baseline_before='),text.index('checked_e,proof=validate('));self.assertLess(text.index('checked_e,proof=validate('),text.index('baseline_after='))
  self.assertIn('STREAM.verify(phase[',text);self.assertNotIn("expected=[{k:v",text)
  self.assertIn('self.policy._firstdecode_final_verify(None)',text)
  self.assertIn('self.K.tree(phase[',text)
if __name__=='__main__':unittest.main()
