import ast,copy,hashlib,json,types,unittest
from pathlib import Path
import prior_released_empty_r21 as R
from test_stream_closed_tree import current_mm_peak
P=Path(__file__).resolve().parent
def need(v,s):
 if not v:raise ValueError(s)
class Fixes(unittest.TestCase):
 def test_current_mm_HWM_strict_no128_limit_change(self):
  self.assertEqual(current_mm_peak('VmRSS: 100 kB\nVmHWM:\t16384 kB\n'),16*2**20)
  for s in('VmRSS: 1 kB','VmHWM: 1 MB','VmHWM: -1 kB','VmHWM: 0 kB','VmHWM: 1 kB\nVmHWM: 2 kB'):
   with self.assertRaises(ValueError):current_mm_peak(s)
  text=(P/'test_stream_closed_tree.py').read_text();self.assertIn("self.assertLess(v['actual_process_peak_bytes'],128*1024**2)",text);self.assertIn('legacy_ru_maxrss_bytes',text)
 def test_actual_R21_six_document_chain_and_original_FAIL(self):
  source=json.loads((P/'software_dependencies/R21_SOURCE_MANIFEST.json').read_bytes());owner=json.loads((P/'software_dependencies/R21_RESULT.json').read_bytes());journal=json.loads((P/'software_dependencies/R21_JOURNAL.json').read_bytes());cleanup=json.loads((P/'software_dependencies/R21_CLEANUP.json').read_bytes());receipt=json.loads((P/'software_dependencies/R21_INSPECT.json').read_bytes())
  # Same actual baseline ledger was frozen in the old exact six-document set.
  import base64
  old=json.loads((P/'R20R1_ORIGINAL_METADATA_FIXTURE.json').read_bytes());base=next(json.loads(base64.b64decode(''.join(x['base64_chunks'])))for x in old['originals']if x['ref']==R.BASE)
  values={R.SOURCE['path']:(R.SOURCE,source),R.OWNER['path']:(R.OWNER,owner),R.JOURNAL['path']:(R.JOURNAL,journal),R.CLEANUP['path']:(R.CLEANUP,cleanup),R.INSPECT['path']:(R.INSPECT,receipt),R.BASE['path']:(R.BASE,base)}
  def obj(r):
   expected,value=values[r['path']];need(r==expected,'exact actual Ref');return copy.deepcopy(value)
  proof=R.documents(types.SimpleNamespace(obj=obj,need=need));self.assertEqual(proof['sole_released_cpu'],R.CID);self.assertIs(proof['numeric_qualified'],False);self.assertFalse(proof['candidate_created'])
  owner['all_created_containers_release_verified']=False
  with self.assertRaises(ValueError):R.documents(types.SimpleNamespace(obj=obj,need=need))
 def test_real_heavy_bind_order_before_closed_and_Guard_body_unchanged(self):
  tree=ast.parse((P/'bind_source.py').read_bytes());main=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='main');calls=[n for n in ast.walk(main)if isinstance(n,ast.Call)]
  gate=next(n for n in calls if isinstance(n.func,ast.Attribute)and isinstance(n.func.value,ast.Name)and n.func.value.id=='EARLY'and n.func.attr=='require');closed=next(n for n in calls if isinstance(n.func,ast.Attribute)and n.func.attr=='bind_closed');self.assertLess(gate.lineno,closed.lineno)
  fixture=json.loads((P/'R22_FIX_EVIDENCE.json').read_bytes());self.assertEqual(hashlib.sha256((P/'readonly_binder_guard.py').read_bytes()).hexdigest(),fixture['unchanged_guard']['sha256'])
 def test_missing_actual_sameimage_receipt_refuses_not_prepared_bool(self):
  import early_software_gate22 as E
  with self.assertRaises(ValueError):E.require(types.SimpleNamespace(need=need),dict(early_software_policy=dict(prepared_owner_source=None)),{})
if __name__=='__main__':unittest.main()
