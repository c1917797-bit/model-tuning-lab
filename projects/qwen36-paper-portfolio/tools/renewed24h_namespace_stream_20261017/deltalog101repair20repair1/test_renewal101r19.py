"""Renewal-only controls; no historical numeric PASS is manufactured."""
import ast,hashlib,importlib.util,json,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
import renewed_closed_reader101r19 as R

class Renewal(unittest.TestCase):
 def test_authority_exact_scope_and_cut(self):
  # Source-bound actual authority content, explicitly local software alias.
  a=P/'renewal_authority_snapshot.json';b=a.read_bytes()
  alias={R.AUTHORITY['path']:a,R.REUSE['path']:P/'renewal_reuse_scope_snapshot.json'}
  with patch.object(R,'Path',side_effect=lambda x:alias.get(x,Path(x))):
   with patch.object(R.time,'time',return_value=R.START):self.assertFalse(R.check()['numeric_qualified'])
   for x in(R.START-1,R.CUT):
    with patch.object(R.time,'time',return_value=x):
     with self.assertRaisesRegex(ValueError,'current window'):R.check()
   with patch.object(R,'AUTHORITY',dict(path=a.as_posix(),bytes=len(b),sha256='0'*64)):
    with self.assertRaisesRegex(ValueError,'exact renewed'):R.check()
 def test_full_body_inverse_and_only_validate_installed(self):
  original=(P/'historical_capture_closed2.py').read_bytes();s=types.ModuleType('_historical');s.__file__=(P/'historical_capture_closed2.py').as_posix();exec(compile(original,s.__file__,'exec'),s.__dict__)
  before=(s.capture,s.main,s.canonical,s.prior_policy);r=dict(path=s.__file__,bytes=len(original),sha256=hashlib.sha256(original).hexdigest())
  R.install(s,r);self.assertEqual(before,(s.capture,s.main,s.canonical,s.prior_policy))
  # The live derived body gates the new clock BEFORE touching historical IO.
  with patch.object(R,'check',side_effect=ValueError('new authority denied')):
   # Globals captured the check callable, not a caller-supplied boolean.
   pass
  calls=[]
  s.validate.__globals__['_renewed_authority_check']=lambda:calls.append('new-authority')
  s.validate.__globals__['canonical']=lambda sr:(_ for _ in()).throw(ValueError('actual old source boundary'))
  with self.assertRaisesRegex(ValueError,'actual old source boundary'):s.validate(None,None)
  self.assertEqual(calls,['new-authority'])
  self.assertIn('_renewed_authority_check',s.validate.__code__.co_names)
  self.assertIs(s.readset.__globals__['validate'],s.validate)
 def test_binder_and_lease_same_adapter_and_guard_order(self):
  f=(P/'firstdecode_refs.py').read_text(encoding='utf8');o=(P/'firstdecode_owner.py').read_text(encoding='utf8')
  self.assertLess(f.index('readonly_guard.install(seal)'),f.index('renewal.install(seal'))
  for text in(f,o):self.assertIn("renewal.install(seal,sm['files']['capture_closed2.py'])",text)
  self.assertIn('types.FunctionType(self.seal.validate.__code__,scope',(P/'model_snapshot_budget.py').read_text(encoding='utf8'))
 def test_math_unchanged_and_no_time_patch(self):
  text=(P/'renewed_closed_reader101r19.py').read_text(encoding='utf8');self.assertNotIn('time.time=',text);self.assertNotIn('time.time =',text)
  snap=json.loads((P/'renewal_math_anchors.json').read_bytes())
  for name,r in snap.items():
   b=(P/name).read_bytes();self.assertEqual((len(b),hashlib.sha256(b).hexdigest()),(r['bytes'],r['sha256']))
if __name__=='__main__':unittest.main()
