"""Actual fixture predicate -> producer Diagnostics -> independent consumers.

CPU software callables/temporary artifacts only. No test object is an actual
NPU producer, qualifier, or persisted success receipt.
"""
import ast,copy,importlib.util,json,math,sys,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import bridge_io as C,collection_policy as K
from qwen36_deltalog_fresh import native_fixture as F

def complete(steps=16):
 records=[]
 for b in(1,16):
  records.extend(dict(kind='dead_flush',batch=b)for _ in range(2));records.extend(dict(kind='mixed',batch=b,step=i)for i in range(steps));records.extend(dict(kind='copy',batch=b,length=i)for i in(1,7))
 refs=[dict(path='/software-only/raw-%03d.pt'%i,bytes=1,sha256='%064d'%i)for i in range(2*steps+31)]
 return dict(schema='deltalog.actual-fresh-bridge/v5',source={'software-only-source':1},primary=None,steps=steps,collection_policy=K.POLICY,NPU=True,graph=False,fullmodel=False,records=records,actual_sidecar_records=refs,actual_mixed_sidecar_records=refs[:2*steps],boundary_controls=[dict(case=c,raw=refs[2*steps+i])for i,c in enumerate(('normal','tiny','subnormal','positive-zero','negative-zero','cancellation','overflow','finite-final-normalized-query','finite-final-unscaled-query','cancellation-permuted','gqa-vtile-witness','original-B16-step80','original-B16-step137'))])

def actual_diagnostics():
 tree=ast.parse((P/'producer.py').read_bytes());node=next(n for n in ast.walk(tree)if isinstance(n,ast.ClassDef)and n.name=='Diagnostics');ns=dict(C=C,R=SimpleNamespace(OUTPUT_LIMIT=.00303),time=time,start=time.monotonic(),sr={'software-only-source':1},pr={'software-only-plan':1},records=[])
 saved=[]
 def save(name,value):saved.append(copy.deepcopy(value));return dict(path='/software-only/'+name,bytes=1,sha256='a'*64)
 ns['save']=save;exec(compile(ast.Module(body=[node],type_ignores=[]),str(P/'producer.py'),'exec'),ns)
 return ns['Diagnostics'],ns,saved

