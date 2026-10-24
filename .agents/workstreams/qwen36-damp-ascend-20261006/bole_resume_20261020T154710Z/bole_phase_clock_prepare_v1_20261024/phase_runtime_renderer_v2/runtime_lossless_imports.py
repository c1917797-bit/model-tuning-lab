"""Source-only shared-parent phase overlay on the exact existing cache renderer."""
import argparse,copy,hashlib,json,sys,types
from pathlib import Path
from contextlib import contextmanager
WS=Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z")
PREP=WS/'bole_phase_clock_prepare_v1_20261024/phase_runtime_renderer_v2'
ASSETS=PREP.parent
ROOT=PREP/'prepared-source-short8-shared-phase-v2'
OUT=Path('/opt/host/vnf/austinov/run-bole32k-cache-shared-phase-short8-v2-20261024')
PARENT=dict(path=str(WS/'bole_fa_cache_diagnostic_prepare_v1_20261024/runtime_lossless_imports.py'),bytes=16556,sha256='5be3ebff0287227cd4a07c00d80babf25e7b2be8bbe7ccb855f77e962f3f4ef3')
ASSET_REFS={
 'adapt_phase_clock.py':dict(path=str(ASSETS/'adapt_phase_clock.py'),bytes=2026,sha256='b1b7fbe6ecda968b7c4fdbebe2f1cf43950984d5aaf983eec4d3d28c71a86cac'),
 'shared_phase_clock.py':dict(path=str(ASSETS/'shared_phase_clock.py'),bytes=9288,sha256='deec7d583b5c94c196511269546fdd86e909623b91c0555d21371957cabbac30')}
def need(v,s):
 if not v:raise ValueError(s)
def ref(p,b):return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def checked(r):
 p=Path(r['path']);need(p.is_absolute() and p.is_file() and not any(q.is_symlink()for q in(p,*p.parents)),'ordinary pinned phase preparation')
 raw=p.read_bytes();need(ref(p,raw)==r,'whole exact phase preparation Ref');return raw
def module(raw,path,name):
 obj=types.ModuleType(name);obj.__file__=str(path);sys.modules[name]=obj
 exec(compile(raw,str(path),'exec'),obj.__dict__);return obj
@contextmanager
def isolated():
 old=dict(sys.modules);paths=list(sys.path)
 try:yield
 finally:sys.modules.clear();sys.modules.update(old);sys.path[:]=paths
def inverse(bundle):
 out=dict(bundle['files'])
 need({n for n,b in out.items()if bundle['parent']['files'].get(n)!=b}==set(bundle['delta']),'all-and-only shared-phase delta')
 for n,r in bundle['delta'].items():
  need(out[n]==r['after'],'exact shared-phase inverse')
  if r['before']is None:del out[n]
  else:out[n]=r['before']
 need(out==bundle['parent']['files'],'all exact cache-parent source bytes restored')
 return out
