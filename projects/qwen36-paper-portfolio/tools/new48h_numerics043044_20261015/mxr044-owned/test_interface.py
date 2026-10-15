"""CPU software contract tests; no synthetic evidence is an experiment PASS."""
import ast,copy,importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import probe_contract as G,common as C
def probe():return dict(schema='mxr.block-refinement-owned-probe/v044',source={'software-only':1},raws=[dict(path='/software-only/%d'%i)for i in range(9)],primary=None,outputs_per_case=3,NPU=True,pool_released=True,mapped_library=['software-only'],actual_algorithm_identity={'software-only':True},model_ready=False)
class Controls(unittest.TestCase):
 def test_actual_nine_case_producer_contract_and_partial_negatives(self):
  v=probe();self.assertTrue(G.ready(v,v['source']))
  for key,value in(('primary','retainedfail'),('raws',v['raws'][:8]),('outputs_per_case',2),('pool_released',False),('mapped_library',[]),('source',{'old042':1})):
   self.assertFalse(G.ready(dict(v,**{key:value}),v['source']))
  q=copy.deepcopy(v);q['raws'][8]=q['raws'][0];self.assertFalse(G.ready(q,v['source']))
 def test_actual_receiver_contract_all27_outputs_and_no_model_permission(self):
  sr={'software-only':1};v=dict(schema='mxr.block-refinement-owned-consumer/v044',source=sr,complete=True,rows=[{}]*9,case_outputs=[3]*9,numerical_qualification_granted=False,model_ready=False,performance_ready=False)
  self.assertTrue(G.consumer_ready(v,sr))
  for key,value in(('complete',False),('rows',[{}]*8),('case_outputs',[3]*8+[2]),('model_ready',True),('numerical_qualification_granted',True)):
   self.assertFalse(G.consumer_ready(dict(v,**{key:value}),sr))
 def test_real_host_child_and_cpu_report_contract_are_new_not_fourarm(self):
  t=(P/'mainhost.py').read_text();self.assertIn("m['_probe_contract'].consumer_ready(v,sr)",t);self.assertNotIn('m[\'_probe_contract\'].FRAMES*m[\'_probe_contract\'].REPEATS',t)
  self.assertIn("output=str(leaf/'numeric/cases')",t);self.assertIn("source=m['component044_source']",t);self.assertIn("run-mxr-block-refinement044-",t)
  self.assertIn("refs.extend([plan,probe,v['actual_result'],*v['raws']])",t)
  parsed=ast.parse(t)
  keys={n.slice.value for n in ast.walk(parsed)if isinstance(n,ast.Subscript)and isinstance(n.value,ast.Subscript)and isinstance(n.value.value,ast.Name)and n.value.value.id=='m'and isinstance(n.value.slice,ast.Constant)and n.value.slice.value=='files'and isinstance(n.slice,ast.Constant)}
  self.assertTrue(all((P/key).is_file()for key in keys),keys)
  child=ast.parse((P/'replay.py').read_bytes());call=next(n for n in ast.walk(child)if isinstance(n,ast.Call)and ast.unparse(n.func)=='Q.produce');kw={k.arg:ast.unparse(k.value)for k in call.keywords}
  self.assertEqual(kw['output'],"out / 'cases'");self.assertEqual(kw['source_ref'],"m['component044_source']");self.assertEqual(kw['deadline_monotonic'],'child_deadline')
  self.assertIn("L.KeepalivePool(512*1024**2,2)",(P/'replay.py').read_text());self.assertNotIn('32*1024**2',(P/'replay.py').read_text())
 def test_true_defaultOFF_cold_argv_and_helpless_no_hardware_import(self):
  for name in('bind.py','mainhost.py','replay.py','consume.py','cpu_preflight.py','software_controls.py'):
   r=subprocess.run([sys.executable,'-I','-B',str(P/name)],capture_output=True,text=True);self.assertEqual(r.returncode,0,(name,r.stderr));self.assertEqual(json.loads(r.stdout),dict(enabled=False,NPU=False))
 def test_actual_consumer_wrapper_retains_failed_metric_without_falsequalification(self):
  spec=importlib.util.spec_from_file_location('_044realconsumercontrol',P/'consume.py');M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
  with tempfile.TemporaryDirectory()as td:
   out=Path(td)/'RESULT.json';sr={'software-only':1};pr={'software-probe':1};cr={'software-component':1};ar={'software-actual-result':1};v=probe();v['actual_result']=ar
   import torch
   refs=[]
   for i in range(9):
    path=Path(td)/('software-%d.pt'%i);torch.save(dict(outputs=[torch.zeros(1)]*3,operator=v['actual_algorithm_identity']),path);refs.append(C.ref(path))
   v['raws']=refs
   actual=dict(source=cr,raws=refs);m=dict(component044_source=cr,files={'probe_contract.py':{'software':'contract'}});component=dict(files={'qualification_probe.py':{'software':'independent'}})
   # Real receiver body runs; only absent independently owned044 API is a
   # software double. This never substitutes a numeric correctness control.
   def independent(cs,actualref,target):
    C.write(target,dict(source=cr,actual_result=ar,complete=True,rows=[dict(pass_gate=False)]*9,pass_gate=False));return 3
   realobj=C.obj
   def objects(r):return v if r==pr else component if r==cr else actual if r==ar else realobj(r)
   api=SimpleNamespace(consume=independent)
   with patch.object(M.C,'source',return_value=m),patch.object(M.C,'obj',side_effect=objects),patch.object(M.C,'load',side_effect=lambda r,n:G if 'contract'in n else api),patch.object(G,'ready',return_value=True),patch.object(sys,'argv',['consume.py','--execute','--source-ref',json.dumps(sr),'--probe-ref',json.dumps(pr),'--output',str(out)]):
    M.main()
   value=json.loads(out.read_bytes());self.assertTrue(G.consumer_ready(value,sr));self.assertFalse(value['pass_gate']);self.assertFalse(value['numerical_qualification_granted'])
   # The actual host remains diagnostic even when all raw outputs exist; a
   # metric failure is retained and never converted to numerical permission.
 def test_real_meta_geometry_all_nine_cases_no_dispatcher_or_NPU_claim(self):
  import torch
  torch.set_num_threads(1)
  # Sameimage CPU tests use the real bound component Ref path. The local
  # sibling fallback is only for this source-only Windows software review.
  if(P/'SOURCE_MANIFEST.json').is_file():component=C.checked(C.obj(C.ref(P/'SOURCE_MANIFEST.json'))['component044_source']).parent
  else:component=P.parent/'mxr-block-refinement-new48h-044'
  def load(name):
   s=importlib.util.spec_from_file_location('_044owned_meta_'+name,component/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
  B=load('block_refine');Q=load('qualification_probe');cases=Q.recipes();self.assertEqual(len(cases),9)
  for name,cu in cases:
   A=torch.empty((1,cu[-1],12,64),dtype=torch.float32,device='meta');tiles,groups=B.plan(cu,cu[-1]);out=torch.empty_like(A,dtype=torch.bfloat16)
   result=B._correct_blocks(torch,A,torch.empty_like(A),groups,out,B.allocate(torch,A))
   self.assertEqual(result.shape,A.shape);self.assertEqual(result.device.type,'meta');self.assertEqual(result.dtype,torch.bfloat16);self.assertTrue(B.budget(cu,cu[-1])['formal_one_live_fit'])
if __name__=='__main__':unittest.main()
