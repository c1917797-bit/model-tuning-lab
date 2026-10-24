"""Minimal source-pin successor for frozen whole_v2; no authority or runtime action."""
import argparse,json,sys,types
from pathlib import Path
WS=Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
PARENT=dict(path=str(WS/'bole32k_fixed1024_performance_prepare_v1_20261023/whole_v2/formal_composer.py'),bytes=12649,sha256='0be60eb171a326dc135f3c6d78c06cea29d3c9b2d3bfe220fc66a407f1d419c0')
PREPARATION=WS/"bole_v16_followup_prepare_v2_20261024"
# Bootstrap only the already-frozen whole renderer, with ordinary full Ref checks.
import hashlib
def _load_parent():
 p=Path(PARENT['path']);a=p.stat()
 if not p.is_absolute()or not p.is_file()or any(x.is_symlink()for x in(p,*p.parents)):raise ValueError('ordinary frozen whole renderer')
 raw=p.read_bytes();z=p.stat()
 if (a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)!=(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns)or len(raw)!=PARENT['bytes']or hashlib.sha256(raw).hexdigest()!=PARENT['sha256']:raise ValueError('exact frozen whole renderer Ref')
 module=types.ModuleType('_frozen_source_pin_whole');module.__file__=str(p)
 old=sys.modules.get(module.__name__);present=module.__name__ in sys.modules;sys.modules[module.__name__]=module
 try:exec(compile(raw,str(p),'exec'),module.__dict__)
 finally:
  if present:sys.modules[module.__name__]=old
  else:sys.modules.pop(module.__name__,None)
 return module
_F=_load_parent()
for _n,_v in vars(_F).items():
 if not _n.startswith('__'):globals()[_n]=_v

