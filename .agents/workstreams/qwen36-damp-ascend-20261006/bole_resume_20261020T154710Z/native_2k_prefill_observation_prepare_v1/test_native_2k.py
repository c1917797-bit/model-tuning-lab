"""Pure ABI/metadata controls, explicitly not same-image or NPU evidence."""
import copy,hashlib,importlib.util,json,os,subprocess,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import render_observation as R
import consume_native_2k as N
import native_2k_prefill_observer as O
SR=dict(path='/unit-fixture/SOURCE_BOUND.json',bytes=1,sha256='0'*64)
def mod(name,text,file,extra=None):
 m=types.ModuleType(name);m.__file__=str(file);m.__dict__.update(extra or{});exec(compile(text,str(file),'exec'),m.__dict__);return m
def ident(shape,dtype='torch.int32',device='npu:0',addr=100):
 stride=[];x=1
 for dim in reversed(shape):stride.insert(0,x);x*=dim
 return [addr,addr,0,shape,stride,dtype,device]
def op(values,device='npu:0',addr=100):
 identity=ident([len(values)],device=device,addr=addr)
 return dict(identity=identity,shape=identity[3],stride=identity[4],dtype=identity[5],device=device,values=values)
def tensor(shape,dtype='torch.bfloat16',addr=100):
 identity=ident(shape,dtype=dtype,addr=addr)
 return dict(identity=identity,shape=identity[3],stride=identity[4],dtype=dtype,device='npu:0')
