"""Actual2k input/profile/client/independent-SSE entry; fake wire, no HTTP/NPU."""
import ast,copy,hashlib,importlib.util,json,sys,tempfile,types,unittest
from dataclasses import make_dataclass
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import render_input_stage as R
import representative_input_contract as DOMAIN
B=R.render()
def need(v,s):
 if not v:raise ValueError(s)
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def ref(p):
 b=Path(p).read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def checked(r):need(ref(r['path'])==r,'whole actual software fixture Ref');return Path(r['path'])
def obj(r):return json.loads(checked(r).read_bytes())
def load(r,n):
 p=checked(r);spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);sys.modules[n]=m
 exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def write(p,v):
 with p.open('xb')as f:f.write(canonical(v)+b'\n')
 return ref(p)
C=types.SimpleNamespace(need=need,canonical=canonical,ref=ref,checked=checked,obj=obj,load=load,write=write)
Result=make_dataclass('RequestResult',[(n,object)for n in('index','ok','ttft_ms','duration_s','output_tokens','output_sha256','requested_output_tokens','finish_reason')])
class Clock:
 def __init__(self):self.n=100
 def __call__(self):self.n+=1;return self.n
class Response:
 status=200;headers=types.SimpleNamespace(get_content_type=lambda:'text/event-stream')
 def __init__(self,chunks,clock):self.chunks=list(chunks);self.clock=clock
 def __enter__(self):return self
 def __exit__(self,*a):return False
 def read1(self,n):at,b=self.chunks.pop(0);self.clock.n=at;return b
 def __iter__(self):
  for at,b in self.chunks:
   self.clock.n=at
   for line in b.splitlines(keepends=True):yield line
class Tokenizer:
 vocab_size=248320
 def __init__(self):self.calls=[]
 def encode(self,text,add_special_tokens):
  self.calls.append((text,add_special_tokens));return [1]*4096
class Donor:
 RequestResult=Result
 PromptCase=lambda self,ids,prefix:types.SimpleNamespace(ids=ids)
 _post_json=None
 def _stream_completion(self,args,index,case,unused,count):
  payload=dict(model=args.model,prompt=case.ids,max_tokens=count,temperature=0,stream=True,ignore_eos=True,seed=0)
  with self._post_json(args.base_url+'/v1/completions',payload,args.timeout)as response:
   for _ in response:pass
  return Result(index,True,1,1,count,'fixture-barrier',count,'length')
 def _summary(self,results,duration,concurrency):
  return dict(output_tokens=results[0].output_tokens,duration_s=duration,concurrency=concurrency,software_fixture_only=True)
