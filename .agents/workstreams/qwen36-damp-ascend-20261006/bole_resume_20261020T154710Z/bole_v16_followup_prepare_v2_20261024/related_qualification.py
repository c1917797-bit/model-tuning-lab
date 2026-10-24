"""Related160 V7 CPU-domain and diagnostics successor; no inherited qualification."""
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

FOLLOWUP_INPUT=ref(WS/'bole_related160_v14_output_scan_prepare_20261024/followup_input.py')
SUCCESSOR=PREPARATION
FOLLOWUP_DISK_ADAPTER=ref(PREPARATION/'adapt_followup_disk.py')
CPU_ASSETS=WS/'bole_textonly_v8_prepare_20261024'
TEXT_ADAPTER=dict(path=str(WS/'bole_textonly_v8_prepare_20261024/adapt_textonly.py'),bytes=2397,sha256='ff0b41b104115bc4f071180320a423b70827f2c1f8cb6920c217041108bcaa83')
TEXT_HELPER=dict(path=str(WS/'bole_textonly_v8_prepare_20261024/text_only_profile.py'),bytes=1276,sha256='0ae4161808a08f03085184d27307e6c53263022448c6abcd6ba054571da972cb')
SHORT8_REVIEW=dict(path=str(WS/'renew24_20261023T073553Z/BOLE_V8_TEXTONLY_MAIN_REVIEW.json'),bytes=197994,sha256='5d8b43b7698fdb283e0e2d8d45d78c98f35003e3867bd3e347d6b448c25f8359')
LIVE_REPAIR=dict(path=str(WS/'bole_live_bindings_v11_prepare_20261024/live_binding_identity.py'),bytes=1797,sha256='2c6b9b18ae562bcadb0d57e612717e651db00e9b302cfa316dcd77c352e0b7cc')
CONV_REPAIR=dict(path=str(WS/'bole_conv_resource_v13_prepare_20261024/conv_resource_layout.py'),bytes=5571,sha256='1bcd624eba62f68066de1d06682cf5f7042393996863c755da0d185687fce8e7')
PHASE_REPAIR=dict(path=str(WS/'bole_lifecycle_v12_prepare_20261024/lifecycle_admission.py'),bytes=2311,sha256='0f609a8a3965e18794c80a5a1137778be16de7c6eb5a50c71aa4b674524de18e')
DISK_HELPER={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bole_profile_disk_ledger_v16_prepare_20261024/disk_ledger.py","bytes":5336,"sha256":"c876710ac37bedfdd300951cf5d5cb37177a7989817d7b8b3f0ff68c6b31c7cf"}
DISK_ADAPTER={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bole_profile_disk_ledger_v16_prepare_20261024/adapt_disk_ledger.py","bytes":3638,"sha256":"ebd2bf6fd42acd6be58d77140159777a4119430c16a72e4f2caedb8d0387d2ad"}
SCAN_REPAIR=dict(path=str(WS/'bole_output_scan_v14_prepare_20261024/output_scan_retry.py'),bytes=1185,sha256='c1d78350fbd93eafce1cdb65b41d159f4557a5183b12da9518d665a2441e7ce3')
SHORT8_SOURCE={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bole_profile_disk_ledger_v16_prepare_20261024/prepared-source-short8-v16/SOURCE_BOUND.json","bytes":1727366,"sha256":"3d052df4d27e55b87d2b53eced2dcdc5280f3cd9deacaa514f55062cad7b837d"}
SHORT8_CURRENT_REVIEW={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/renew24_20261023T073553Z/BOLE_V16_PROFILE_DISK_MAIN_REVIEW.json","bytes":189899,"sha256":"1b41670e75f32dd8aa0a69bb60feacf3e389561a521ede893f6d25b7dcede699"}
RELATED_PARENT=dict(path=str(WS/'bole32k_fixed1024_performance_prepare_v1_20261023/whole_v2/related_qualification.py'),bytes=16695,sha256='016ec1a4b8e449f566020ddad655742a3e92f007f9576640bd665d2d85adba88')
GUARD=dict(path=str(WS/'bole_guard_observation_prepare_v7_20261024/guard_failure_delta.py'),bytes=5628,sha256='fb25f8329ff2c58f16ccf8a64f9d068c0bc30c4944aca364393cf8d6d78e5136')
with _F.isolated():
 sys.modules['formal_composer']=_F
 _Q=_F.module(RELATED_PARENT,'_frozen_related160_v2')
_BASE_RENDER=_Q.render
_BASE_INVERSE=_Q.inverse
def _assets():
 return dict({n:ref((SUCCESSOR if n=='related_qualification.py'else CPU_ASSETS)/n)for n in('related_qualification.py','cpu_release_policy.py','cpu_precreate_policy.py','adapt_cpu_precreate.py')},**{'adapt_textonly.py':TEXT_ADAPTER,'text_only_profile.py':TEXT_HELPER})
def adapt(files):
 out=dict(files)
 need('cpu_release_policy.py'not in out and 'cpu_precreate_policy.py'not in out,'legacy related160 has no stacked CPU policies')
 marker=' observer_race_repair.install(S,C)'
 added=marker+"\n raw(current['files']['cpu_release_policy.py'])\n import cpu_release_policy as CPU_RELEASE\n CPU_RELEASE.install(S,C,current)"
 out['owned_substrate.py']=once(out['owned_substrate.py'].decode(),marker,added).encode()
 assets=_assets()
 out['cpu_release_policy.py']=checked(assets['cpu_release_policy.py'])
 with _F.isolated():
  module(assets['cpu_precreate_policy.py'],'cpu_precreate_policy')
  A=module(assets['adapt_cpu_precreate.py'],'_related160_CPU_initial')
  out,_=A.adapt(out)
  G=module(GUARD,'_related160_guard')
  out,_=G.adapt(out)
 out['adapt_cpu_precreate.py']=checked(assets['adapt_cpu_precreate.py'])
 with _F.isolated():
  T=module(TEXT_ADAPTER,'_related160_exact_V8_textonly');out,_=T.adapt(out)
 need(out['text_only_profile.py']==checked(TEXT_HELPER),'exact V8 common text-only helper')
 out['adapt_textonly.py']=checked(TEXT_ADAPTER)
 with _F.isolated():
  F=module(FOLLOWUP_INPUT,'_related_actual_V10_input');out=F.adapt(out)
 with _F.isolated():
  LIVE=module(LIVE_REPAIR,'_related_exact_live_binding');out,_live=LIVE.adapt(out)
 out['live_binding_identity.py']=checked(LIVE_REPAIR)
 with _F.isolated():
  PHASE=module(PHASE_REPAIR,'_related_exact_prefill_phase');out,_phase=PHASE.adapt(out)
 out['lifecycle_admission.py']=checked(PHASE_REPAIR)
 with _F.isolated():
  CONV=module(CONV_REPAIR,'_related_conv_resource');out,_conv=CONV.adapt(out)
 out['conv_resource_layout.py']=checked(CONV_REPAIR)
 with _F.isolated():
  SCAN=module(SCAN_REPAIR,'_related_V14_output_scan');out,_scan=SCAN.adapt(out)
 out['output_scan_retry.py']=checked(SCAN_REPAIR)
 with _F.isolated():
  DISK=module(FOLLOWUP_DISK_ADAPTER,'_exact_V16_followup_profile_disk');before_disk=dict(out)
  out,_disk=DISK.adapt(out,helper=checked(DISK_HELPER),domain='related160')
  need(DISK.inverse(out,_disk)==before_disk,'complete V16 disk inverse')
 out['adapt_disk_ledger.py']=checked(DISK_ADAPTER)
 out['adapt_followup_disk.py']=checked(FOLLOWUP_DISK_ADAPTER)
 out['related_qualification.py']=checked(assets['related_qualification.py'])
 return out
def render(*,base_root=None,authority_ref=None,permit_materialized=False,parent_pair_preparation_root=None,historical_short_source_ref=None,parent_preparation_readset=None):
 base=Path(base_root)if base_root is not None else SUCCESSOR/'bole-v16-followup-v2-20261024-related160-rawON'
 need(base.name.endswith(('-rawON','-rawOFF')),'explicit related160 capture identity')
 parent=_BASE_RENDER(base_root=base,authority_ref=None,permit_materialized=permit_materialized,parent_pair_preparation_root=parent_pair_preparation_root,historical_short_source_ref=historical_short_source_ref,parent_preparation_readset=parent_preparation_readset)
 files=adapt(parent['files']);m=rebase(parent['manifest'],files,Path(parent['manifest']['root']))
 with _F.isolated():
  CONV=module(CONV_REPAIR,'_related_conv_profile');P=types.ModuleType('_related_profile_module');P.__file__=str(Path(m['root'])/'input_resource_profile.py');exec(compile(files['input_resource_profile.py'],P.__file__,'exec'),P.__dict__)
  m['input_resource_profile32k']=CONV.profile(P,m)
 m['fa_lossless_capture']=dict(m['fa_lossless_capture'],raw_cap=m['input_resource_profile32k']['per_rank_disk_cap'])
 assets=_assets()
 assets.update(followup_disk_adapter=FOLLOWUP_DISK_ADAPTER,disk_ledger=DISK_HELPER,disk_adapter=DISK_ADAPTER,output_scan=SCAN_REPAIR,current_short8_source=SHORT8_SOURCE,current_short8_review=SHORT8_CURRENT_REVIEW,conv_resource=CONV_REPAIR,prefill_phase=PHASE_REPAIR,live_binding=LIVE_REPAIR,followup_input=FOLLOWUP_INPUT,V10_input_adapter=ref(WS/'bole_client_input_v10_prepare_20261024/adapt_input_preflight.py'),V10_input_helper=ref(WS/'bole_client_input_v10_prepare_20261024/input_preflight.py'))
 with _F.isolated():
  CPU=module(assets['cpu_release_policy.py'],'_related160_CPU_release_contract')
  INITIAL=module(assets['cpu_precreate_policy.py'],'_related160_CPU_initial_contract')
  m['deviceless_cpu_release']=copy.deepcopy(CPU.CONTRACT)
  m['cpu_precreate_intent']=copy.deepcopy(INITIAL.CONTRACT)
 m['text_only_common_configuration']=dict(schema='bole.common-text-only-image-video-zero/v1',limits={'image':0,'video':0},same_dense_candidate=True,actual_parser_pending=True,algorithm_gain=False)
 m['related_v16_runtime_preparation']=dict(schema='bole.related160-V7-CPU-and-guard-source/v1',assets=assets,parent=RELATED_PARENT,guard_delta=GUARD,qualification_inherited=False,short8_review=SHORT8_REVIEW,current_short8_source=SHORT8_SOURCE,current_short8_review=SHORT8_CURRENT_REVIEW,actual_short8_qualification_pending=True)
 m['actual_input_preflight']=dict(schema='bole.same-image-local-tokenizer-preflight/v1',required=True,actual_execution_pending=True,HTTP=False,NPU=False)
 m['short2k_helper_refs'].update({'related_v7_'+n:r for n,r in assets.items()})
 m['short2k_helper_refs']['related_v7_guard_delta']=GUARD
 deps={r['path']:r for r in m['dependencies']}
 for r in(RELATED_PARENT,GUARD,SHORT8_REVIEW,*assets.values()):
  need(r['path']not in deps or deps[r['path']]==r,'unambiguous related160 successor dependency');deps[r['path']]=r
 m['dependencies']=list(deps.values());m['qualification_authority_ref']=authority_ref
 if authority_ref is not None:
  a=json.loads(checked(authority_ref));review=json.loads(checked(a['MAIN_review_ref']))
  m['related_control_predecessor_ref']=review.get('related_control_predecessor_ref')
 for key in('resources','input_resource_profile32k','fastpath_numeric_qualification','runtime_joint_capture_ledger','fa_lossless_capture','short_state_digest_profile'):
  need(m[key]==(CONV.profile(P,parent['manifest'])if key=='input_resource_profile32k'else dict(parent['manifest'][key],raw_cap=m['input_resource_profile32k']['per_rank_disk_cap'])if key=='fa_lossless_capture'else parent['manifest'][key]),'unchanged related160 contract except exact conv derivation '+key)
 ledger={n:dict(before=parent['parent'].get(n),after=raw)for n,raw in files.items()if parent['parent'].get(n)!=raw}
 for n,raw in files.items():
  if n.endswith('.py'):compile(raw,n,'exec')
 return dict(parent,files=files,manifest=m,delta=ledger,NPU=False,source_bound=False,qualification_inherited=False)
def inverse(bundle):return _BASE_INVERSE(bundle)
def check_control_predecessor(m):return _Q.check_control_predecessor(m)
def consume_pair(*args,**kwargs):return _Q.consume_pair(*args,**kwargs)
_Q.render=render
_Q.inverse=inverse
def main():return _Q.main()
if __name__=='__main__':main()
