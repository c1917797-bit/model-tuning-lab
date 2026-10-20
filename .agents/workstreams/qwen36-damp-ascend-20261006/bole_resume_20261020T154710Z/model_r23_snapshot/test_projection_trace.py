import hashlib,importlib.util,sys,types,unittest
from pathlib import Path
P=Path(__file__).parent;sys.path.insert(0,str(P))
import projection_trace as W
S=P/'evidence'
def ref(p):
 b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
class C:
 ref=staticmethod(lambda p:ref(Path(p)))
 checked=staticmethod(lambda r:Path(r['path']))
def native(file,qualname,scope):
 p=S/file;mod=types.ModuleType('_software_'+file.replace('.','_')+'_'+str(len(sys.modules)));mod.__file__=str(p);mod.__dict__.update(scope);sys.modules[mod.__name__]=mod
 codes=[]
 def visit(c,path=()):
  path=path+(()if c.co_name=='<module>'else(c.co_name,))
  if getattr(c,'co_qualname','.'.join(path))==qualname:codes.append(c)
  for x in c.co_consts:
   if isinstance(x,types.CodeType):visit(x,path)
 visit(compile(p.read_bytes(),str(p),'exec',dont_inherit=True))
 f=types.FunctionType(codes[0],mod.__dict__);f.__qualname__=qualname;return f
class Tests(unittest.TestCase):
 def fixture(self):
  local=object();reduced=object();ops=[]
  def gemm(x,w,b):ops.append(('gemm',x,w,b));return local
  def collective(x):ops.append(('collective',x));return reduced
  q=native('ascend_linear.py','AscendUnquantizedLinearMethod.apply',{'torch':types.SimpleNamespace(ops=types.SimpleNamespace(vllm=types.SimpleNamespace(unquantized_gemm=gemm)))})
  qtype=type('SoftwareQuant',(),{'apply':q});quant=qtype()
  f=native('vllm_linear.py','RowParallelLinear.forward',{'tensor_model_parallel_all_reduce':collective})
  cls=type('SoftwareLayer',(),{'forward':f});layer=cls()
  for k,v in dict(custom_op=None,quant_method=quant,input_is_parallel=True,tp_rank=0,tp_size=4,bias=None,skip_bias_add=False,reduce_results=True,return_bias=True,prefix='model.layers.0.linear_attn.out_proj',weight=object()).items():setattr(layer,k,v)
  return layer,ops,local,reduced
 def test_actual_complete_source_body_four_calls_trace_no_extra_ops(self):
  layer,ops,local,reduced=self.fixture();ordinal=[0];rows=[]
  refs={str(S/n):ref(S/n)for n in ('ascend_linear.py','vllm_linear.py')}
  gdn=types.SimpleNamespace(out_proj=layer)
  observer=W.ProjectionTrace(C,layer,refs,lambda c,s,v:rows.append((c,s,v)),lambda:(ordinal[0],gdn))
  def trace(frame,event,arg):return trace if observer.event(frame,event,arg)else None
  x=object();old=sys.gettrace()
  try:
   sys.settrace(trace)
   for i in(0,2):ordinal[0]=i;self.assertIs(layer.forward(x)[0],reduced)
  finally:sys.settrace(old)
  result=observer.finish();self.assertFalse(result['qualified'])
  self.assertEqual(len(ops),4)
  for i in(0,2):
   stages={s for c,s,v in rows if c==i}
   self.assertIn('projection.forward.output_parallel',stages);self.assertIn('projection.forward.return',stages)
   localrows=[v['output_parallel']for c,s,v in rows if c==i and s=='projection.forward.output_parallel']
   self.assertEqual(localrows,[local])
 def test_source_or_wrapped_body_mismatch_refuses_before_trace(self):
  layer,ops,_,_=self.fixture();refs={str(S/n):ref(S/n)for n in ('ascend_linear.py','vllm_linear.py')}
  refs[str(S/'vllm_linear.py')]=dict(refs[str(S/'vllm_linear.py')],sha256='0'*64)
  with self.assertRaises(ValueError):W.ProjectionTrace(C,layer,refs,lambda *x:None,lambda:None)
  self.assertFalse(ops)
 def test_unknown_quant_source_refuses(self):
  layer,ops,_,_=self.fixture();refs={str(S/'vllm_linear.py'):ref(S/'vllm_linear.py')}
  with self.assertRaises(ValueError):W.ProjectionTrace(C,layer,refs,lambda *x:None,lambda:None)
  self.assertFalse(ops)
if __name__=='__main__':unittest.main()
