"""Actual22569 observe + actual memory wrapper closure regression; software-only."""
import ast,datetime,hashlib,importlib.util,os,types,unittest,unittest.mock
from pathlib import Path
P=Path(__file__).resolve().parent
def load(name):
 s=importlib.util.spec_from_file_location('_guard013_'+name,P/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
O=load('ownership_observation')
def need(v,m):
 if not v:raise ValueError(m)
def ref(p):
 b=p.read_bytes();return dict(path=str(p.resolve()),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def memory_wrap(Owned):
 # Exact actual nested wrapper AST, not a retyped version of its call chain.
 tree=ast.parse((P/'memory_observer.py').read_bytes());install=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='install')
 node=next(n for n in install.body if isinstance(n,ast.FunctionDef)and n.name=='observe')
 maker=ast.FunctionDef(name='maker',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg='original_observe'),ast.arg(arg='snapshot')],kwonlyargs=[],kw_defaults=[],defaults=[]),body=[node,ast.Return(value=ast.Name(id='observe',ctx=ast.Load()))],decorator_list=[])
 scope={};exec(compile(ast.fix_missing_locations(ast.Module(body=[maker],type_ignores=[])),'actual_memory_wrapper_AST','exec'),scope)
 Owned.observe=scope['maker'](Owned.observe,lambda *a,**k:None)
def fixture(foreign=False):
 records=[];safety=P/'guard_test_inputs/actual_safety.py';helper=P/'guard_test_inputs/actual_helper.py'
 need(ref(safety)['sha256']=='8c83e08318b530c4d022b91bbacd34b12121b3380e1a14d32262c9a3875f6fa7','actual22569 source')
 need(ref(helper)['sha256']=='4ddd75d6ce7558f0131992da3a5514df43dfb4b33f45674722ba5769ecef5e20','actual40202 helper source')
 c=types.SimpleNamespace(sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest(),require=need)
 c.write=lambda p,v:(records.append((str(p),v))or dict(path=str(p)))
 now=datetime.datetime.now(datetime.timezone.utc);cid='a'*64
 proof=dict(pid=777,cgroup='/docker/'+('b'*64 if foreign else cid),started_utc=now.isoformat(),argv=['python','fixture'],start_ticks=1)
 H=types.SimpleNamespace(__file__=str(helper.resolve()),started=lambda p:p)
 H.protected=lambda text:[];H.gate_process=lambda pid:dict(proof)
 H.legacy=lambda:types.SimpleNamespace(process_rows=lambda text:[(5,0,777)])
 H.idle_one=lambda *a:None
 tree=ast.parse(safety.read_bytes());node=next(n for n in next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='Controller').body if isinstance(n,ast.FunctionDef)and n.name=='observe')
 scope=dict(H=H,c=c,PHYSICAL=(4,5,6,7),Path=Path,datetime=datetime,time=__import__('time'),os=os,json=__import__('json'),SMI='fixture-smi',DOCKER='fixture-docker',actual_hbm=lambda text,card:dict(physical=card),protected_boundary=lambda *a:{},fd_holders=lambda:[],device_map=lambda:{})
 exec(compile(ast.Module(body=[node],type_ignores=[]),str(safety.resolve()),'exec'),scope)
 class Controller:pass
 Controller.observe=scope['observe']
 class Owned(Controller):
  def __init__(self):
   self.out=P/'SOFTWARE_ONLY_NEVER_WRITTEN';self.cid=cid;self.h=H;self.server_started=now;self.protected=None;self.process_proofs=[];self.observations=[]
  def call(self,label,args,**kw):return dict(stdout='fixture'if label=='smi'else'',observed_utc=now.isoformat()),{}
  def resources(self,initial=False):return {}
 S=types.SimpleNamespace(Controller=Controller,H=H,__file__=str(safety.resolve()))
 return S,Owned,c,ref(safety),ref(helper),records
class Order(unittest.TestCase):
 def test_original010_order_bypasses_observer_and_validation_refuses(self):
  S,Owned,c,s,h,rows=fixture();memory_wrap(Owned);installed=O.install(S,c,s,h)
  with unittest.mock.patch.object(os,'readlink',return_value='/usr/bin/python3'):Owned().observe('source-fixture')
  self.assertFalse(any('ownership-before-guard-'in p for p,v in rows))
  with self.assertRaises(ValueError):O.validate_chain(S,Owned,installed)
 def test_repaired_order_actual_MRO_closure_records_owned_operands(self):
  S,Owned,c,s,h,rows=fixture();installed=O.install(S,c,s,h);memory_wrap(Owned);chain=O.validate_chain(S,Owned,installed)
  with unittest.mock.patch.object(os,'readlink',return_value='/usr/bin/python3'):Owned().observe('source-fixture')
  proof=[v for p,v in rows if 'ownership-before-guard-'in p]
  self.assertEqual(len(proof),1);self.assertTrue(all(x is True for x in proof[0]['operands'].values()));self.assertTrue(chain['guard_H_is_S_H'])
 def test_repaired_order_foreign_still_rejected_after_saved_operands(self):
  S,Owned,c,s,h,rows=fixture(True);installed=O.install(S,c,s,h);memory_wrap(Owned);O.validate_chain(S,Owned,installed)
  with unittest.mock.patch.object(os,'readlink',return_value='/usr/bin/python3'):
   with self.assertRaisesRegex(ValueError,'real foreign PID/UDA/start/program conflict'):Owned().observe('source-fixture')
  proof=[v for p,v in rows if 'ownership-before-guard-'in p]
  self.assertEqual(len(proof),1);self.assertFalse(proof[0]['operands']['cgroup_matches'])
if __name__=='__main__':unittest.main()
