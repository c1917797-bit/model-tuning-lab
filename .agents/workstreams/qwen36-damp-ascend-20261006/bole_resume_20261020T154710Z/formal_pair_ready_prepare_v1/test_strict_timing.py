"""Pure actual-function integration; synthetic SSE, no HTTP/model/device."""
import ast,copy,hashlib,importlib.util,json,sys,tempfile,types,unittest
from dataclasses import make_dataclass
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import strict_token_timing as T
s=importlib.util.spec_from_file_location('render',P/'render_strict_timing.py');R=importlib.util.module_from_spec(s);s.loader.exec_module(R)
B=R.render()
def need(v,m):
 if not v:raise ValueError(m)
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def ref(p):
 b=Path(p).read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def obj(r):
 need(ref(r['path'])==r,'actual whole fixture file');return json.loads(Path(r['path']).read_bytes())
def checked(r):need(ref(r['path'])==r,'actual whole fixture file');return Path(r['path'])
def load(r,n):
 p=checked(r);s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
C=types.SimpleNamespace(need=need,canonical=canonical,ref=ref,obj=obj,checked=checked,load=load)
Result=make_dataclass('RequestResult',[(n,object)for n in ('index','ok','ttft_ms','duration_s','output_tokens','output_sha256','requested_output_tokens','finish_reason')])
class Clock:
 def __init__(self):self.n=100
 def __call__(self):self.n+=1;return self.n
class Response:
 status=200
 headers=types.SimpleNamespace(get_content_type=lambda:'text/event-stream')
 def __init__(self,chunks,clock):self.chunks=list(chunks);self.clock=clock
 def __enter__(self):return self
 def __exit__(self,*args):return False
 def read1(self,n):
  at,b=self.chunks.pop(0);self.clock.n=at;return b
def events(kind='normal',tail=10000,label='measured'):
 def event(c,usage=None):
  return b'data: '+canonical(dict(id='cmpl-bole-perf-131-'+label,model='qwen36-mxr-eager',object='text_completion',created=1,choices=c,usage=usage))+b'\n\n'
 role=event([dict(index=0,text='',token_ids=[],finish_reason=None)])
 first=event([dict(index=0,text='',token_ids=[7],prompt_token_ids=[1]*131,finish_reason=None)])
 rest=event([dict(index=0,text='x',token_ids=[8]*1023,finish_reason='length')])
 usage=event([],dict(prompt_tokens=131,completion_tokens=1024,total_tokens=1155))
 if kind=='missing':rest=event([dict(index=0,text='x',token_ids=[8]*1022,finish_reason='length')])
 if kind=='extra':rest=event([dict(index=0,text='x',token_ids=[8]*1024,finish_reason='length')])
 chunks=[(110,role),(200,first),(1000,rest),(tail,usage),(tail+100,b'data: [DONE]\n\n'),(tail+1000,b'')]
 if kind=='duplicate':chunks.insert(3,(2000,first))
 return chunks
