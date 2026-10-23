"""Default-OFF real Torch CPU lifetime probe; no model/NPU/algorithm admission."""
import argparse,ast,copy,hashlib,json,os,sys,time,types,weakref
from pathlib import Path

WS=Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z")
PINS={
 "formal_pair_ready_prepare_v1/strict-source-proposal-v3/prepared-source-bole/diagnostic_export.py": {
  "bytes": 1912,
  "sha256": "7af77f4e42864b83c454bb6eb05cbcd3ad936c90af097709523bf7662646d46c"
 },
 "formal_pair_ready_prepare_v1/strict-source-proposal-v3/prepared-source-bole/sourceio.py": {
  "bytes": 1038,
  "sha256": "0bd97743aa2ac06ea55488a54f5045fd08cff2fdfa4869acc9b1414d2965a0cd"
 },
 "formal_pair_ready_prepare_v1/strict-source-proposal-v3/prepared-source-bole/model_entry.py": {
  "bytes": 32009,
  "sha256": "8684325946bfb2d5cf1ab972c10be98f86c8b95605f676c709668277b360d0b9"
 },
 "formal_pair_ready_prepare_v1/strict-source-proposal-v3/prepared-source-bole/service_bridge.py": {
  "bytes": 7063,
  "sha256": "8fae536aac8bcadf0479098d0f38a45ae2890018fd9c24d70cfe6e6b76c5edf7"
 },
 "formal_pair_ready_prepare_v1/strict-source-proposal-v3/prepared-source-bole/service_runner.py": {
  "bytes": 51175,
  "sha256": "730ff8d03824d5da0cbe960eb1f2e47dddabae22b282b610e2deee6fb8119d6a"
 },
 "fastpath_numeric_bridge_prepare_v1/qualification_tap_delta.py": {
  "bytes": 2577,
  "sha256": "349bd1da965eca33df950f6817d88d9e9a3759771ce589f9b901c62302fe27da"
 },
 "fastpath_numeric_bridge_prepare_v1/fastpath_numeric_observer.py": {
  "bytes": 8846,
  "sha256": "c5943291ed026402f67bbc0f6c515ba506439943c2baf55b9f12153836f6c6b2"
 },
 "fastpath_numeric_bridge_prepare_v1/fastpath_numeric_sink.py": {
  "bytes": 5497,
  "sha256": "adfd91fd06ca949bdb32dc9617bb60ffc794fd06a7aa50298d02cac1cbd1b62a"
 },
 "state_capture_codec_prepare_v1/render_state_codec.py": {
  "bytes": 5745,
  "sha256": "bc1fa64b1c792496a140f8a2e3ac9f139784cc288b87200db6f2881aeb20c7fa"
 },
 "state_capture_codec_prepare_v1/state_capture_codec.py": {
  "bytes": 15394,
  "sha256": "b7bc24128b2ba3561a03a7f5cf5694258ab77c6d4d09b02f9b07eabd9a349e86"
 }
}
BASE='formal_pair_ready_prepare_v1/strict-source-proposal-v3/prepared-source-bole/'
QUAL='fastpath_numeric_bridge_prepare_v1/'
CODEC='state_capture_codec_prepare_v1/'
MiB=2**20
LOGICAL_CAP=384*MiB
JOINT_CAP=2**30
CHECKPOINT_RESERVE=128*MiB
METADATA_RESERVE=64*MiB
# Conditional shape-object subset, not an observed first frame. Keep native24;
# private scratch25->17 changes K/V, bool mask and int32 table for16FA.
FULL_LOGICAL=253046592-16*(25-17)*(2*128*256*2+3*128+4)
MODES={'small':2*MiB,'conditional-first2k':FULL_LOGICAL}

def need(value,message):
 if not value:raise ValueError(message)

