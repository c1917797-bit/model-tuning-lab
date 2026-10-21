"""Finite 120+60+120 software allocation inside the original3600/cleanup180.

Every completed or failed subprocess retains whole stdout/stderr and a terminal.
The allocation is prospective, not a guarantee that installed imports finish.
"""
import json,math,os,signal,subprocess,sys,time
from pathlib import Path
import sourceio as C

CAPS=dict(parent279=120.,controls=60.,metadata=120.)
LANE_CAP=300.
PHASE=3600.
CLEANUP=180.


def finite(x):return type(x)in(int,float)and math.isfinite(x)


def one(data,schema):
 def pairs(rows):
  out={}
  for k,v in rows:C.need(k not in out,'unique software JSON keys');out[k]=v
  return out
 found=[]
 for line in data.splitlines():
  try:v=json.loads(line,object_pairs_hook=pairs,parse_constant=lambda s:(_ for _ in()).throw(ValueError(s)))
  except(UnicodeDecodeError,ValueError):continue
  if type(v)is dict and v.get('schema')==schema:found.append(v)
 C.need(len(found)==1,'one exact schema result in retained complete software stdout')
 return found[0]


class Budget:
 def __init__(self,phase_entry,lane_start,lane_deadline,cutoff,guest_entry):
  now=time.monotonic();wall=time.time()
  C.need(all(finite(x)for x in(phase_entry,lane_start,lane_deadline,guest_entry,cutoff))and phase_entry<=lane_start<=guest_entry<=now and lane_start<lane_deadline<=lane_start+LANE_CAP and lane_deadline<=phase_entry+PHASE-CLEANUP,'actual host firstentry and one finite software lane; no deadline renewal')
  C.need(cutoff==1792597630 and lane_deadline-now<=cutoff-wall-CLEANUP+0.01,'same unchanged absolute cutoff and cleanup reserve')
  self.phase_entry=phase_entry;self.start=lane_start;self.deadline=lane_deadline;self.cutoff=cutoff;self.excluded=0.
 def remaining(self,kind):
  now=time.monotonic();common=min(self.deadline-now,self.phase_entry+PHASE-CLEANUP-now,self.cutoff-time.time()-CLEANUP)
  control=CAPS['controls']-(now-self.start-self.excluded)
  value=min(common,control if kind=='controls'else CAPS[kind]);C.need(value>0,'original phase/lane/stage budget exhausted; never retry/renew');return value
 def exclude(self,elapsed):
  C.need(finite(elapsed)and elapsed>=0,'actual excluded child elapsed only');self.excluded+=elapsed
 def check(self):self.remaining('controls')


def process(root,label,argv,limit,*,source,env=None):
 C.need(finite(limit)and 0<limit<=120 and type(argv)is list and all(type(x)is str for x in argv),'one bounded exact process argv')
 root=Path(root);root.mkdir();so=root/'STDOUT.raw';se=root/'STDERR.raw';start=time.monotonic();pid=None;code=None;timed=False;fault=None
 try:
  with so.open('xb')as out,se.open('xb')as err:
   child=subprocess.Popen(argv,stdout=out,stderr=err,env=env,start_new_session=True);pid=child.pid
   try:code=child.wait(timeout=limit)
   except subprocess.TimeoutExpired:
    timed=True;os.killpg(child.pid,signal.SIGKILL);code=child.wait(timeout=10)
   finally:out.flush();os.fsync(out.fileno());err.flush();os.fsync(err.fileno())
 except BaseException as error:fault=repr(error)
 elapsed=time.monotonic()-start
 terminal=C.write(root/'TERMINAL.json',dict(schema='bole.actual-software-stage-terminal/v11',source=source,label=label,actual_argv=argv,child_pid=pid,start_monotonic=start,end_monotonic=start+elapsed,elapsed_seconds=elapsed,allocated_seconds=limit,returncode=code,timed_out=timed,primary=fault,stdout=C.ref(so),stderr=C.ref(se),complete_streams_retained=True,cached_PASS_reused=False))
 C.need(fault is None and code==0 and not timed and elapsed<=limit,'actual software stage failed or exceeded allocation; complete terminal/raw retained, never retry')
 C.need(so.stat().st_size+se.stat().st_size<=32*2**20,'bounded whole software streams, never truncate')
 return dict(terminal=terminal,stdout=C.ref(so),stderr=C.ref(se)),elapsed


