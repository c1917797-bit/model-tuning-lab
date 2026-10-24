"""Actual observer/actual guard AST, with explicit stdlib-only process fixtures."""
import ast,copy,datetime,hashlib,importlib.util,json,os,re,resource,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
WS=HERE.parent
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
G=load(HERE/'guard_failure_delta.py','_guard_delta_test')
OLD=WS/'bole_cpu_precreate_whole_v5_prepare_20261023/prepared-source-short8-v5'
MR=json.loads((OLD/'SOURCE_BOUND.json').read_bytes())
RAW=Path(MR['files']['observer_race_repair.py']['path']).read_bytes()
SAFETY=Path('/cache/cch/qwen36-paper-preparation-20261007/sparse/adakv-tp4-model-once-v1-025/safety_host.py')
ST=ast.parse(SAFETY.read_bytes())
ORIGINAL=next(n for n in ast.walk(ST)if isinstance(n,ast.FunctionDef)and n.name=='observe')
GUARD=next(n for n in ast.walk(ORIGINAL)if isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and any(isinstance(a,ast.Constant)and a.value=='real foreign PID/UDA/start/program conflict; never canary authority'for a in n.value.args))
class Tests(unittest.TestCase):
 def make(self,out,mode='membership',changed=False):
  # Exact original predicate, explicit synthetic local/OS producer fixtures.
  pre=ast.parse("p=self.process\nproof={'physical':5,'chip':0,'stage':label,'raw_observation':{'path':'/unit/raw','bytes':0,'sha256':'0'*64}}\npid=42\nn=5\nch=0\n").body
  post=ast.parse("return 'original-success'").body
  fn=copy.deepcopy(ORIGINAL);fn.body=pre+[copy.deepcopy(GUARD)]+post;fn.decorator_list=[]
  code=ast.Module(body=[fn],type_ignores=[]);ast.fix_missing_locations(code)
  C=types.SimpleNamespace()
  def require(v,s):
   if not v:raise C.error
  C.require=require;C.error=ValueError('real foreign PID/UDA/start/program conflict; never canary authority')
  host=types.SimpleNamespace(require=require)
  ns=dict(datetime=datetime,Path=Path,os=types.SimpleNamespace(readlink=lambda p:'/bin/not-python'if mode=='python'else'/usr/bin/python3'),C=C,c=C,H=host)
  exec(compile(code,str(SAFETY),'exec'),ns)
  original=ns['observe'];K=type('Controller',(),{'observe':original});S=types.SimpleNamespace(Controller=K,H=host)
  source=G.adapt({'observer_race_repair.py':RAW})[0]['observer_race_repair.py']
  tree=ast.parse(source)
  wanted=[n for n in tree.body if isinstance(n,ast.FunctionDef)]+[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.Assign))and n.lineno>39]
  env=dict(Path=Path,os=os,re=re,__file__=str(HERE/'observer_race_repair.py'))
  exec(compile(ast.fix_missing_locations(ast.Module(body=wanted,type_ignores=[])),'observer_race_repair.py','exec'),env)
  env['install'](S,C)
  obj=K();obj.out=out;obj.cid='abc123';obj.server_started=datetime.datetime.now(datetime.timezone.utc)
  obj.process=dict(cgroup='different'if mode=='membership'else'container/abc123',started_utc=(obj.server_started+datetime.timedelta(seconds=5)).isoformat(),argv=['python','DO-NOT-PRINT-secret'])
  return obj,C.error,env,original
 def test_exact_inverse_and_original_protected_handler_body(self):
  out,d=G.adapt({'observer_race_repair.py':RAW});self.assertEqual(G.inverse(out,d),{'observer_race_repair.py':RAW})
  old=next(n for n in ast.walk(ast.parse(RAW))if isinstance(n,ast.ExceptHandler));new=[n for n in ast.walk(ast.parse(out['observer_race_repair.py']))if isinstance(n,ast.ExceptHandler)and isinstance(n.type,ast.Name)and n.type.id=='FileNotFoundError']
  self.assertEqual(len(new),1);self.assertEqual(ast.dump(old,include_attributes=False),ast.dump(new[0],include_attributes=False))
  with self.assertRaises(ValueError):G.adapt({'observer_race_repair.py':RAW+b'#bad\n'})
 def test_actual_predicate_membership_failure_same_error_no_argv_leak(self):
  with tempfile.TemporaryDirectory(prefix='guard-unit-')as td:
   o,e,env,orig=self.make(Path(td))
   with self.assertRaises(ValueError)as got:o.observe('startup')
   self.assertIs(got.exception,e);files=list(Path(td).glob('GUARD-OPERANDS-*'));self.assertEqual(len(files),1)
   raw=files[0].read_bytes();self.assertNotIn(b'DO-NOT-PRINT-secret',raw)
   r=json.loads(raw);self.assertFalse(r['predicate_checks'][2]['value']);self.assertFalse(r['predicate_checks'][6]['evaluated']);self.assertIsNone(r['predicate_checks'][6]['value']);self.assertFalse(r['admission'])
 def test_actual_final_python_false_is_explicit_inference_not_exe_snapshot(self):
  with tempfile.TemporaryDirectory(prefix='guard-unit-')as td:
   o,e,env,orig=self.make(Path(td),'python')
   with self.assertRaises(ValueError)as got:o.observe('startup')
   self.assertIs(got.exception,e);r=json.loads(next(Path(td).glob('GUARD-OPERANDS-*')).read_bytes());last=r['predicate_checks'][6]
   self.assertTrue(last['inferred_from_exact_original_guard_failure']);self.assertFalse(last['value']);self.assertFalse(last['original_exe_path_retained'])
 def test_writer_failure_preserves_exact_error_and_no_retry(self):
  with tempfile.TemporaryDirectory(prefix='guard-unit-')as td:
   o,e,env,orig=self.make(Path(td))
   with patch.dict(env,{'_guard_failure_record':lambda *a:(_ for _ in()).throw(OSError('unit writer denied'))}):
    with self.assertRaises(ValueError)as got:o.observe('startup')
   self.assertIs(got.exception,e);self.assertEqual(list(Path(td).glob('GUARD-OPERANDS-*')),[])
 def test_success_and_other_exception_never_observed_or_retried(self):
  with tempfile.TemporaryDirectory(prefix='guard-unit-')as td:
   o,e,env,orig=self.make(Path(td),'success');self.assertEqual(o.observe('startup'),'original-success');self.assertEqual(list(Path(td).glob('GUARD-OPERANDS-*')),[])
   o.process['cgroup']='different';e.args=('unrelated unit error',)
   with self.assertRaises(ValueError)as got:o.observe('startup')
   self.assertIs(got.exception,e);self.assertEqual(list(Path(td).glob('GUARD-OPERANDS-*')),[])
if __name__=='__main__':
 resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));unittest.main()
