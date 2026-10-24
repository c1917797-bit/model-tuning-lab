"""Minimal source-pin successor for frozen whole_v2; no authority or runtime action."""
import argparse,json,sys,types
from pathlib import Path
WS=Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
PARENT=dict(path=str(WS/'bole32k_fixed1024_performance_prepare_v1_20261023/whole_v2/formal_composer.py'),bytes=12649,sha256='0be60eb171a326dc135f3c6d78c06cea29d3c9b2d3bfe220fc66a407f1d419c0')
PREPARATION=WS/'bole_cpu_precreate_whole_v5_prepare_20261023'
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
PIN_PREPARATION=PREPARATION
CPU_POLICY=dict(path=str(WS/'bole_cpu_precreate_whole_v5_prepare_20261023/cpu_release_policy.py'),bytes=3952,sha256='a7da0a2ef2116b80f18d4d00c1646e8d190aede11df5411aa382a93b7e4b4895')
def adapt(files):
 out=dict(files);old=out['performance_prerequisite.py'].decode()
 seam=""" with R.isolated():
  R.module(R.DELTA,'performance_delta')
  S=R.module(R.PREREQ,'_actual_short8_reopen')
  short=S.consume(p['short8_scope'],p['short8_host'])"""
 out['performance_prerequisite.py']=once(old,seam," import short8_source_pin as PIN\n short=PIN.consume(m)").encode()
 out['formal_composer.py']=(PIN_PREPARATION/'formal_runtime.py').read_bytes()
 out['short8_source_pin.py']=(PIN_PREPARATION/'short8_source_pin.py').read_bytes()
 out['cpu_release_policy.py']=checked(CPU_POLICY)
 marker=' observer_race_repair.install(S,C)'
 added=marker+"\n raw(current['files']['cpu_release_policy.py'])\n import cpu_release_policy as CPU_RELEASE\n CPU_RELEASE.install(S,C,current)"
 out['owned_substrate.py']=once(out['owned_substrate.py'].decode(),marker,added).encode()
 with _F.isolated():
  module(ref(PIN_PREPARATION/'cpu_precreate_policy.py'),'cpu_precreate_policy')
  A=module(ref(PIN_PREPARATION/'adapt_cpu_precreate.py'),'_formal_CPU_initial_adapter')
  out,_initial=A.adapt(out)
 out['adapt_cpu_precreate.py']=(PIN_PREPARATION/'adapt_cpu_precreate.py').read_bytes()
 delta={n:dict(before=files.get(n),after=b)for n,b in out.items()if files.get(n)!=b}
 return out,delta
def inverse_delta(files,delta):
 out=dict(files);need({n for n in out if delta.get(n,{}).get('before',out[n])!=out[n]}==set(delta),'only source-pin delta')
 for n,row in delta.items():
  need(out[n]==row['after'],'exact source-pin inverse byte')
  if row['before']is None:out.pop(n)
  else:out[n]=row['before']
 return out
def render(base,arm='bole',trial=0,authority_ref=None,prerequisites=None,preparation_assets=None,permit_materialized=False):
 b=_F.render(base,arm=arm,trial=trial,authority_ref=authority_ref,prerequisites=prerequisites,preparation_assets=preparation_assets,permit_materialized=permit_materialized)
 files,delta=adapt(b['files']);need(inverse_delta(files,delta)==b['files'],'whole source-pin inverse')
 m=rebase(b['manifest'],files,Path(b['manifest']['root']))
 assets={n:ref(PIN_PREPARATION/n)for n in('formal_runtime.py','short8_source_pin.py','cpu_precreate_policy.py','adapt_cpu_precreate.py','runtime_lossless_imports.py')}
 m['formal_source_pin_preparation']=assets
 m['formal_source_pin_scope']=dict(schema='bole.reviewed-short8-CPUcleanup-source-pin/v1',no_qualification_inherited=True)
 with _F.isolated():
  CPU=_F.module(CPU_POLICY,'_source_pin_CPUrelease_contract')
  m['deviceless_cpu_release']=copy.deepcopy(CPU.CONTRACT)
  INITIAL=_F.module(ref(PIN_PREPARATION/'cpu_precreate_policy.py'),'_formal_CPU_initial_contract')
  m['cpu_precreate_intent']=copy.deepcopy(INITIAL.CONTRACT)
 deps={r['path']:r for r in m['dependencies']}
 for r in(PARENT,CPU_POLICY,*assets.values()):
  need(r['path']not in deps or deps[r['path']]==r,'unambiguous source-pin readset');deps[r['path']]=r
 m['dependencies']=list(deps.values())
 ledger={n:dict(before=b['parent'].get(n),after=raw)for n,raw in files.items()if b['parent'].get(n)!=raw}
 for n,raw in files.items():
  if n.endswith('.py'):compile(raw,n,'exec')
 return dict(b,files=files,manifest=m,delta=ledger)
def inverse(bundle):return _F.inverse(bundle)
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
