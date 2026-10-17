"""R17 saved math only: real snapshots retained; live frontend proof missing."""
import ast,importlib,json,sys
from pathlib import Path
SOURCE=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/bole-model-three-node-entry-new24h-v1-131-repair17/SOURCE_BOUND.json',bytes=59418,sha256='1a6a1e1b6be6afa5ca91bd2909bcdc5fe3a821b4968b5cf04f9e2b2752977552')
OWNER=dict(path='/opt/host/vnf/austinov/run-bole-model131repair17-MAIN-NEW24H_001/RESULT.json',bytes=106940,sha256='d74973577c0df392768cc30b2a002aa3378c4f79948888e101316ab84109fada')
ROOT=Path(OWNER['path']).parent

def first_fault_ref(C,r):
 C.need(type(r)is dict and set(r)=={'path','bytes'}and type(r['bytes'])is int and r['bytes']>=0 and r['path']==str(ROOT/'HOST-FIRST-FAULT.json'),'exact original owner-local first-fault path/bytes receipt')
 full=C.ref(r['path']);C.need(full['bytes']==r['bytes'],'original first-fault recorded bytes unchanged');C.checked(full)
 return full

def ref2(C,r):
 C.need(type(r)is dict and set(r)=={'path','sha256'}and Path(r['path']).is_relative_to(ROOT),'exact original owner-local Ref2')
 full=C.ref(r['path']);C.need(full['sha256']==r['sha256'],'stable original Ref2→3 bytes/hash');C.checked(full);return full

def parent_modules(C):
 m=C.obj(SOURCE)
 C.need(m['root']==str(Path(SOURCE['path']).parent)and m['prepared_only']is False,'exact actual R17 bound source')
 for r in m['files'].values():C.checked(r)
 old=list(sys.path);sys.path.insert(0,m['root'])
 try:
  modules={name:importlib.import_module(name)for name in('consume_model','model_calibration131r12','independent_model','oracle112','identity_oracle','load_consumer114')}
  for name,mod in modules.items():C.need(C.ref(mod.__file__)==m['files'][name+'.py'],'actual exact original math reader '+name)
  for name in('sourceio','model_entry','registration_audit131r11','calibrate_conv118'):
   mod=importlib.import_module(name);C.need(C.ref(mod.__file__)==m['files'][name+'.py'],'actual exact transitive math reader '+name)
 finally:sys.path[:]=old
 return m,modules

def terminal(C,r):
 v=C.obj(r);C.need(v['schema']=='agentweb.operation/v1','actual unmodified R17 terminal operation envelope')
 C.need(v['operationId']=='exec-000000000000127e'and v['found']is v['terminal']is True and v['status']=='completed'and v['kind']=='exec'and v['succeeded']is False,'exact actual R17 failed terminal, not success/not_found')
 record=v['operation']['result']['record'];C.need(record['id']==v['operationId']and record['state']=='completed'and record['exitCode']==3 and record['timedOut']is record['cancelled']is False,'original failed owner exit3, not numerical success')
 argv=record['args'];C.need(record['command']=='/usr/bin/env'and len(argv)==11 and argv[:6]==['BOLE_MODEL131_MAIN_ENABLE=1','DENSE090_EXTERNAL_OUTPUT_ENABLE=1','/usr/bin/python3','-I','-B',(Path(SOURCE['path']).parent/'host090.py').as_posix()]and argv[6:] == ['--execute','--source-ref',argv[8],'--output',ROOT.as_posix()]and json.loads(argv[8])==SOURCE,'actual terminal complete original source/output argv')
 published=[json.loads(x[len('MAIN_DENSE090 '):])for x in record['stdout'].splitlines()if x.startswith('MAIN_DENSE090 ')]
 C.need(dict(path=OWNER['path'],sha256=OWNER['sha256'])in published,'actual terminal publishes exact failed owner')
 return v

def snapshots(C,m,bindings_ref,receiptroot):
 """Reopen actual durable snapshots; never manufacture a live frontend join."""
 bindings=C.obj(bindings_ref);C.need(type(bindings)is list and len(bindings)==4,'actual four original worker bindings')
 pin_tree=ast.parse(C.checked(m['files']['native_receipt090.py']).read_bytes())
 pins=[ast.literal_eval(n.value)for n in pin_tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='PINS'for t in n.targets)]
 C.need(len(pins)==1 and len(pins[0])==4,'exact original native receipt module pins')
 paths=sorted(receiptroot.glob('worker-*-snapshot-*.json'));C.need(len(paths)==4,'exact four real durable original snapshots, no replacement')
 refs=[];values=[]
 for path in paths:
  r=C.ref(path);v=C.obj(r)
  C.need(v['schema']=='dense.native-worker-snapshot/v090'and v['source_ref']==SOURCE and v['native_core']is v['native_inverse']is True and v['allow_hf32']is v['tensor_capture']is v['qualification']is False,'actual native snapshot source/core/inverse/HF32OFF, never qualification')
  C.need(type(v['ordinal'])is int and v['ordinal']>0 and path.name=='worker-%d-snapshot-%d.json'%(v['pid'],v['ordinal']),'actual PID/ordinal snapshot filename')
  C.need(set(v['framework_sources'])==set(pins[0])and all(v['framework_sources'][k]['sha256']==sha for k,sha in pins[0].items()),'original exact native module receipt identities')
  matches=[b for b in bindings if b['guest']==v];C.need(len(matches)==1,'actual saved worker binding embeds this exact snapshot')
  refs.append(r);values.append(v)
 C.need(len({v['pid']for v in values})==4 and {b['host']['physical']for b in bindings}=={4,5,6,7}and len({b['host']['pid']for b in bindings})==4,'four original independent physical worker lifetimes')
 return bindings,refs,values

