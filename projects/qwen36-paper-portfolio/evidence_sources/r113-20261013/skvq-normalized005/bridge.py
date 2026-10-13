"""Scoped normalized-common adapter; old source/mathematics stay immutable."""
import ast,copy,hashlib,importlib.util,json,os,sys,types,time
from pathlib import Path
ROOT=Path('/cache/cch/qwen36-paper-preparation-20261007/lowbit/_draft_adakv_current_prepare/R87/skvq-normalized-full47-v1-005')
DONOR={'path':'/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-full47-r87-v1-002/SOURCE_MANIFEST.json','bytes':158126,'sha256':'a533a37184c274ce62d3c13ed69abd268dcfa7baef9bdbfcec5b605e9978f6e9'}
CONFIG={'path':'/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-skvq-formal-013-r87-main-full47-001/round0-candidate/CONFIG_SMOKE_001.json','bytes':3499,'sha256':'a62f797af0c92b69280d73d80bb6ef44dee80f9105884ef74cfe5e3d0509912e'}
ENV='MAIN_SKVQ_NORMALIZED_ADAPTER_SHA'
B=None;COMMON=None;OWN=None
def need(ok,msg):
 if not ok:raise ValueError(msg)
def read(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'},'strict source Ref')
 p=Path(r['path']);need(p.is_absolute()and p.is_file()and not p.is_symlink(),'ordinary source')
 raw=p.read_bytes();need(len(raw)==r['bytes']and hashlib.sha256(raw).hexdigest()==r['sha256'],'exact source bytes');return raw
def ref(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def load(name,r,binding=None):
 import builtins
 m=types.ModuleType(name);m.__file__=r['path'];ns=dict(vars(builtins));old=ns['__import__']
 if binding is not None:
  def importer(name,globals=None,locals=None,fromlist=(),level=0):return binding if name=='binding'and level==0 else old(name,globals,locals,fromlist,level)
  ns['__import__']=importer
 m.__dict__['__builtins__']=ns;exec(compile(read(r),r['path'],'exec',dont_inherit=True),m.__dict__);return m
def common(fc):
 global COMMON
 if COMMON is not None:return COMMON
 raw=read(fc.COMMON_REF);old=ast.parse(raw,fc.COMMON_REF['path']);tree=copy.deepcopy(old);changed=[]
 class Patch(ast.NodeTransformer):
  def visit_keyword(self,n):
   if n.arg=='cudagraph_num_of_warmups':
    need(isinstance(n.value,ast.Constant)and n.value.value==2,'original common warmup2');n.value=ast.Constant(1);changed.append('policy')
   return self.generic_visit(n)
  def visit_Compare(self,n):
   if ast.unparse(n.left)=='cc.cudagraph_num_of_warmups':
    need(len(n.ops)==1 and isinstance(n.ops[0],ast.Eq)and ast.unparse(n.comparators[0])=='2','original runner warmup2');n.comparators=[ast.Constant(1)];changed.append('runner')
   return self.generic_visit(n)
 tree=Patch().visit(tree);need(changed==['policy','runner'],'all and only common warmup policy/runner')
 inverse=copy.deepcopy(tree)
 class Undo(ast.NodeTransformer):
  def visit_keyword(self,n):
   if n.arg=='cudagraph_num_of_warmups':n.value=ast.Constant(2)
   return self.generic_visit(n)
  def visit_Compare(self,n):
   if ast.unparse(n.left)=='cc.cudagraph_num_of_warmups':n.comparators=[ast.Constant(2)]
   return self.generic_visit(n)
 need(ast.dump(Undo().visit(inverse),include_attributes=False)==ast.dump(old,include_attributes=False),'complete common inverse AST')
 m=types.ModuleType('_skvq_normalized_common');m.__file__=str(ROOT/'bridge.py')
 exec(compile(ast.fix_missing_locations(tree),m.__file__,'exec'),m.__dict__)
 value=json.loads(read(CONFIG));need(value['status']=='ACTUAL_NATIVE_CONFIGURATION_CAPTURED_NOT_QUALIFIED'and value['engine_ref']==B.ENGINE and value['adapter_ref']==DONOR and value['weights_loaded']is value['AsyncLLM_created']is False,'real configuration-only diagnostic provenance')
 expected=copy.deepcopy(value['expected_common']);expected['compilation_config']['cudagraph_num_of_warmups']=1
 need(m.COMMON==expected==value['actual_common']and len(value['diffs'])==1 and all(v for k,v in value['extra_assertions'].items()if k!='actual_common_equal'),'only proven warmup normalization')
 # CLI requested additional remains original pa_shape_list. Its ACTUAL expanded
 # platform values are a separate shared effective policy, never silently copied.
 m.EFFECTIVE_ADDITIONAL=copy.deepcopy(value['extras']['additional_config'])
 need(m.EFFECTIVE_ADDITIONAL['pa_shape_list']==list(range(1,17)),'actual native PA shapes unchanged')
 m.NORMALIZATION_SOURCE=CONFIG;COMMON=m;return m
def boot(sha):
 global B,OWN
 r=ref(ROOT/'SOURCE_MANIFEST.json');need(r['sha256']==sha,'explicit normalized adapter pin')
 mf=json.loads(read(r));need(mf['schema']=='skvq.normalized-common-adapter/v1'and mf['root']==str(ROOT)and mf['donor_ref']==DONOR and mf['configuration_ref']==CONFIG,'new lineage, not relabelled engine')
 for leaf in mf['files']:read(leaf)
 need({x['path']for x in mf['files']}=={str(ROOT/n)for n in ('bridge.py','host.py','guest.py','independent.py','whole.py','skvq_normalized_worker.py','software_check.py','warmup.py')},'complete scoped seven source leaves')
 if B is not None:need(OWN==r,'one immutable adapter in process');return B
 dm=json.loads(read(DONOR));dr=next(x for x in dm['files']if x['path']==str(Path(DONOR['path']).parent/'binding.py'))
 D=load('_skvq_normalized_donor_binding',dr);D.boot(DONOR['sha256'])
 B=types.ModuleType('binding');B.__dict__.update(D.__dict__);B.ROOT=ROOT;B.own=OWN=r
 B.manifest=mf;B.boot=lambda value:(need(value==OWN['sha256'],'same normalized adapter child source')or(OWN,mf))
 oldset=D.readset_manifest
 def readset():
  original=oldset();new=dict(original);new['dependencies']=list(original['dependencies'])
  for leaf in [r,*mf['files'],CONFIG]:
   if leaf['path']not in{x['path']for x in original['files']+new['dependencies']}:new['dependencies'].append(leaf)
  return new
 B.readset_manifest=readset
 need('binding'not in sys.modules,'no foreign global binding');sys.modules['binding']=B
 # This deliberate source-qualified resolver rebinding is shared by private
 # graph and original spawned workers; old files and all other functions stay.
 sys.path.insert(0,str(Path(B.ENGINE['path']).parent))
 import formal_contract as fc
 need(ref(fc.__file__)==B.role('formal_contract.py'),'actual original contract module, not ambient replacement')
 old_loader=fc.load_common;shared=common(fc)
 def load_common(path=None):
  need(path is None or str(path)==fc.COMMON_REF['path'],'no foreign common path')
  read(fc.COMMON_REF);read(CONFIG);read(OWN);return shared
 fc.load_common=load_common
 for name,m in list(sys.modules.items()):
  if name.startswith('formal_')and getattr(m,'load_common',None)is old_loader:
   need(ref(m.__file__)==B.role(Path(m.__file__).name),'source-bound previously loaded common consumer')
   m.load_common=load_common
 B.normalized_original_loader=old_loader;B.normalized_common=shared
 cp=load('_skvq_normalized_cpu',next(x for x in dm['files']if Path(x['path']).name=='cpu_safe.py'),B)
 hp=load('_skvq_normalized_hal',next(x for x in dm['files']if Path(x['path']).name=='native_hal.py'),B)
 original_consume=hp.consume
 def consume(arm_ref,source,manifest):
  result=original_consume(arm_ref,source,manifest)
  paths=list((Path(arm_ref['path']).parent/'service').glob('NORMALIZED_CONFIG_PREASSERT-*.json'))
  need(len(paths)==1,'one actual normalized preassert configuration')
  v=B.engine.obj(ref(paths[0]));need(v['adapter_source_ref']==OWN and v['source_ref']==source and v['configuration_origin_ref']==CONFIG and v['actual_policy']==shared.COMMON and v['actual_additional_config']==shared.EFFECTIVE_ADDITIONAL and v['weights_created']is False,'actual shared effective config before unchanged production assertion')
  return result
 hp.consume=consume
 sys.modules['cpu_safe']=cp;sys.modules['native_hal']=hp
 V=load('_skvq_normalized_original_view',next(x for x in dm['files']if Path(x['path']).name=='private_view.py'),B)
 B.normalized_view=V
 warm=load('_skvq_normalized_warmup',ref(ROOT/'warmup.py'));B.warmup=warm
 B.warmup_install=warm.install(B,OWN,ref(ROOT/'warmup.py'))
 sys.path.insert(0,str(ROOT));return B
def projection(cfg):
 m,s,c,p,cc=cfg.model_config,cfg.scheduler_config,cfg.cache_config,cfg.parallel_config,cfg.compilation_config
 actual=dict(COMMON.COMMON)
 for n in ('max_model_len','enforce_eager','seed'):actual[n]=getattr(m,n)
 actual['dtype']=str(m.dtype).removeprefix('torch.')
 for n in ('max_num_seqs','max_num_batched_tokens','enable_chunked_prefill','async_scheduling'):actual[n]=getattr(s,n)
 for n in ('kv_cache_memory_bytes','enable_prefix_caching','mamba_cache_mode'):actual[n]=getattr(c,n)
 for n in ('tensor_parallel_size','data_parallel_size'):actual[n]=getattr(p,n)
 actual['compilation_config']=dict(cudagraph_mode=cc.cudagraph_mode.name,cudagraph_capture_sizes=list(cc.cudagraph_capture_sizes),cudagraph_num_of_warmups=cc.cudagraph_num_of_warmups)
 extras=dict(pipeline_parallel_size=p.pipeline_parallel_size,prefill_context_parallel_size=p.prefill_context_parallel_size,decode_context_parallel_size=p.decode_context_parallel_size,enable_dbo=p.enable_dbo,num_gpu_blocks_override=c.num_gpu_blocks_override,cache_dtype=c.cache_dtype,model=m.model,worker_cls=p.worker_cls,speculative_config=repr(cfg.speculative_config),lora_config=repr(cfg.lora_config),kv_transfer_config=repr(cfg.kv_transfer_config))
 return actual,copy.deepcopy(cfg.additional_config),extras
def worker_name_function(v,module,name):
 row=B.role(module+'.py');tree,_=B.normalized_view.transform(module,read(row),row)
 old=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name==name);fn=copy.deepcopy(old);hits=[]
 class Patch(ast.NodeTransformer):
  def visit_Constant(self,n):
   if n.value=='formal_worker.FormalWorker':
    hits.append(n);return ast.copy_location(ast.Constant('skvq_normalized_worker.FormalWorker'),n)
   return n
 fn=Patch().visit(fn);need(len(hits)==1,'one exact original worker resolver name in '+name)
 inverse=copy.deepcopy(fn)
 class Undo(ast.NodeTransformer):
  def visit_Constant(self,n):
   return ast.copy_location(ast.Constant('formal_worker.FormalWorker'),n)if n.value=='skvq_normalized_worker.FormalWorker'else n
 need(ast.dump(Undo().visit(inverse),include_attributes=False)==ast.dump(old,include_attributes=False),'complete worker-name-only inverse AST')
 namespace=v[module].__dict__
 exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(ROOT/'bridge.py'),'exec'),namespace)
 return namespace[name]
