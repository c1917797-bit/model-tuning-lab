import copy,json,subprocess,sys,tempfile,unittest
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import prepare_inputs as M

class Inputs(unittest.TestCase):
 def fixture(self):
  sr={'actual_fixture_only':'not qualification'};ps={'payload_fixture_only':'not qualification'};cid='a'*64;root='/payload'
  parent=dict(source=sr,status='failed',primary='actual deliberate child failure fixture',secondary=[],elapsed=1200,cleanup_seconds=100,post_work_verification=dict(source_after=True,metadata_after_hash=True,registered_cap_seconds=900,actual_cap_seconds=900),all_created_containers_release_verified=True,owned_containers=[dict(stage='/model/candidate',cid=cid,exact_owned_release_verified=True)])
  x=dict(Id=cid,Image=M.IMAGE,State=dict(Running=False,Pid=0,OOMKilled=False),ExecIDs=None)
  loaded=dict(source=sr,rows=[]);reports=[]
  for rank in range(4):
   pid=100+rank;ns=10+rank;start=1000+rank
   loaded['rows'].append(dict(rank=rank,logical=rank,physical=rank+4,namespace_pid=ns,actual_host_process=dict(pid=pid,start_ticks=start)))
   reports.append((dict(path=root+'/FIRST-DECODE-'+str(ns)+'/FIRST-DECODE-REPORT.json'),dict(source=ps,model_source=sr,namespace_pid=ns,domain=dict(rank=rank,physical=rank+4,cid=cid,host_pid=pid,start_ticks=start))))
  return [sr,ps,parent,x,loaded,dict(cid=cid),reports,root]
 def test_four_actual_identity_shapes_metadata_only(self):M.validate_rows(*self.fixture())
 def test_missing_duplicate_or_old_rank_rejected(self):
  for change in('missing','duplicate','oldpid','wrongroot','oldsource','wrongcandidate','parentpass','secondary','missingfence','overtime'):
   x=self.fixture()
   if change=='missing':x[6].pop()
   elif change=='duplicate':x[6][3]=copy.deepcopy(x[6][0])
   elif change=='oldpid':x[6][0][1]['domain']['start_ticks']-=1
   elif change=='wrongroot':x[6][0][0]['path']='/old/FIRST-DECODE-10/FIRST-DECODE-REPORT.json'
   elif change=='oldsource':x[6][0][1]['model_source']={'old':True}
   elif change=='wrongcandidate':x[2]['owned_containers'][0]['cid']='b'*64
   elif change=='parentpass':x[2]['status']='pass'
   elif change=='secondary':x[2]['secondary']=['failed final fence']
   elif change=='missingfence':x[2]['post_work_verification']['source_after']=False
   else:x[2]['elapsed']=2701
   with self.subTest(change=change),self.assertRaises(ValueError):M.validate_rows(*x)
 def test_wrong_hash_pending_and_exclusive_output(self):
  with self.assertRaises(ValueError):M.checked(None)
  with tempfile.TemporaryDirectory()as d:
   p=Path(d)/'input.json';r=M.write(p,dict(metadata_fixture=True));self.assertEqual(M.obj(r),dict(metadata_fixture=True))
   with self.assertRaises(FileExistsError):M.write(p,{})
   r['sha256']='0'*64
   with self.assertRaises(ValueError):M.checked(r)
 def test_fresh_I_off_missing_actual_refs(self):
  path=str(Path(M.__file__).resolve())
  x=subprocess.run([sys.executable,'-I','-B',path],capture_output=True,text=True);self.assertEqual(x.returncode,0,x.stderr);self.assertEqual(json.loads(x.stdout),dict(enabled=False,NPU=False))
  x=subprocess.run([sys.executable,'-I','-B',path,'--execute'],capture_output=True,text=True);self.assertNotEqual(x.returncode,0);self.assertIn('actual three Ref3 required',x.stderr)
 def test_exact_R19_pin_old_source_rejected(self):
  import difflib,hashlib
  inv=json.loads((Path(__file__).parent/'INVERSE.json').read_bytes())
  self.assertEqual(''.join(difflib.restore(inv['whole_ndiff'],2)).encode(),Path(M.__file__).read_bytes())
  oldbytes=''.join(difflib.restore(inv['whole_ndiff'],1)).encode();self.assertEqual(hashlib.sha256(oldbytes).hexdigest(),inv['original_collector']['sha256'])
  self.assertEqual(M.MODEL_TEMPLATE,{'path': '/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-first-real-decode-owned-renew24h-v1-101-repair19-20261017-001/SOURCE_TEMPLATE.json', 'bytes': 234563, 'sha256': 'adca9c401d3beaa22fb560c9be9a0f8ec659bacf449f608502877dde32d1ea89'})
  self.assertTrue(M.OUTPUT.as_posix().endswith('/run-dl-firstdecode-input-R19-MAIN-001'))
  self.assertEqual(M.PAYLOAD,{'path': '/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-selected-firstdecode-renew24h-20261017-001/SOURCE_MANIFEST.json', 'bytes': 17250, 'sha256': '413dfbf5b8dd3444cfafc19c6ce3e1e49cbb5414fb4ee1202f91a924cb232a29'})
  self.assertEqual(M.KEYS,{'schema','model_source','payload_source','owner_ref','inspect_ref','loaded_ref','reports_ref'})
  old=dict(prepared_only=False,prepared_template=dict(path='/old/R18/SOURCE_TEMPLATE.json',bytes=226639,sha256='87c5ed0c880f07ad03f6284ba6190e7bebc47c324dbbfac6d143467fd3b9942d'))
  with patch.object(M,'obj',return_value=old),self.assertRaisesRegex(ValueError,'exact bound R19'):M.prepare({'software':'old-pin-negative-only'},None,None)
  with self.assertRaises(ValueError):M.prepare(None,None,None)

if __name__=='__main__':unittest.main()
