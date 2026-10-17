"""Actual original document chain; no mock of document predicates or hashes."""
import base64,copy,hashlib,json,types,unittest
from pathlib import Path
from unittest.mock import patch
import prior_released_empty_r20r1 as R
P=Path(__file__).resolve().parent

def need(v,m):
 if not v:raise ValueError(m)

def originals():
 fixture=json.loads((P/'R20R1_ORIGINAL_METADATA_FIXTURE.json').read_bytes());out={}
 for row in fixture['originals']:
  b=base64.b64decode(''.join(row['base64_chunks']),validate=True);r=row['ref'];need((len(b),hashlib.sha256(b).hexdigest())==(r['bytes'],r['sha256']),'actual original bytes/SHA')
  out[r['path']]=(r,json.loads(b))
 return fixture,out

class Prior(unittest.TestCase):
 def test_actual_six_originals_sole_released_CPU_not_model(self):
  fixture,rows=originals()
  def obj(r):
   expected,value=rows[r['path']];need(r==expected,'actual exact original Ref');return copy.deepcopy(value)
  proof=R.documents(types.SimpleNamespace(obj=obj,need=need))
  self.assertEqual(proof['sole_released_cpu'],R.CID);self.assertIs(proof['numeric_qualified'],False)
  self.assertEqual(tuple(fixture['empty']['stat'][k]for k in R.FIELDS),R.EMPTY);self.assertIs(fixture['candidate_dir_exists'],False)

 def test_wrong_source_hash_owner_or_CPU_release_reject(self):
  for defect in('source','noCID','moreCID','notreleased','postfence','NPU','ownerlabel','qualified','cleanup','poststate'):
   fixture,rows=originals();source=rows[R.SOURCE['path']][1];owner=rows[R.OWNER['path']][1];clean=rows[R.CLEANUP['path']][1];rec=rows[R.INSPECT['path']][1];v=json.loads(rec['stdout'])
   if defect=='source':source['prepared_template']['sha256']='0'*64
   elif defect=='noCID':owner['owned_containers'][0]['cid']=None
   elif defect=='moreCID':owner['owned_containers'].append(dict(owner['owned_containers'][0]))
   elif defect=='notreleased':owner['all_created_containers_release_verified']=False
   elif defect=='postfence':owner['post_work_verification']['metadata_after_hash']=False
   elif defect=='NPU':v[0]['HostConfig']['Devices']=[{}]
   elif defect=='ownerlabel':v[0]['Config']['Labels']['model-tuning-lab.owner']='other'
   elif defect=='qualified':owner['production_admitted']=True
   elif defect=='cleanup':clean['deleted']=True
   else:owner['post_work_verification']['current_owned_inspects'][0]['State']['Pid']=10
   rec['stdout']=json.dumps(v)
   def obj(r):
    rr,value=rows[r['path']];need(r==rr,'exact fixture Ref');return copy.deepcopy(value)
   with self.subTest(defect=defect),self.assertRaises((ValueError,KeyError)):R.documents(types.SimpleNamespace(obj=obj,need=need))
  fixture,rows=originals()
  def checked(r):
   rr,value=rows[r['path']];need(rr==r,'wrong actual Ref rejected');return value
  with patch.object(R,'SOURCE',dict(R.SOURCE,sha256='0'*64)),self.assertRaisesRegex(ValueError,'wrong actual Ref'):R.documents(types.SimpleNamespace(obj=checked,need=need))

 def test_actual_empty_guard_and_two_exact_old_roots_all_writer_gates(self):
  # Explicit proc/FS boundary fixture; NOT evidence of actual no-writers.
  scope=dict(CIDS=(),PHASES=(),SOURCE=None,leaf=None,CID=R.CID,__builtins__=__builtins__)
  exec("def no_writers():\n assert PHASES==('payload','control')\n assert [str(leaf(i)) for i in range(len(PHASES))]==[str(LEAF),str(OPT)]\n return {'software_boundary_only':True}\ndef inspect_all():\n assert CIDS==((CID,),)\n return [{'Id':CID}]\n",dict(scope,LEAF=R.LEAF,OPT=R.OPT),scope)
  K=types.SimpleNamespace(**scope)
  # Functions require globals in the same namespace as their implementation.
  K.__dict__.update(LEAF=R.LEAF,OPT=R.OPT)
  with patch.object(R,'documents',return_value={'numeric_qualified':False}),patch.object(R,'empty',return_value=R.EMPTY)as e:
   proof=R.validate(types.SimpleNamespace(need=need),K)
   self.assertEqual(proof['current_stopped_cpu'],[{'Id':R.CID}]);self.assertEqual(e.call_count,2)
  with patch.object(R,'documents',return_value={}),patch.object(R,'empty',side_effect=ValueError('candidate exists')),self.assertRaisesRegex(ValueError,'candidate'):
   R.validate(types.SimpleNamespace(need=need),K)

 def test_all_runtime_rechecks_and_original_R19_gate_retained(self):
  text=(P/'model_snapshot_budget.py').read_text();refs=(P/'firstdecode_refs.py').read_text()
  self.assertEqual(text.count('prior_released_empty_r20r1.validate('),3)
  self.assertEqual(text.count('prior_empty_r19.validate('),3)
  self.assertIn('prior_released_empty_r20r1.refs(O)',refs);self.assertIn('released=prior_released_empty_r20r1.validate(O,early)',refs)
  self.assertIn('self.policy._firstdecode_final_verify(None)',text);self.assertIn("tree=self.seal.read_tree",text)

if __name__=='__main__':unittest.main()