def views(clock=None):
 v,t=B.normalized_view.build(clock=clock);B.normalized_view.validate_chain(v)
 original=worker_name_function(v,'formal_runtime','configuration')
 worker_name_function(v,'formal_guest','server_argv')
 def configuration(cfg,common):
  need(common is COMMON,'single source-qualified shared normalized common')
  actual,additional,extras=projection(cfg)
  identity=B.engine.obj(json.loads(os.environ['MAIN_SKVQ_FORMAL_IDENTITY_REF']))
  B.engine.publish(Path(identity['service_root'])/('NORMALIZED_CONFIG_PREASSERT-'+str(os.getpid())+'.json'),
   dict(adapter_source_ref=OWN,source_ref=B.ENGINE,configuration_origin_ref=CONFIG,actual_policy=actual,
    actual_additional_config=additional,extra_actual_fields=extras,identity_ref=json.loads(os.environ['MAIN_SKVQ_FORMAL_IDENTITY_REF']),weights_created=False))
  need(additional==COMMON.EFFECTIVE_ADDITIONAL,'same actual expanded Ascend additional config in both arms')
  return original(cfg,common)
 v['formal_runtime'].configuration=v['formal_guest'].configuration=configuration
 v['formal_guest'].HERE=ROOT
 source_proxy=v['formal_guest'].S;original_source=source_proxy.source
 def source_then_spawn_root(sha):
  result=original_source(sha)
  need(result[0]==B.ENGINE,'unchanged actual engine source after source resolver')
  sys.path.insert(0,str(ROOT));return result
 source_proxy.source=source_then_spawn_root
 # Original guest uses HERE for actual spawned-worker PYTHONPATH.
 sys.path.insert(0,str(ROOT));return v,t