def checked_sources():
 result={}
 for name,pin in PINS.items():
  p=WS/name
  need(p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary pinned source '+name)
  raw=p.read_bytes()
  need(len(raw)==pin['bytes']and hashlib.sha256(raw).hexdigest()==pin['sha256'],'unchanged source '+name)
  result[name]=raw
 return result

def private(raw,path):
 ns={'__file__':str(path),'__name__':'_cpu_lifetime_source_only'}
 exec(compile(raw,str(path),'exec'),ns)
 return ns

def prefix_sources(raw):
 tap=private(raw[QUAL+'qualification_tap_delta.py'],WS/QUAL/'qualification_tap_delta.py')
 files={n:raw[BASE+n].decode()for n in('model_entry.py','service_bridge.py','service_runner.py')}
 files=tap['render'](files)
 files.update({n:raw[QUAL+n].decode()for n in('fastpath_numeric_observer.py','fastpath_numeric_sink.py')})
 renderer=private(raw[CODEC+'render_state_codec.py'],WS/CODEC/'render_state_codec.py')
 released,inverse=renderer['adapt'](files)
 need(renderer['undo'](released,inverse)==files,'complete codec source inverse')
 # The actual renderer reads this helper. Independently check it against the
 # pre-read pin again, not just a module path or caller success field.
 need(released['state_capture_codec.py'].encode()==raw[CODEC+'state_capture_codec.py'],'actual helper read stable')
 return files['fastpath_numeric_sink.py'],released['fastpath_numeric_sink.py']

def reservation(logical,cap):
 need(type(logical)is int and 0<logical<=LOGICAL_CAP,'unchanged384MiB logical cap')
 need(type(cap)is int and 0<cap<=JOINT_CAP,'at most original1GiB joint reserve')
 total=2*logical+CHECKPOINT_RESERVE+METADATA_RESERVE
 need(total<=cap,'two logical copies plus unchanged128MiB/64MiB reserve before allocation')
 return total

def prefix_ast(text,variant):
 tree=ast.parse(text)
 sink=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='sink')
 assigned=lambda x,n:isinstance(x,ast.Assign)and any(isinstance(y,ast.Name)and y.id==n for y in x.targets)
 start=next(i for i,x in enumerate(sink.body)if assigned(x,'logical'))
 stop=next(i for i,x in enumerate(sink.body)if assigned(x,'previous'))
 body=copy.deepcopy(sink.body[start:stop])
 raw_deletes=[x for x in body if isinstance(x,ast.Delete)and any(isinstance(y,ast.Name)and y.id=='raw'for y in x.targets)]
 need(len(raw_deletes)==(1 if variant=='released'else 0),'actual variant delraw boundary')
 if raw_deletes:
  line=raw_deletes[0].lineno
  need(not any(isinstance(x,ast.Name)and x.id=='raw'and isinstance(x.ctx,ast.Load)and x.lineno>line
       for n in body for x in ast.walk(n)),'no later actual raw reference')
 result=[]
 def event(name,arg=None):
  args=[ast.Constant(name)]+([]if arg is None else[ast.Name(arg,ast.Load())])
  return ast.Expr(ast.Call(ast.Name('observe',ast.Load()),args,[]))
 for node in body:
  if assigned(node,'saved'):result.append(event('before_independent_reopen'))
  result.append(node)
  if assigned(node,'raw'):result.append(event('after_export','raw'))
  elif isinstance(node,ast.With):result.append(event('after_save_fsync_close','raw'))
  elif isinstance(node,ast.Delete):result.append(event('after_export_owner_release'))
  elif assigned(node,'saved'):result.append(event('after_independent_reopen','saved'))
 result.append(ast.Return(ast.Name('saved',ast.Load())))
 fn=ast.FunctionDef(name='actual_sink_save_reopen',args=ast.arguments(posonlyargs=[],args=[],
  kwonlyargs=[],kw_defaults=[],defaults=[]),body=result,decorator_list=[])
 return ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[]))

def proc_memory():
 def fields(path):
  result={}
  try:
   for line in Path(path).read_text().splitlines():
    key,sep,tail=line.partition(':')
    if sep and tail.strip().endswith('kB'):
     value=tail.strip().split()[0]
     if value.isdigit():result[key]=int(value)*1024
   return dict(available=True,bytes=result)
  except OSError as error:return dict(available=False,error=repr(error))
 return dict(status=fields('/proc/self/status'),smaps_rollup=fields('/proc/self/smaps_rollup'),
             monotonic_ns=time.monotonic_ns())

def tensor_leaves(t,x):
 if isinstance(x,t.Tensor):yield x
 elif type(x)is dict:
  for value in x.values():yield from tensor_leaves(t,value)
 elif type(x)in(list,tuple):
  for value in x:yield from tensor_leaves(t,value)

def storage_stats(t,groups):
 rows=[];unique={}
 for label,obj in groups:
  for value in tensor_leaves(t,obj):
   need(value.device.type=='cpu','CPU-only probe tensor, not a fake NPU')
   storage=value.untyped_storage()
   key=(str(value.device),storage.data_ptr(),storage.nbytes())
   unique[key]=storage.nbytes()
   rows.append(dict(group=label,tensor_id=id(value),dtype=str(value.dtype),shape=list(value.shape),
    stride=list(value.stride()),storage_offset=value.storage_offset(),logical_bytes=value.numel()*value.element_size(),
    storage_key=list(key)))
 return dict(tensors=rows,unique_storages=len(unique),unique_storage_bytes=sum(unique.values()),
             logical_tensor_bytes=sum(x['logical_bytes']for x in rows))

