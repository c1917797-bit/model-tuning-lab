"""Actual-source AST CPU controls; no installed Ascend/NPU claim."""
import ast,copy,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
import torch
import sourceio as C,native_dtype131r13 as N
P=Path(__file__).parent
class Tests(unittest.TestCase):
 def test_all_finite_bf16_values_roundtrip_and_signed_zero_without_mutation(self):
  bits=torch.arange(-32768,32768,dtype=torch.int32).to(torch.int16);x=bits.view(torch.bfloat16);x=x[torch.isfinite(x)].reshape(1,-1);before=x.view(torch.int16).clone();out=N.promote(torch,x)
  self.assertEqual(out.dtype,torch.float32);self.assertTrue(torch.equal(out.to(torch.bfloat16).view(torch.int16),before));self.assertTrue(torch.equal(x.view(torch.int16),before));y=torch.tensor([[1.,-0.]],dtype=torch.float32);self.assertIs(N.promote(torch,y),y)
  import consume_model as V
  policy=dict(lmhead_tp=False,reduce_sample=True,vocab_size=8)
  global_logits=torch.tensor([[0.,1.,2.,3.,4.,5.,6.,7.]],dtype=torch.float32)
  rows=[dict(policy=policy,local=global_logits[:,i*2:i*2+2].to(torch.bfloat16),global_logits=global_logits.clone(),target=global_logits.clone(),tokens=(1,2,3),children=torch.tensor([[7,6]]))for i in range(4)]
  self.assertTrue(V.vocabulary_join(torch,rows));rows[0]['local']=rows[0]['local'].float()
  with self.assertRaises(ValueError):V.vocabulary_join(torch,rows)
  rows[0]['local']=rows[0]['local'].to(torch.bfloat16);rows[0]['local'][0,0]=float('nan')
  with self.assertRaises(ValueError):V.vocabulary_join(torch,rows)
 def test_nan_inf_other_dtype_and_dimension_still_reject(self):
  for x in(torch.tensor([[float('nan')]],dtype=torch.bfloat16),torch.tensor([[float('inf')]]),torch.tensor([[float('-inf')]]),torch.ones((1,2),dtype=torch.float16),torch.ones(2,dtype=torch.bfloat16)):
   with self.assertRaises(ValueError):N.promote(torch,x)
 def test_actual_override_normal_body_dtype_gather_slice_and_source_controls(self):
  files={'ascend_vocab':P/'evidence/actual660_ascend_vocab_parallel_embedding.py','vocab_parallel':P/'evidence/actual660_vocab_parallel_embedding.py','logits_processor':P/'evidence/actual660_logits_processor.py'}
  mods={};config=types.SimpleNamespace(enable_reduce_sample=True);gathers=[]
  def load(key,classes,base=object):
   path=files[key];tree=ast.parse(path.read_bytes());ns=types.ModuleType('_actual_'+key);ns.__file__=str(path);ns.__dict__.update(torch=torch,LogitsProcessor=base,ParallelLMHead=object,PluggableLayer=object,QuantizeMethodBase=object,get_ascend_config=lambda:config,lmhead_tp_enable=lambda:False,envs=types.SimpleNamespace(VLLM_BATCH_INVARIANT=False),dispatch_unquantized_gemm=lambda:lambda layer,x,w,bias:x)
   selected=[]
   for name,methods in classes:
    cls=copy.deepcopy(next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name==name));cls.decorator_list=[];cls.body=[n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name in methods]or[ast.Pass()];selected.append(cls)
   body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),*selected];exec(compile(ast.fix_missing_locations(ast.Module(body=body,type_ignores=[])),str(path),'exec'),ns.__dict__);mods[ns.__name__]=ns;return ns
  lpbase=load('logits_processor',[('LogitsProcessor',('forward',))]);asc=load('ascend_vocab',[('AscendLogitsProcessor',('_get_logits','_get_logits_normal')),('AscendParallelLMHead',())],lpbase.LogitsProcessor);qmod=load('vocab_parallel',[('UnquantizedEmbeddingMethod',('apply',))])
  with patch.dict(sys.modules,mods):
   lp=asc.AscendLogitsProcessor();lp.logits_as_input=False;lp.soft_cap=None;lp.scale=1.;lp.org_vocab_size=4
   lp._gather_logits=lambda x:gathers.append(True)or torch.cat([x,x],dim=-1)
   head=asc.AscendParallelLMHead();head.quant_method=qmod.UnquantizedEmbeddingMethod();head.weight=torch.ones((2,2),dtype=torch.bfloat16);head.num_org_embeddings_per_partition=2
   model=types.SimpleNamespace(logits_processor=lp,lm_head=head);m=dict(runtime_sources={k:C.ref(v)for k,v in files.items()});self.assertTrue(N.validate_sources(C,m,model))
   x=torch.tensor([[1,2,3]],dtype=torch.bfloat16);y=lp.forward(head,x);self.assertEqual(y.dtype,torch.bfloat16);self.assertTrue(torch.equal(y,x[:,:2]));self.assertEqual(gathers,[])
   config.enable_reduce_sample=False;y=lp.forward(head,x);self.assertEqual(y.shape,(1,4));self.assertEqual(gathers,[True]);self.assertEqual(y.dtype,torch.bfloat16)
   original=head.quant_method;head.quant_method=types.SimpleNamespace(apply=original.apply)
   with self.assertRaises(ValueError):N.validate_sources(C,m,model)
   head.quant_method=original;bad=dict(runtime_sources=dict(m['runtime_sources']));bad['runtime_sources']['ascend_vocab']=C.ref(files['logits_processor'])
   with self.assertRaises(ValueError):N.validate_sources(C,bad,model)
   lp._get_logits_normal=lp._get_logits
   with self.assertRaises(ValueError):N.validate_sources(C,m,model)
if __name__=='__main__':unittest.main()
