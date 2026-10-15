"""Thin validation guest over genuine025 Controller/Joint; no new controller."""
import argparse,json,os,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
def main():
 if '--execute'not in sys.argv:print('disabled');return 0
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref',required=True);a=p.parse_args()
 from screen_admission import source,checked
 from owned_substrate import load,REFS
 from owned_create import create
 sr=json.loads(a.source_ref);m=source(sr);c,S,H,pairs=load();started=time.monotonic()
 if time.time()+3600>1792135097:raise ValueError('full existing owner budget must fit fixed cutoff')
 os.sched_setaffinity(0,{166});out=Path(m['validation_output_root'])
 if out.parent!=c.PREP/'lowbit' or not out.name.startswith('run-dl-production-validation-PF037R5-')or out.exists():raise ValueError('exclusive PF037R5 production validation output, not savedraw033')
 plan=c.obj(m['validation_inputs_ref']);prod=c.obj(plan['producer_ref'])
 refs=[sr,*m['files'].values(),*m['dependencies'],*REFS.values(),m['validation_inputs_ref'],plan['producer_ref'],plan['source031_ref'],plan['diagnostic_primitives_ref'],plan['oracle_ref']]
 refs.extend(row['raw']for row in prod['records']if row['kind']=='mixed')
 old_source=c.obj(m['diagnostic_predecessor_ref']);refs.extend(old_source['files'].values());refs.append(m['diagnostic_predecessor_ref'])
 unique={r['path']:r for r in refs}
 for r in unique.values():checked(r)
 out.mkdir(mode=0o700);co=H.Joint(started);leaf=H.fresh_leaf(out/'numeric');H.outputs(leaf)
 ctl=H.controller(S,co)(argparse.Namespace(output_dir=leaf),started);primary=None;numeric=None;cleanup=None
 try:
  ctl.observe('production-validation-admission',initial=True);create(c,S,ctl,sr,list(unique.values()),'candidate',P)
  H.child(ctl,'PRODUCTION_NUMERIC',[str(P/'production_numeric.py'),'--execute','--source-ref',json.dumps(sr),'--output',str(leaf/'NUMERIC.json')],600,observe=True)
  numeric=c.ref(leaf/'NUMERIC.json');v=c.obj(numeric)
  if not(v['source']==sr and v['finite_domain_equal']and v['invalid_live_whole_arm_rejected']):raise ValueError('actual production numeric policy failed')
 except BaseException as error:primary=repr(error)
 finally:
  try:cleanup=ctl.cleanup()
  except BaseException as error:co.secondary.append(repr(error))
  co.secondary.extend(ctl.secondary)
  value=dict(schema='deltalog.production-validation-owned/v033',source=sr,numeric=numeric,primary=primary,secondary=co.secondary,cleanup=cleanup,stopped_retained=cleanup is not None and c.obj(cleanup)['stopped']and c.obj(cleanup)['retained']and not c.obj(cleanup)['errors'],elapsed=time.monotonic()-started,actual_host_argv=[x.decode()for x in Path('/proc/self/cmdline').read_bytes().split(b'\0')if x])
  rr=c.write(out/'RESULT.json',value);print('MAIN_DL_PRODUCTION_VALIDATION '+json.dumps(rr),flush=True)
 if primary or co.secondary:raise RuntimeError('production validation failed; original evidence retained')
 return 0
if __name__=='__main__':raise SystemExit(main())
