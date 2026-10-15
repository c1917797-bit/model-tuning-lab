"""Actual frozen control generator→collector→domain aggregate on CPU ONLY.

CPUProxy explicitly rewrites device allocation and supplies synthetic operators.
It is software ABI evidence, never Ascend FTZ/kernel correctness evidence.
"""
import ast,copy,hashlib,sys,tempfile,types,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
import torch,npu_controls,sidecar_capture,sidecar_audit,raw_codec,oracle as R,precast as P,direct_round as D,domain_consumer as C
torch.set_num_threads(1)
class CPUProxy:
 npu=types.SimpleNamespace(synchronize=lambda:None)
 def __getattr__(self,name):
  fn=getattr(torch,name)
  if name in('zeros','ones','full','empty','tensor'):
   def alloc(*a,**kw):
    if str(kw.get('device','')).startswith('npu:'):kw['device']='cpu'
    return fn(*a,**kw)
   return alloc
  return fn
def allocate(initial):
 slots=len(initial)
 return dict(base=initial.clone(),k_log=torch.zeros(slots,4,7,128,dtype=torch.bfloat16),u_log=torch.zeros(slots,12,7,128),lambda_log=torch.zeros(slots,12,16),decay=torch.zeros(slots,12,16),length=torch.zeros(slots,12,16,dtype=torch.int32))
def readout(args):
 q,k,v,g,beta,base,kl,ul,lam,dec,length,seq,ids=args;y=torch.empty((len(ids),12,128),dtype=torch.float32)
 for j,s in enumerate(ids.tolist()):
  for h in range(12):y[j,h]=(base[s,h]@q[j,h//3].float())*(128**-.5)
  length[s,:,0]=1
 return y
def production(*args):return D.round_bf16(torch,readout(args).double())
def diagnostic(*args):
 y=readout(args[:-1]);args[-1].copy_(y);return D.round_bf16(torch,y.double())
def aggregate_function():
 source=(ROOT/'domain_consumer.py').read_text(encoding='utf8');tree=ast.parse(source);run=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='run');body=[];taking=False
 for n in run.body:
  if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='records'for t in n.targets):taking=True
  if taking:
   if isinstance(n,ast.For)and isinstance(n.target,ast.Name)and n.target.id=='record':break
   body.append(n)
 body.append(ast.Return(ast.Name('sidecar_rows',ast.Load())))
 f=ast.FunctionDef(name='actual_aggregate',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg=x)for x in('torch','R','producer')],kwonlyargs=[],kw_defaults=[],defaults=[]),body=body,decorator_list=[])
 module=ast.fix_missing_locations(ast.Module(body=[f],type_ignores=[]));scope=dict(vars(C));exec(compile(module,str(ROOT/'domain_consumer.py')+'::actualcontrolblock','exec'),scope);return scope['actual_aggregate']
class Aggregate(unittest.TestCase):
 def fixture(self,root):
  store=raw_codec.Store(torch,root,32*1024**3);capture=sidecar_capture.Capture(CPUProxy(),production,diagnostic);capture.sink=lambda n,v:store.write(root/n,v)
  controls=npu_controls.run(CPUProxy(),types.SimpleNamespace(allocate_state=allocate),capture)
  original=raw_codec.install(torch)
  try:normal=torch.load(controls[0]['raw']['path'],weights_only=False)['before']
  finally:torch.load=original
  for j in range(50):capture(*[x.clone()for x in normal]);capture.take('mixed'if j<32 else None)
  p=dict(records=[],steps=16,actual_sidecar_records=capture.records,actual_mixed_sidecar_records=capture.mixed_records,boundary_controls=controls)
  return p,store
 def test_actual_seven_control_aggregate(self):
  with tempfile.TemporaryDirectory()as d:
   p,store=self.fixture(Path(d));original=raw_codec.install(torch)
   try:
    rows=aggregate_function()(torch,R,p);self.assertEqual(len(rows),57)
    controls={x['raw']['path']:x['case']for x in p['boundary_controls']};by={controls[x['raw']['path']]:x for x in rows if x['raw']['path']in controls}
    self.assertEqual(set(by),set(npu_controls.CASES));self.assertTrue(all(x['passed']for x in by.values()));self.assertFalse(by['overflow']['actual_precast']['finite']);self.assertTrue(by['overflow']['expected_overflow_rejection'])
   finally:torch.load=original
 def test_FTZ_is_definite_failure_not_zero_truth(self):
  with tempfile.TemporaryDirectory()as d:
   p,store=self.fixture(Path(d));original=raw_codec.install(torch)
   try:
    sub=next(x for x in p['boundary_controls']if x['case']=='subnormal');s=torch.load(sub['raw']['path'],weights_only=False);s['actual_precast_FP32'].zero_();s['production_output'].zero_();s['debug_output'].zero_()
    verdict=sidecar_audit.audit(torch,R,P,s);self.assertFalse(verdict['passed']);self.assertEqual(verdict['state_errors'],[0.]);self.assertEqual(verdict['actual_precast']['peak'],1.);self.assertEqual(verdict['actual_precast']['relative_l2'],1.)
   finally:torch.load=original
 def test_overflow_with_bad_state_is_not_accepted_rejection(self):
  with tempfile.TemporaryDirectory()as d:
   p,store=self.fixture(Path(d));original=raw_codec.install(torch)
   try:
    rr=next(x['raw']for x in p['boundary_controls']if x['case']=='overflow');s=torch.load(rr['path'],weights_only=False);s['after'][5][0].fill_(float('nan'));s['debug_after'][5][0].fill_(float('nan'))
    with self.assertRaisesRegex(ValueError,'finite represented state'):sidecar_audit.audit(torch,R,P,s,overflow=True)
   finally:torch.load=original
 def test_finite_wrong_state_original_counterexample_and_aggregate_reject(self):
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);p,store=self.fixture(root);original=raw_codec.install(torch)
   try:
    item=next(x for x in p['boundary_controls']if x['case']=='overflow');old=item['raw'];s=torch.load(old['path'],weights_only=False);s['after'][5][0].zero_();s['debug_after'][5][0].zero_()
    # Same real frozen API that previously returned passed=True,state_errors=[1.].
    v=sidecar_audit.audit(torch,R,P,s,overflow=True);self.assertEqual(v['state_errors'],[1.]);self.assertFalse(v['passed'])
    rr=store.write(root/'wrong-overflow-state.pt',s);item['raw']=rr;p['actual_sidecar_records']=[rr if x==old else x for x in p['actual_sidecar_records']]
    with self.assertRaisesRegex(ValueError,'all actual production/debug/precast call predicates'):aggregate_function()(torch,R,p)
   finally:torch.load=original
if __name__=='__main__':unittest.main()
