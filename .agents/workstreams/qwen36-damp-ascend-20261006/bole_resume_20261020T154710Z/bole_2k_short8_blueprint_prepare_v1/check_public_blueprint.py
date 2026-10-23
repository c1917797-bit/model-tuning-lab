"""Actual public SOURCE/command/phase tests using original readonly memory adapter."""
import ast,copy,hashlib,json,sys,time,types
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import short2k_blueprint as B

def data(x):return (json.dumps(x,sort_keys=True,allow_nan=False)+'\n').encode()
def reference(p,b):return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())

def fixture():
 path=B.WORK/'fastpath_clock_seam_prepare_v1/check_public_clock.py'
 source=path.read_bytes()
 B.need(len(source)==9447 and hashlib.sha256(source).hexdigest()=='40ed89de927474f31fe3934302059acf0d3bcd9619e8b3a140125fc27ba231da','pinned original full clock fixture')
 fn=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)and n.name=='fixture')
 class Review(ast.NodeTransformer):
  def visit_Assign(self,node):
   if any(isinstance(t,ast.Name)and t.id=='review'for t in node.targets):
    node.value.keywords.append(ast.keyword(arg='short2k_helper_refs',value=ast.parse("m['short2k_helper_refs']",mode='eval').body))
   return self.generic_visit(node)
 fn=Review().visit(fn);tree=ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[]))
 ns=dict(BUILD=types.SimpleNamespace(render=B.render,inverse=B.inverse),Path=Path,types=types,
  json=json,copy=copy,time=time,ast=ast,reference=reference,data=data)
 exec(compile(tree,str(path),'exec'),ns);return ns['fixture']()

