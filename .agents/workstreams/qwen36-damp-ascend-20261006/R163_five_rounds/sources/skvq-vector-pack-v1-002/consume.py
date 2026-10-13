"""Original scalar raw-byte oracle + genuine own operation/release consumption."""
import argparse,itertools,json,math,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import common as J
def main():
 start=time.monotonic();p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--source');p.add_argument('--source-sha256');p.add_argument('--result',type=Path);p.add_argument('--result-sha256');p.add_argument('--operation-ref-json',type=Path);p.add_argument('--peer');p.add_argument('--operation');p.add_argument('--cohort',type=Path);p.add_argument('--cohort-sha256');p.add_argument('--run-id');p.add_argument('--physical',type=int);p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print(json.dumps(dict(default_enabled=False,NPU=False)));return 0
 own,m=J.boot(a.source,a.source_sha256);hr=J.ref(a.result);J.need(hr['sha256']==a.result_sha256,'actual complete host result');h=J.obj(hr)
 R=J.load('_vector_consume_cohort',m['cohort_runtime']);binding=R.static_binding(m,own,a,J.checked,J.load);B,A,C=J.contract(m,[own,*m['files'].values(),*m['dependencies']])
 opref=json.loads(a.operation_ref_json.read_bytes());outer=J.obj(opref);rec=B.original(outer,a.peer,a.operation)
 lines=rec['stdout'].splitlines();J.need(len(lines)==1 and lines[0].startswith('MAIN_SKVQ_VECTOR256_R156 ')and json.loads(lines[0][len('MAIN_SKVQ_VECTOR256_R156 '):])==hr and [rec['command'],*rec['args']]==h['actual_host_argv']==R.exact_host_argv(own,binding['ref'],binding['row']),'real exact operation/CLI/result')
 J.need(h['schema']=='skvq.vector256-cohort-host/v1'and h['source']==own and h['cohort']==binding['ref']and h['primary']is None and h['secondary']==[]and h['status']=='RAW_PENDING_INDEPENDENT'and h['physical']==a.physical and(h['phase_seconds'],h['cleanup_seconds'])==(180,60),'complete exact owned chain')
 J.need(type(h['elapsed_seconds'])in(int,float)and math.isfinite(h['elapsed_seconds'])and 0<h['elapsed_seconds']<=180 and 0<=h['cumulative_cleanup_seconds']<=60 and h['admitted_epoch']>=J.START and h['admitted_epoch']+h['elapsed_seconds']<J.CUT,'actual original clock bounds')
 J.need([s['label']for s in h['stages']]==['cpu-preflight','physical-single']and len(h['cleanups'])==2,'actual both stages and cleanup')
 for s in h['stages']:
  v=C.load(s['result']);child=C.load(s['child']);owned=C.load(s['owned'])
  J.need(v['source']==own and v['primary']is None and child['child_termination_observed']is True and child['exit_code']==0 and child['primary_error']is None and child['expected_image_python_argv']==s['argv']==v['actual_argv']and child['requested_argv']==['/usr/bin/docker','exec',owned['cid'],*s['argv']],'genuine complete original subprocess')
  J.checked(child['stdout_ref']);J.checked(child['stderr_ref'])
  if s['label']=='physical-single':
   J.need(s['process_proofs']==child['physical_pid_proofs']and s['process_proofs']and all(q['physical']==a.physical and q['chip']==0 and q['argv']==s['argv']and owned['cid']in q['cgroup']for q in s['process_proofs']),'real physical singleton PID/cgroup');B.validate_process(v,s['process_proofs'],s['argv'])
   rawref=v['raw_ref'];raw=C.load(rawref)
  else:J.need(owned['physical']is None and v['NPU']is False and v['software']==dict(tests=5,affine_CPU_cells=128,exhaustive_integer_words=512,NPU=False,source_inverse_complete=True),'actual CPU128 source semantics')
 for cr in h['cleanups']:
  cl=C.load(cr);J.need(cl['stopped']is cl['retained']is True and cl['errors']==[],'real exact stopped-retained cleanup');J.checked(cl['after_inspect']);J.checked(cl['release_smi'])
 J.need(raw['source_ref']==own and raw['stage']==m['stage']and raw['status']=='WRITER_COMPONENT_RAW_AND_SELF_CHECK_COMPLETE'and raw['primary']is None and raw['actual_capture_mode']=='GLOBAL'and raw['native_model']is raw['FULL47_ready']is False,'new actual component raw only')
 oracle={};exec(compile(J.checked(m['oracle']),m['oracle']['path'],'exec',dont_inherit=True),oracle);seen=set();guards=set();parent=Path(rawref['path']).parent
 for r in raw['results']:
  if r['phase']=='GLOBAL-full-launch-guards':
   key=(r['kind'],r['bits'],r['batch']);J.need(key not in guards and r['error']==1 and r['sticky']is True,'unique whole-pool sticky observation');guards.add(key);continue
  key=(r['kind'],r['bits'],r['batch'],r['phase'],r['axis']);J.need(key not in seen,'unique raw cell');seen.add(key);data={}
  for n,x in r['raw'].items():J.need(parent in Path(x['path']).parents,'bounded own raw');data[n]=J.checked(x)
  expected=oracle['encode_scalar'](data.pop('input'),r['layout'],r['bits'],r['kind']);J.need(data==expected,'independent original every payload/scale/zero byte')
 expected=set(itertools.product(('float16','bfloat16'),(2,4),range(1,17),('eager','GLOBAL'),('K','V')))
 J.need(seen==expected and guards==(set(itertools.product(('float16','bfloat16'),(2,4),range(1,17)))if m['stage']=='full-launch'else set()),'all256 original raw cells/required64 guards')
 J.need(time.monotonic()-start<120 and time.time()<J.CUT and not {'torch','torch_npu','triton'}.intersection(sys.modules),'bounded independent CPU no candidate')
 rr=J.publish(a.output,dict(schema='skvq.vector256-independent-component/v1',source=own,host_ref=hr,operation_ref=opref,cohort=binding['ref'],actual_all256_byte_cells=True,actual64_guard_observations=m['stage']=='full-launch',actual_capture_mode='GLOBAL',model_ready=False,performance_ready=False,task_ready=False,component_only=True));print(json.dumps(rr));return 0
if __name__=='__main__':raise SystemExit(main())
