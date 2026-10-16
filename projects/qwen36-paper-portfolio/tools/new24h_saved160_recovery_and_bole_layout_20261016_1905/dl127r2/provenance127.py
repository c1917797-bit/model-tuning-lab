"""Only the actual completed-NPU / original consumer TimeoutExpired category."""
import ast,json,re
TIMEOUT=585.6111058300012
PRIMARY="independent consumer ValueError('actual GE child failed; preserved logs/raw')"
IMAGE='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'
def need(x,m):
 if not x:raise ValueError(m)
def arm(a,dv,handshake,plan_ref,plan,producer,source,cid):
 need(a['physical']==5 and a['pid']>0 and a['start_ticks']>0 and cid in a['cgroup'],'original actual ARM process/physical5/source proof')
 need(dv['logical']==0 and dv['physical']==5 and dv['visible']=='0'and dv['canary']==[4.,5.]and dv['plan']==plan_ref==producer['plan']and cid in dv['cgroup'],'original actual DEVICE/canary/PLAN identity')
 ticks=int(dv['stat'][dv['stat'].rfind(')')+2:].split()[19])
 need(a['namespace_pids'][-1]==dv['pid']and a['start_ticks']==ticks and handshake==dict(schema='deltalog.fresh-bridge-arm/v2',pid=dv['pid'],plan_sha256=plan_ref['sha256'],physical=5),'original actual host/guest PID/start and ARM handshake')
 need(plan['schema']=='deltalog.fresh-bridge-plan/v2'and plan['source']==producer['source']and plan['authority']==producer['authority']and plan['lifecycle']==producer['lifecycle']and plan['steps']==160 and plan['physical']==5 and plan['logical']==0 and plan['graph']is False and plan['phase_seconds']==1800 and plan['cleanup_seconds']==90,'original exact numeric plan')
 argv=a['argv'];need(len(argv)==21 and argv[:7]==['/usr/local/python3.12.13/bin/python3','-I','-B',source['files']['entry.py']['path'],'--execute','--stage','numeric'],'actual original host entry (not producer.py) argv')
 need(argv[7::2]==['--source-ref','--authority-ref','--lifecycle-ref','--steps','--output','--plan-ref','--cpu-preflight-ref'],'all original host arguments/order')
 need(json.loads(argv[8])==producer['source']and json.loads(argv[10])==producer['authority']and json.loads(argv[12])==producer['lifecycle']and argv[14]=='160'and argv[16]==plan['output']and json.loads(argv[18])==plan_ref and json.loads(argv[20])==plan['cpu_preflight'],'actual entry source/authority/lifecycle/160/output/PLAN/CPUrefs')
 return True
def validate(e,read):
 need(e['schema']=='deltalog.actual160-consumer-fault-readonly-evidence/v1','actual fault schema')
 r=e['refs'];v={k:read(ref)for k,ref in r.items()if k not in ('source','producer')}
 for k,document in e['small_documents'].items():need(v[k]==document,'exact re-opened fault document '+k)
 o=v['owner'];p=read(r['producer']);s=read(r['source']);strict=v['strict']
 need(o['schema']=='deltalog.diagnostic-owned-host/v035'and o['source']==o['target_source']==r['source']and o['result']==r['producer']and o['primary']==PRIMARY and o['secondary']==[]and o['stopped_retained']is o['resource_admitted']is o['NPU']is True and o['steps']==160 and o['physical']==[5]and o['independent_consumer']is None,'original failed owner retained, not numeric FAIL or success')
 need(p['source']==r['source']and p['primary']is None and p['steps']==160 and p['NPU']is True and p['graph']is False,'complete actual original160 producer')
 need(len(p['records'])==328 and len(p['actual_sidecar_records'])==351 and len({x['raw']['path']for x in p['records']})==328 and len({x['path']for x in p['actual_sidecar_records']})==351,'exact681 unique main/sidecar refs')
 need(strict['source']==r['source']and strict['producer']==r['producer']and strict['pass_gate']is False and strict['primary']=="ValueError('independent raw numerical/bitwise gate')",'original strict FAIL preserved')
 child=v['first_child'];need(child['returncode']==0 and child['stderr']==child['stdout']=='','original strict completed normally')
 argv=child['argv'];need(argv[1:4]==['-I','-B',s['files']['raw_reader_entry.py']['path']]and argv[4:7]==['--script','consume.py','--execute'],'actual original strict command')
 def arg(name):return argv[argv.index(name)+1]
 need(json.loads(arg('--source-ref'))==r['source']and json.loads(arg('--producer-ref'))==r['producer']and arg('--output')==r['strict']['path'],'exact strict input/output identities')
 log=v['logs'];need(log['exit_code']==0 and log['stdout']=='','actual logs read successful')
 lines=[line.split(' subprocess.TimeoutExpired: ',1)[1]for line in log['stderr'].splitlines()if ' subprocess.TimeoutExpired: 'in line]
 need(len(lines)==1,'one exact original TimeoutExpired')
 match=re.fullmatch(r"Command '(.*)' timed out after ([0-9.]+) seconds",lines[0]);need(match is not None,'exact TimeoutExpired syntax')
 actual=ast.literal_eval(match[1]);expected=list(argv);expected[expected.index('--script')+1]='run_consumer088.py';expected[expected.index('--output')+1]=r['strict']['path'].rsplit('/',1)[0]+'/DOMAIN088.json'
 need(actual==expected and float(match[2])==TIMEOUT and 0<TIMEOUT<590,'only original shared590 domain timeout, no budget expansion')
 for kind,key,exitcode in [('numeric','numeric_cleanup',0),('consumer','consumer_cleanup',1)]:
  ip=e['inspect'][kind];x=read(ip['ref']);need(x==ip['projection'],'actual inspect projection exact')
  state=x['state'];cl=v[key]
  need(x['schema']=='deltalog.actual-quiescent-container-inspection/v1'and x['image']==IMAGE and x['source_sha256']==r['source']['sha256']and x['id']==cl['cid'],'actual original source/CID/image')
  need(state['Status']=='exited'and state['Running']is state['Paused']is state['Restarting']is state['OOMKilled']is state['Dead']is False and state['Pid']==0 and state['ExitCode']==exitcode and state['Error']==''and x['ExecIDs']is None,'original numeric0 / CPUtimeout1 stopped without OOM/exec')
  need(cl['stopped']is cl['retained']is cl['resource_release_verified']is True and cl['errors']==cl['secondary_guard_cleanup']==[]and cl['unresolved_active_cid']is None and cl['rm_authorized']is False,'both original exact release proofs')
  if kind=='consumer':need(x['devices']==[],'original consumer Devices[]')
  else:need({(z['PathOnHost'],z['PathInContainer'])for z in x['devices']}=={('/dev/davinci5','/dev/davinci0'),('/dev/davinci_manager','/dev/davinci_manager'),('/dev/devmm_svm','/dev/devmm_svm'),('/dev/hisi_hdc','/dev/hisi_hdc')},'original physical5 -> logical0 only')
 return s,p
