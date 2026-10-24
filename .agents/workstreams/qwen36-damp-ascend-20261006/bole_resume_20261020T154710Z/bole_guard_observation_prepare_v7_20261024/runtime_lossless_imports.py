"""V4 private CPU-only release domain; unchanged NPU admission/calculation."""
import argparse,copy,hashlib,json,sys,types
from pathlib import Path
from contextlib import contextmanager
WS=Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
PREP=WS/'bole_guard_observation_prepare_v7_20261024'
ROOT=PREP/'prepared-source-short8-v7'
OUT=Path('/opt/host/vnf/austinov/run-bole32k-lossless-guard-observation-short8-v7-20261024')
PARENT=dict(path=str(WS/'bole_lossless_health_prepare_v1_20261023/runtime_lossless_health.py'),
 bytes=9844,sha256='4c95ea070fbe0c9c97ed34aa208a3abd9af1354447d1c134d9033b0797f00535')
def need(v,s):
 if not v:raise ValueError(s)
def ref(p,b):return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def checked(r):
 p=Path(r['path']);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary pinned parent')
 b=p.read_bytes();need(ref(p,b)==r,'full exact source Ref');return b
def module(raw,path,name):
 m=types.ModuleType(name);m.__file__=str(path);sys.modules[name]=m
 exec(compile(raw,str(path),'exec'),m.__dict__);return m
@contextmanager
def isolated():
 old=dict(sys.modules);paths=list(sys.path)
 try:yield
 finally:sys.modules.clear();sys.modules.update(old);sys.path[:]=paths
def once(s,a,b):
 need(s.count(a)==1,'one exact health successor seam '+a[:80]);return s.replace(a,b,1)
def outputs(v,old,new):
 if type(v)is str:return new+v[len(old):]if v==old or v.startswith(old+'/')or v==old+'-CPU'or v.startswith(old+'-CPU/')else v
 if type(v)is dict:return{k:outputs(x,old,new)for k,x in v.items()}
 if type(v)is list:return[outputs(x,old,new)for x in v]
 return v
def compose(parent):
 files=dict(parent['files']);oldm=parent['manifest'];oldout=oldm['output_root']
 for name in('test_short_state_digest.py','test_digest_reader.py'):
  text=files[name].decode()
  text=once(text,"sys.path.insert(0,str(Path(__file__).parent/'fixtures'))\n",'')
  files[name]=text.encode()
 text=files['contract090.py'].decode()
 for a,b in((oldout,str(OUT)),(oldout+'-CPU',str(OUT)+'-CPU')):text=once(text,repr(a),repr(b))
 files['contract090.py']=text.encode()
 old=("    read_ref(m['files']['runtime_lossless_health.py'])\n"
      "    import runtime_lossless_health as LF\n"
      "    need(C.ref(LF.__file__)==m['files']['runtime_lossless_health.py'],'actual source-owned whole lossless health renderer')")
 new=("    read_ref(m['files']['runtime_lossless_imports.py'])\n"
      "    import runtime_lossless_imports as LF\n"
      "    need(C.ref(LF.__file__)==m['files']['runtime_lossless_imports.py'],'actual source-owned whole lossless import renderer')")
 files['qualification_source_validate.py']=once(files['qualification_source_validate.py'].decode(),old,new).encode()
 text=files['qualification_source_producer.py'].decode()
 need(text.count('    import runtime_lossless_health as Q')==2,'two actual public reconstruction entries')
 files['qualification_source_producer.py']=text.replace('    import runtime_lossless_health as Q','    import runtime_lossless_imports as Q').encode()
 files['runtime_lossless_imports.py']=(PREP/'runtime_lossless_imports.py').read_bytes()
 files['cpu_release_policy.py']=(PREP/'cpu_release_policy.py').read_bytes()
 text=files['owned_substrate.py'].decode()
 before=" observer_race_repair.install(S,C)"
 after=before+"\n raw(current['files']['cpu_release_policy.py'])\n import cpu_release_policy as CPU_RELEASE\n CPU_RELEASE.install(S,C,current)"
 files['owned_substrate.py']=once(text,before,after).encode()
 CPU=module(files['cpu_release_policy.py'],PREP/'cpu_release_policy.py','_cpu_release_contract')
 initial_raw=(PREP/'cpu_precreate_policy.py').read_bytes()
 INITIAL=module(initial_raw,PREP/'cpu_precreate_policy.py','cpu_precreate_policy')
 A=module((PREP/'adapt_cpu_precreate.py').read_bytes(),PREP/'adapt_cpu_precreate.py','_exact_CPU_initial_adapter')
 files,initial_delta=A.adapt(files)
 files['adapt_cpu_precreate.py']=(PREP/'adapt_cpu_precreate.py').read_bytes()
 G=module((PREP/'guard_failure_delta.py').read_bytes(),PREP/'guard_failure_delta.py','_exact_guard_observation_delta')
 files,guard_delta=G.adapt(files)
 m=outputs(copy.deepcopy(oldm),oldout,str(OUT))
 m.update(root=str(ROOT),qualification_preparation_root=str(PREP),performance_ready=False,numerical_qualified=False)
 m['deviceless_cpu_release']=copy.deepcopy(CPU.CONTRACT)
 m['cpu_precreate_intent']=copy.deepcopy(INITIAL.CONTRACT)
 aliases={r['path']:(n,r)for n,r in oldm['files'].items()}
 newrefs={n:ref(ROOT/n,b)for n,b in files.items()}
 def rebase(v):
  if type(v)is dict:
   if set(v)=={'path','bytes','sha256'}and v['path']in aliases:
    n,r=aliases[v['path']];need(v==r,'exact parent source alias');return newrefs[n]
   return{k:rebase(x)for k,x in v.items()}
  if type(v)is list:return[rebase(x)for x in v]
  return v
 m=rebase(m);m['files']=newrefs
 external=dict(lossless_import_parent=PARENT,
  lossless_import_runtime=ref(PREP/'runtime_lossless_imports.py',files['runtime_lossless_imports.py']),
  cpu_release_policy=ref(PREP/'cpu_release_policy.py',files['cpu_release_policy.py']),
  cpu_precreate_policy=ref(PREP/'cpu_precreate_policy.py',files['cpu_precreate_policy.py']),
  cpu_precreate_adapter=ref(PREP/'adapt_cpu_precreate.py',files['adapt_cpu_precreate.py']))
 external['guard_failure_delta']=ref(PREP/'guard_failure_delta.py',(PREP/'guard_failure_delta.py').read_bytes())
 m['short2k_helper_refs'].update(external)
 deps={r['path']:r for r in m['dependencies']}
 for r in(*external.values(),newrefs['runtime_lossless_imports.py']):
  need(r['path']not in deps or deps[r['path']]==r,'unambiguous current readset');deps[r['path']]=r
 m['dependencies']=list(deps.values())
 delta={n:dict(before=parent['files'].get(n),after=b)for n,b in files.items()if parent['files'].get(n)!=b}
 for name,body in files.items():
  if name.endswith('.py'):compile(body,name,'exec')
 V=module(files['qualification_source_validate.py'],ROOT/'qualification_source_validate.py','_current_import_shape')
 V.qualification_shape(m)
 for key in('resources','input_resource_profile32k','fastpath_numeric_qualification','runtime_joint_capture_ledger','fa_lossless_capture'):
  need(m[key]==oldm[key],'unchanged mathematics/input/capture/resource contract '+key)
 return dict(files=files,manifest=m,parent=parent,delta=delta,NPU=False,source_bound=False,
  execution_ready=False,numerical_qualified=False,pending=['MAIN exact new source review and authority',
   'actual current source bind/audit/sameimage25/parser/retained CPU release; no old PASS reuse',
   'actual same-worker short8 geometry/math/resources; then160/performance/task gates'])