def metadata_gate(v,sr):
 C.need(v['schema']=='bole.service-installed-class-protocol-devicefree/v1'and v['source']==sr and v['NPU']is False and v['actual_model_constructed']is False and v['actual_batch_constructed']is False and v['actual_scheduler_executed']is False and v['actual_torch_context_class_checked']is True and len(v['classes'])==len(v['complete_native_sources_compiled'])==6 and all(r['full_source_compiled']is True and r['import_executed']is False for r in v['complete_native_sources_compiled']),'all unchanged original installed metadata assertions must actually finish')


def scope(m,sr):
 from g2_ack_proof import SOURCE
 s=m['service_software_scope']
 C.need(s['schema']=='bole.G2-four-source-ACK-staged-software-scope/v12'and
  s['parent_exact_cases']==279 and s['controls_source_cases']==25 and s['historical_stage_cases']==18 and
  s['historical_stage_source']==SOURCE==m['g2_ack_serialization_v12']['parent_source']and
  s['parent_source']==m['g2_cold_clock_v9']['parent_source']and s['controls_source']==m['g2_software_phases_v11']['parent_source']and
  s['allocation_seconds']==CAPS and s['aggregate_cap_seconds']==LANE_CAP and
  s['parent_suite_runs_in_separate_exact_source_process']is True and s['controls_run_only_tests_in_exact_source_process']is True and
  s['current_pattern']=='test_g2_ack*.py'and type(s['new_current_cases'])is int and s['new_current_cases']>0 and
  m['service_required_sameimage_software_cases']==322+s['new_current_cases'],
  'source8 fresh279/source10 fresh25/source11 fresh18/current12 ACK controls, no old whole-software replay or output alias')
 return s


def run(sr,*,phase_entry,lane_start,lane_deadline,guest_entry):
 b=Budget(phase_entry,lane_start,lane_deadline,1792597630,guest_entry)
 m=C.obj(sr);s=scope(m,sr);P=Path(m['root']);C.need(C.ref(__file__)==m['files']['g2_software_stages.py'],'source-bound coordinator')
 from g2_validate import validate
 proof=validate(sr);b.check()
 options=[Path(m['output_root'])/'cpu-preflight',Path(m['output_root']+'-CPU')/'cpu-preflight'];matches=[p for p in options if p.is_dir()and p.samefile('/adakv-results')]
 C.need(len(matches)==1,'one actual preexisting owned RW output, no source writes');actual=matches[0];root=actual/'G2-V12-SOFTWARE';root.mkdir()
 admission=C.write(root/'ADMISSION.json',dict(schema='bole.actual-four-source-software-admission/v12',source=sr,phase_entry=phase_entry,lane_start=lane_start,lane_deadline=lane_deadline,guest_entry=guest_entry,allocation_seconds=CAPS,aggregate_cap_seconds=LANE_CAP,validation_elapsed_before_parent=time.monotonic()-lane_start,original_phase_seconds=PHASE,original_cleanup_seconds=CLEANUP,fixed_cutoff=1792597630))
 parent=C.obj(s['parent_source']);entry=C.checked(parent['files']['service_entry.py']);C.need(entry==Path(parent['root'])/'service_entry.py','exact original parent entry')
 env={k:v for k,v in os.environ.items()if not k.startswith('BOLE_')}
 ev,elapsed=process(root/'PARENT279','parent279',[sys.executable,'-I','-B',str(entry),'--software'],b.remaining('parent279'),source=sr,env=env);b.exclude(elapsed)
 from g2_cold_parent_output import extract,alias_exports
 prior=extract(C.checked(ev['stdout']).read_bytes(),s['parent_source'],parent);exports=alias_exports(prior['parent_software_evidence'],Path(parent['output_root'])/'cpu-preflight',actual)
 extraction=C.write(root/'PARENT279/EXTRACTION.json',dict(schema='bole.actual-three-source-parent-extraction/v11',source=sr,parent_source=s['parent_source'],stage=ev,original_summary=prior,original_guest_evidence_to_actual_host_refs=exports,original_source_owned_extract_used=True,original_G1_and_G2_controls_really_rerun=True,NPU=False));b.check()
 controls={}
 for role,count,test_source in(('source10',25,s['controls_source']),('source11',18,s['historical_stage_source']),('current12',s['new_current_cases'],sr)):
  row,cost=process(root/role,role,[sys.executable,'-I','-B',str(C.checked(m['files']['g2_exact_controls.py'])),'--execute','--source-ref',json.dumps(sr),'--role',role],b.remaining('controls'),source=sr)
  value=one(C.checked(row['stdout']).read_bytes(),'bole.actual-exact-source-only-unittest/v12')
  C.need(value==dict(schema='bole.actual-exact-source-only-unittest/v12',source=sr,test_source=test_source,role=role,pattern={'source10':'test_g2_cold*.py','source11':'test_g2_stage*.py','current12':'test_g2_ack*.py'}[role],tests=count,all_tests_passed=True,skipped=0,cached_PASS_reused=False,original_software_entry_invoked=False,NPU=False),'exact actual source/count/zeroSkip only-tests receipt')
  controls[role]=dict(stage=row,result=value);b.check()
 metadata_path=root/'METADATA.json'
 meta,cost=process(root/'METADATA','metadata',[sys.executable,'-B',str(C.checked(m['files']['service_metadata.py'])),'--execute','--source-ref',json.dumps(sr),'--output',str(metadata_path)],b.remaining('metadata'),source=sr);b.exclude(cost)
 installed=C.obj(C.ref(metadata_path));metadata_gate(installed,sr);C.need(one(C.checked(meta['stdout']).read_bytes(),installed['schema'])==installed,'completed original metadata CLI output and actual retained file agree');b.check()
 value=dict(schema='bole.actual-G2-four-source-staged-software-gate/v12',source=sr,tests=m['service_required_sameimage_software_cases'],source8_fresh_cases=279,source10_fresh_cases=25,source11_fresh_cases=18,current12_fresh_cases=s['new_current_cases'],all_tests_passed=True,admission=admission,parent_source=s['parent_source'],parent_software_result=prior,parent_software_evidence=dict(stage=ev,extraction=extraction),controls=controls,actual_installed_metadata=installed,actual_installed_metadata_ref=C.ref(metadata_path),metadata_stage=meta,source_validated=proof,phase_entry=phase_entry,lane_start=lane_start,lane_deadline=lane_deadline,elapsed_seconds=time.monotonic()-lane_start,controls_total_elapsed_seconds=time.monotonic()-lane_start-b.excluded,allocation_seconds=CAPS,aggregate_cap_seconds=LANE_CAP,NPU=False,actual_scheduler_executed=False,model_ready=False,timing_is_formal=False)
 C.write(root/'RESULT.json',value);b.check();C.need(time.monotonic()<=lane_deadline,'final software export remains inside same admitted lane');return value


