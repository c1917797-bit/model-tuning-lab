"""Execute exact installed-source method AST without imports/Torch/HAL."""
import ast,hashlib,unittest
from pathlib import Path
from types import SimpleNamespace as N
P=Path(__file__).parent/'evidence'
def method(file,cls,name,scope):
 tree=ast.parse((P/file).read_bytes());node=next(x for x in tree.body if isinstance(x,ast.ClassDef)and x.name==cls)
 fn=next(x for x in node.body if isinstance(x,ast.FunctionDef)and x.name==name)
 fn.decorator_list=[]
 future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
 exec(compile(ast.fix_missing_locations(ast.Module(body=[future,fn],type_ignores=[])),str(P/file),'exec'),scope)
 return scope[name]
class Tests(unittest.TestCase):
 def test_actual_out_proj_selector_is_not_o_proj_branch(self):
  raw=(P/'ascend_linear_op.py').read_bytes()
  self.assertEqual(hashlib.sha256(raw).hexdigest(),'0333d3229dbfed3010413510b76395a9ad89138dfd1d578caab057573b6cd0fb')
  fn=next(x for x in ast.parse(raw).body if isinstance(x,ast.FunctionDef)and x.name=='_get_row_parallel_op')
  flags={'matmul':False,'flash':False,'sp':False};hits=[]
  scope={k:(lambda *a:False)for k in ('oproj_tp_enable','enable_dsa_cp_with_layer_shard','mlp_tp_enable','is_moe_layer')}
  scope.update(matmul_allreduce_enable=lambda:flags['matmul'],flashcomm2_enable=lambda:flags['flash'],enable_sp=lambda:flags['sp'])
  for name in ('DSV4OProjRowParallelOp','ShardedCPRowParallelOp','MLPRowParallelOp','OProjRowParallelOp','MatmulAllreduceRowParallelOp','Flashcomm2OProjRowParallelOp','SequenceRowParallelOp'):
   scope[name]=lambda layer,name=name:(hits.append(name),name)[1]
  future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
  exec(compile(ast.fix_missing_locations(ast.Module(body=[future,fn],type_ignores=[])),'actual-selector','exec'),scope)
  choose=scope['_get_row_parallel_op'];layer=object();prefix='model.layers.0.linear_attn.out_proj'
  self.assertIsNone(choose(prefix,layer))
  for flag,name in [('sp','SequenceRowParallelOp'),('flash','Flashcomm2OProjRowParallelOp'),('matmul','MatmulAllreduceRowParallelOp')]:
   flags[flag]=True;self.assertEqual(choose(prefix,layer),name)
 def test_actual_custom_route_one_call_preserves_objects(self):
  self.assertEqual(hashlib.sha256((P/'ascend_linear.py').read_bytes()).hexdigest(),'3f14a92019a6612158ba41a26c358c8f164cbda66b743c518a5e4019694b5dc3')
  calls=[];x=object();result=(object(),None)
  fn=method('ascend_linear.py','AscendRowParallelLinear','forward',{})
  obj=N(custom_op=N(apply=lambda value:(calls.append(value),result)[1]))
  self.assertIs(fn(obj,x),result);self.assertEqual(calls,[x])
 def test_actual_generic_route_local_then_collective_once(self):
  calls=[];x=object();local=object();reduced=object()
  def apply(layer,value,bias):calls.append(('local',layer,value,bias));return local
  def reduce(value):calls.append(('collective',value));return reduced
  fn=method('vllm_linear.py','RowParallelLinear','forward',{'tensor_model_parallel_all_reduce':reduce})
  obj=N(input_is_parallel=True,tp_rank=0,skip_bias_add=False,bias=None,quant_method=N(apply=apply),reduce_results=True,tp_size=4,return_bias=True)
  result=fn(obj,x);self.assertIs(result[0],reduced)
  self.assertEqual(calls,[('local',obj,x,None),('collective',local)])
 def test_actual_quant_apply_keeps_weight_and_input(self):
  calls=[];x=object();weight=object();bias=object();result=object()
  def gemm(*args):calls.append(args);return result
  fn=method('ascend_linear.py','AscendUnquantizedLinearMethod','apply',{'torch':N(ops=N(vllm=N(unquantized_gemm=gemm)))})
  self.assertIs(fn(object(),N(weight=weight),x,bias),result)
  self.assertEqual(calls,[(x,weight,bias)])
if __name__=='__main__':unittest.main()
