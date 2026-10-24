"""Minimal source-pin successor for frozen whole_v2; no authority or runtime action."""
import argparse,json,sys,types
from pathlib import Path
WS=Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
PARENT=dict(path=str(WS/'bole32k_fixed1024_performance_prepare_v1_20261023/whole_v2/formal_composer.py'),bytes=12649,sha256='0be60eb171a326dc135f3c6d78c06cea29d3c9b2d3bfe220fc66a407f1d419c0')
PREPARATION=WS/'bole_formal_v10_input_pin_prepare_20261024'
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
REGISTERED_PARENT=dict(path=str(WS/'bole_formal_v7_related160_pin_prepare_20261024/formal_runtime.py'),bytes=4670,sha256='761b1b73d31296219cdee78718fa076519c27d90852a81fae2d34e7e63ac865d')
RELATED_Q=ref(WS/'bole_related160_v10_input_prepare_20261024/related_qualification.py')
FOLLOWUP_INPUT=ref(WS/'bole_related160_v10_input_prepare_20261024/followup_input.py')
TEXT_ADAPTER=dict(path=str(WS/'bole_textonly_v8_prepare_20261024/adapt_textonly.py'),bytes=2397,sha256='ff0b41b104115bc4f071180320a423b70827f2c1f8cb6920c217041108bcaa83')
TEXT_HELPER=dict(path=str(WS/'bole_textonly_v8_prepare_20261024/text_only_profile.py'),bytes=1276,sha256='0ae4161808a08f03085184d27307e6c53263022448c6abcd6ba054571da972cb')
SHORT_RENDERER=dict(path=str(WS/'bole_client_input_v10_prepare_20261024/runtime_lossless_imports.py'),bytes=11591,sha256='3f4ac564768f3931492a23756083dc14f3e29efc8b354e7e62ad45a6cf7570e2')
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
 files['formal_composer.py']=(CURRENT_PREPARATION/'formal_runtime.py').read_bytes()
 files['short8_source_pin.py']=(CURRENT_PREPARATION/'short8_source_pin.py').read_bytes()
 files['related_qualification.py']=checked(RELATED_Q)
 files['adapt_textonly.py']=checked(TEXT_ADAPTER)
 need(files['text_only_profile.py']==checked(TEXT_HELPER),'exact common V8 text-only bytes')
 m=rebase(b['manifest'],files,Path(b['manifest']['root']))
 assets={n:ref(CURRENT_PREPARATION/n)for n in('formal_runtime.py','short8_source_pin.py')}
 assets.update(related_renderer=RELATED_Q,followup_input=FOLLOWUP_INPUT,V10_input_adapter=ref(WS/'bole_client_input_v10_prepare_20261024/adapt_input_preflight.py'),V10_input_helper=ref(WS/'bole_client_input_v10_prepare_20261024/input_preflight.py'),textonly_adapter=TEXT_ADAPTER,textonly_helper=TEXT_HELPER,V8_short8_review=V8_REVIEW,actual_short_renderer=SHORT_RENDERER)
 for n in('cpu_release_policy.py','cpu_precreate_policy.py','adapt_cpu_precreate.py'):assets['V8_'+n]=ref(WS/'bole_textonly_v8_prepare_20261024'/n)
 m['formal_v10_input_preparation']=dict(schema='bole.formal-V8-textonly-source-registration/v1',assets=assets,qualification_inherited=False)
 m['actual_input_preflight']=dict(schema='bole.same-image-local-tokenizer-preflight/v1',required=True,actual_execution_pending=True,HTTP=False,NPU=False)
 m['text_only_common_configuration']=dict(schema='bole.common-text-only-image-video-zero/v1',limits={'image':0,'video':0},same_dense_candidate=True,actual_parser_pending=True,algorithm_gain=False)
 deps={r['path']:r for r in m['dependencies']}
 for r in(REGISTERED_PARENT,GUARD_DELTA,*assets.values()):
  need(r['path']not in deps or deps[r['path']]==r,'unambiguous exact formal V8 registration');deps[r['path']]=r
 m['dependencies']=list(deps.values())
 for key in('resources','input_resource_profile32k','fastpath_numeric_qualification','runtime_joint_capture_ledger','fa_lossless_capture'):
  if key in b['manifest']:need(m[key]==b['manifest'][key],'unchanged formal protected contract '+key)
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