def fixture(rank=0):
 runtime={k:dict(path='/fixture-runtime/'+k,bytes=1,sha256='1'*64)for k in('runner','block_table','attention','ascend_attention','forward_context','ascend_forward_context','qwen35','qwen_next','worker','base_runner')}
 worker=dict(distributed_rank=rank,npu_logical_device=rank,pid=100+rank)
 registry=dict(source=SR,pid=worker['pid'],rank=rank,counts=dict(gdn=48,fa=16),rows=[])
 ids=list(range(2048));rows=[];gdn=[];table=list(range(60,84));slots=[table[p//128]*128+p%128 for p in range(2048)]
 for i in range(64):
  kind='fa'if i%4==3 else'gdn';prefix='layer.'+str(i);registry['rows'].append(dict(index=i,kind=kind,prefix=prefix))
  if kind=='gdn':
   gdn.append(dict(layer=i,prefix=prefix,group=1,request_object_id=50,allocated=1,CPU_table=op([2],'cpu'),selected=op([2]),conv=tensor([8,3]),state=tensor([8,2])))
  else:
   key=tensor([200,128,1,256],addr=10000+i*100);value=tensor([200,128,1,256],addr=20000+i*100)
   rows.append(dict(layer=i,prefix=prefix,group=0,request_object_id=50,layer_object_id=200+i,metadata_object_id=300+i,context_object_id=400,group_object_id=500,block_object_id=600,
    allocated=24,request_physical_blocks=[5,6],physical_block_size=1536,kernel_block_size=128,blocks_per_phys_block=12,use_hybrid_blocks=True,pcp=1,dcp=1,
    CPU_table=op(table,'cpu'),GPU_table=op(table),metadata_table=op(table),native_slot_mapping=op(slots,addr=200),metadata_slot_mapping=op(slots,addr=200),generic_slot_mapping=None,
    key=key,value=value,impl_key=copy.deepcopy(key),impl_value=copy.deepcopy(value),num_prefills=1,num_decodes=0,num_actual_tokens=2048,seq_lens_list=[2048],actual_seq_lengths_q=[2048]))
 value=dict(schema='native.actual-2k-prefill-observation/v1',source=SR,rank=rank,npu_logical_device=rank,pid=worker['pid'],request_epoch=1,request_id='actual-randomized-engine-id',request_object_id=50,worker_object_id=60,runner_object_id=70,
  actual_token_ids=ids,input_identity_sources={k:runtime[k]for k in('runner','base_runner','qwen35','qwen_next')},actual_input_mode='native-token-ids',no_mm_features=True,no_soft_prompt=True,
  runtime_sources=runtime,generic_context_type='dict',generic_context_keys=[],native_output_not_substituted=True,cache_contents_captured=False,integer_metadata_D2H=True,rows=rows,GDN_selected_operands=gdn,**N.FALSES)
 def device(v):
  if isinstance(v,dict):
   if v.get('device')=='npu:0':v['device']='npu:%d'%rank;v['identity'][6]=v['device']
   for x in v.values():device(x)
  elif isinstance(v,list):
   for x in v:device(x)
 device(value)
 return value,ids,worker,registry,runtime
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.texts,cls.plan=R.render()
 def test_actual_render_and_failclosed_original_gates(self):
  for n in R.CHANGED:self.assertNotEqual(self.texts[n],R.checked(json.loads(R.checked(R.TEMPLATE).read_bytes())['files'][n]).read_text())
  p=json.loads(R.checked(R.TEMPLATE).read_bytes())
  for n in('contract090.py','bind_model.py','performance_validate.py'):self.assertEqual(self.texts[n],R.checked(p['files'][n]).read_text())
  with self.assertRaisesRegex(ValueError,'incomplete'):R.require_complete(self.plan)
  self.assertFalse(self.plan['source_complete']);self.assertEqual((self.plan['phase_seconds'],self.plan['cleanup_seconds']),(3600,180))
  self.assertIn('native_MTP',self.plan);self.assertIs(self.plan['native_MTP'],False)
 def test_actual_profile_native_argv_no_MTP(self):
  profile=mod('unit_profile',self.texts['bole_performance_profile.py'],HERE/'unit_profile.py');sys.modules['unit_profile']=profile
  try:
   decl=dict(schema=profile.SCHEMA,enabled=True,scope=dict(profile.EXPECTED_SCOPE))
   result=profile.select({profile.FLAG:'1'},decl);self.assertEqual((result.input_tokens,result.output_tokens,result.warmup_requests),(2048,1,0))
   argv=['python','-m','api','--enforce-eager','--no-enable-prefix-caching','--no-async-scheduling','--speculative-config',json.dumps(profile.NATIVE_SPEC)]
   self.assertNotIn('--speculative-config',profile.paired_argv(argv)['native_ar'])
   self.assertIn('--speculative-config',profile.paired_argv(argv)['bole'])
   decl['scope']['input_tokens']=131
   with self.assertRaises(ValueError):profile.select({profile.FLAG:'1'},decl)
  finally:sys.modules.pop('unit_profile',None)
 def test_observer_defaultoff_and_source_before_backend(self):
  with patch.dict(os.environ,{},clear=True):self.assertIsNone(O.register(None,None));self.assertIsNone(O.install_frontend(None,None))
  calls=[]
  class C:
   def source(self,sr):calls.append(sr);raise ValueError('fixture missing current native2k source')
  with patch.dict(os.environ,{O.FLAG:'1'},clear=True),self.assertRaisesRegex(ValueError,'current native2k'):O.register(C(),SR)
  with self.assertRaisesRegex(ValueError,'current native2k'):
   O.capture(C(),SR,None,None,request_id=None,request=None,input_ids=None,positions=None,metadata=None,forward_context=None,native_input=None)
  self.assertEqual(calls,[SR,SR])
 def test_real_afterload_native_prefill_original_return_and_once(self):
  p=json.loads(R.checked(R.TEMPLATE).read_bytes());e=mod('model_entry',R.checked(p['files']['model_entry.py']).read_text(),R.PARENT/'model_entry.py')
  with patch.dict(sys.modules,{'model_entry':e}):
   W=mod('unit_worker',self.texts['worker_entry.py'],HERE/'unit_worker.py')
  output=object();load_result=object();events=[]
  class Inner:
   def forward(self,input_ids,positions,intermediate_tensors=None,inputs_embeds=None):events.append('native-forward');return output
  inner=Inner();request=object();ctx=types.SimpleNamespace(in_profile_run=False,attn_metadata={'x':types.SimpleNamespace(num_prefills=1)})
  def context():return ctx
  class Worker:
   def load_model(self):events.append('native-load');return load_result
  worker=Worker();worker.model_runner=types.SimpleNamespace(get_model=lambda:object(),requests={'real':request},input_batch=types.SimpleNamespace(req_ids=['real'],req_id_to_index={'real':0}))
  W.discover=lambda*args:(inner,{})
  class C:
   def ref(self,path):return dict(path=str(path))
  sr=dict(path=str(HERE/'test_native_2k.py'))
  restores=[]
  def callback(**kw):events.append('observe');self.assertIs(kw['request'],request);self.assertIs(kw['hidden'],output)
  def loaded(w,registry):
   restores.append(W.install_after_native_prefill(w,C(),qwen_next_ref=sr,get_forward_context=context,context_source_ref=sr,callback=callback,callback_source_ref=sr))
  with patch.dict(os.environ,{O.FLAG:'1'},clear=True):
   restore=W.install_after_load(Worker,C(),worker_ref=sr,qwen35_ref=None,qwen_next_ref=None,emit=loaded)
   try:
    self.assertIs(worker.load_model(),load_result)
    self.assertIs(inner.forward(object(),object()),output);self.assertIs(inner.forward(object(),object()),output)
    self.assertEqual(events,['native-load','native-forward','observe','native-forward'])
   finally:
    for fn in reversed(restores):fn()
    restore()
 def test_independent_complete_metadata_and_24_not_25(self):
  value,ids,worker,registry,runtime=fixture()
  proof=N.observation(value,SR,ids,worker,registry,runtime)
  self.assertEqual(set(proof['allocated_kernel_pages'].values()),{24})
  self.assertIs(proof['numerical_qualified'],False)
 def test_independent_missing_wrong_alias_shape_and_bool_negatives(self):
  value,ids,worker,registry,runtime=fixture()
  edits=[
   lambda v:v['rows'].pop(),
   lambda v:v['rows'][0]['native_slot_mapping']['values'].pop(),
   lambda v:v['rows'][0]['metadata_table']['identity'].__setitem__(0,999),
   lambda v:v['rows'][0]['impl_key']['identity'].__setitem__(0,999),
   lambda v:v['rows'][0].__setitem__('pcp',True),
   lambda v:v['rows'][0].__setitem__('num_prefills',True),
   lambda v:v['rows'][0].__setitem__('actual_seq_lengths_q',[131]),
   lambda v:v['actual_token_ids'].pop(),
   lambda v:v.__setitem__('source',dict(SR,sha256='2'*64)),
   lambda v:v['GDN_selected_operands'][0]['selected'].__setitem__('values',[999]),
  ]
  for edit in edits:
   wrong=copy.deepcopy(value);edit(wrong)
   with self.assertRaises((ValueError,IndexError)):N.observation(wrong,SR,ids,worker,registry,runtime)
 def test_real_client_fake_HTTP_and_no_overwrite(self):
  p=json.loads(R.checked(R.TEMPLATE).read_bytes());C=mod('sourceio_fixture',R.checked(p['files']['sourceio.py']).read_text(),R.PARENT/'sourceio.py')
  C.source=lambda sr:dict(performance_arm='native_ar',native_2k_observation=R.DECL,native_2k_request_identity='unit')
  with patch.dict(sys.modules,{'contract090':C}):
   client=mod('unit_client',self.texts['native_2k_client.py'],HERE/'native_2k_client.py')
  class Tok:
   vocab_size=5000
   def encode(self,text,**kw):self.text=text;self.kw=kw;return list(range(2500))
  class Response:
   status=200
   def __enter__(self):return self
   def __exit__(self,*a):pass
   def read(self,n):return json.dumps(dict(id='cmpl-native-2k-prefill-unit',usage=dict(prompt_tokens=2048,completion_tokens=1),choices=[dict(index=0,token_ids=[12])])).encode()
  calls=[]
  def wire(request,timeout):
   calls.append(json.loads(request.data));return Response()
  with tempfile.TemporaryDirectory()as t:
   result=client.run(SR,Path(t),Tok(),wire)
   self.assertEqual(len(calls),1);self.assertEqual(len(calls[0]['prompt']),2048);self.assertEqual(calls[0]['max_tokens'],1);self.assertNotIn('speculative_config',calls[0])
   self.assertIs(result['formal_performance'],False)
   with self.assertRaisesRegex(ValueError,'no overwrite'):client.run(SR,Path(t),Tok(),wire)
 def test_actual_serving_source_single_input_join_and_no_header_guess(self):
  p=HERE.parent/'task_http_runtime_sources_v3/completion_serving.py'
  b=p.read_bytes();self.assertEqual((len(b),hashlib.sha256(b).hexdigest()),(27822,'c67bff55fa29c5f89000c3afdc9c7c66305612b13a8a1d85976e5872cee086d7'))
  s=b.decode();self.assertIn('request_id_item = f"{request_id}-{i}"',s);self.assertIn('self.engine_client.generate(\n                    engine_input,\n                    sampling_params,\n                    request_id_item,',s)
  self.assertIn("engine_id=event['after_request_id']",self.texts['consume_native_2k.py'])
  self.assertIn('install_assignment(InputProcessor,emit)',self.texts['native_2k_prefill_observer.py'])
 def test_actual_public_consumer_four_rank_randomized_join_and_rejections(self):
  # Virtual JSON readset only: no physical SOURCE_BOUND/ticket/HTTP/worker is
  # created. The actual public consumer and original native worker_flags run.
  p=json.loads(R.checked(R.TEMPLATE).read_bytes())
  native=mod('native_ar_control_consumer',R.checked(p['files']['native_ar_control_consumer.py']).read_text(),R.PARENT/'native_ar_control_consumer.py')
  records={};refs={};root=Path('/unit-native2k');client=root/'client';receipts=root/'receipts'
  def put(path,value):
   b=json.dumps(value,sort_keys=True).encode();rr=dict(path=str(path),bytes=len(b),sha256=hashlib.sha256(b).hexdigest());records[str(path)]=value;refs[str(path)]=rr;return rr
  runtime=fixture()[4];ids=list(range(2048));header='native-2k-prefill-unit';engine='actual-randomized-engine-id'
  processor=dict(path='/fixture/input_processor.py',bytes=1,sha256='c5673988c0f7cfec268220e3f044e718702c015a4f236c020937cfd40a793f15')
  serving=dict(path='/fixture/serving.py',bytes=27822,sha256='c67bff55fa29c5f89000c3afdc9c7c66305612b13a8a1d85976e5872cee086d7')
  manifest=dict(performance_arm='native_ar',native_2k_request_identity='unit',runtime_sources=runtime,native_2k_input_processor_ref=processor,native_2k_completion_serving_ref=serving,
   files={'consume_native_2k.py':R.ref(HERE/'consume_native_2k.py'),'native_ar_control_consumer.py':p['files']['native_ar_control_consumer.py']})
  put(client/'INPUTS.json',dict(source=SR,token_ids=ids,input_tokens=2048))
  response=put(client/'HTTP.json',dict(id='cmpl-'+header,usage=dict(prompt_tokens=2048,completion_tokens=1),choices=[dict(index=0,token_ids=[9])]))
  body=dict(model='qwen36-mxr-eager',prompt=ids,max_tokens=1,temperature=0,top_p=1,n=1,stream=False,ignore_eos=True,return_token_ids=True,seed=0)
  put(client/'HTTP_RESULT.json',dict(schema='native.2k-prefill-http/v1',source=SR,status=200,header=header,request=body,response=response,**N.FALSES))
  put(receipts/'NATIVE2K-ASSIGNMENT.json',dict(schema='native.actual-2k-assignment/v1',source=SR,input_processor_ref=processor,completion_serving_ref=serving,
   event=dict(schema='vllm023.actual-assignment/v1',source_sha256=processor['sha256'],before_request_id='cmpl-'+header+'-0',after_request_id=engine,identity=dict(pid=99,start_ticks=100,cgroup='fixture'),disable_request_id_randomization=False)))
  put(receipts/'SERVER_COMMAND.json',dict(source=SR,performance_arm='native_ar',native_MTP=False,num_speculative_tokens=0,argv=['python','api','--tensor-parallel-size','4']))
  bindings=[]
  for rank in range(4):
   obs,_,worker,registry,_=fixture(rank)
   rr=put(receipts/('NATIVE2K-PREFILL-RANK-%d.json'%rank),obs)
   put(receipts/('NATIVE2K-LOADED-RANK-%d.json'%rank),registry)
   worker.update(schema='dense.native-worker-snapshot/v090',source_ref=SR,native_core=True,native_inverse=True,allow_hf32=False,
    runtime_environment=dict(HCCL_DETERMINISTIC='true',VLLM_PLUGINS='ascend,dense_opportunity090',ASCEND_RT_VISIBLE_DEVICES='0,1,2,3'),active_bole_environment_names=[],
    native_2k_observation=dict(source=SR,pid=worker['pid'],rank=rank,receipt=rr,request_id=engine,request_absent=True))
   bindings.append(dict(host=dict(pid=1000+rank),guest=worker))
  put(root/'WORKER_BINDINGS.json',bindings)
  class C:
   def ref(self,path):
    if str(path)in refs:return refs[str(path)]
    return R.ref(path)
   def obj(self,rr):
    self.test.assertEqual(refs[rr['path']],rr);return records[rr['path']]
  C.test=self
  def consume():return N.consume(C=C(),source=SR,manifest=manifest,client_output=client,receipt_root=receipts)
  with patch.dict(sys.modules,{'native_ar_control_consumer':native}):
   result=consume();self.assertEqual(len(result['rows']),4);self.assertIs(result['live_candidate_binding_proven'],False)
   actual=bindings[0]['guest']['native_2k_observation']
   for key,wrong in [('request_id',header),('request_absent',False)]:
    original=actual[key];actual[key]=wrong
    with self.assertRaises(ValueError):consume()
    actual[key]=original
   obs=records[str(receipts/'NATIVE2K-PREFILL-RANK-3.json')];obs['rank']=2
   with self.assertRaises(ValueError):consume()
if __name__=='__main__':unittest.main()