CURRENT_PREPARATION=PREPARATION
FOLLOWUP_DISK_ADAPTER=ref(PREPARATION/'adapt_followup_disk.py')
REGISTERED_PARENT=dict(path=str(WS/'bole_formal_v7_related160_pin_prepare_20261024/formal_runtime.py'),bytes=4670,sha256='761b1b73d31296219cdee78718fa076519c27d90852a81fae2d34e7e63ac865d')
DISK_HELPER={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bole_profile_disk_ledger_v16_prepare_20261024/disk_ledger.py","bytes":5336,"sha256":"c876710ac37bedfdd300951cf5d5cb37177a7989817d7b8b3f0ff68c6b31c7cf"}
DISK_ADAPTER={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bole_profile_disk_ledger_v16_prepare_20261024/adapt_disk_ledger.py","bytes":3638,"sha256":"ebd2bf6fd42acd6be58d77140159777a4119430c16a72e4f2caedb8d0387d2ad"}
SCAN_REPAIR=dict(path=str(WS/'bole_output_scan_v14_prepare_20261024/output_scan_retry.py'),bytes=1185,sha256='c1d78350fbd93eafce1cdb65b41d159f4557a5183b12da9518d665a2441e7ce3')
SHORT8_SOURCE={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bole_profile_disk_ledger_v16_prepare_20261024/prepared-source-short8-v16/SOURCE_BOUND.json","bytes":1727366,"sha256":"3d052df4d27e55b87d2b53eced2dcdc5280f3cd9deacaa514f55062cad7b837d"}
SHORT8_CURRENT_REVIEW={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/renew24_20261023T073553Z/BOLE_V16_PROFILE_DISK_MAIN_REVIEW.json","bytes":189899,"sha256":"1b41670e75f32dd8aa0a69bb60feacf3e389561a521ede893f6d25b7dcede699"}
RELATED_Q=ref(CURRENT_PREPARATION/'related_qualification.py')
FOLLOWUP_INPUT=ref(WS/'bole_related160_v14_output_scan_prepare_20261024/followup_input.py')
LIVE_REPAIR=dict(path=str(WS/'bole_live_bindings_v11_prepare_20261024/live_binding_identity.py'),bytes=1797,sha256='2c6b9b18ae562bcadb0d57e612717e651db00e9b302cfa316dcd77c352e0b7cc')
CONV_REPAIR={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bole_formal_v15_arm_geometry_prepare_20261024/formal_conv_resource_layout.py","bytes":7489,"sha256":"1e686bf797750732de62856b3eefa0260f7847bf7efaf9620cd1e72b60c8c14f"}
PHASE_REPAIR=dict(path=str(WS/'bole_lifecycle_v12_prepare_20261024/lifecycle_admission.py'),bytes=2311,sha256='0f609a8a3965e18794c80a5a1137778be16de7c6eb5a50c71aa4b674524de18e')
TEXT_ADAPTER=dict(path=str(WS/'bole_textonly_v8_prepare_20261024/adapt_textonly.py'),bytes=2397,sha256='ff0b41b104115bc4f071180320a423b70827f2c1f8cb6920c217041108bcaa83')
TEXT_HELPER=dict(path=str(WS/'bole_textonly_v8_prepare_20261024/text_only_profile.py'),bytes=1276,sha256='0ae4161808a08f03085184d27307e6c53263022448c6abcd6ba054571da972cb')
SHORT_RENDERER={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bole_profile_disk_ledger_v16_prepare_20261024/runtime_lossless_imports.py","bytes":15505,"sha256":"600873d012062d4018befcf4bbec407388f7fa9ae9b65b92b222c0b854aa728d"}
V8_REVIEW=dict(path=str(WS/'renew24_20261023T073553Z/BOLE_V8_TEXTONLY_MAIN_REVIEW.json'),bytes=197994,sha256='5d8b43b7698fdb283e0e2d8d45d78c98f35003e3867bd3e347d6b448c25f8359')
GUARD_DELTA=dict(path=str(WS/'bole_guard_observation_prepare_v7_20261024/guard_failure_delta.py'),bytes=5628,sha256='fb25f8329ff2c58f16ccf8a64f9d068c0bc30c4944aca364393cf8d6d78e5136')
with _F.isolated():
 _L=module(REGISTERED_PARENT,'_frozen_related160_registered_formal')
def render(base,arm='bole',trial=0,authority_ref=None,prerequisites=None,preparation_assets=None,permit_materialized=False):
 b=_L.render(base,arm=arm,trial=trial,authority_ref=authority_ref,prerequisites=prerequisites,preparation_assets=preparation_assets,permit_materialized=permit_materialized)
 files=dict(b['files'])
 with _F.isolated():
  T=module(TEXT_ADAPTER,'_formal_exact_V8_textonly');files,_text=T.adapt(files)
 with _F.isolated():
  F=module(FOLLOWUP_INPUT,'_formal_actual_V10_input');files=F.adapt(files)
 with _F.isolated():
  LIVE=module(LIVE_REPAIR,'_formal_exact_live_binding');files,_live=LIVE.adapt(files)
 files['live_binding_identity.py']=checked(LIVE_REPAIR)
 with _F.isolated():
  PHASE=module(PHASE_REPAIR,'_formal_exact_prefill_phase');files,_phase=PHASE.adapt(files)
 files['lifecycle_admission.py']=checked(PHASE_REPAIR)
 with _F.isolated():
  CONV=module(CONV_REPAIR,'_formal_conv_resource');files,_conv=CONV.adapt(files)
 files['conv_resource_layout.py']=checked(CONV_REPAIR)
 with _F.isolated():
  SCAN=module(SCAN_REPAIR,'_formal_V14_output_scan');files,_scan=SCAN.adapt(files)
 files['output_scan_retry.py']=checked(SCAN_REPAIR)
 with _F.isolated():
  DISK=module(FOLLOWUP_DISK_ADAPTER,'_exact_V16_followup_profile_disk');before_disk=dict(files)
  files,_disk=DISK.adapt(files,helper=checked(DISK_HELPER),domain='formal')
  need(DISK.inverse(files,_disk)==before_disk,'complete V16 disk inverse')
 files['adapt_disk_ledger.py']=checked(DISK_ADAPTER)
 files['adapt_followup_disk.py']=checked(FOLLOWUP_DISK_ADAPTER)
 files['formal_composer.py']=(CURRENT_PREPARATION/'formal_runtime.py').read_bytes()
 files['short8_source_pin.py']=(CURRENT_PREPARATION/'short8_source_pin.py').read_bytes()
 files['related_qualification.py']=checked(RELATED_Q)
 files['adapt_textonly.py']=checked(TEXT_ADAPTER)
 need(files['text_only_profile.py']==checked(TEXT_HELPER),'exact common V8 text-only bytes')
 m=rebase(b['manifest'],files,Path(b['manifest']['root']))
 with _F.isolated():
  P=types.ModuleType('_formal_profile_module');P.__file__=str(Path(m['root'])/'input_resource_profile.py');exec(compile(files['input_resource_profile.py'],P.__file__,'exec'),P.__dict__)
  m['input_resource_profile32k']=CONV.profile(P,m)
 m['fa_lossless_capture']=dict(m['fa_lossless_capture'],raw_cap=m['input_resource_profile32k']['per_rank_disk_cap'])
 assets={n:ref(CURRENT_PREPARATION/n)for n in('formal_runtime.py','short8_source_pin.py')}
 assets.update(followup_disk_adapter=FOLLOWUP_DISK_ADAPTER,disk_ledger=DISK_HELPER,disk_adapter=DISK_ADAPTER,output_scan=SCAN_REPAIR,current_short8_source=SHORT8_SOURCE,current_short8_review=SHORT8_CURRENT_REVIEW,conv_resource=CONV_REPAIR,prefill_phase=PHASE_REPAIR,live_binding=LIVE_REPAIR,related_renderer=RELATED_Q,followup_input=FOLLOWUP_INPUT,V10_input_adapter=ref(WS/'bole_client_input_v10_prepare_20261024/adapt_input_preflight.py'),V10_input_helper=ref(WS/'bole_client_input_v10_prepare_20261024/input_preflight.py'),textonly_adapter=TEXT_ADAPTER,textonly_helper=TEXT_HELPER,V8_short8_review=V8_REVIEW,actual_short_renderer=SHORT_RENDERER)
 for n in('cpu_release_policy.py','cpu_precreate_policy.py','adapt_cpu_precreate.py'):assets['V8_'+n]=ref(WS/'bole_textonly_v8_prepare_20261024'/n)
 m['formal_v16_arm_geometry_preparation']=dict(schema='bole.formal-V8-textonly-source-registration/v1',assets=assets,qualification_inherited=False)
 m['actual_input_preflight']=dict(schema='bole.same-image-local-tokenizer-preflight/v1',required=True,actual_execution_pending=True,HTTP=False,NPU=False)
 m['text_only_common_configuration']=dict(schema='bole.common-text-only-image-video-zero/v1',limits={'image':0,'video':0},same_dense_candidate=True,actual_parser_pending=True,algorithm_gain=False)
 deps={r['path']:r for r in m['dependencies']}
 for r in(REGISTERED_PARENT,GUARD_DELTA,*assets.values()):
  need(r['path']not in deps or deps[r['path']]==r,'unambiguous exact formal V8 registration');deps[r['path']]=r
 m['dependencies']=list(deps.values())
 for key in('resources','input_resource_profile32k','fastpath_numeric_qualification','runtime_joint_capture_ledger','fa_lossless_capture'):
  if key in b['manifest']:need(m[key]==(CONV.profile(P,b['manifest'])if key=='input_resource_profile32k'else dict(b['manifest'][key],raw_cap=m['input_resource_profile32k']['per_rank_disk_cap'])if key=='fa_lossless_capture'else b['manifest'][key]),'unchanged formal protected contract except conv '+key)
 delta={n:dict(before=b['parent'].get(n),after=raw)for n,raw in files.items()if b['parent'].get(n)!=raw}
 for n,raw in files.items():
  if n.endswith('.py'):compile(raw,n,'exec')
 return dict(b,files=files,manifest=m,delta=delta)
def inverse(bundle):return _L.inverse(bundle)
def prepare(base,*,arm,trial=0,authority_ref=None,prerequisites=None):
 b=render(base,arm=arm,trial=trial,authority_ref=authority_ref,prerequisites=prerequisites);inverse(b)
 root=Path(b['manifest']['root']);root.parent.mkdir(parents=True,exist_ok=True);root.mkdir(mode=0o700)
 for n,raw in b['files'].items():
  f=root/n;need(root in f.parents and '..'not in f.parts,'contained source-only file');f.parent.mkdir(parents=True,exist_ok=True)
  with f.open('xb')as stream:stream.write(raw)
 raw=(json.dumps(b['manifest'],sort_keys=True)+'\n').encode()
 with(root/'SOURCE_TEMPLATE.json').open('xb')as stream:stream.write(raw)
 return dict(template=refbytes(root/'SOURCE_TEMPLATE.json',raw),source_bound=False,NPU=False)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);g=p.add_mutually_exclusive_group();g.add_argument('--check',action='store_true');g.add_argument('--prepare',action='store_true')
 p.add_argument('--base');p.add_argument('--arm',choices=('native_ar','bole'),default='bole');p.add_argument('--trial',type=int,default=0);p.add_argument('--authority-ref');p.add_argument('--prerequisites');a=p.parse_args()
 if not(a.check or a.prepare):
  need(a.base is None and a.authority_ref is None and a.prerequisites is None,'explicit source-only mode');print('{"enabled":false,"NPU":false}');return
 need(a.base,'exclusive source identity')
 kw=dict(arm=a.arm,trial=a.trial,authority_ref=None if a.authority_ref is None else json.loads(a.authority_ref),prerequisites=None if a.prerequisites is None else json.loads(a.prerequisites))
 if a.prepare:result=prepare(a.base,**kw)
 else:
  b=render(a.base,**kw);inverse(b);result=dict(files=len(b['files']),inverse=True,source_bound=False,NPU=False)
 print(json.dumps(result))
if __name__=='__main__':main()
