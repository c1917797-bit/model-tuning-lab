"""Actual modified byte-store/J/terminal boundary controls; no Torch or NPU."""
import ast,copy,hashlib,importlib.util,json,os,resource,sys,tempfile,types
from pathlib import Path
os.sched_setaffinity(0,{145});resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
HERE=Path(__file__).resolve().parent
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def ref(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
class C:
 refs=0
 @classmethod
 def ref(cls,p):cls.refs+=1;return ref(p)
 @staticmethod
 def need(v,s):
  if not v:raise ValueError(s)
 @staticmethod
 def checked(r):
  p=Path(r['path']);C.need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents))and ref(p)==r,'actual ordinary complete Ref');return p
 @staticmethod
 def obj(r):return json.loads(C.checked(r).read_bytes())
def reject(fn):
 try:fn()
 except(ValueError,TypeError,KeyError):return
 raise AssertionError('expected rejection')
def function(raw,name,namespace,cls=None):
 tree=ast.parse(raw)
 if cls is not None:tree=next(x for x in tree.body if isinstance(x,ast.ClassDef)and x.name==cls)
 node=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name==name)
 exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual-source-function>','exec'),namespace)
 return namespace[name]
def main():
 R=load(HERE/'runtime_lossless_imports.py','_disk16_whole');b=R.render();R.inverse(b);files=b['files'];m=b['manifest']
 assert m['fa_lossless_capture']['raw_cap']==m['input_resource_profile32k']['per_rank_disk_cap']==4362076160
 P=load(R.WS/'bole_output_scan_v14_prepare_20261024/prepared-source-short8-v14/input_resource_profile.py','input_resource_profile')
 D=load(HERE/'disk_ledger.py','disk_ledger')
 unit_m=copy.deepcopy(m);unit_m['files']['disk_ledger.py']=ref(HERE/'disk_ledger.py');unit_m['files']['input_resource_profile.py']=ref(P.__file__)
 source=dict(path='/software-fixture/SOURCE_BOUND.json',bytes=1,sha256='a'*64)
 def context(root,used=0,metadata=0):
  return dict(C=C,m=unit_m,source=source,rank=0,root=root,used=used,metadata_bytes=metadata)
 events=[]
 with tempfile.TemporaryDirectory(prefix='bole-disk16-')as td:
  root=Path(td);c=context(root);cap=D.limit(c);assert cap==4362076160
  before=C.refs
  for _ in range(10):assert D.limit(c)==cap
  assert C.refs==before;events.append('same-context scalar accounting has no repeated source hashes/tree scan')
  c['used']=2**30;D.archive_before(c,65536,metadata=False)
  c['used']=cap-D.CHECKPOINT-D.METADATA-8
  D.archive_before(c,8,metadata=False);reject(lambda:D.archive_before(c,9,metadata=False))
  reject(lambda:D.pt_before(c,9));D.pt_before(c,8)
  c['metadata_bytes']=D.METADATA;reject(lambda:D.metadata_before(c,1))
  c['metadata_bytes']=0;c['used']=0
  other=dict(c);reject(lambda:D.limit(other))
  altered=copy.deepcopy(unit_m);altered['input_resource_profile32k']['conv_slot_bytes']=32768
  reject(lambda:D.limit(dict(c,m=altered,_profile_disk_state=c['_profile_disk_state'])))
  events.append('old1GiB is not disk cap; exact disk/PT/metadata boundary and cross-context/source mutation reject')
  B=types.ModuleType('_actual_disk16_store');B.__file__=str(root/'virtual-fa_block_store.py')
  exec(compile(files['fa_block_store.py'],B.__file__,'exec'),B.__dict__)
  cr=root/'FASTPATH-NUMERIC-R0';cr.mkdir();cc=context(cr)
  S=B.Store(cc);raw=b'x'*65536;r=S.put(raw);n=cc['used'];assert S.put(raw)==r and cc['used']==n
  rejected_root=root/'rejected';rejected_root.mkdir();rc=context(rejected_root,cap-D.CHECKPOINT-D.METADATA-10);bad=B.Store(rc)
  reject(lambda:bad.put(b'y'*11));assert bad.failed and not list(bad.root.iterdir())
  partial_root=root/'partial';partial_root.mkdir();pc=context(partial_root);partial=B.Store(pc)
  original=B.os.fsync
  def fail(_):raise OSError('fixture fsync first fault')
  B.os.fsync=fail
  try:
   reject(lambda:partial.put(b'partial'))
  finally:B.os.fsync=original
  assert partial.failed and pc['used']==7 and len(list(partial.root.iterdir()))==1
  reject(lambda:partial.put(b'next'));events.append('actual Store dedup/nocharge, disk prewrite refusal and retained partial sticky failure')
  # Actual changed J methods execute, with RAM/L fixtures explicitly outside this boundary test.
  ns=dict(D=D,BudgetReject=ValueError,need=C.need,LOGICAL_CAP=m['runtime_joint_capture_ledger']['logical_cap'],
   RAW_CAP=m['runtime_joint_capture_ledger']['raw_cap'],CHECKPOINT_RESERVE=D.CHECKPOINT,
   METADATA_RESERVE=D.METADATA,FRAME_WIRE_CAP=m['runtime_joint_capture_ledger']['frame_wire_cap'])
  total=function(files['runtime_joint_ledger.py'],'total',ns,'Joint')
  pre=function(files['runtime_joint_ledger.py'],'_pre_export',ns,'Joint')
  jc=context(root,cap-D.CHECKPOINT-D.METADATA-7)
  owner=types.SimpleNamespace(c=jc,phase='idle',failed=False,
   L=types.SimpleNamespace(raw_reservation=lambda a,b,c,d,e:a+b+c+d+e),
   ram=types.SimpleNamespace(enter=lambda *a:None))
  owner.total=types.MethodType(total,owner)
  frame=dict(source=source,rank=0,generation=1,ordinal=0)
  pre(owner,frame,0);assert owner.quota==7
  reject(lambda:total(owner,8))
  owner.phase='idle';jc['used']+=7;reject(lambda:pre(owner,frame,0))
  old=R.module((R.WS/'bole_output_scan_v14_prepare_20261024/prepared-source-short8-v14/runtime_joint_ledger.py').read_bytes(),R.ROOT/'old-J.py','_old_J_AST') if False else None
  parent_j=(R.WS/'bole_output_scan_v14_prepare_20261024/prepared-source-short8-v14/runtime_joint_ledger.py').read_bytes()
  def method(raw,kind,name):
   t=ast.parse(raw);node=next(x for x in t.body if isinstance(x,ast.ClassDef)and x.name==kind)
   return ast.dump(next(x for x in node.body if isinstance(x,ast.FunctionDef)and x.name==name),include_attributes=False)
  assert method(parent_j,'Writer','write')==method(files['runtime_joint_ledger.py'],'Writer','write')
  assert method(parent_j,'Joint','serialization_failed')==method(files['runtime_joint_ledger.py'],'Joint','serialization_failed')
  events.append('actual J disk quota7/evidence larger, +1 reject; original byte Writer/partial/noACK AST unchanged')
  # Original terminal graph and all-and-only census execute on real tiny files.
  rr=S.tensor([raw],shape=[65536],dtype='uint8',family='software',witness={'software':True})
  fm=cr/'frame.json';fm.write_text(json.dumps(dict(schema='bole.actual-fa-frame-block-manifest/v1',source=source,rank=0,numerical_qualified=False,formal_performance=False,tensor_roots=[rr['tensor']])))
  unit_m['model_receipt_root']=str(root)
  terminal=function(files['fa_stream_capture.py'],'terminal',dict(B=B,D=D,json=json,Path=Path,need=C.need))
  result=terminal(C,unit_m,source,0,[ref(fm)])
  extra=S.root/'unknown';extra.write_bytes(b'x');reject(lambda:terminal(C,unit_m,source,0,[ref(fm)]));extra.unlink()
  shared_file=root/'shared.json';shared_file.write_bytes(b'{}');shared=dict(references=[ref(shared_file)],bytes=2)
  rows=[D.rank_terminal(context(root),rank=i,source=source,total=100,json_bytes=20)for i in range(4)]
  summed=D.all_terminal(C,unit_m,source,rows,shared=shared);assert summed['actual_total_bytes']==394
  reject(lambda:D.all_terminal(C,unit_m,source,rows[:3],shared=shared))
  wrong=copy.deepcopy(rows);wrong[1]['rank']=0;reject(lambda:D.all_terminal(C,unit_m,source,wrong,shared=shared))
  wrong=copy.deepcopy(rows);wrong[1]['source']=dict(source,sha256='b'*64);reject(lambda:D.all_terminal(C,unit_m,source,wrong,shared=shared))
  events.append('actual FA terminal closure rejects unknown leaf; exact4 ranks/source/shared bytes once and independent sum')
 # Preserve all original math, source input and resource contracts outside the explicit FA disk sublimit.
 old=R.module((R.WS/'bole_output_scan_v14_prepare_20261024/runtime_lossless_imports.py').read_bytes(),R.WS/'bole_output_scan_v14_prepare_20261024/runtime_lossless_imports.py','_old_V14_disk_compare')
 ob=old.render()
 for key in('resources','input_resource_profile32k','fastpath_numeric_qualification','runtime_joint_capture_ledger'):
  assert m[key]==ob['manifest'][key],key
 for name in('fastpath_numeric_consumer.py','independent_model.py','boundary_oracle.py'):
  if name in files:assert files[name]==ob['files'][name],name
 for name,raw in files.items():
  if name.endswith('.py'):compile(raw,name,'exec')
 V=R.module(files['qualification_source_validate.py'],R.ROOT/'qualification_source_validate.py','_disk16_scope')
 seven=dict(scope=V.SCOPE,source_root=m['root'],output_root=m['output_root'],files=m['files'],parent_preparation_readset=m['qualification_parent_preparation_readset'],historical_short_source=m['qualification_historical_short_source'],short2k_helper_refs=m['short2k_helper_refs'])
 def write(name,value):
  p=HERE/name
  with p.open('xb')as f:f.write((json.dumps(value,sort_keys=True)+'\n').encode())
  return ref(p)
 review=write('REVIEW_OPERANDS_ONLY.json',seven)
 refs=[]
 for p in sorted(HERE.iterdir()):
  if p.is_file()and p.suffix in('.py','.md'):
   raw=p.read_bytes();assert raw.endswith(b'\n')and not raw.endswith(b'\n\n')and all(x==x.rstrip()for x in raw.splitlines());refs.append(ref(p))
 preparation=write('SOURCE_PREPARATION.json',dict(schema='bole.profile-disk-ledger-source-preparation/v16',files=refs,review_operands=review,source_root=m['root'],output_root=m['output_root'],whole_inverse=True,source_files=len(files),controls=events,source_bound=False,authority=False,NPU=False,Torch=False,numerical_qualified=False,actual160_fit=False))
 print(json.dumps(dict(events=events,review=review,preparation=preparation,files=refs,whole_inverse=True,source_files=len(files),NPU=False,Torch=False)))
if __name__=='__main__':main()
