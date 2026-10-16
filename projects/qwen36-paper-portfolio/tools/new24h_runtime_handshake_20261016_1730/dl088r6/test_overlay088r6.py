import copy,importlib.util,json,sys,types,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import bridge_io as C,closed_overlay088r6 as O,storage_bridge121 as B,storage061 as S
class Tests(unittest.TestCase):
 def fixture(self):
  refs=[B.ACTUAL_GENERATION,O.SIXTEEN,O.BASE];values={};rows=[]
  values[refs[0]['path']]=dict(root=O.ROOT.as_posix(),authority_ref={'exact':'authority'},reservations=[])
  for i,r in enumerate(refs[1:]):
   rows=rows+[dict(leaf=O.LEAVES[i].as_posix(),stage='cpu'if i==0 else'numeric',budget_bytes=(1 if i==0 else 33)*O.G)]
   values[r['path']]=dict(root=O.ROOT.as_posix(),authority_ref={'exact':'authority'},reservations=rows,previous_ledger_ref=refs[i],storage069_template_ref=B.SOURCE121,sealed_evidence_ref=B.ACTUAL_EVIDENCE)
  proxy=types.SimpleNamespace(obj=lambda r:values[r['path']],ref=lambda p:next(r for r in refs if r['path']==p.as_posix()),need=C.need)
  return refs,values,proxy
 def test_actual16_17_typed_chain(self):
  from unittest.mock import patch
  refs,v,c=self.fixture()
  with patch.object(B,'generations',return_value=[Path(r['path'])for r in refs]):self.assertEqual(O.history(c)[0],O.BASE)
 def test_history_wrong_context_missing_generation_prefix_rejected(self):
  from unittest.mock import patch
  for mutate in('context','prefix','missing'):
   refs,v,c=self.fixture()
   if mutate=='context':v[O.BASE['path']]['storage069_template_ref']={}
   if mutate=='prefix':v[O.BASE['path']]['reservations'][0]['budget_bytes']=0
   if mutate=='missing':refs=refs[:1]+refs[2:]
   with patch.object(B,'generations',return_value=[Path(r['path'])for r in refs]):
    with self.assertRaises(ValueError):O.history(c)
 def test_original_failed_exit1_not_promoted(self):
  states=[dict(Id=cid,ExecIDs=None,State=dict(Pid=0,Running=False,Status='exited',OOMKilled=False,ExitCode=i))for i,cid in enumerate(O.CIDS)]
  O.states(C,states)
  for key,value in(('Pid',99),('Running',True),('OOMKilled',True),('ExitCode',0)):
   bad=copy.deepcopy(states);bad[1]['State'][key]=value
   with self.assertRaises(ValueError):O.states(C,bad)
 def test_missing_overlay_refuses_before_any_read(self):
  with self.assertRaisesRegex(ValueError,'Ref3 mandatory'):O.validate(C,{},None)
 def test_new67GiB_plus_actual_closed_is_not_double_reserved(self):
  self.assertLess(S.committed_bytes(6451449660,[6450000000,0,0,0],[6450000000,O.G,33*O.G,33*O.G]),80*O.G)
  self.assertGreater(S.committed_bytes(6451449660,[6450000000,0,0,0],[34*O.G,O.G,33*O.G,33*O.G]),80*O.G)
 def test_canonical_no_writer_inverse_and_exact_CID_inspection(self):
  donor=(P.parent/'deltalog-closed-storage-new24h-119'/'sealed119.py')if sys.platform!='linux'else Path(B.SOURCE119['path']).parent/'sealed119.py';sp=importlib.util.spec_from_file_location('actual119software',donor);k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
  q=O.observer(types.SimpleNamespace(prior=lambda:k),{'path':'/exact/R5/SOURCE.json'})
  self.assertEqual(q.inspect_all.__code__,k.inspect_all.__code__)
  self.assertIn('range',q.no_writers.__code__.co_names);self.assertIn(2,q.no_writers.__code__.co_consts)
if __name__=='__main__':unittest.main()