def render(*,base_root=None,permit_materialized=True,parent_pair_preparation_root=None,
 historical_short_source_ref=None,authority_ref=None,parent_preparation_readset=None):
 with isolated():
  need(base_root is None or Path(base_root)==PREP,'exact phase preparation root')
  if not permit_materialized:need(not ROOT.exists() and not OUT.exists() and not Path(str(OUT)+'-CPU').exists(),'exclusive new phase source and outputs')
  P=module(checked(PARENT),PARENT['path'],'_actual_cache_phase_parent')
  parent=P.render(permit_materialized=True,parent_pair_preparation_root=parent_pair_preparation_root,
   historical_short_source_ref=historical_short_source_ref,authority_ref=authority_ref,
   parent_preparation_readset=parent_preparation_readset)
  P.inverse(parent)
  helper=checked(ASSET_REFS['shared_phase_clock.py']);adapter=checked(ASSET_REFS['adapt_phase_clock.py'])
  module(helper,ASSET_REFS['shared_phase_clock.py']['path'],'shared_phase_clock')
  A=module(adapter,ASSET_REFS['adapt_phase_clock.py']['path'],'_exact_shared_phase_overlay')
  files,phase_delta=A.adapt(parent['files'])
  need(A.inverse(files,phase_delta)==parent['files'],'whole direct four-module phase inverse')
  oldm=parent['manifest'];oldout=oldm['output_root'];text=files['contract090.py'].decode()
  for before,after in ((oldout,str(OUT)),(oldout+'-CPU',str(OUT)+'-CPU')):
   need(text.count(repr(before))==1,'one exact output literal')
   text=text.replace(repr(before),repr(after),1)
  files['contract090.py']=text.encode()
  files['runtime_lossless_imports.py']=Path(__file__).read_bytes()
  files['adapt_phase_clock.py']=adapter
  m=A.manifest(P.outputs(copy.deepcopy(oldm),oldout,str(OUT)))
  m.update(root=str(ROOT),qualification_preparation_root=str(PREP),performance_ready=False,numerical_qualified=False)
  aliases={r['path']:(n,r)for n,r in oldm['files'].items()}
  refs={n:ref(ROOT/n,raw)for n,raw in files.items()}
  def rebase(v):
   if type(v)is dict:
    if set(v)=={'path','bytes','sha256'} and v['path']in aliases:
     n,r=aliases[v['path']];need(v==r,'unambiguous original file alias');return refs[n]
    return{k:rebase(x)for k,x in v.items()}
   if type(v)is list:return[rebase(x)for x in v]
   return v
  m=rebase(m);m['files']=refs
  external=dict(phase_parent_renderer=PARENT,phase_adapter=ASSET_REFS['adapt_phase_clock.py'],
   phase_helper=ASSET_REFS['shared_phase_clock.py'],phase_runtime=ref(PREP/'runtime_lossless_imports.py',files['runtime_lossless_imports.py']))
  m['short2k_helper_refs'].update(external)
  deps={r['path']:r for r in m['dependencies']}
  for r in (*external.values(),refs['runtime_lossless_imports.py'],refs['adapt_phase_clock.py'],refs['shared_phase_clock.py']):
   need(r['path']not in deps or deps[r['path']]==r,'unambiguous phase readset');deps[r['path']]=r
  m['dependencies']=list(deps.values())
  expected={'contract090.py','host_service.py','external025.py','owned_create.py','shared_phase_clock.py','adapt_phase_clock.py','runtime_lossless_imports.py'}
  delta={n:dict(before=parent['files'].get(n),after=raw)for n,raw in files.items()if parent['files'].get(n)!=raw}
  need(set(delta)==expected,'only four runtime seams plus helper adapter renderer')
  for n,raw in files.items():
   if n.endswith('.py'):compile(raw,n,'exec')
  for k in ('resources','input_resource_profile32k','fastpath_numeric_qualification','runtime_joint_capture_ledger','fa_lossless_capture','qualification_authority_ref'):
   need(m[k]==oldm[k],'unchanged original protected resource/math/authority '+k)
  V=module(files['qualification_source_validate.py'],ROOT/'qualification_source_validate.py','_phase_shape_only')
  V.qualification_shape(m)
  bundle=dict(files=files,manifest=m,parent=parent,delta=delta,source_bound=False,execution_ready=False,NPU=False,
   numerical_qualified=False,pending=['MAIN full source review; this renderer does not materialize or bind',
    'original 07:35:53 UTC cutoff unchanged; no new full phase fits this window',
    'actual same-image readonly custody/cgroup/time namespace and subsequent NPU remain untested'])
  inverse(bundle);return bundle
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--check',action='store_true');a=p.parse_args()
 if not a.check:print('{"enabled":false,"source_bound":false,"NPU":false}');return
 b=render(permit_materialized=False)
 print(json.dumps(dict(files=len(b['files']),changed=sorted(b['delta']),whole_inverse=True,
  source_bound=False,NPU=False,root=str(ROOT),output=str(OUT),
  delta={n:dict(before=b['parent']['manifest']['files'].get(n),after=b['manifest']['files'][n])for n in b['delta']},
  preparation_refs={k:v for k,v in b['manifest']['short2k_helper_refs'].items()if k.startswith('phase_')}),sort_keys=True))
if __name__=='__main__':main()
