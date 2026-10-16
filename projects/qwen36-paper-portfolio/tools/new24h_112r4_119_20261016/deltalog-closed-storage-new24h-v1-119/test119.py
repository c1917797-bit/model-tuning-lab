import importlib.util,json,sys,unittest,types
from unittest.mock import patch
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import sealed119 as S
class Tests(unittest.TestCase):
 def test_exact_current_commitment_requires_seal(self):
  v=json.loads((P.parent/'deltalog088r2-retry002-ticket/MAIN_CURRENT_LEDGER_20261016.json').read_bytes());d=next(x for x in v['documents']if(x['ref']['bytes'],x['ref']['sha256'])==(S.BASE['bytes'],S.BASE['sha256']));self.assertEqual(len(d['value']['reservations']),9)
  pending=sum(x['budget_bytes']for x in d['value']['reservations'][6:]);self.assertEqual(pending,67*S.G);self.assertGreater(pending+33*S.G,80*S.G)
 def test_exact_four_original_cids_not_three(self):
  self.assertEqual([len(x)for x in S.CIDS],[1,2,1]);self.assertEqual(len(set(x for row in S.CIDS for x in row)),4)
 def test_failed_cleanup_not_relabelled(self):
  text=(P/'sealed119.py').read_text();self.assertIn('old_cleanup_failures_preserved=True',text);self.assertNotIn("c['resource_release_verified']is True",text);self.assertIn("s['Pid']==0",text);self.assertIn("not v.get('ExecIDs')",text)
 def test_80_100_are_unchanged(self):
  self.assertIn('<=80*G',(P/'sealed119.py').read_text());self.assertIn('>=100*G',(P/'sealed119.py').read_text())
 def test_actual_inspect_reader_missing_live_exec_rejected(self):
  values=[dict(Id=cid,State=dict(Status='exited',Running=False,Pid=0,OOMKilled=False,ExitCode=137),ExecIDs=None)for row in S.CIDS for cid in row]
  def response(*a,**k):
   self.assertEqual(a[0][:4],['/usr/bin/prlimit','--as=unlimited','--','/usr/bin/docker']);self.assertEqual(a[0][4],'inspect');self.assertEqual(k['timeout'],20)
   return types.SimpleNamespace(returncode=0,stdout=json.dumps(values).encode(),stderr=b'')
  with patch.object(S.subprocess,'run',side_effect=response):
   self.assertEqual(len(S.inspect_all()),4)
   values[0]['State']['Pid']=123
   with self.assertRaises(ValueError):S.inspect_all()
   values[0]['State']['Pid']=0;values[0]['ExecIDs']=['foreign']
   with self.assertRaises(ValueError):S.inspect_all()
   values[0]['ExecIDs']=None;values.pop()
   with self.assertRaises(ValueError):S.inspect_all()
if __name__=='__main__':unittest.main()
