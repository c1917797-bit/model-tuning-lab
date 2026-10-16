"""Thin existing075/025 owner recipe, not a new resource/controller class.

Exclusive TP4 controller is retained exactly; numerical guest uses logical0.
This is explicit resource conservatism, not four-card useful-compute evidence.
"""
import argparse,json,os,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import api122 as A
def main():
 start=time.monotonic()
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 import resource
 A.need(os.environ.get('DL122_VALIDATE_ENABLE')=='1','MAIN-only validation optin');sr=json.loads(a.source_ref);m,q=A.qualify(sr,pair=False);A.need(m['stage']=='validation','only validation source')
 A.need(a.output==Path('/opt/host/vnf/austinov/run-dl-production122R2-validation-MAIN-NEW24H_001')and not a.output.exists()and time.time()+3600<A.CUT,'fresh explicit output and whole3600 fixed cutoff')
 from owned_substrate import load,REFS
 from owned_create import create
 refs=[sr,*A.readset(m),*REFS.values()];pm,model,o,prod,bridge=A.component_inputs(m)
 # The codec independently verifies every raw/blob Ref. Mount ONLY this actual
 # producer's retained directory RO, never a broad experiment/cache parent.
 rawroot=Path(o['result']['path']).parent;A.need(rawroot.name=='result'and all(Path(r['path']).parent==rawroot for r in prod['actual_mixed_sidecar_records']),'one exact retained raw directory')
 refs +=[o['result'],*bridge['files'].values(),*A.obj(model['plugin_source'])['files'].values()]
 modelrows=A.model_inputs(m);modelroots={str(Path(r['independent']['actual_sidecar_ref']['path']).parent)for r in modelrows}
 A.need(len(modelroots)==4 and all(Path(r).name.startswith('worker-')for r in modelroots),'four precise actual model tensor raw directories')
 refs +=[r['independent']['actual_sidecar_ref']for r in modelrows]
 refs=list({r['path']:r for r in refs}.values());[A.checked(r)for r in refs]
 os.sched_setaffinity(0,{166});soft,hard=resource.getrlimit(resource.RLIMIT_AS);A.need(hard==resource.RLIM_INFINITY,'original Docker child ABI');resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,hard))
 c,S,H,pairs=load(a.output);co=H.Joint(start);a.output.mkdir(mode=0o700);owned=[];primary=None;numeric=None;cleanup=None
 try:
  for role in('cpu-preflight','candidate'):
   leaf=H.fresh_leaf(a.output/role);H.outputs(leaf);ctl=H.controller(S,co)(argparse.Namespace(output_dir=leaf),start);owned.append(ctl);ctl.observe('health-'+role+'-admission',initial=True)
   # Existing source creator is used unchanged. Exact raw read-only directory
   # is inserted as one explicit mount, followed by original inspect validation.
   if role=='candidate':
    import owned_create
    original=ctl.create_owned
    def create_extra(source_hashes):
     ctl.expected['mounts'][str(rawroot)]=(str(rawroot),False)
     for root in modelroots:ctl.expected['mounts'][root]=(root,False)
     return original(source_hashes)
    ctl.create_owned=create_extra
   create(c,S,ctl,sr,refs,role,P)
   if role=='cpu-preflight':
    H.child(ctl,'CPU',[str(P/'cpu_preflight.py'),'--source-ref',json.dumps(sr),'--output',str(leaf/'CPU.json')],120,observe=False)
    cv=c.obj(c.ref(leaf/'CPU.json'));from software_contract import SOFTWARE_CASES
    A.need(cv==dict(schema='deltalog.production-pair-CPU/v122',source=sr,tests=SOFTWARE_CASES,pass_software=True,Devices=[],NPU=False,model=False),'real complete same-source Devices[] software')
   else:
    H.child(ctl,'HEALTH',[str(P/'health_guest122.py'),'--execute','--source-ref',json.dumps(sr),'--output',str(leaf/'NUMERIC.json')],600,observe=True);numeric=A.ref(leaf/'NUMERIC.json')
   cleanup=ctl.cleanup();cleanup=A.original025_ref3(cleanup);ctl._pair_closed=True;z=c.obj(cleanup);A.need(z['stopped']and z['retained']and not z['errors'],'actual release before next role')
 except BaseException as e:primary=repr(e)
 finally:
  for ctl in reversed(owned):
   if ctl.cid and not getattr(ctl,'_pair_closed',False):
    ctl.primary=primary
    try:cleanup=ctl.cleanup();cleanup=A.original025_ref3(cleanup)
    except BaseException as e:co.secondary.append(repr(e))
   co.secondary.extend(ctl.secondary)
  co.secondary.extend(S.formal_time_failures(co.deadline));A.need(co.cleanup_used<=180,'original shared180 cleanup')
  try:[A.checked(r)for r in refs]
  except BaseException as e:co.secondary.append('source-after '+repr(e))
  value=dict(schema='deltalog.production-health-owned/v122',source=sr,numeric=numeric,primary=primary,secondary=co.secondary,cleanup=cleanup,released=primary is None and not co.secondary and all(getattr(x,'_pair_closed',False)for x in owned),NPU=True,qualified=False,elapsed=time.monotonic()-start)
  if primary is None and not co.secondary:
   try:A.health_gate(value,c.obj(numeric),sr,m['production_source_ref'],m['production_qualification_ref'])
   except BaseException as e:primary=repr(e);value.update(primary=primary)
  c.write(a.output/'RESULT.json',value)
 if primary or co.secondary:raise RuntimeError('production health failed, original evidence retained')
 return 0
if __name__=='__main__':raise SystemExit(main())