def bitwise(t,a,b):
 if isinstance(a,t.Tensor):
  need(isinstance(b,t.Tensor)and a.dtype==b.dtype and a.shape==b.shape and a.stride()==b.stride()
   and a.storage_offset()==b.storage_offset()and
   t.equal(a.contiguous().view(t.uint8),b.contiguous().view(t.uint8)),'complete reopened tensor ABI/bytes')
 elif type(a)is dict:
  need(type(b)is dict and set(a)==set(b),'complete reopened dict')
  for key in a:bitwise(t,a[key],b[key])
 elif type(a)in(list,tuple):
  need(type(b)is type(a)and len(a)==len(b),'complete reopened sequence')
  for x,y in zip(a,b):bitwise(t,x,y)
 else:need(type(a)is type(b)and a==b,'complete reopened primitive')

def durable_json(root,name,value):
 data=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode()
 need(len(data)<=MiB,'bounded control report metadata')
 p=root/name
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb')as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
 fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
 try:os.fsync(fd)
 finally:os.close(fd)
 return dict(path=str(p),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())

def execute(args,raw):
 root=Path(args.output)
 need(root.is_absolute()and root.parent.is_dir()and not root.exists()and
  not any(x.is_symlink()for x in root.parents),'fresh absolute owned output leaf, no overwrite')
 root.mkdir(mode=0o700)
 report=dict(schema='bole.real-Torch-CPU-export-lifetime-control/v1',mode=args.mode,variant=args.variant,
  logical_subset_bytes=MODES[args.mode],conditional_first2k_geometry_not_observed=True,
  tensor_payload_is_synthetic=True,same_image_host_provenance_pending=True,
  model_NPU_capture=dict(status='not_measured_not_released',bytes=None),
  NPU=False,algorithm_qualified=False,numerical_qualified=False,formal_performance=False,joint_fit=False,
  source_pins=PINS,stages=[],original_two_logical_reserve_unchanged=True)
 try:
  logical=MODES[args.mode]
  report['preallocation_reserve_bytes']=reservation(logical,args.joint_cap_bytes)
  need(type(args.process_cap_bytes)is int and 0<args.process_cap_bytes<=JOINT_CAP,'bounded observed CPU process cap')
  free=os.statvfs(root);need(free.f_bavail*free.f_frsize>=report['preallocation_reserve_bytes'],'free evidence disk covers conservative reserve')
  # Torch is NEVER imported by default/--check. MAIN owns future same-image
  # invocation and any container/host proof; this script creates no such proof.
  import torch as t
  report['torch_version']=str(t.__version__)
  report['torch_file']=str(t.__file__)
  C=types.SimpleNamespace(**private(raw[BASE+'sourceio.py'],WS/BASE/'sourceio.py'))
  X=types.SimpleNamespace(**private(raw[BASE+'diagnostic_export.py'],WS/BASE/'diagnostic_export.py'))
  original,released=prefix_sources(raw)
  sources={'original':original,'released':released}
  frame=None;export_refs=[]
  def observe(stage,payload=None):
   if stage=='after_export':
    export_refs.extend(weakref.ref(v)for v in tensor_leaves(t,payload))
   memory=proc_memory()
   need(memory['smaps_rollup']['available']and 'Pss'in memory['smaps_rollup']['bytes'],
    'actual Linux PSS observable, not an estimated memory success')
   row=dict(stage=stage,memory=memory,export_python_tensor_owners_alive=sum(r()is not None for r in export_refs))
   groups=[]
   if frame is not None:groups.append(('input_CPU_frame_still_owned',frame))
   if payload is not None:groups.append(('export'if stage.startswith('after_export')or stage=='after_save_fsync_close'else'reopened',payload))
   row['storage']=storage_stats(t,groups);report['stages'].append(row)
   if stage=='before_independent_reopen':
    alive=row['export_python_tensor_owners_alive']
    need((alive==0)if args.variant=='released'else(alive>0),'real Torch wrapper weakrefs distinguish actual variants')
    report['export_Python_owner_released_before_reopen']=alive==0
    if args.inject_failure_before_reopen:raise ValueError('injected failure after durable save; raw must remain retained')
   pss=memory['smaps_rollup']['bytes']['Pss'];hwm=memory['status']['bytes'].get('VmHWM')
   need(hwm is not None and max(pss,hwm)<=args.process_cap_bytes,'observed process PSS/RSS-HWM cap; no inferred storage release')
  observe('before_tensor_allocation')
  baseline=report['stages'][-1]['memory']['smaps_rollup']['bytes']['Pss']
  need(baseline+report['preallocation_reserve_bytes']<=args.process_cap_bytes,
       'baseline plus original two-logical/checkpoint/metadata reserve before tensor allocation')
  # Fixed opaque byte workload sized to the conditional subset, not fabricated
  # model state. Deliberate view sharing exposes real storage dedup behavior.
  main=t.full((logical-8192,),19,dtype=t.uint8)
  main[0]=1;main[len(main)//2]=127;main[-1]=254
  alias=t.arange(4096,dtype=t.int64).to(t.uint8)
  frame=dict(generation=1,ordinal=0,payload=dict(main=main,alias_base=alias,alias_view=alias.reshape(64,64)))
  del main,alias
  observe('input_CPU_frame_allocated')
  ns=dict(t=t,C=C,X=X,c=dict(root=root,used=0,metadata_bytes=0),frame=frame,os=os,observe=observe)
  # Use the exact original logical_bytes function alongside the exact original
  # or rendered durable-save/reopen AST; no serialization logic is reimplemented.
  tree=ast.parse(sources[args.variant]);fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='logical_bytes')
  exec(compile(ast.Module(body=[copy.deepcopy(fn)],type_ignores=[]),'actual-logical-bytes','exec'),ns)
  need(ns['logical_bytes'](t,frame)==logical,'exact controlled logical byte count')
  exec(compile(prefix_ast(sources[args.variant],args.variant),'actual-sink-save-reopen','exec'),ns)
  saved=ns['actual_sink_save_reopen']()
  bitwise(t,frame,saved['payload']);observe('full_reopened_bitwise_verified',saved)
  report['full_reopened_bitwise']=True
  report['real_CPU_export_may_share_input_storage']=True
  report['original_NPU_D2H_storage_behavior_not_tested']=True
  report['all_created_raw_files_retained']=[C.ref(p)for p in root.glob('*.pt')]
  report['cpu_control_completed']=True
  return durable_json(root,'RESULT.json',report)
 except BaseException as error:
  report['primary']=dict(type=type(error).__name__,message=str(error))
  report['cpu_control_completed']=False
  report['all_created_raw_files_retained']=[dict(path=str(p),bytes=p.stat().st_size)for p in root.glob('*.pt')]
  try:durable_json(root,'FAILURE.json',report)
  except BaseException as secondary:print(json.dumps(dict(primary=report['primary'],failure_report_error=repr(secondary))),file=sys.stderr)
  raise

