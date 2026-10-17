"""No-device real-entry CLI, strict response, all48 trajectory controls."""
import ast,copy,importlib.util,json,os,pathlib,subprocess,sys,types,unittest
from unittest import mock
P=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(P))
import owner_overlay as O
from consume import response
from consume_trajectory import check
class Tests(unittest.TestCase):
 def test_allcold_and_actual_namespace(self):
  for n in('host_ticket.py','entry.py','client.py','consume.py','probe.py','bind_source.py'):
   r=subprocess.run([sys.executable,'-I','-B',str(P/n)],capture_output=True,text=True);self.assertEqual(r.returncode,0,(n,r.stderr))
  import importlib.metadata as md
  e=md.entry_points();e=e.select(group='vllm.general_plugins')if hasattr(e,'select')else e.get('vllm.general_plugins',[])
  rows=[x for x in e if x.name=='deltalog_service025_trace'];self.assertEqual({x.value for x in rows},{'native_observer_plugin101r12:register'});rows[0].load()()
  cold=subprocess.run([sys.executable,'-I','-B','-c',"import sys;sys.path.insert(0,"+repr(str(P))+");import trace_plugin;trace_plugin.register();assert 'torch'not in sys.modules"],capture_output=True,text=True);self.assertEqual(cold.returncode,0,cold.stderr)
 def test_strict_ten_tokens_not_two_or_duplicate_DONE(self):
  request={'request_id':'opaque','payload':dict(n=1,max_tokens=10,min_tokens=10,ignore_eos=True,echo=False,return_token_ids=True,temperature=0,seed=0,prompt=[1,2,3])}
  wire=('data: '+json.dumps(dict(id='cmpl-opaque',choices=[dict(index=0,token_ids=list(range(10)),finish_reason='length')]))+'\n\ndata: '+json.dumps(dict(id='cmpl-opaque',choices=[],usage=dict(prompt_tokens=3,completion_tokens=10)))+'\n\ndata: [DONE]\n\n').encode()
  self.assertEqual(response(request,wire)['output_tokens'],10)
  with self.assertRaises(ValueError):response(request,wire.replace(b'"completion_tokens": 10',b'"completion_tokens": 2'))
  with self.assertRaises(ValueError):response(request,wire+wire)
  with self.assertRaises(ValueError):response(request,wire.replace(b'cmpl-opaque',b'opaque'))
 def test_actual_source_header_response_engine_identity(self):
  from request_identity import identities
  self.assertEqual(identities('request-129'),dict(http_header='request-129',response_id='cmpl-request-129',passed_request_id='cmpl-request-129-0'))
  with self.assertRaises(ValueError):identities('')
 def rows(self):
  values=[];prefixes=['l%d'%i for i in range(48)]
  for rank in range(4):
   counts={p:0 for p in prefixes};epoch=0
   for rid in('engine-actual-a','engine-actual-b'):
    for step in range(10):
     epoch+=1
     if step:counts={p:n+1 for p,n in counts.items()}
     values.append(dict(schema='deltalog.actual-dispatch-trajectory/v025',rank=rank,pid=rank+100,epoch=epoch,request_ids=[rid],groups={'0':dict(decode=[4]if step else[],prefill=[]if step else[4])},registered_prefixes=prefixes,decode_calls=dict(counts),all48_finished=True,numerical_qualified=False,actual_merge_observed=False))
  return values
 def test_actual9decode_all48_and_missinglayer_rejected(self):
  from consume_trajectory import pid_join
  source=self.rows();workers=[dict(rank=r,namespace_pid=r+100)for r in range(4)];self.assertTrue(pid_join(source,workers));source[0]['pid']=999
  with self.assertRaises(ValueError):pid_join(source,workers)
  rows=self.rows();self.assertTrue(check(rows)['dispatch_trajectory_pass']);rows[-1]['decode_calls']['l47']-=1
  with self.assertRaises(ValueError):check(rows)
 def test_two_tokens_no_merge_coverage_rejected(self):
  rows=[r for r in self.rows()if r['epoch']in(1,2,11,12)]
  with self.assertRaises(ValueError):check(rows)
 def test_no_numeric_claim_or_missing160(self):
  r=self.rows();r[0]['numerical_qualified']=True
  with self.assertRaises(ValueError):check(r)
  with self.assertRaises(ValueError):O.model_gate({})
 def test_actual017_environment_call_signature(self):
  original=O.current;gate=O.model_gate;calls=[]
  O.current=lambda sr:dict(plugin_source={'path':'/plugin/SOURCE_MANIFEST.json'},composite_source_ref={})
  O.model_gate=lambda m:{}
  class Base:
   def environment_original(self,*a):calls.append(a);return dict(a[0])
  try:
   e=O.environment(types.SimpleNamespace(WORKER='/worker'),Base(),{},dict(ASCEND_RT_VISIBLE_DEVICES='0,1,2,3'),'/source','/audit','run')
   self.assertEqual(len(calls[0]),4);self.assertEqual(e['QWEN36_DELTALOG_SERVICE023_ENABLE'],'0');self.assertEqual(e['QWEN36_DELTALOG_SERVICE003_ENABLE'],'0');self.assertNotIn('qwen36_deltalog_service023',e['VLLM_PLUGINS'])
  finally:O.current=original;O.model_gate=gate
 def test_actual_native_request_once_10token_assertion(self):
  import client,hashlib,tempfile,io
  source=pathlib.Path(os.environ.get('DL025_CAPTURE_CLIENT_LOCAL','C:/Users/Huawei/AppData/Local/Temp/mxr-r118-capture-launch-20261013-003/capture_client.py'))
  def need(v,m):
   if not v:raise ValueError(m)
  def write(path,value):
   with path.open('x')as f:json.dump(value,f)
  own=types.SimpleNamespace(need=need,write_new=write,sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest())
  c=client.http_module(source.read_bytes(),own,need,source)
  class Response(io.BytesIO):
   status=200
  with tempfile.TemporaryDirectory()as td:
   body=dict(prompt=[1,2,3]);out=pathlib.Path(td)
   for count in(10,2):
    wire=('data: '+json.dumps(dict(choices=[],usage=dict(prompt_tokens=3,completion_tokens=count)))+'\n\ndata: [DONE]\n').encode()
    with mock.patch.object(c.urllib.request,'urlopen',return_value=Response(wire)):
     if count==10:self.assertEqual(c.request_once('http://127.0.0.1/mock',body,out/'ten','id')['usage']['completion_tokens'],10)
     else:
      with self.assertRaises(ValueError):c.request_once('http://127.0.0.1/mock',body,out/'two','id')
 def test_realprobe_cli_and_result_fields_match_run(self):
  run=(P/'run_owned.py').read_text();probe=(P/'probe.py').read_text();self.assertIn("'--mode','parser'",run);self.assertNotIn("'--mode','n1'",run)
  self.assertIn('pass_preflight=True',probe);self.assertIn('real_plugin_registered=True',probe)
 def test_asts(self):
  for p in P.rglob('*.py'):ast.parse(p.read_bytes())
 def test_real017_actual008_full_inverse_then_two_scope_deltas(self):
  oldroot=pathlib.Path(os.environ.get('DL025_DONOR017_LOCAL','C:/Users/Huawei/AppData/Local/Temp/deltalog-service-empirical-new48h-20261015-017/owner'))
  old008=pathlib.Path(os.environ.get('DL025_DONOR008_LOCAL','C:/Users/Huawei/AppData/Local/Temp/mxr-r118-proc-snapshot-repair-20261013-008/host_ticket.py'))
  s=importlib.util.spec_from_file_location('_actual017_for025test',oldroot/'host_ticket.py');H=importlib.util.module_from_spec(s);s.loader.exec_module(H);text=old008.read_text()
  from packet_contract import OUTPUT
  m=dict(runtime_identity=dict(owner='deltalog-service025-test',run_id='deltalog-service025-test',container_prefix='deltalog-service025-'),output_root=OUTPUT)
  fn=next(x for x in ast.walk(ast.parse((P/'host_ticket.py').read_bytes()))if isinstance(x,ast.FunctionDef)and x.name=='adapted');ns=dict(original_adapt=H.adapt,H=H,m=m,HERE=pathlib.Path('/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-model-precast-smoke-new48h-v1-045'),O=O,Path=pathlib.Path)
  ns['json']=json
  import window_overlay as W
  ns['W']=W
  exec(compile(ast.Module(body=[copy.deepcopy(fn)],type_ignores=[]),'<actual025-adapter>','exec'),ns)
  with mock.patch.object(pathlib.Path,'read_bytes',return_value=json.dumps(m).encode()):value,pairs=ns['adapted'](text,{}, {})
  ast.parse(value);self.assertIn('CLEANUP_TOTAL = 270',value);self.assertIn(OUTPUT,value);self.assertIn('_EXTERNAL.docker_gate(self, S, free, initial)',value);self.assertGreater(len(pairs),20)
if __name__=='__main__':unittest.main()