class Contract(unittest.TestCase):
 def flags(self):return {k:True for k in K.FLAGS}
 def test_actual_fixture_guard_keeps_default_and_producer_optin(self):
  Diag,ns,saved=actual_diagnostics();d=Diag(16,{});d.initial(dict(batch=16))
  self.assertTrue(F.collection_reject(.0036231884057971015,1.4558461459069486e-7,self.flags(),None,.00303,7.92e-7))
  self.assertFalse(F.collection_reject(.0036231884057971015,1.4558461459069486e-7,self.flags(),d,.00303,7.92e-7))
  d.step((16,'eager','mixed-prefill-decode'),9,None,None,1.4558461459069486e-7,.0036231884057971015,lambda:dict(actual_raw_retained=True),{})
  self.assertTrue(saved[-1]['actual_raw_retained']);self.assertIn('initial_anchor_ref',saved[-1]);self.assertFalse(ns['records'][-1]['producer_old_BF16_point_pass']);self.assertTrue(ns['records'][-1]['producer_old_BF16_point_diagnostic_only'])
 def test_every_hard_state_finite_byte_gate_still_stops(self):
  Diag,_,_=actual_diagnostics();d=Diag(1,{})
  self.assertFalse(F.collection_reject(.004,7.920001e-7,self.flags(),d,.00303,7.92e-7))
  for value in(float('nan'),float('inf'),-1.,True):self.assertTrue(F.collection_reject(.004,value,self.flags(),d,.00303,7.92e-7))
  for key in K.FLAGS:
   row=self.flags();row[key]=False;self.assertTrue(F.collection_reject(.004,1e-8,row,d,.00303,7.92e-7),key)
 def test_real_fixture_calls_guard_not_only_string_contract(self):
  # Execute the actual source's guard IF node, preserving its real raise and
  # capture callback rather than checking a string or reimplementing the gate.
  tree=ast.parse((P/'qwen36_deltalog_fresh/native_fixture.py').read_bytes());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='mixed_case')
  node=next(n for n in ast.walk(fn)if isinstance(n,ast.If)and isinstance(n.test,ast.Call)and isinstance(n.test.func,ast.Name)and n.test.func.id=='collection_reject')
  Diag,_,_=actual_diagnostics();d=Diag(1,{});d.last={'retained':'software-only'}
  ns=dict(collection_reject=F.collection_reject,output_error=.004,state_error=1e-8,row=self.flags(),diagnostics=d,OUTPUT_LIMIT=.00303,STATE_LIMIT=7.92e-7,batch=1,mode='eager',step=9)
  code=compile(ast.Module(body=[node],type_ignores=[]),str(P/'qwen36_deltalog_fresh/native_fixture.py'),'exec');exec(code,ns)
  ns['state_error']=8e-7
  exec(code,ns)  # Across-history state only is deferred; changed decode/flush remain independent hard gates.
 def test_complete160_345_and_partial_oldfailure_reject_before_children(self):
  p=complete(160);self.assertTrue(K.require_complete(C,p,p['source']))
  for kind in('primary','gap','sidecar','mixed','copy','policy'):
   q=copy.deepcopy(p)
   if kind=='primary':q['primary']='retained original firstfail'
   elif kind=='gap':q['records'].pop(5)
   elif kind=='sidecar':q['actual_sidecar_records'].pop()
   elif kind=='mixed':q['actual_mixed_sidecar_records'].pop()
   elif kind=='copy':q['records'][-1]['length']=6
   else:q['collection_policy']=dict(K.POLICY,qualified=True)
   with self.assertRaises(ValueError):K.require_complete(C,q,p['source'])
 def test_actual_independent_precast_failure_not_overridden_by_collection(self):
  import torch,direct_round as D,oracle as R,domain_consumer as Domain
  from test_collector_abi import Contract as Capture
  with tempfile.TemporaryDirectory()as td:
   _,side,raw=Capture().run_fixture(Path(td));self.assertTrue(all(x['request_pass']for x in Domain.per_request_metrics(torch,R,raw,D)))
   side['actual_precast_FP32'].fill_(1.);path=Path(td)/'precast-fail.pt';torch.save(side,path);raw['captures']['decode'][0]['actual_sidecar043']=C.ref(path);raw['native_output'][0,0,0]=.00390625
   actual_rows=Domain.per_request_metrics(torch,R,raw,D);self.assertFalse(actual_rows[0]['request_pass']);self.assertTrue(any(not x['old_point_pass']for x in actual_rows))
   # The real pair entry can retain completed collection but must publish
   # diagnostic_capture_complete=False when the independent domain fails.
   spec=importlib.util.spec_from_file_location('_actual_collection_pair',P/'consume_pair.py');G=importlib.util.module_from_spec(spec);spec.loader.exec_module(G)
   producer=complete();sr=producer['source'];pr={'software-only-producer':1};out=Path(td)/'PAIR.json';old=dict(schema='deltalog.fresh-bridge-consumption/v5',source=sr,producer=pr,pass_gate=False,primary='old point FAIL retained')
   anchors={}
   for b in(1,16):
    anchor=Path(td)/('anchor-%d.json'%b);C.write(anchor,dict(software_only=True));anchors[str(b)]=C.ref(anchor)
   domain=dict(anchors=anchors,domain_checks_pass=False,missing_evidence=[],failures=[dict(actual_precast=False)],validation_contract={},original_strict_result_preserved=dict(pass_gate=False,primary=old['primary']))
   realobj=G.C.obj
   def objects(r):return producer if r==pr else realobj(r)
   def child(argv,**kw):
    target=Path(argv[argv.index('--output')+1]);script=argv[argv.index('--script')+1];G.C.write(target,old if script=='consume.py'else domain);return SimpleNamespace(returncode=0,stdout='',stderr='')
   with patch.object(G.C,'source',return_value={}),patch.object(G.C,'obj',side_effect=objects),patch.object(G.subprocess,'run',side_effect=child),patch.object(sys,'argv',[str(P/'consume_pair.py'),'--execute','--source-ref',json.dumps(sr),'--producer-ref',json.dumps(pr),'--output',str(out)]):G.main()
   verdict=json.loads(out.read_bytes());self.assertFalse(verdict['diagnostic_capture_complete']);self.assertFalse(verdict['domain_checks_pass']);self.assertFalse(verdict['pass_gate']);self.assertFalse(verdict['model_ready']);self.assertFalse(verdict['performance_ready']);self.assertEqual(verdict['original_strict_result_preserved']['pass_gate'],False)
if __name__=='__main__':
 import torch
 torch.set_num_threads(1);unittest.main()