def main():
 parser=argparse.ArgumentParser(allow_abbrev=False)
 parser.add_argument('--execute',action='store_true');parser.add_argument('--check',action='store_true')
 parser.add_argument('--mode',choices=tuple(MODES));parser.add_argument('--variant',choices=('original','released'))
 parser.add_argument('--output');parser.add_argument('--joint-cap-bytes',type=int,default=JOINT_CAP)
 parser.add_argument('--process-cap-bytes',type=int,default=JOINT_CAP)
 parser.add_argument('--inject-failure-before-reopen',action='store_true')
 args=parser.parse_args()
 need(not(args.execute and args.check),'one explicit action')
 if not args.execute and not args.check:
  need(not any((args.mode,args.variant,args.output,args.inject_failure_before_reopen)),'work arguments need explicit --execute')
  print(json.dumps(dict(enabled=False,Torch_imported=False,NPU=False)));return
 raw=checked_sources()
 if args.check:
  need(not any((args.mode,args.variant,args.output,args.inject_failure_before_reopen)),'source-only check, not an execution')
  original,released=prefix_sources(raw)
  prefix_ast(original,'original');prefix_ast(released,'released')
  for n in MODES.values():reservation(n,JOINT_CAP)
  for logical,cap in((LOGICAL_CAP+1,JOINT_CAP),(MODES['small'],2*MODES['small']),(True,JOINT_CAP)):
   try:reservation(logical,cap)
   except ValueError:pass
   else:raise ValueError('budget/type refusal missing')
  print(json.dumps(dict(source_check_passed=True,Torch_imported=False,NPU=False,full_Torch_pending=True,
    conditional_full_bytes=FULL_LOGICAL)));return
 need(args.mode is not None and args.variant is not None and args.output is not None,'explicit distinct mode/variant/fresh output')
 print(json.dumps(execute(args,raw),sort_keys=True))
if __name__=='__main__':main()