def route(role):
 clock=dict(started=time.monotonic(),epoch=time.time())
 if '--execute'not in sys.argv:print(json.dumps(dict(enabled=False,NPU=False)));return
 need('--adapter-sha'in sys.argv,'explicit normalized source pin')
 sha=sys.argv[sys.argv.index('--adapter-sha')+1];boot(sha);B.source104()
 os.environ[ENV]=sha;v,_=views(clock)
 if role=='host':need('--mode'in sys.argv and sys.argv[sys.argv.index('--mode')+1]in('diagnostic','screen','formal'),'no task or undeclared scope')
 v['formal_'+role].main()
def worker(namespace):
 sha=os.environ.get(ENV);need(sha,'normalized worker default OFF');boot(sha)
 row=B.role('formal_worker.py')
 # Real original module, registered by original strict source loader. Never
 # alias the wrapper, rewrite its __file__, or hide a loaded foreign module.
 need(Path(namespace['__file__'])==ROOT/'skvq_normalized_worker.py','actual unique wrapper origin retained')
 need('formal_worker'not in sys.modules,'unique bootstrap rejects any preexisting original worker module')
 original=B.engine.module('formal_worker',row)
 need(sys.modules.get('formal_worker')is original and ref(original.__file__)==row,'actual original worker module retained')
 need(original.SOURCE==B.ENGINE and original.MANIFEST==B.engine_manifest and hasattr(original,'ADAPTER')and hasattr(original,'Base'),'complete genuine original worker body')
 from formal_contract import pin_function
 for method in ('address_maps','memory_baseline','install','capture_begin','capture_end','finish'):pin_function(getattr(original.ADAPTER,method),row['sha256'])
 cls=original.FormalWorker
 need(cls.__module__=='formal_worker'and cls is original.FormalWorker,'original receiver/class provenance')
 namespace['FormalWorker']=cls