def inspect_release(C,cleanup_ref,cid):
 v=C.obj(cleanup_ref);C.need(v['stopped']is v['retained']is True and v['container']==cid and v['errors']==[],'original stopped-retained exact CID')
 ir=ref2(C,v['after_inspect']);raw=C.obj(ir);C.need(raw['exit_code']==0,'actual original Docker inspect exit0')
 rows=json.loads(raw['stdout']);C.need(len(rows)==1,'one complete actual inspect');x=rows[0];s=x['State']
 C.need(x['Id']==cid and s['Running']is False and s['Pid']==0 and not x.get('ExecIDs')and s['OOMKilled']is False,'actual stopped/Pid0/noExec/noOOM')
 return ir

def bind(C,terminal_ref):
 terminal(C,terminal_ref);o=C.obj(OWNER);m,mods=parent_modules(C)
 C.need(o['schema']=='bole.actual-three-node-model-owned/v131'and o['source']==SOURCE and o['primary']=="FileNotFoundError(2, 'No such file or directory')"and o['secondary']==[]and o['source_before']==o['source_after']and o['source_before'],'exact original R17 namespace failure and immutable source fences')
 C.need(all(o['source_before'].get(r['path'])==r['sha256']for r in m['files'].values()),'all actual bound original source files present in both source fences')
 C.need(o['model_ready']is o['scheduler_committed']is o['cpu_only']is False and 0<o['elapsed']<=3600 and o['cleanup_spent']<=180,'old diagnostic failure budget/scope retained')
 argv=o['actual_host_argv'];C.need(argv[1:4]==['-I','-B',m['files']['host090.py']['path']]and json.loads(argv[argv.index('--source-ref')+1])==SOURCE,'original actual host source argv')
 refs=[SOURCE,OWNER,terminal_ref,m['prepared_template'],m['authority_ref'],*m['files'].values(),*m['dependencies']]
 fault_ref=first_fault_ref(C,o['summary']['first_host_fault']);fault=C.obj(fault_ref);C.need(fault['source']==SOURCE and fault['error_repr']==o['primary']and fault['phase']['step']=='frontend-identity'and fault['errno']==2 and fault['filename']=='/usr/local/python3.12.13','precise original frontend namespace fault, not a math/snapshot fault');refs.append(fault_ref)
 C.need('frontend_binding'not in o['summary']and 'independent'not in o['summary']and not(ROOT/'CONSUMER_INPUTS.json').exists(),'original live frontend/independent proof absent and not reconstructed')
 actual_client=o['summary']['actual_client_terminal'];cv=C.obj(actual_client);C.need(cv['exit_code']==0,'actual HTTP client0');refs.extend([actual_client,cv['stdout'],cv['stderr']])
 http=C.ref(ROOT/'dense/HTTP_RESULT.json');hv=C.obj(http);C.need(hv['source']==SOURCE and [r['label']for r in hv['rows']]==['tree','retirement-barrier'],'actual two original HTTP requests');refs.append(http)
 for row in hv['rows']:
  C.need(row['http_status']==200,'actual HTTP200');C.checked(row['response']);refs.append(row['response'])
 receiptroot=ROOT/'dense/receipts';bindings_ref=o['summary']['worker_bindings'];C.need(bindings_ref['path']==str(ROOT/'dense/WORKER_BINDINGS.json'),'exact original durable worker bindings path')
 bindings,snapshot_refs,snapshot_values=snapshots(C,m,bindings_ref,receiptroot);refs.extend([bindings_ref,*snapshot_refs])
 cpu_ref=o['summary']['CPU_report'];cpu=C.obj(cpu_ref);C.need(cpu['source']==SOURCE and cpu['pass_preflight']is True and cpu['Devices']==[],'actual original sameimage CPU preflight/source before model')
 load_refs=o['summary']['MTP_load_receipts'];load_rows=[C.obj(r)for r in load_refs]
 loaded=mods['load_consumer114'].consume(load_rows,cpu['actual_checkpoint_mtp_names'],m['installed_sources']['qwen_mtp'],m['files']['load_receipt111.py'])
 C.need(loaded==C.obj(o['summary']['MTP_load'])and {v['pid']for v in snapshot_values}=={v['pid']for v in load_rows},'original independent load reader result and native snapshot worker lifetime join')
 refs.extend([cpu_ref,o['summary']['MTP_load'],*load_refs])
 journals=[C.ref(p)for p in sorted(receiptroot.glob('IDENTITY-*.json'))];C.need(journals,'actual retained identity journal, no invented worker events')
 for r in journals:C.need(C.obj(r)['source']==SOURCE,'journal actual source');refs.append(r)
 ranks=[];signals=[];cids=set()
 oldabi=C.obj(m['actual118c']['capture'])['actual_device_abi_ref'];refs.extend([*m['actual118c'].values(),oldabi])
 for rank in range(4):
  rr=C.ref(receiptroot/('BOLE-TREE-RANK-%d.json'%rank));v=C.obj(rr)
  C.need(v['source']==SOURCE and v['rank']==rank and v['primary']is None and Path(v['raw']['path'])==receiptroot/('BOLE-TREE-RANK-%d.pt'%rank),'actual complete same-source rank capture')
  matches=[]
  for path in sorted(receiptroot.glob('SIGNAL-AFTER-MODEL-host*.json')):
   sr=C.ref(path);sig=C.obj(sr);p=sig['actual_process'];ns=p['namespace_pids']
   if ns and ns[-1]==v['pid']:matches.append((sr,sig))
  C.need(len(matches)==1,'actual signal observation/NSpid matches original capture guestPID');signal_ref,sig=matches[0];p=sig['actual_process'];cid=sig['owned_cid'];cids.add(cid)
  rest=v['stat'][v['stat'].rfind(')')+2:].split();C.need(sig['signal']=='SIGUSR1'and sig['outside_timed_client']is True and p['physical']==4+rank and p['start_ticks']==int(rest[19])and p['cgroup']==v['cgroup']and cid in v['cgroup'],'exact original host→guest PID/start/cgroup/rank binding')
  bound=[b for b in bindings if b['host']==p and b['guest']['pid']==v['pid']];C.need(len(bound)==1,'real snapshot/binding/signal same actual host worker object data')
  sv=bound[0]['guest'];sf=sv['proc_stat'][sv['proc_stat'].rfind(')')+2:].split();C.need(int(sf[19])==int(rest[19])and sf[0]not in('Z','X')and sv['cgroup']==v['cgroup'],'same original snapshot and rank PID/start/cgroup')
  refs.extend([rr,v['raw'],v['model_calibration_ref'],signal_ref,ref2(C,sig['observation']),ref2(C,p['raw_observation']),ref2(C,p['smi'])]);signals.append(signal_ref)
  cal=mods['model_calibration131r12'].validate(C,v['model_calibration_ref'],oldabi,SOURCE,rank);refs.extend([*cal['rows'],*cal['before']]);ranks.append(dict(receipt=rr,raw=v['raw'],calibration=v['model_calibration_ref'],signal=signal_ref))
 C.need(len(cids)==1,'all4 original ranks in one actual CID');cid=next(iter(cids))
 release=[]
 for role in('cpu-preflight','dense'):
  cr=C.ref(ROOT/role/'cleanup.json');c=C.obj(cr);C.need(role!='dense'or c['container']==cid,'rank CID is actual dense owned CID');ir=inspect_release(C,cr,c['container']);refs.extend([cr,ir]);release.append(cr)
 refs.extend(o['summary'].get('MTP_load_receipts',[]))
 for r in refs:C.checked(r)
 unique={}
 for r in refs:
  if r['path']in unique:C.need(unique[r['path']]==r,'no conflicting exact recovery Ref')
  unique[r['path']]=r
 return dict(schema='bole.r17-failed-owner-math-recovery-plan/v1',original_source=SOURCE,failed_owner=OWNER,terminal=terminal_ref,http=http,journals=journals,ranks=ranks,signals=signals,snapshots=snapshot_refs,worker_bindings=bindings_ref,releases=release,readset=list(unique.values()),native_snapshot_status='actual-original-durable-four-not-new-proof',live_frontend_binding_status='missing-not-reconstructed',lifecycle_qualified=False,original_owner_pass=False,qualified=False)

def consume(C,r):
 p=C.obj(r);C.need(p['schema']=='bole.r17-failed-owner-math-recovery-plan/v1'and p['original_source']==SOURCE and p['failed_owner']==OWNER,'exact typed R17 original failed-owner math-only plan')
 C.need(p==bind(C,p['terminal']),'fresh full source/raw/terminal/release proof equals bound plan');return p