def inverse(bundle):
 out=dict(bundle['files'])
 need({n for n in out if bundle['parent']['files'].get(n)!=out[n]}==set(bundle['delta']),'all-and-only complete health delta')
 for name,row in bundle['delta'].items():
  need(out[name]==row['after'],'exact health source inverse')
  if row['before']is None:out.pop(name)
  else:out[name]=row['before']
 need(out==bundle['parent']['files'],'restore every original454 source byte')
 return out
def render(*,base_root=None,permit_materialized=True,parent_pair_preparation_root=None,
 historical_short_source_ref=None,authority_ref=None,parent_preparation_readset=None):
 with isolated():
  need(base_root is None or Path(base_root)==PREP,'exact health successor preparation')
  if not permit_materialized:need(not ROOT.exists()and not OUT.exists(),'new exclusive health source/output')
  sys.path.insert(0,str(Path(PARENT['path']).parent))
  P=module(checked(PARENT),PARENT['path'],'_exact_lossless_parent')
  parent=P.render(permit_materialized=True,parent_pair_preparation_root=parent_pair_preparation_root,
   historical_short_source_ref=historical_short_source_ref,authority_ref=None,
   parent_preparation_readset=parent_preparation_readset)
  result=compose(parent);result['manifest']['qualification_authority_ref']=authority_ref;inverse(result)
  if authority_ref is not None:
   checked(authority_ref)
   V=module(result['files']['qualification_source_validate.py'],ROOT/'qualification_source_validate.py','_current_health_authority')
   V.execution_window(result['manifest'],clock=False,require_phase=False)
  return result
def materialize(authority_ref):
 need(authority_ref is not None,'actual new MAIN source-specific authority required')
 b=render(authority_ref=authority_ref,permit_materialized=False)
 V=module(b['files']['qualification_source_validate.py'],ROOT/'qualification_source_validate.py','_actual_health_materialize')
 V.execution_window(b['manifest'],clock=True,require_phase=True)
 ROOT.mkdir(mode=0o700)
 for name,raw in b['files'].items():
  p=ROOT/name;need(ROOT in p.parents and '..'not in Path(name).parts,'contained reviewed source')
  p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('xb')as f:f.write(raw)
 def write(name,value):
  raw=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode();p=ROOT/name
  with p.open('xb')as f:f.write(raw)
  return ref(p,raw)
 delta={n:dict(before=b['parent']['manifest']['files'].get(n),after=b['manifest']['files'][n])for n in b['delta']}
 return dict(prepared_template=write('SOURCE_TEMPLATE.json',b['manifest']),
  inverse_delta=write('SOURCE_DELTA.json',delta),source_bound=False,NPU=False)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);g=p.add_mutually_exclusive_group()
 g.add_argument('--check',action='store_true');g.add_argument('--prepare',action='store_true');p.add_argument('--authority-ref');a=p.parse_args()
 if a.prepare:
  need(a.authority_ref is not None,'new exact MAIN authority mandatory');print(json.dumps(materialize(json.loads(a.authority_ref))));return
 need(a.authority_ref is None,'no ambient authority')
 if not a.check:print('{"enabled":false,"source_bound":false,"NPU":false}');return
 b=render();inverse(b);print(json.dumps(dict(files=len(b['files']),whole_inverse=True,NPU=False,source_bound=False,pending=b['pending'])))
if __name__=='__main__':main()