def main():
 B.need(sys.argv[1:]==['--check'],'pure memory --check only')
 b,extra,sr,authority=fixture();events=[]
 B.inverse(b);events.append('actual-Q419-whole-input-clock-components-b53-codec-inverse')
 def run(virtual,bundle,root):
  import sourceio as C
  import qualification_source_validate as V
  import contract090 as CONTRACT
  import host_service as HOST
  import owned_substrate as OWNED
  proof=V.validate(sr)
  C.need(proof['source_validated']is True and proof['actual_NPU_two_generation_qualified']is False,
   'actual full2k public validator, no fabricated success row')
  events.append('actual-public-full-source-reconstruction-component-command-readset')
  C.need(CONTRACT.source(sr)==bundle['manifest'],'actual public SOURCE whole equality')
  events.append('actual-contract-SOURCE')
  class Stop(Exception):pass
  def stop(*args,**kwargs):raise Stop('PREDEVICE before owned helper load')
  model=json.loads(virtual[str(root/'COMMANDS.json')])['model'];ix=model.index('/usr/bin/python3')
  virtual['/proc/self/cmdline']=b'\0'.join(x.encode()for x in model[ix:])+b'\0'
  import resource
  argv=[str(root/'host_service.py'),'--execute','--source-ref',json.dumps(sr),'--output',bundle['manifest']['output_root']]
  env=dict(BOLE_MODEL131_MAIN_ENABLE='1',DENSE090_EXTERNAL_OUTPUT_ENABLE='1',
   BOLE_PAIRED_PERFORMANCE_ENABLE='1',BOLE_SHORT_STATE_DIGEST_ENABLE='1',
   BOLE_FASTPATH_NUMERIC_QUALIFICATION_ENABLE='1',BOLE_NATIVE_2K_GEOMETRY_ENABLE='1',
   BOLE_STATE_CAPTURE_CODEC_ENABLE='1')
  with patch.object(sys,'argv',argv),patch.dict('os.environ',env),patch.object(OWNED,'load',stop),\
       patch('os.sched_setaffinity',lambda *a:None),patch.object(resource,'getrlimit',lambda *a:(resource.RLIM_INFINITY,resource.RLIM_INFINITY)),\
       patch.object(resource,'setrlimit',lambda *a:None):
   try:HOST.main()
   except Stop:events.append('actual-host-MODEL-command-phase-predevice')
   else:raise ValueError('public HOST must stop before device/ownership')
  def reject(action,label):
   try:action()
   except ValueError as e:events.append(dict(rejected=label,actual_error=str(e)))
   else:raise ValueError('negative accepted '+label)
  absent=copy.deepcopy(bundle['manifest']);absent['qualification_authority_ref']=None
  reject(lambda:V.execution_window(absent,clock=True,require_phase=True),'NULL-authority')
  stale=copy.deepcopy(authority);stale['scope']['input_tokens']=131
  r=reference(root/'SYNTHETIC_BAD_SCOPE.json',data(stale));virtual[r['path']]=data(stale)
  wrong=copy.deepcopy(bundle['manifest']);wrong['qualification_authority_ref']=r
  reject(lambda:V.execution_window(wrong,clock=True,require_phase=True),'old131-authority')
  badreview=json.loads(extra[authority['MAIN_review_ref']['path']]);badreview['short2k_helper_refs']={}
  rr=reference(root/'SYNTHETIC_BAD_REVIEW.json',data(badreview));virtual[rr['path']]=data(badreview)
  a=copy.deepcopy(authority);a['MAIN_review_ref']=rr;ar=reference(root/'SYNTHETIC_BAD_HELPER_AUTH.json',data(a));virtual[ar['path']]=data(a)
  wrong=copy.deepcopy(bundle['manifest']);wrong['qualification_authority_ref']=ar
  reject(lambda:V.execution_window(wrong,clock=False,require_phase=False),'MAIN-helper-closure-mismatch')
  import numeric_prefix_2k as PREFIX
  import state_capture_codec as SC
  import fa_native_geometry as GEO
  reject(lambda:GEO.require(None),'actual-live-prefill-geometry-missing')
  reject(lambda:PREFIX.require_runtime_admission(C,bundle['manifest'],None),'actual-numeric-prefill-and-joint-admission-unbound')
  reject(lambda:SC.require_runtime_admission(C,bundle['manifest']),'actual-codec-joint-measurement-unbound')
  # Run the REAL derived Observer constructor: it reaches PREFIX hard refusal before tensor use.
  import fastpath_numeric_observer as FQ
  with patch.dict('os.environ',{'BOLE_FASTPATH_NUMERIC_QUALIFICATION_ENABLE':'1'}):
   reject(lambda:FQ.install(None,C,sr,bundle['manifest'],0,snapshot=None,sink=None),'actual-observer-reaches-runtime-hard-refusal')
  # Prove actual source review does not accept a mutated whole source as recipe PASS.
  changed=copy.deepcopy(bundle['manifest']);changed['files']['service_runner.py']['sha256']='0'*64
  reject(lambda:V.execution_window(changed,clock=False,require_phase=False),'whole-source-file-mismatch')
 path=B.WORK/'fastpath_numeric_bridge_prepare_v1/check_source_imports.py'
 tree=ast.parse(path.read_text())
 class Adapt(ast.NodeTransformer):
  def visit_Assign(self,node):
   if any(isinstance(t,ast.Name)and t.id=='b'for t in node.targets):
    return ast.copy_location(ast.Assign(targets=node.targets,value=ast.Name(id='FIXTURE',ctx=ast.Load())),node)
   if any(isinstance(t,ast.Subscript)and isinstance(t.value,ast.Name)and t.value.id=='virtual'for t in node.targets):
    return [node,ast.Expr(ast.Call(func=ast.Attribute(value=ast.Name(id='virtual',ctx=ast.Load()),attr='update',ctx=ast.Load()),args=[ast.Name(id='EXTRA',ctx=ast.Load())],keywords=[]))]
   return self.generic_visit(node)
  def visit_Expr(self,node):
   if isinstance(node.value,ast.Call)and ast.unparse(node.value.func)=='Q.inverse':return None
   return self.generic_visit(node)
  def visit_With(self,node):
   if node.body and isinstance(node.body[0],ast.Import)and any(n.name=='qualification_source_validate'for n in node.body[0].names):
    node.body=ast.parse('RUN(virtual,b,root)').body;return node
   return self.generic_visit(node)
 tree=ast.fix_missing_locations(Adapt().visit(tree))
 ns=dict(__name__='_whole2k_memory_adapter',__file__=str(path),FIXTURE=b,EXTRA=extra,RUN=run)
 with patch.object(sys,'argv',[str(path),'--reconstruct-only']):
  exec(compile(tree,'original-readonly-adapter-with-new-fixture','exec'),ns);ns['main']()
 print(json.dumps(dict(schema='bole.synthetic-whole2k-short8-public-chain/v1',files=len(b['files']),
  events=events,physical_BOUND=False,physical_authority=False,actual_bound_validated=False,
  whole2k_ready=False,numerical_qualified=False,NPU=False)))
if __name__=='__main__':main()