def host_run(C,c,H,ctl,sr,entry_start):
 C.need(C.ref(__file__)==C.obj(sr)['files']['g2_software_stages.py']and ctl.deadline==entry_start+PHASE and ctl.created_monotonic==entry_start,'actual original host firstentry/controller/software helper')
 now=time.monotonic();available=min(LANE_CAP,ctl.remaining(cap=LANE_CAP));C.need(finite(available)and available>0,'same remaining original phase admits finite software lane')
 deadline=now+available;C.need(deadline<=entry_start+PHASE-CLEANUP+0.01,'no renewed software phase')
 args=[str(Path(__file__).with_name('service_entry.py')),'--software','--phase-entry',repr(entry_start),'--lane-start',repr(now),'--lane-deadline',repr(deadline)]
 C.write(ctl.out/'SOFTWARE-ADMISSION.json',dict(schema='bole.actual-host-software-allocation/v11',source=sr,phase_entry=entry_start,lane_start=now,lane_deadline=deadline,allocated_seconds=available,allocation_seconds=CAPS,aggregate_cap_seconds=LANE_CAP,requested_args=args,original_phase_seconds=PHASE,original_cleanup_seconds=CLEANUP))
 result=H.child(ctl,'SOFTWARE',args,min(deadline-time.monotonic(),ctl.remaining(cap=LANE_CAP)),observe=False)
 raw=C.checked(C.ref(ctl.out/'SOFTWARE.stdout')).read_bytes();value=one(raw,'bole.actual-G2-four-source-staged-software-gate/v12')
 C.need(value['source']==sr and value['phase_entry']==entry_start and value['lane_start']==now and value['lane_deadline']==deadline and value['all_tests_passed']is True and value['tests']==C.obj(sr)['service_required_sameimage_software_cases']and value['allocation_seconds']==CAPS and value['aggregate_cap_seconds']==LANE_CAP and 0<=value['controls_total_elapsed_seconds']<=CAPS['controls']and 0<=value['elapsed_seconds']<=deadline-now,'actual source-owned complete stage result, never subprocess exit alone')
 return result
