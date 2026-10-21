
import os,resource,pathlib,json,hashlib,subprocess,sys,time
os.sched_setaffinity(0,{166});resource.setrlimit(resource.RLIMIT_CPU,(166,166));_,h=resource.getrlimit(resource.RLIMIT_AS);resource.setrlimit(resource.RLIMIT_AS,(512*2**20,h))
T=pathlib.Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z");R=pathlib.Path('/opt/host/vnf/austinov/bole-gdn-g1-probe-matched-v5');O=pathlib.Path('/opt/host/vnf/austinov/run-bole-gdn-g1-probe-matched-v5-CPU')
def ref(p):
 p=pathlib.Path(p);h=hashlib.sha256();n=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b);n+=len(b)
 return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def checked(r):
 a=ref(r['path']);assert a['sha256']==r['sha256']and('bytes'not in r or a['bytes']==r['bytes']);return a
def obj(r):checked(r);return json.loads(pathlib.Path(r['path']).read_bytes())
sr=ref(R/'SOURCE_BOUND.json');assert sr['bytes']==117604 and sr['sha256']=='f5308ea9d74e92293fd00a73f156a324fab064bfb2dcca3997728054deff4831'
rr=ref(O/'RESULT.json');assert rr['bytes']==235527 and rr['sha256']=='73733f6268cea5226dbcb9f5099c461e396b72c3aa274e5726b5a9d0e796ffa0'
v=obj(rr);m=obj(sr);cmd=obj(ref(R/'COMMANDS.json'))
assert v['source']==sr and v['primary']is None and v['secondary']==[]and v['cpu_only']is True and v['source_before']==v['source_after']and len(v['source_before'])==732
assert v['actual_host_argv']==cmd['CPU'][8:]and v['entry_clock_before_source_replay']is True and v['deadline_renewed']is False and v['phase_seconds']==3600 and v['cleanup_seconds']==180 and v['elapsed']<=3600 and v['cleanup_spent']<=180
sys.path.insert(0,str(R));import sourceio as C,bind_model as B,command_contract as CC,gdn_probe_runtime as GP
for n,module in [('sourceio.py',C),('bind_model.py',B),('command_contract.py',CC),('gdn_probe_runtime.py',GP)]:assert ref(module.__file__)==m['files'][n]
refs=B.readset(sr)+m['dependencies']+CC.validate(C,sr,m)+GP.host_readset(C,sr,m)+GP.handoff_readset(C,sr,m,v['summary']['GDN_software'])
before={r['path']:r['sha256']for r in refs};assert before==v['source_before']
for p,sha in before.items():assert ref(p)['sha256']==sha
handoff=obj(v['summary']['GDN_software']);report=handoff['actual_report']
assert handoff['source']==report['source']==sr and report['tests']==240 and report['all_tests_passed']is True and report['complete_readset_audited']is True and report['NPU']is False
assert len(report['actual_cold_cli'])==10 and all(x['exit_code']==0 for x in report['actual_cold_cli'])
proof=obj(v['summary']['CPU_report']);assert proof['source']==sr and proof['pass_preflight']is True and proof['Devices']==[]and proof['native_runtime_parser_checked']is True and proof['registry_arch_enumerated']is True and proof['torch_NPU_initialized']is False and proof['weights_loaded']is False
refs.extend(GP.collect(C,[v['summary'],handoff],installed_refs=tuple(m['runtime_sources'].values())))
for name in ['CPU_child','actual_software_child']:
 child=obj(v['summary'][name]);assert child['exit_code']==0 and child['child_termination_observed']is True
 argv=child['requested_argv'];assert argv[:2]==['/usr/bin/docker','exec']and argv[3:6]==['/bin/bash','-c','source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"']and '-B'in argv and '-I'not in argv
rel=obj(v['summary']['CPU_release']);assert rel['stopped']is True and rel['retained']is True and rel['deleted']is False and rel['errors']==[]
ownref=ref(O/'cpu-preflight/OWNED.json');own=obj(ownref);assert own['cid']==rel['container']and own['source']==sr and own['image']=='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'
insref=checked(rel['after_inspect']);ins=obj(insref);assert ins['exit_code']==0
records=json.loads(ins['stdout']);assert type(records)is list and len(records)==1;i=records[0];cfg=i['HostConfig'];st=i['State']
assert i['Id']==own['cid']and i['Image']==own['image']and i['Name']=='/'+own['name']
assert st['Running']is False and st['Pid']==0 and st['OOMKilled']is False and st['Status']=='exited'and not i.get('ExecIDs')
assert cfg['Devices']==[]and cfg['CpusetCpus']=='0' and own['guest_cpus']==[0]and cfg['NanoCpus']==1000000000 and cfg['Memory']==8*2**30 and cfg['MemorySwap']==8*2**30 and cfg['ReadonlyRootfs']is True and cfg['NetworkMode']=='none'and cfg['IpcMode']=='private'
mounts={a['Destination']:(a['Source'],a['RW'])for a in i['Mounts']};assert len(mounts)==len(i['Mounts'])and mounts=={p:tuple(z)for p,z in own['mounts'].items()}
createref=checked(own['create_receipt']);create=obj(createref);assert create['exit_code']==0 and create['stdout'].strip()==own['cid']
argv=create['requested_argv'];assert argv[argv.index('--cpuset-cpus')+1]=='0' and argv[argv.index('--cpus')+1]=='1' and argv[argv.index('--memory')+1]=='8589934592' and argv[argv.index('--memory-swap')+1]=='8589934592'
unit='bole-gdn-matched-v5-cpu-20261020t154710z.service';q=subprocess.run(['/usr/bin/systemctl','show',unit,'--property=Id,ActiveState,SubState,Result,ExecMainStatus,MainPID,ControlPID,Type,Restart'],capture_output=True,text=True,timeout=10);assert q.returncode==0 and q.stderr==''
props=dict(x.split('=',1)for x in q.stdout.splitlines());assert props['Id']==unit and props['ActiveState']=='active'and props['SubState']=='exited'and props['Result']=='success'and props['ExecMainStatus']==props['MainPID']==props['ControlPID']=='0'
tp=T/'GDN_MATCHED_V5_CPU_SYSTEMD_TERMINAL.json'
with tp.open('x')as f:json.dump(dict(schema='bole.actual-finite-unit-terminal/v1',observed_epoch=time.time(),properties=props),f,sort_keys=True);f.write('\n')
refs.extend([rr,sr,ownref,insref,createref,ref(tp)]);unique={r['path']:checked(r)for r in refs}
out=dict(schema='bole.GDN-matched-v5-CPU-metadata-independent-qualification/v1',source=sr,result_ref=rr,unit_terminal_ref=ref(tp),source_readset_count=len(before),original_full_source_and_software_gate_reexecuted=True,actual240_sameimage_pass=True,native_parser_pass=True,all_original_create_and_inspect_mounts_equal=True,owned_stopped_retained=True,Devices=[],current_live_container_queried=False,saved_stopped_metadata_only=True,retained_refs=list(unique.values()),reader_ref=ref(__file__),reader_argv=['/usr/bin/python3','-I','-B',str(pathlib.Path(__file__).absolute())],model_ready=False,formal_success=False,NPU=False)
p=T/'GDN_MATCHED_V5_CPU_METADATA_READBACK.json'
with p.open('x')as f:json.dump(out,f,sort_keys=True);f.write('\n')
print(json.dumps(dict(qualification_ref=ref(p),source=sr,source_readset_count=len(before),retained_refs_count=len(unique),actual240_sameimage_pass=True,owned_stopped_retained=True,model_ready=False,formal_success=False)))
