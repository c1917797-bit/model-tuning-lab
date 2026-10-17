"""Real CPU tensors and installed method ASTs; no backend qualification."""
import ast,sys,types,unittest,__future__,os,tempfile
from pathlib import Path
from unittest.mock import patch
import torch as t
import input_identity as I,worker_entry as W,sourceio as C
P=Path(__file__).resolve().parent

def function(path,cls,name):
 tree=ast.parse(path.read_bytes());node=next(x for x in tree.body if isinstance(x,ast.ClassDef)and x.name==cls)
 fn=next(x for x in node.body if isinstance(x,ast.FunctionDef)and x.name==name)
 ns={};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(path),'exec',flags=__future__.annotations.compiler_flag),ns)
 return ns[name]

class Tests(unittest.TestCase):
 def fixture(self):
  base=P/'evidence/base_runner.py';runner=P/'evidence/runner.py';q=P/'evidence/qwen3_5.py';n=P/'evidence/qwen3_next.py'
  GPU=type('GPUModelRunner',(),{k:function(base,'GPUModelRunner',k)for k in('_preprocess','_prepare_mm_inputs')})
  R=type('NPUModelRunner',(GPU,),{'_preprocess':function(runner,'NPUModelRunner','_preprocess')});r=R()
  ids=t.arange(131,dtype=t.int32);request=types.SimpleNamespace(prompt_token_ids=ids.tolist(),prompt_embeds=None,mm_features=[],prompt_is_token_ids=None)
  r.input_batch=types.SimpleNamespace(req_ids=['actual'],req_id_to_index={'actual':0},token_ids_cpu=ids[None,:].clone());r.requests={'actual':request};r.input_ids=types.SimpleNamespace(gpu=ids)
  r.supports_mm_inputs=True;r.enable_prompt_embeds=False;r.model_config=types.SimpleNamespace(is_encoder_decoder=False)
  inner=types.SimpleNamespace(embed_tokens=lambda x:x[:,None].expand(131,5120).to(t.bfloat16))
  inner.embed_input_ids=types.MethodType(function(n,'Qwen3NextModel','embed_input_ids'),inner)
  head=types.SimpleNamespace(model=inner);head.embed_input_ids=types.MethodType(function(q,'Qwen3_5ForCausalLMBase','embed_input_ids'),head)
  worker=types.SimpleNamespace(model_runner=r,_bole_model_objects={'outer':head})
  refs={k:C.ref(p)for k,p in [('runner',runner),('base_runner',base),('qwen35',q),('qwen_next',n)]}
  return worker,inner,head,refs
 def test_actual_source_embedded_int32_and_reject_corruption(self):
  worker,inner,head,refs=self.fixture();gpu=worker.model_runner.input_ids.gpu;emb=head.embed_input_ids(gpu)
  with patch.object(I,'actual_logits_head',return_value=types.SimpleNamespace(__self__=head)):
   result=I.capture(C,worker,inner,None,emb,None,refs)
   self.assertEqual(result['actual_input_mode'],'native-text-embeddings');self.assertEqual(result['actual_token_ids'].dtype,t.int32)
   bad=emb.clone();bad[0,0]=1
   with self.assertRaises(ValueError):I.capture(C,worker,inner,None,bad,None,refs)
   worker.model_runner.input_batch.token_ids_cpu[0,0]=99
   with self.assertRaises(ValueError):I.capture(C,worker,inner,None,emb,None,refs)
 def test_direct_dtype_and_mm_reject(self):
  worker,inner,head,refs=self.fixture();gpu=worker.model_runner.input_ids.gpu
  self.assertEqual(I.capture(C,worker,inner,gpu,None,None,refs)['actual_input_mode'],'native-token-ids')
  with self.assertRaises(ValueError):I.capture(C,worker,inner,gpu.to(t.int64),None,None,refs)
  worker.model_runner.requests['actual'].mm_features=['image']
  with self.assertRaises(ValueError):I.capture(C,worker,inner,gpu,None,None,refs)
 def test_actual_native_prepare_mm_inputs_keeps_none_and_embeddings(self):
  worker,inner,head,refs=self.fixture();r=worker.model_runner
  r.model=types.SimpleNamespace(requires_raw_input_tokens=False)
  r.inputs_embeds=types.SimpleNamespace(gpu=head.embed_input_ids(r.input_ids.gpu))
  ids,emb=r._prepare_mm_inputs(131)
  self.assertIsNone(ids);self.assertTrue(t.equal(emb,r.inputs_embeds.gpu))
 def test_actual_HF_top_config_has_no_vocab_forwarder(self):
  tree=ast.parse((P/'evidence/configuration_utils.py').read_bytes())
  cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='PreTrainedConfig')
  self.assertFalse(any(isinstance(n,ast.FunctionDef)and n.name=='__getattr__'for n in cls.body))
  fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=='__getattribute__')
  self.assertNotIn('text_config',ast.unparse(fn))
  outer=types.SimpleNamespace(text_config=types.SimpleNamespace(vocab_size=248320))
  with self.assertRaises(AttributeError):_ = outer.vocab_size
 def test_unique_actual_text_LM_owner_and_MTP_config(self):
  q=P/'evidence/qwen3_5.py';m=P/'evidence/mtp.py'
  qm=types.ModuleType('fixture_qwen35');qm.__file__=str(q)
  mm=types.ModuleType('fixture_mtp');mm.__file__=str(m)
  Head=type('Qwen3_5ForCausalLM',(),{'__module__':qm.__name__,'compute_logits':function(q,'Qwen3_5ForCausalLMBase','compute_logits')})
  Draft=type('Qwen3_5MTP',(),{'__module__':mm.__name__,'compute_logits':function(m,'Qwen3_5MTP','compute_logits')})
  text=types.SimpleNamespace(vocab_size=248320);inner=types.SimpleNamespace(config=text,vocab_size=248320)
  h=Head();h.model=inner;h.config=text;h.model_config=types.SimpleNamespace(hf_text_config=text)
  d=Draft();d.config=types.SimpleNamespace(vocab_size=248320);drafter=types.SimpleNamespace(model=d)
  outer=types.SimpleNamespace(language_model=h,named_modules=lambda:[('',h)])
  with patch.dict(sys.modules,{qm.__name__:qm,mm.__name__:mm}):
   self.assertEqual(W.actual_vocabulary(C,outer,inner,drafter,qwen35_ref=C.ref(q),mtp_ref=C.ref(m)),248320)
   d.config.vocab_size=1
   with self.assertRaises(ValueError):W.actual_vocabulary(C,outer,inner,drafter,qwen35_ref=C.ref(q),mtp_ref=C.ref(m))
   d.config.vocab_size=248320;inner.config=types.SimpleNamespace(vocab_size=248320)
   with self.assertRaises(ValueError):W.actual_vocabulary(C,outer,inner,drafter,qwen35_ref=C.ref(q),mtp_ref=C.ref(m))
   inner.config=text;outer.named_modules=lambda:[('',h),('duplicate',h)]
   with self.assertRaises(ValueError):W.actual_vocabulary(C,outer,inner,drafter,qwen35_ref=C.ref(q),mtp_ref=C.ref(m))
 def test_real_prefill_wrapper_preserves_native_embedded_arguments(self):
  worker,_,head,refs=self.fixture();events=[];result=object()
  class Inner:
   def forward(self,input_ids,positions,intermediate_tensors=None,inputs_embeds=None):
    events.append((input_ids,positions,intermediate_tensors,inputs_embeds));return result
  inner=Inner();worker._bole_model_objects['inner']=inner
  ctx=types.SimpleNamespace(attn_metadata={'gdn':types.SimpleNamespace(num_prefills=1)})
  def context():return ctx
  observed={'actual_token_ids':worker.model_runner.input_ids.gpu.clone(),'actual_input_mode':'native-text-embeddings'}
  seen=[]
  def callback(**kw):seen.append(kw)
  pos=t.arange(131);emb=head.embed_input_ids(worker.model_runner.input_ids.gpu)
  with tempfile.TemporaryDirectory()as td:
   sr=C.write(Path(td)/'source.json',dict(files={'input_identity.py':C.ref(I.__file__)},runtime_sources=refs))
   with patch.dict(os.environ,BOLE_MODEL_OBJECT_AUDIT_ENABLE='1'),patch.object(I,'capture',return_value=observed)as cap:
    restore=W.install_after_native_prefill(worker,C,qwen_next_ref=C.ref(__file__),get_forward_context=context,context_source_ref=C.ref(__file__),callback=callback,callback_source_ref=C.ref(__file__),native_input_source_ref=sr)
    self.assertIs(inner.forward(None,pos,None,emb),result);restore()
    cap.assert_called_once();self.assertIs(events[0][0],None);self.assertIs(events[0][1],pos);self.assertIs(events[0][3],emb)
    self.assertIs(seen[0]['native_input'],observed);self.assertTrue(t.equal(seen[0]['input_ids'],observed['actual_token_ids']))
