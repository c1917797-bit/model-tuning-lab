"""Pure native2048/1 owning-source derivation. No review/authority/bind issued."""
import argparse,ast,copy,hashlib,importlib.util,json
from pathlib import Path
HERE=Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/native_2k_owning_source_prepare_v1")
OBS=HERE.parent/'native_2k_prefill_observation_prepare_v1'
ROOT=HERE.parent/'bound-native-2k-prefill-observation-v1'
OUT=Path('/opt/host/vnf/austinov/run-native-2k-prefill-observation-v1')
OBSERVER_RENDER={'path':str(OBS/'render_observation.py'),'bytes':7345,'sha256':'e14f0c3b86bbda41e1d4febdf77a214f3c6dfd8f22572d06d925512b4229d690'}
INPUT_PROCESSOR={"bytes":20815,"path":"/vllm-workspace/vllm/vllm/v1/engine/input_processor.py","sha256":"c5673988c0f7cfec268220e3f044e718702c015a4f236c020937cfd40a793f15"}
INPUT_HOST={"bytes":20815,"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/native_2k_owning_source_prepare_v1/dependencies/input_processor.py","sha256":"c5673988c0f7cfec268220e3f044e718702c015a4f236c020937cfd40a793f15"}
SERVING=dict(path='/vllm-workspace/vllm/vllm/entrypoints/openai/completion/serving.py',bytes=27822,sha256='c67bff55fa29c5f89000c3afdc9c7c66305612b13a8a1d85976e5872cee086d7')
SCOPE=dict(kind='native-prefill-geometry-only',input_tokens=2048,output_tokens=1,request_count=1,concurrency=1,
 physical_NPUs=[4,5,6,7],common_environment={'HCCL_DETERMINISTIC':'true'},phase_seconds=3600,cleanup_seconds=180)
def need(v,s):
 if not v:raise ValueError(s)
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def checked(r):
 p=Path(r['path']);need(ref(p)==r and not any(x.is_symlink()for x in(p,*p.parents)),'whole exact preparation Ref');return p
def obj(r):return json.loads(checked(r).read_bytes())
def one(s,a,b,count=1):
 need(s.count(a)==count,'exact owning seam '+a[:80]);return s.replace(a,b)
def preimport_gate():
 return """def _native2k_helper(m):
 need(ref(__file__)==m['files']['contract090.py']and str(Path(__file__).resolve().parent)==m['root'],'actual deployed owning gate before helper')
 r=m.get('native_2k_authority_ref');need(r is not None,'new native2k authority unbound; original131 cannot authorize2048')
 a=obj(r);review=obj(a['MAIN_review_ref'])
 scope="""+repr(SCOPE)+"""
 wanted=dict(source_root=m['root'],output_root=m['output_root'],files=m['files'],renderer_refs=m['native_2k_renderer_refs'],
  parent_template=m['native_2k_parent_template'],input_processor_runtime_ref=m['native_2k_input_processor_ref'],
  completion_serving_ref=m['native_2k_completion_serving_ref'],protocol=m['native_2k_observation'])
 need(a.get('approved')is True and a.get('schema')=='native2k.MAIN-reviewed-metadata-execution-authority/v1'and a.get('scope')==scope and
  review.get('approved')is True and review.get('schema')=='native2k.MAIN-metadata-execution-review/v1'and
  review.get('scope')==scope and review.get('source_review')==wanted,'exact independent MAIN source/runtime/renderer pins BEFORE helper execution')
 for asset in m['native_2k_renderer_refs'].values():checked(asset)
 r=m['files']['native_2k_source.py'];program=checked(r).read_bytes()
 spec=importlib.util.spec_from_file_location('_native2k_checked_source',r['path'])
 module=importlib.util.module_from_spec(spec)
 exec(compile(program,r['path'],'exec'),module.__dict__)
 return module

def source(sr,clock=True):
 global START,CUT
 m=obj(sr);N=_native2k_helper(m);a=N.source(sys.modules[__name__],sr,m,clock=clock)
 START,CUT=a['start_epoch'],a['cutoff_epoch']
 return m
"""
def clock_delta(s):
 old="""def phase_admission(C,entry_start):
    C.need(type(entry_start)in(int,float)and C.CUT==CUTOFF,'original fixed source-owned cutoff')"""
 new="""def current_authority(C):
    from pathlib import Path
    m=C.obj(C.ref(Path(C.__file__).resolve().parent/'SOURCE_BOUND.json'))
    C.need(C.ref(__file__)==m['files']['g2_cold_clock.py'],'source-owned current native2k cold clock')
    return C._native2k_helper(m).execution_window(C,m,clock=True,require_phase=False)

def phase_admission(C,entry_start):
    C.need(type(entry_start)in(int,float),'original actual first-entry clock')
    cutoff=current_authority(C)['cutoff_epoch']
    entry_wall=time.time()-(time.monotonic()-entry_start)
    C.need(entry_wall+PHASE+CLEANUP<=cutoff,'complete original main3600+180 must fit new finite window')"""
 s=one(s,old,new)
 s=one(s,'min(entry_start+PHASE-now,C.CUT-time.time())','min(entry_start+PHASE-now,cutoff-time.time())')
 s=one(s,'def controller_admission(C,c,S,ctl,entry_start):\n    C.need(S.PHASE==PHASE and S.CLEANUP==CLEANUP and c.CUTOFF==CUTOFF and',
 'def controller_admission(C,c,S,ctl,entry_start):\n    cutoff=current_authority(C)[\'cutoff_epoch\']\n    C.need(S.PHASE==PHASE and S.CLEANUP==CLEANUP and c.CUTOFF==cutoff and')
 return s