class Tests(unittest.TestCase):
 def input_function(self,arm):
  text=B['arms'][arm]['files']['service_client.py'].decode()
  node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)and n.name=='inputs')
  env=dict(C=C);exec(compile(ast.Module(body=[node],type_ignores=[]),'actual2k-service-inputs','exec'),env);return env['inputs']
 def fixture(self,root,arm):
  m=copy.deepcopy(B['arms'][arm]['manifest'])
  for n in ('formal_token_client.py','formal_token_reader.py','formal_token_evidence.py','strict_token_timing.py','bole_performance_profile.py'):
   (root/n).write_bytes(B['arms'][arm]['files'][n]);m['files'][n]=ref(root/n)
  write(root/'CALL_SOURCE.json',m)
  return m
 def test_actual_inputs_and_old131_hard_negative(self):
  for arm in('native_ar','bole'):
   tok=Tokenizer();ids=self.input_function(arm)(tok)
   self.assertEqual(ids,[1]*2048);self.assertEqual(tok.calls,[(DOMAIN.TEXT*1024,False)])
   DOMAIN.validate_prompt(ids,tok.vocab_size)
   for bad in ([1]*131,[1]*2047,[1]*2049,[True]*2048):
    with self.assertRaises(ValueError):DOMAIN.validate_prompt(bad,tok.vocab_size)
   class TooShort(Tokenizer):
    def encode(self,*a,**k):return [1]*131
   with self.assertRaises(ValueError):self.input_function(arm)(TooShort())
 def test_actual_public_client_run_both_arms_with_strict_independent_reader(self):
  for arm in('native_ar','bole'):
   with tempfile.TemporaryDirectory(dir=P)as d:
    root=Path(d);m=self.fixture(root,arm);clock=Clock();bodies=[]
    names=('strict_token_timing','sourceio','service_client');old={n:sys.modules.get(n)for n in names};present={n:n in sys.modules for n in names}
    try:
     T=load(m['files']['strict_token_timing.py'],'strict_token_timing')
     PERF=load(m['files']['bole_performance_profile.py'],'_actual2k_PERF')
     sys.modules['sourceio']=C
     sys.modules['service_client']=types.SimpleNamespace(inputs=self.input_function(arm))
     def transport(request,timeout):
      body=json.loads(request.data);bodies.append(body);count=body['max_tokens'];start=clock.n
      header=next(v for k,v in request.header_items()if k.lower()=='x-request-id')
      def event(choices,usage=None):
       return b'data: '+canonical(dict(id='cmpl-'+header,model=body['model'],object='text_completion',created=1,choices=choices,usage=usage))+b'\n\n'
      role=event([dict(index=0,text='',token_ids=[],finish_reason=None)])
      first=event([dict(index=0,text='',token_ids=[7],prompt_token_ids=body['prompt'],finish_reason='length'if count==1 else None)])
      rest=event([dict(index=0,text='x',token_ids=[8]*(count-1),finish_reason='length')])
      usage=event([],dict(prompt_tokens=2048,completion_tokens=count,total_tokens=2048+count))
      chunks=[(start+10,role),(start+100,first)]
      if count>1:chunks.append((start+900,rest))
      chunks.extend([(start+10000,usage),(start+11000,b'data: [DONE]\n\n'),(start+12000,b'')])
      return Response(chunks,clock)
     text=B['arms'][arm]['files']['performance_service_client.py'].decode()
     nodes=[n for n in ast.parse(text).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))and n.name in('run','request','Capture')]
     env=dict(C=C,PERF=PERF,json=json,sys=sys,asdict=__import__('dataclasses').asdict,traceback=__import__('traceback'),SimpleNamespace=types.SimpleNamespace)
     exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual2k-public-client','exec'),env)
     with patch.object(T.request,'__defaults__',(None,None,clock)):
      result=env['run'](ref(root/'CALL_SOURCE.json'),root,Tokenizer(),donor=Donor(),transport=transport)
     self.assertEqual([x['max_tokens']for x in bodies],[1024,1024,1])
     self.assertTrue(all(x['prompt']==[1]*2048 for x in bodies))
     self.assertEqual([row['usage']['prompt_tokens']for row in result['rows']],[2048]*3)
     self.assertFalse(result['formal_performance'])
     for row in result['rows'][:2]:
      metrics=T.consume(C,m,row,source_ref=ref(root/'CALL_SOURCE.json'),client_output=root)
      self.assertEqual(metrics['output_tokens'],1024)
     old_ids=[1]*131
     reader=T.modules(C,m)[1]
     with self.assertRaises(ValueError):reader.expected_request(old_ids)
    finally:
     for n in names:
      sys.modules.pop(n,None)
      if present[n]:sys.modules[n]=old[n]
 def test_same_delta_original_math_gate_and_geometry_not_guessed(self):
  for n in R.INPUT_COMPONENT_PINS:
   self.assertEqual(B['arms']['native_ar']['files'][n],B['arms']['bole']['files'][n])
  a=B['arms']['native_ar'];b=B['arms']['bole']
  self.assertIsNone(a['manifest']['effective_speculative_config'])
  self.assertEqual(b['manifest']['effective_speculative_config'],dict(method='mtp',num_speculative_tokens=8))
  self.assertEqual(a['manifest']['paired_common_environment'],b['manifest']['paired_common_environment'])
  for arm,p in B['arms'].items():
   for n in('core112.py','adapter.py','oracle112.py','g2_numeric.py','g3_fia_contract.py','live_owner.py','cache_registry.py'):
    self.assertEqual(p['files'][n],p['parent131']['files'][n])
  self.assertEqual(DOMAIN.required_geometry()['maximum_private_kernel_pages'],25)
  self.assertEqual(DOMAIN.required_geometry()['maximum_committed_path_kernel_pages'],24)
  self.assertFalse(DOMAIN.required_geometry()['actual_allocated_table_proven'])
  with self.assertRaises(ValueError):DOMAIN.require_model_qualification(passed=True)
 def test_actual_native_input_identity_2048_ABI_and_old131_rejected(self):
  # Pure ABI fixture, not torch math, model-source provenance or NPU proof.
  class Tensor:
   dtype='i32'
   def __init__(self,values):self.values=list(values);self.shape=(len(values),)
   def __getitem__(self,s):return Tensor(self.values[s])
   def detach(self):return self
   def cpu(self):return self
   def tolist(self):return list(self.values)
   def clone(self):return Tensor(self.values)
  class CPU:
   def __init__(self,values):self.values=values
   def __getitem__(self,key):return Tensor(self.values[key[1]])
  Base=type('GPUModelRunner',(),{'_preprocess':lambda *a:None,'_prepare_mm_inputs':lambda *a:None})
  Runner=type('Runner',(Base,),{})
  for arm in ('native_ar','bole'):
   text=B['arms'][arm]['files']['input_identity.py'].decode()
   node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)and n.name=='capture')
   env=dict(need=need,code_source=lambda *a:None)
   exec(compile(ast.Module(body=[node],type_ignores=[]),'actual2k-native-input-identity','exec'),env)
   ids=[1]*2048;runner=Runner()
   req=types.SimpleNamespace(prompt_token_ids=ids,prompt_embeds=None,mm_features=[],prompt_is_token_ids=None)
   runner.requests={'r':req};runner.input_ids=types.SimpleNamespace(gpu=Tensor(ids))
   runner.input_batch=types.SimpleNamespace(req_ids=['r'],req_id_to_index={'r':0},token_ids_cpu=CPU(ids))
   worker=types.SimpleNamespace(model_runner=runner,_bole_model_objects={'outer':object()})
   refs={k:'software-fixture-only'for k in('runner','base_runner','qwen35','qwen_next')}
   t=types.SimpleNamespace(int32='i32',equal=lambda a,b:a.shape==b.shape and a.values==b.values)
   with patch.dict(sys.modules,{'torch':t}):
    result=env['capture'](C,worker,None,Tensor(ids),None,None,refs)
    self.assertEqual(result['actual_token_ids'].shape,(2048,))
    self.assertEqual(result['actual_CPU_token_ids'],ids)
    self.assertEqual(result['request_prompt_token_ids'],ids)
    req.prompt_token_ids=[1]*131
    with self.assertRaises(ValueError):env['capture'](C,worker,None,Tensor(ids),None,None,refs)
    req.prompt_token_ids=ids;runner.input_ids.gpu=Tensor([1]*131)
    with self.assertRaises(ValueError):env['capture'](C,worker,None,Tensor(ids),None,None,refs)
 def test_reviewed_literal_counts_and_corrected_diagnostics(self):
  for n,r in R.INPUT_COMPONENT_PINS.items():
   values={131:2048}
   if n in('strict_token_timing.py','formal_token_reader.py'):values[1155]=3072
   with self.subTest(file=n),self.assertRaises(ValueError):
    R.literal_delta(R.checked(r),values,expected_count=R.EXPECTED_COUNTS[n]+1)
   text=B['arms']['bole']['files'][n].decode()
   for before,after in R.MESSAGE_DELTAS.get(n,[]):
    self.assertNotIn(before,text);self.assertEqual(text.count(after),1)
if __name__=='__main__':unittest.main()
