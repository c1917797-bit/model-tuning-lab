"""Software controls only. Synthetic join fixtures are never NPU receipts."""
import copy,importlib.util,io,json,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('composite022',P/'composite.py');C=importlib.util.module_from_spec(s);s.loader.exec_module(C)
SUMMARY=P/'fixtures/actual019-summary.json'
OLD=P/'fixtures/actual016002-owner.json'
ERROR=P/'fixtures/actual016002-error.json'
class Controls(unittest.TestCase):
 def valid_audit(self):
  # Actual report header/regression with explicit synthetic324 test-only rows.
  a=json.loads(SUMMARY.read_bytes())['audit_summary']
  a['records']=[dict(phase=p,batch=b,step=t,passed=True,checks=dict.fromkeys(C.COMMON_CHECKS|({'initial_recipe'}if t==0 else set()),True))for p,b,n in(('smoke',16,4),('full',1,160),('full',16,160))for t in range(n)]
  return a
 def bad(self,f,*args):
  with self.assertRaises((ValueError,KeyError,TypeError)):f(*args)
 def test_only_observed_019_gap(self):
  a=self.valid_audit();C.strict019(a)
  for edit in('false324','missing324','duplicate','extra_false137','missing137','removedcheck137','upgrade019'):
   b=copy.deepcopy(a)
   if edit=='false324':b['records'][61]['checks']['inactive']=False
   elif edit=='missing324':del b['records'][61]['checks']['inactive']
   elif edit=='duplicate':b['records'][61]=copy.deepcopy(b['records'][60])
   elif edit=='extra_false137':b['regression']['checks']['inactive']=False
   elif edit=='missing137':b['regression']['missing'].pop()
   elif edit=='removedcheck137':del b['regression']['checks']['inactive']
   else:b['strict_pass']=True
   self.bad(C.strict019,b)
 def policy(self):
  return dict(original002_exact_primary=C.OLD_PRIMARY,original002_error_evidence_ref={'test_only':True},original_cpu_stage_ref=json.loads(SUMMARY.read_bytes())['numerical_summary']['actual_cpu_preflight_ref'])
 def test_exact_old_failure(self):
  o=json.loads(OLD.read_bytes());p=self.policy();C.allowed_old_failure(o,p)
  for key,val in(('primary','some other failure'),('secondary',['cleanup failure']),('stopped_retained',False),('resource_admitted',False),('physical',[4]),('lifecycle_gate_pass',True)):
   b=copy.deepcopy(o);b[key]=val;self.bad(C.allowed_old_failure,b,p)
 def test_exact_traceback(self):
  e=json.loads(ERROR.read_bytes());p=self.policy();C.cause(e,p)
  b=copy.deepcopy(e);b['stderr']=b['stderr'].replace('FileNotFoundError:','MemoryError:');self.bad(C.cause,b,p)
  b=copy.deepcopy(e);b['requested_argv'][-1]='a'*64;self.bad(C.cause,b,p)
  b=copy.deepcopy(e);b['stderr']=b['stderr'].replace(p['original_cpu_stage_ref']['path'],'/some/other.json');self.bad(C.cause,b,p)
 def test_required_actual_guard(self):
  self.bad(C.consume_policy,{},lambda r:None,None)
 def test_physical_source_terminal(self):
  v=dict(source='source',target_source='source',stage='numeric',primary=None,secondary=[],stopped_retained=True,resource_admitted=True,NPU=True,physical=[4],authority={'sha256':C.AUTHORITY})
  C.terminal(v,'source','numeric',cpu=False,physical=[4])
  self.bad(lambda:C.terminal(v,'other','numeric',cpu=False,physical=[4]))
  self.bad(lambda:C.terminal(v,'source','numeric',cpu=False,physical=[5]))
 def test_byte_semantics(self):
  import torch
  torch.set_num_threads(1)
  a=torch.tensor([float('nan'),0.],dtype=torch.float32);b=a.clone()
  self.assertTrue(C.samebytes(torch,a,b))
  b[1]=-0.;self.assertFalse(C.samebytes(torch,a,b))
  self.assertFalse(C.samebytes(torch,torch.tensor([0.]),torch.tensor([0.],dtype=torch.float64)))
 def test_actual_raw_join_software_fixture(self):
  import torch
  torch.set_num_threads(1)
  class Memory:
   def __init__(self):self.values={};self.next=0
   def add(self,x):
    b=io.BytesIO();torch.save(x,b);r={'path':'/TEST_ONLY/'+str(self.next),'bytes':len(b.getvalue()),'sha256':C.hashlib.sha256(b.getvalue()).hexdigest()};self.next+=1;self.values[r['path']]=b.getvalue();return r
   def bytes(self,r):
    b=self.values[r['path']];C.need(len(b)==r['bytes']and C.hashlib.sha256(b).hexdigest()==r['sha256'],'fixture whole bytes');return b
  r=Memory();state={k:r.add(torch.tensor([float('nan'),0.]))for k in('base','k_log','u_log','lambda_log','decay','length')};inp={'query':torch.tensor([1.]),'indices':torch.tensor([0],dtype=torch.int32)};seq=torch.tensor([0,1],dtype=torch.int32);z=torch.tensor([1.],dtype=torch.bfloat16);y=z.float();origin=r.add(dict(event={'step':137},before=state,after=state,candidate_output=z,inputs=inp,sequence=seq));old=dict(original_raw=origin,before=state,after=state,debug_after=state,candidate_output=z,debug_output=z,actual_precast_FP32=y,inputs_after=inp);new=dict(old,sequence_after=seq);oldref=r.add(old);newref=r.add(new)
  self.assertTrue(C.join_raw(torch,r,oldref,newref,origin)['actual_tensor_join'])
  for change in('sign','dtype','frame','output','input'):
   bad=copy.deepcopy(new)
   if change=='sign':bad['after']=dict(state,base=r.add(torch.tensor([float('nan'),-0.])))
   elif change=='dtype':bad['actual_precast_FP32']=y.double()
   elif change=='frame':bad['original_raw']={'path':'/TEST_ONLY/foreign','bytes':1,'sha256':'0'*64}
   elif change=='output':bad['candidate_output']=torch.tensor([2.],dtype=torch.bfloat16)
   else:bad['inputs_after']['query']=torch.tensor([2.])
   self.bad(C.join_raw,torch,r,oldref,r.add(bad),origin)
 def test_light_receipt_does_not_recompute_or_upgrade(self):
  # Deliberately synthetic receipt fixture, only to exercise the reader contract.
  r=lambda key:dict(path='/TEST_ONLY/'+key,bytes=1,sha256='0'*64)
  sr,ow,st,cr=[r(k)for k in('source','owner','stage','certificate')]
  p={k:r(k)for k in('owner019','owner020','original002_owner','CPU016_owner','source016','audit019','numeric019','error_evidence','old137_raw','original137_raw')}
  own=dict(schema='deltalog.readout-diagnostic-owned-host/v005',source=sr,target_source=sr,stage='cpu',primary=None,secondary=[],stopped_retained=True,resource_admitted=True,NPU=False,physical=[],authority={'sha256':C.AUTHORITY},diagnostic_complete=True,diagnostic_only=True,model_ready=False,result=st)
  b=(P/'composite.py').read_bytes();selfref=dict(path=str(P/'composite.py'),bytes=len(b),sha256=C.hashlib.sha256(b).hexdigest())
  m=dict(schema='deltalog.composite-source/v022',root=str(P),window=dict(start=1791962297,cutoff=1792135097),default_enabled=False,prepared_only=False,files={'composite.py':selfref,'test_composite.py':r('tests')},policy=p,authority_ref=own['authority'],library_ref=dict(r('B010'),sha256=C.B010),operator_schema='test-only-schema')
  cert=dict(schema='deltalog.composite-component-qualification/v022',source=sr,owner019=p['owner019'],owner020=p['owner020'],old002_owner=p['original002_owner'],component_source=p['source016'],library=m['library_ref'],operator_schema=m['operator_schema'],strict324=True,original_numeric325=True,strict325_composed=True,original019_strict_pass=False,old002_failure_unchanged=True,strict137_join=dict(actual_tensor_join=True,old_guardless_raw=p['old137_raw'],original_raw=p['original137_raw']),model_ready=False,performance_ready=False,task_ready=False,graph=False,PDC=False,readset=list(p.values()))
  stage=dict(schema='deltalog.composite-CPU/v022',source=sr,authority=own['authority'],NPU=False,pass_gate=True,model_ready=False,certificate=cr,software_controls=dict(source=m['files']['test_composite.py'],discovered=9,executed=9,passed=True))
  values={sr['path']:m,ow['path']:own,st['path']:stage,cr['path']:cert}
  class FakeReader:
   def __call__(self,r):return values[r['path']]
   def bytes(self,r):return b'fixture-not-an-actual-artifact'
  original=C.Reader;C.Reader=FakeReader
  try:
   result=C.admit_receipt(sr,ow);self.assertFalse(result['model_ready']);self.assertEqual(result['certificate_ref'],cr)
   for key in('model_ready','performance_ready','original019_strict_pass'):
    cert[key]=True;self.bad(C.admit_receipt,sr,ow);cert[key]=False
   own['secondary']=['release failure'];self.bad(C.admit_receipt,sr,ow);own['secondary']=[]
   cert['owner020']=r('wrong guard');self.bad(C.admit_receipt,sr,ow)
  finally:C.Reader=original
 def test_original_host_single_reversible_delta(self):
  import ast
  hs=importlib.util.spec_from_file_location('adapter022',P/'host.py');H=importlib.util.module_from_spec(hs);hs.loader.exec_module(H)
  source=(P.parent/'deltalog-raw-bitwise-audit-v019/host.py').read_text(encoding='utf8');tree=ast.parse(source);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main');body=ast.get_source_segment(source,node)
  changed=H.transform_main(body);old="om['schema']=='deltalog.raw-bitwise-audit-source/v019'";new="om['schema']=='deltalog.composite-source/v022'"
  self.assertEqual(changed.replace(new,old),body);self.bad(H.transform_main,body.replace(old,'False'))
if __name__=='__main__':unittest.main()