class Tests(unittest.TestCase):
 def fixture(self,root,arm):
  manifest=copy.deepcopy(B['arms'][arm]['manifest'])
  for n in ('formal_token_client.py','formal_token_reader.py','formal_token_evidence.py'):
   (root/n).write_bytes(B['arms'][arm]['files'][n]);manifest['files'][n]=ref(root/n)
  manifest['files']['strict_token_timing.py']=ref(P/'strict_token_timing.py')
  (root/'CALL_SOURCE.json').write_bytes(canonical(manifest))
  args=types.SimpleNamespace(base_url='http://127.0.0.1:8230',timeout=2400)
  return manifest,args
 def real_client(self,m,args,root,chunks,clock,label='measured'):
  text=B['arms'][m['performance_arm']]['files']['performance_service_client.py'].decode()
  node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)and n.name=='request')
  env=dict(C=C);exec(compile(ast.Module(body=[node],type_ignores=[]),'actual-rendered-client','exec'),env)
  def transport(request,timeout):
   self.assertEqual(json.loads(request.data)['seed'],0);self.assertEqual(json.loads(request.data)['echo'],False)
   header=next(v for k,v in request.header_items()if k.lower()=='x-request-id')
   actual=[(at,raw.replace(('cmpl-bole-perf-131-'+label).encode(),('cmpl-'+header).encode()))for at,raw in chunks]
   return Response(actual,clock)
  with patch.object(T.request,'__defaults__',(None,None,clock)):
   return env['request'](types.SimpleNamespace(RequestResult=Result),args,[1]*131,0,1024,label,transport,[],capture_root=root,manifest=m,source_ref=ref(root/'CALL_SOURCE.json'))
 def test_actual_client_and_consumer_empty_text_role_tail_both_arms(self):
  for arm in ('native_ar','bole'):
   with tempfile.TemporaryDirectory(dir=P)as d:
    root=Path(d);m,args=self.fixture(root,arm);clock=Clock()
    result,row=self.real_client(m,args,root,events(),clock)
    metrics=T.consume(C,m,row,source_ref=ref(root/'CALL_SOURCE.json'),client_output=root)
    self.assertEqual(metrics['TTFT_ns'],100) # first token at201, start101; role-only111 ignored
    self.assertEqual(metrics['T_total_ns'],900) # last token1001 minus101; tail not included
    self.assertEqual(metrics['TPOT_numerator_ns'],800)
    self.assertEqual(metrics['output_tokens'],1024);self.assertAlmostEqual(result.duration_s,900/1e9)
    self.assertFalse(metrics['formal_performance'])
 def test_usage_DONE_delay_does_not_change_any_token_metric(self):
  values=[]
  for tail in (10000,100000000):
   with tempfile.TemporaryDirectory(dir=P)as d:
    root=Path(d);m,args=self.fixture(root,'native_ar');result,row=self.real_client(m,args,root,events(tail=tail),Clock())
    x=T.consume(C,m,row,source_ref=ref(root/'CALL_SOURCE.json'),client_output=root);values.append([x[k]for k in ('TTFT_ns','TPOT_numerator_ns','T_total_ns')])
  self.assertEqual(values[0],values[1])
 def test_missing_or_extra_tokens_fail_retained(self):
  for kind in ('missing','extra','duplicate'):
   with tempfile.TemporaryDirectory(dir=P)as d:
    root=Path(d);m,args=self.fixture(root,'bole')
    with self.assertRaises(ValueError):self.real_client(m,args,root,events(kind),Clock())
    self.assertTrue((root/'TOKEN-WIRE-measured/SSE.raw').is_file())
 def test_independent_consumer_refuses_claimed_metric_or_token_drift(self):
  with tempfile.TemporaryDirectory(dir=P)as d:
   root=Path(d);m,args=self.fixture(root,'native_ar');result,row=self.real_client(m,args,root,events(),Clock())
   for k in ('duration','ids'):
    bad=copy.deepcopy(row)
    if k=='duration':bad['timing']['duration_s']+=1
    else:bad['token_ids'][0]=123
    with self.assertRaises(ValueError):T.consume(C,m,bad,source_ref=ref(root/'CALL_SOURCE.json'),client_output=root)
 def test_same_timing_optimization_two_distinct_true_arms_inverse(self):
  a=B['arms']['native_ar'];b=B['arms']['bole']
  for n in ('strict_token_timing.py','formal_token_client.py','formal_token_reader.py','formal_token_evidence.py','performance_service_client.py','performance_client_consumer.py'):
   self.assertEqual(a['files'][n],b['files'][n])
  self.assertIsNone(a['manifest']['effective_speculative_config'])
  self.assertEqual(b['manifest']['effective_speculative_config'],dict(method='mtp',num_speculative_tokens=8))
  self.assertEqual(a['manifest']['paired_common_environment'],b['manifest']['paired_common_environment'])
  self.assertNotIn('observation_only_profile',a['manifest'])
  self.assertFalse(a['manifest']['performance_ready']);self.assertFalse(b['manifest']['numerical_qualified'])
  self.assertEqual(set(a['strict_timing_inverse']),set(b['strict_timing_inverse']))
  for arm in(a,b):
   m=arm['manifest']
   self.assertEqual(m['performance_streaming_client'],m['files']['performance_service_client.py'])
   self.assertIn(m['performance_streaming_client'],m['dependencies'])
 def test_actual_public_native_consumer_calls_new_independent_reader(self):
  with tempfile.TemporaryDirectory(dir=P)as d:
   root=Path(d);m,args=self.fixture(root,'native_ar')
   _,warm=self.real_client(m,args,root,events(label='warmup'),Clock(),'warmup')
   _,measured=self.real_client(m,args,root,events(),Clock())
   source=ref(root/'CALL_SOURCE.json')
   header,identity=T.request_identity(C,m,source,root,'retirement-barrier')
   barrier=dict(label='retirement-barrier',header=header,id='cmpl-'+header,request_identity=identity)
   (root/'HTTP_RESULT.json').write_bytes(canonical(dict(rows=[warm,measured,barrier])))
   text=B['arms']['native_ar']['files']['performance_client_consumer.py'].decode()
   n=[n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)and n.name=='consume'][-1]
   env=dict(original_consume=lambda **kwargs:dict(legacy_metadata_gate_stub_only=True))
   exec(compile(ast.Module(body=[n],type_ignores=[]),'actual-rendered-consumer','exec'),env)
   out=env['consume'](C=C,source=source,manifest=m,client_output=root,receipt_root=root)
   self.assertEqual(len(out['actual_token_receive_metrics']),2);self.assertFalse(out['formal_performance'])
 def test_global_ids_unique_for_two_arms_and_three_trials_and_identity_drift_refused(self):
  ids=set()
  for trial in range(3):
   for arm in ('native_ar','bole'):
    with tempfile.TemporaryDirectory(dir=P)as d:
     root=Path(d);m,args=self.fixture(root,arm)
     with patch.object(T.uuid,'uuid4',return_value=types.SimpleNamespace(hex='a'*32)):
      _,row=self.real_client(m,args,root,events(),Clock())
     self.assertNotIn(row['id'],ids);ids.add(row['id'])
     for field,value in [('arm','observerOFF'),('client_output','/foreign'),('label','warmup')]:
      bad=copy.deepcopy(row);bad['request_identity'][field]=value
      with self.assertRaises(ValueError):T.validate_identity(C,m,bad,ref(root/'CALL_SOURCE.json'),root)
  self.assertEqual(len(ids),6)
if __name__=='__main__':unittest.main()
