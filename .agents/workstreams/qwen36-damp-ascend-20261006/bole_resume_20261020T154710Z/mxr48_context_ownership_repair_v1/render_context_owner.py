"""Source-only exact repair of the observed nested-PCP fixture failure."""
import ast,hashlib,json,sys
from pathlib import Path
PARENT=Path('/cache/cch/qwen36-paper-preparation-20261007/lowbit/mxr-full48-pair-v1-002/shard-0')
PIN=(8576,'b945f7408dcfb7e1a8739132220f9adadbc48dda25aabf3ab7519c4ec51e33de')
GROUPS="('_PCP','_TP','_DP','_PP','_DCP','_WORLD')"
OLD_INIT="""  ps.init_distributed_environment(world_size=1,rank=0,local_rank=0,backend='hccl',distributed_init_method='file://'+str(a.output/'world1-store'),timeout=timedelta(seconds=30))
  ps._PCP=ps.init_model_parallel_group([[0]],local_rank=0,backend='hccl',group_name='pcp',use_device_communicator=False)
  need(ps.get_pcp_group().world_size==1 and ps.get_pcp_group().rank_in_group==0,'actual GroupCoordinator PCP1')"""
NEW_INIT="""  # Each unchanged donor.execute owns its real native_pcp_context. No outer
  # WORLD/PCP exists to collide with that original isolated-fixture guard."""
OLD_CLEANUP="""  for name,fn in(('modelgroups',ps.destroy_model_parallel),('world',ps.destroy_distributed_environment)):
   try:fn();teardown.append(dict(stage=name,pass_release=True))
   except BaseException as exc:teardown.append(dict(stage=name,error=repr(exc)))"""
NEW_CLEANUP="""  try:
   need(not torch.distributed.is_initialized()and all(getattr(ps,name) is None for name in ('_PCP','_TP','_DP','_PP','_DCP','_WORLD')),
        'all unchanged per-frame original native contexts actually released')
   teardown.append(dict(stage='original-per-frame-groups',pass_release=True))
  except BaseException as exc:teardown.append(dict(stage='original-per-frame-groups',error=repr(exc)))"""
PINS={
 'full_bridge.py':(6511,'b1fdec52783c495656b04aa8d45774570d7dc54ebbf74f74929a5edfe34fd97b'),
 'two_arm.py':(3824,'a639b84301226b17b13ea30572dccd94d92f1ba225abb1865a43f96b310f238b'),
 'native_identity.py':(2099,'d59f729c60bfffc2ea9ddc919f44f185a4c6f069ce12a40237c36ec3bbd3cfde')}
EXTERNAL={
 '/cache/cch/qwen36-paper-preparation-20261007/lowbit/mxr-third-residual-saved3frame-new24h-v1-125/guest_core.py':
 (22594,'691b8be9c0e863dd9e3ef8720e2efa876c5efecf49b12d46f420da318c3ab389'),
 '/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-split-scale-numeric-new24h-v1-069-repair1/qwen36_deltalog_fresh/native_fixture.py':
 (16257,'e557b34be77e9e1ea85e4663df879228425eb8931b2aa162eb9e9d156b46aaff')}
def need(v,s):
 if not v:raise ValueError(s)
def identity(raw):return len(raw),hashlib.sha256(raw).hexdigest()
def once(s,a,b):
 need(s.count(a)==1,'one exact observed context seam');return s.replace(a,b,1)
def adapt(files):
 need(type(files)is dict and identity(files['event_probe.py'])==PIN,'exact failed outer source')
 for n,pin in PINS.items():need(identity(files[n])==pin,'actual unchanged downstream source '+n)
 old=files['event_probe.py'];s=old.decode();s=once(s,OLD_INIT,NEW_INIT);s=once(s,OLD_CLEANUP,NEW_CLEANUP)
 need(s.count('with fc.override_forward_context(context):')==1 and
      s.count('native_identity.capture(torch,chunk,sm,builder)()')==1 and
      s.count('START<=time.time()and time.time()+390<=CUT')==1,
      'native identity, context dispatch and existing300+90 cutoff guard retained')
 restored=once(once(s,NEW_CLEANUP,OLD_CLEANUP),NEW_INIT,OLD_INIT)
 need(restored.encode()==old,'complete exact text inverse before delivery')
 compile(s,'derived-event-probe-context-owner','exec')
 out=dict(files);out['event_probe.py']=s.encode()
 return out,dict(schema='mxr48.exact-outer-context-removal/v1',before=old,after=out['event_probe.py'])
def inverse(files,d):
 need(d['schema']=='mxr48.exact-outer-context-removal/v1'and identity(d['before'])==PIN and
      files['event_probe.py']==d['after'],'exact full inverse operands')
 out=dict(files);out['event_probe.py']=d['before']
 need(adapt(out)[0]==files,'forward complete-map equality before inverse');return out
def calls(raw):
 tree=ast.parse(raw)
 return {n:sum(isinstance(x,ast.Attribute)and x.attr==n
  for x in ast.walk(tree))for n in('init_distributed_environment','init_model_parallel_group',
  'destroy_model_parallel','destroy_distributed_environment')}
def check():
 files={}
 for n,pin in{'event_probe.py':PIN,**PINS}.items():
  p=PARENT/n;raw=p.read_bytes();need(identity(raw)==pin,'actual parent source pin');files[n]=raw
 for n,pin in EXTERNAL.items():need(identity(Path(n).read_bytes())==pin,'unchanged real per-frame fixture/donor')
 out,d=adapt(files);need(inverse(out,d)==files,'all supplied source bytes roundtrip')
 need(all(v==0 for v in calls(out['event_probe.py']).values()),'no outer process-group creation/destruction remains')
 # The original inner context is read, never executed or softened.
 fixture=Path(next(n for n in EXTERNAL if n.endswith('native_fixture.py'))).read_text()
 need('numeric fixture requires its own isolated process groups'in fixture and
      'if torch.distributed.is_initialized() or ps._PCP is not None:'in fixture and
      any(isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and
          n.func.attr=='init_distributed_environment'and
          any(k.arg=='backend'and isinstance(k.value,ast.Constant)and k.value.value=='hccl'
              for k in n.keywords)for n in ast.walk(ast.parse(fixture))),
      'original cold/private real-HCCL guard remains exact')
 for mutation in('init','cleanup'):
  bad=dict(files);bad['event_probe.py']=files['event_probe.py'].replace(
   (OLD_INIT if mutation=='init'else OLD_CLEANUP).encode(),b'pass',1)
  try:adapt(bad)
  except ValueError:pass
  else:raise ValueError('mutated original accepted')
 try:adapt(out)
 except ValueError:pass
 else:raise ValueError('double application accepted')
 print(json.dumps(dict(source_only=True,source_bound=False,NPU=False,native_context_executed=False,
  before=dict(bytes=PIN[0],sha256=PIN[1],outer_API_references=calls(files['event_probe.py'])),
  after=dict(bytes=len(out['event_probe.py']),sha256=hashlib.sha256(out['event_probe.py']).hexdigest(),
   outer_API_references=calls(out['event_probe.py'])),whole_inverse=True,negative_controls=True,
  unchanged_downstream=PINS,external_per_frame_context=EXTERNAL,
  old_expired_authority_not_reused=True,actual_sameimage_and_NPU_pending=True),sort_keys=True))
if __name__=='__main__':
 if not sys.argv[1:]:print('{"enabled":false,"NPU":false,"source_bound":false}')
 else:
  need(sys.argv[1:]==['--check'],'only source-only check, no launch/install/device API')
  check()