def render(*,authority_ref=None,permit_materialized=False,io=None):
 if io is None:
  from types import SimpleNamespace
  io=SimpleNamespace(checked=checked,obj=obj)
 # Direct executed module names are not assumed registered.
 check=checked if io is None else io.checked
 need(permit_materialized or(not ROOT.exists()and not OUT.exists()),'prospective unique source/output only; validation mode never writes')
 p=check(OBSERVER_RENDER);spec=importlib.util.spec_from_file_location('_native2k_exact_observer_renderer',str(p));R=importlib.util.module_from_spec(spec);exec(compile(p.read_bytes(),str(p),'exec'),R.__dict__)
 observed,unused=R.render();parent=R.json.loads(R.checked(R.TEMPLATE).read_bytes())
 files={n:R.checked(r).read_bytes()for n,r in parent['files'].items()}
 for n,s in observed.items():files[n]=s.encode()
 assets={n:ref(OBS/n)for n in('render_observation.py','native_2k_prefill_observer.py','native_2k_client.py','consume_native_2k.py','test_native_2k.py')}
 assets.update({n:ref(HERE/n)for n in('prepare_native_2k.py','native_2k_source.py')})
 assets.update(input_processor_host_copy=INPUT_HOST,source_copy_projection=ref(HERE/'dependencies/COPY_PROJECTION.json'),
  completion_serving_snapshot=ref(HERE.parent/'task_http_runtime_sources_v3/completion_serving.py'))
 files['render_observation.py']=(OBS/'render_observation.py').read_bytes();files['test_native_2k.py']=(OBS/'test_native_2k.py').read_bytes()
 for n in('native_2k_source.py','prepare_native_2k.py'):files[n]=(HERE/n).read_bytes()
 # Keep the original131 source function complete under its legacy name. The
 # new explicit native-only branch has its own MAIN-reviewed exact source gate.
 t=files['contract090.py'].decode();t=one(t,'def source(sr,clock=True):','def _legacy_source(sr,clock=True):')
 t=one(t,"OUTPUT_POSIX="+repr(parent['output_root']),"OUTPUT_POSIX="+repr(str(OUT)))
 t=one(t,"CPU_OUTPUT_POSIX="+repr(parent['output_root']+'-CPU'),"CPU_OUTPUT_POSIX="+repr(str(OUT)+'-CPU'))
 files['contract090.py']=(t+'\n\n'+preimport_gate()).encode()
 t=files['bind_model.py'].decode();t=one(t,'def readset(sr):','def _legacy_readset(sr):');t=one(t,'def main():','def _legacy_main():')
 t=one(t,"if __name__=='__main__':raise SystemExit(main())","""def readset(sr):
 import contract090 as C
 m=C.obj(sr)
 return C._native2k_helper(m).readset(C,sr,m)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--reviewed-template-ref');p.add_argument('--component-refs-json');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 import contract090 as C
 tr=json.loads(a.reviewed_template_ref);m=C.obj(tr)
 result=C._native2k_helper(m).bind_template(C,tr,json.loads(a.component_refs_json))
 print(json.dumps(result));return 0
if __name__=='__main__':raise SystemExit(main())""")
 files['bind_model.py']=t.encode()
 files['performance_validate.py']=b"""import contract090 as C
TEST_FILES=('test_native_2k.py',)
def enumerate_tests(m):return C._native2k_helper(m).enumerate_tests(m)
def dependency_contract(m):return C._native2k_helper(m).dependency_contract(m)
def validate(sr):return C._native2k_helper(C.obj(sr)).validate(C,sr)
"""
 t=files['host_service.py'].decode()
 t=one(t,"C.need(m['service_experiment']==G1.SCOPE,'explicit G1 host profile')","C.need(m['service_experiment']==m['native_2k_observation'],'explicit native2k metadata-only host scope')")
 files['host_service.py']=t.encode()
 t=files['performance_host.py'].decode();t=one(t,"'retirement_barrier_output_tokens': 1,","'retirement_barrier_output_tokens': 0,")
 files['performance_host.py']=t.encode()
 files['g2_cold_clock.py']=clock_delta(files['g2_cold_clock.py'].decode()).encode()
 t=files['owned_substrate.py'].decode();t=one(t," c.CUTOFF=1792710600;c.CUT='2026-10-22T23:10:00+00:00'",""" import contract090 as C
 from datetime import datetime,timezone
 m=C.obj(C.ref(Path(C.__file__).resolve().parent/'SOURCE_BOUND.json'))
 a=C._native2k_helper(m).execution_window(C,m,clock=True,require_phase=False)
 c.CUTOFF=a['cutoff_epoch'];c.CUT=datetime.fromtimestamp(c.CUTOFF,timezone.utc).isoformat()""")
 files['owned_substrate.py']=t.encode()
 t=files['performance_software_stages.py'].decode()
 t=one(t,"RESULT_SCHEMA='bole.actual-performance-sameimage-software/v1'","""RESULT_SCHEMA='bole.actual-performance-sameimage-software/v1'
def active_cutoff(sr):
 import contract090 as OWNER
 m=OWNER.obj(sr)
 return OWNER._native2k_helper(m).execution_window(OWNER,m,clock=True,require_phase=False)['cutoff_epoch']""")
 t=one(t,'1792710600','active_cutoff(sr)',3)
 # Source-only native suite count is distinct from historical20/381 receipts.
 t=one(t,'tests=20','tests=9',2);t=one(t,"v['tests']==20","v['tests']==9")
 files['performance_software_stages.py']=t.encode()
 t=files['performance_exact_controls.py'].decode();t=one(t,'==20','==9',2);files['performance_exact_controls.py']=t.encode()
 t=files['g3_budget.py'].decode()
 t=one(t,"    other=set(base.glob('*RANK-%d.json'%rank))-finals",
  "    other=set(base.glob('*RANK-%d.json'%rank))-finals\n    other.update(base.glob('NATIVE2K-ASSIGNMENT.json')) # shared frontend evidence conservatively charged to every rank")
 files['g3_budget.py']=t.encode()
 m=copy.deepcopy(parent)
 m.update(root=str(ROOT),output_root=str(OUT),model_receipt_root=str(OUT/'dense/receipts'),
  stream_channel_root=str(OUT/'dense/receipts/STREAM'),stream_channel_contract_path=str(OUT/'dense/receipts/STREAM/CHANNEL.json'),
  prepared_only=True,default_enabled=False,performance_arm='native_ar',native_speculative_config=None,
  historical_candidate_speculative_recipe=parent['native_speculative_config'],native_2k_observation=R.DECL,
  native_2k_request_identity='source-native2k-prefill-v1',service_experiment=R.DECL,service_required_sameimage_software_cases=9,
  authority_ref=authority_ref,native_2k_authority_ref=authority_ref,native_2k_parent_template=R.TEMPLATE,
  native_2k_renderer_refs=assets,native_2k_input_processor_ref=INPUT_PROCESSOR,native_2k_completion_serving_ref=SERVING,
  source_complete=True,sameimage_preflight=False,numerical_qualified=False,formal_performance=False,task_accuracy=False)
 m['performance_profile']['scope'].update(input_tokens=2048,output_tokens=1,warmup_requests=0)
 m['performance_client_contract'].update(input_tokens=2048,output_tokens=1,warmup_requests=0,retirement_barrier_output_tokens=0)
 m['profile'].update(input_tokens=2048,tree_nodes=0,HTTP_output_tokens=1,HTTP_tree_request_count=1,retirement_barrier_output_tokens=0)
 old={r['path']:(n,r)for n,r in parent['files'].items()}
 m['files']={n:dict(path=str(ROOT/n),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())for n,b in files.items()}
 def rebase(x):
  if type(x)is dict:
   if set(x)=={'path','bytes','sha256'}and x['path']in old:
    n,r=old[x['path']];need(x==r,'exact inherited file operand');return m['files'][n]
   return {k:rebase(v)for k,v in x.items()}
  if type(x)is list:return [rebase(v)for v in x]
  return x
 for k in('dependencies','performance_parent_preparation','performance_timing_donor','service_runtime_source_snapshots'):
  if k in m:m[k]=rebase(m[k])
 m['performance_streaming_client']=m['files']['native_2k_client.py']
 extra=[R.TEMPLATE,*parent['files'].values(),*assets.values(),*m['files'].values()]
 if authority_ref is not None:
  a=io.obj(authority_ref);extra.extend([authority_ref,a['MAIN_review_ref']])
 merged={}
 for r in [*m['dependencies'],*extra]:
  need(r['path']not in merged or merged[r['path']]==r,'unique complete native2k dependency closure');merged[r['path']]=r
 m['dependencies']=list(merged.values())
 for n,b in files.items():
  if n.endswith('.py'):compile(b,str(ROOT/n),'exec')
 return dict(manifest=m,files=files,parent_manifest=parent,parent_files={n:R.checked(r).read_bytes()for n,r in parent['files'].items()},
  physical_bound=False,authority_ref_supplied=authority_ref is not None,NPU=False)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--review',action='store_true');a=p.parse_args()
 if not a.review:print('{"enabled":false,"NPU":false}');return 0
 b=render();print(json.dumps(dict(files=len(b['files']),source_complete=True,actual_source_bound=False,authority_ref=None,MAIN_review_ref=None,sameimage_preflight=False,NPU=False)));return 0
if __name__=='__main__':raise SystemExit(main())
