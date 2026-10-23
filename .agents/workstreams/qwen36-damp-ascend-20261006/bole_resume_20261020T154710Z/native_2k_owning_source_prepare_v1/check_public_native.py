"""Actual owning-prefix pure VM. Synthetic JSON tickets NEVER touch disk/devices."""
import ast,contextlib,copy,hashlib,importlib.abc,importlib.util,json,sys,time,types,unittest,tempfile
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import prepare_native_2k as P
import native_2k_source as AUTHOR_N
def raw(value):return(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode()
def ref_bytes(path,b):return dict(path=str(path),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
class MemoryPath:
 def __init__(self,path,data):self.path=path;self.data=data
 def read_bytes(self):return self.data[self.path]
 def read_text(self,*a,**k):return self.read_bytes().decode()
 def __str__(self):return self.path
@contextlib.contextmanager
def virtual(bundle,extra):
 """New source/authority/commands exist ONLY as in-memory bytes."""
 data={str(P.ROOT/n):b for n,b in bundle['files'].items()};data.update(extra)
 real_io=types.ModuleType('sourceio')
 author=Path(P.OBSERVER_RENDER['path']).parent.parent/'bound-native-ar-common-v3_20261022T213000Z/sourceio.py'
 exec(compile(author.read_bytes(),str(author),'exec'),real_io.__dict__)
 calls=[];physical={}
 def ref(path):
  key=str(path)
  if key in data:return ref_bytes(key,data[key])
  return real_io.ref(path)
 def checked(r):
  key=r['path'];calls.append(key)
  if key in data:
   if ref(key)!=r:raise ValueError('actual full virtual Ref mismatch')
   return MemoryPath(key,data)
  # Real preparation/historical sources stay actual source bytes, not a stub.
  if key not in physical:physical[key]=real_io.checked(r)
  elif real_io.ref(physical[key])!=r:raise ValueError('actual stable historical Ref mismatch')
  return physical[key]
 def obj(r):return json.loads(checked(r).read_bytes())
 fixture=types.ModuleType('sourceio');fixture.need=real_io.need;fixture.ref=ref;fixture.checked=checked;fixture.obj=obj
 fixture.write=lambda *a,**k:(_ for _ in()).throw(AssertionError('forbidden physical binding/output in pure control'))
 names={Path(n).stem for n in bundle['files']if '/'not in n and n.endswith('.py')}
 names.add('sourceio')
 previous={k:(k in sys.modules,sys.modules.get(k))for k in names};oldpath=list(sys.path)
 class Finder(importlib.abc.MetaPathFinder,importlib.abc.Loader):
  def find_spec(self,name,path=None,target=None):
   if name=='sourceio':return None
   n=name+'.py'
   if '.'not in name and n in bundle['files']:return importlib.util.spec_from_loader(name,self,origin=str(P.ROOT/n))
  def create_module(self,spec):return None
  def exec_module(self,module):
   module.__file__=str(P.ROOT/(module.__name__+'.py'));exec(compile(bundle['files'][module.__name__+'.py'],module.__file__,'exec'),module.__dict__)
 finder=Finder()
 try:
  for name in names:sys.modules.pop(name,None)
  sys.modules['sourceio']=fixture;sys.meta_path.insert(0,finder)
  yield types.SimpleNamespace(data=data,ref=ref,obj=obj,checked=checked,calls=calls,fixture=fixture)
 finally:
  sys.meta_path.remove(finder);sys.path[:]=oldpath
  for name,(present,value)in previous.items():
   if present:sys.modules[name]=value
   else:sys.modules.pop(name,None)
def packet():
 initial=P.render();m=initial['manifest']
 review=dict(schema=AUTHOR_N.REVIEW_SCHEMA,approved=True,scope=AUTHOR_N.SCOPE,source_review=AUTHOR_N.review_value(m),
  fixture_only=True,actual_MAIN_review=False)
 rb=raw(review);rr=ref_bytes('/unit-only-native2k/MAIN-review.json',rb)
 now=int(time.time())
 authority=dict(schema=AUTHOR_N.AUTH_SCHEMA,approved=True,start_epoch=now-10,cutoff_epoch=now+10000,scope=AUTHOR_N.SCOPE,MAIN_review_ref=rr)
 ab=raw(authority);ar=ref_bytes('/unit-only-native2k/authority.json',ab)
 io=types.SimpleNamespace(checked=P.checked,obj=lambda r:authority if r==ar else review)
 bundle=P.render(authority_ref=ar,permit_materialized=True,io=io)
 template=bundle['manifest'];tb=raw(template);tr=ref_bytes(P.ROOT/'SOURCE_TEMPLATE.json',tb)
 bound=dict(template,prepared_only=False,prepared_template=tr);bb=raw(bound);sr=ref_bytes(P.ROOT/'SOURCE_BOUND.json',bb)
 extra={ar['path']:ab,rr['path']:rb,tr['path']:tb,sr['path']:bb}
 # Commands use actual unchanged command_contract.expected/validate, including
 # exact JSON operand key order; none is written physically.
 tree=ast.parse(bundle['files']['command_contract.py']);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='expected')
 ns=dict(Path=Path,json=json);exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual_original_command_expected','exec'),ns)
 commands=dict(schema='bole.performance-actual-bound-commands/v1',source=tr,bound_source=sr,
  required_sameimage_software_cases=9,historical_required_sameimage_software_cases=154,G3_stream_protocol=False,actual_G3_execution_claimed=False,
  actual_G1_execution_claimed=False,legacy_entrypoints_retained_for_inverse_tests_only=True,
  **ns['expected'](str(P.ROOT),str(P.OUT),sr,tr,bound['component_refs']))
 cb=raw(commands);cr=ref_bytes(P.ROOT/'COMMANDS.json',cb);extra[cr['path']]=cb
 compatibility=dict(source=sr,template=tr,commands=cr,model=commands['model'],CPU=commands['CPU'],required_sameimage_software_cases=9)
 extra[str(P.ROOT/bound['command_scope']['compatibility_file'])]=raw(compatibility)
 return bundle,extra,sr,ar,rr
class Tests(unittest.TestCase):
 def test_actual_original_budget_shared_assignment_no_missing_charge(self):
  b=P.render()
  with virtual(b,{})as vm,tempfile.TemporaryDirectory()as d:
   import g3_budget as B
   base=Path(d);channel=base/'STREAM';channel.mkdir()
   payload=b'{"fixture":"actual-byte-accounting"}'
   (base/'NATIVE2K-ASSIGNMENT.json').write_bytes(payload)
   m=dict(model_receipt_root=str(base),stream_channel_root=str(channel))
   current=B.actual(vm.fixture,m,0)
   prior=types.ModuleType('original_budget');exec(compile(b['parent_files']['g3_budget.py'],'original_budget','exec'),prior.__dict__)
   historical=prior.actual(vm.fixture,m,0)
   self.assertEqual(current['charges']['other'],len(payload));self.assertEqual(historical['charges']['other'],0)
   self.assertEqual((B.OTHER,B.G.METADATA_CAP,B.G.RAW_CAP),(3*2**20,64*2**20,2**30))
 def test_source_definition_whole_inverse_and_native9(self):
  b=P.render();m=b['manifest']
  self.assertIsNone(m['native_2k_authority_ref']);self.assertTrue(m['prepared_only']);self.assertEqual(m['service_required_sameimage_software_cases'],9)
  old=ast.parse(b['parent_files']['contract090.py']);new=ast.parse(b['files']['contract090.py'])
  original=next(n for n in old.body if isinstance(n,ast.FunctionDef)and n.name=='source')
  retained=next(n for n in new.body if isinstance(n,ast.FunctionDef)and n.name=='_legacy_source');retained.name='source'
  self.assertEqual(ast.dump(original,include_attributes=False),ast.dump(retained,include_attributes=False))
  for n in('adapter.py','core112.py','external025.py','owned_create.py','worker_snapshot_owner.py'):
   self.assertEqual(b['files'][n],b['parent_files'][n])
  self.assertEqual(m['native_2k_input_processor_ref'],P.INPUT_PROCESSOR);self.assertIs(m['native_speculative_config'],None)
  self.assertIn('fixed_cutoff=active_cutoff(sr)',b['files']['performance_software_stages.py'].decode())
 def test_actual_C_source_and_full_MODEL_to_original_predevice_boundary(self):
  bundle,extra,sr,ar,rr=packet()
  with virtual(bundle,extra)as vm:
   import contract090 as C
   import performance_validate as V
   m=C.source(sr)
   self.assertEqual(m['profile']['input_tokens'],2048);self.assertEqual(len(V.enumerate_tests(m)),9)
   import host_service as HOST
   import g2_cold_clock as CLOCK
   original=CLOCK.phase_admission
   class Predevice(Exception):pass
   def stop(C_,entry):
    remaining=original(C_,entry);self.assertGreaterEqual(remaining,60);raise Predevice('real original phase reached; before output/owner imports')
   with patch.object(CLOCK,'phase_admission',stop),patch.object(sys,'argv',['host_service.py','--execute','--source-ref',json.dumps(sr),'--output',str(P.OUT)]):
    with self.assertRaisesRegex(Predevice,'before output/owner'):HOST.main()
   self.assertNotIn('owned_substrate',sys.modules)
   self.assertIn(str(P.ROOT/'COMMANDS.json'),vm.calls)
   self.assertIn(str(P.ROOT/'SOURCE_TEMPLATE.json'),vm.calls)
   self.assertGreater(len(set(vm.calls)),7000)
 def test_missing_authority_and_review_pin_reject_before_executable_helper(self):
  bundle,extra,sr,ar,rr=packet()
  with virtual(bundle,extra)as vm:
   import contract090 as C
   m=vm.obj(sr);m['native_2k_authority_ref']=None
   with self.assertRaisesRegex(ValueError,'authority unbound'):C._native2k_helper(m)
   m=vm.obj(sr);review=json.loads(vm.data[rr['path']]);review['source_review']['files']['native_2k_source.py']['sha256']='0'*64
   wrong=raw(review);wrongref=ref_bytes(rr['path'],wrong);a=json.loads(vm.data[ar['path']]);a['MAIN_review_ref']=wrongref
   vm.data[rr['path']]=wrong;vm.data[ar['path']]=raw(a);m['native_2k_authority_ref']=ref_bytes(ar['path'],vm.data[ar['path']])
   with self.assertRaisesRegex(ValueError,'BEFORE helper'):C._native2k_helper(m)
 def test_current_window_clock_and_bad_raw_source_refs_reject(self):
  bundle,extra,sr,ar,rr=packet()
  with virtual(bundle,extra)as vm:
   import contract090 as C
   m=vm.obj(sr);N=C._native2k_helper(m)
   with patch.object(N.time,'time',return_value=vm.obj(ar)['cutoff_epoch']):
    with self.assertRaisesRegex(ValueError,'finite new native2k'):N.execution_window(C,m,clock=True)
   wrong=dict(sr,sha256='0'*64)
   with self.assertRaisesRegex(ValueError,'Ref mismatch'):C.source(wrong)
   damaged=dict(m);damaged['native_2k_input_processor_ref']=dict(P.INPUT_PROCESSOR,bytes=1)
   with self.assertRaisesRegex(ValueError,'BEFORE helper'):C._native2k_helper(damaged)
if __name__=='__main__':unittest.main()
