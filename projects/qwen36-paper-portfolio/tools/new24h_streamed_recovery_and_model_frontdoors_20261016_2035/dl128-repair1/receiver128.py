"""Explicit failed-NPU-parent + actual completed ownedCPU recovery receiver."""
import importlib.util,json,sys
from pathlib import Path,PurePosixPath
P=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_128_exact_local_transform',P/'reader_transform128.py')
_transform=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_transform)
transform=_transform.transform
_io_spec=importlib.util.spec_from_file_location('_128_local_stable_stream',P/'io128.py')
_io=importlib.util.module_from_spec(_io_spec);_io_spec.loader.exec_module(_io)
def streamed(ref):return _io.obj_file(ref)
OLD_TEMPLATE=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-real-worker-new24h-v1-101-repair5/SOURCE_TEMPLATE.json',bytes=205705,sha256='d657d8e9140f765d402b0619fd9d9589c8ed0479b9c860a1cf5400710b510a8d')
R2_TEMPLATE=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-anchor-consumer-recovery-new24h-v1-127-repair3/SOURCE_TEMPLATE.json',bytes=7483,sha256='eaea9b7e041b6e3b37a032e84c31a06eed8c66ce40119764a61a2c7af46332fd')
FAULT=dict(path='/opt/host/vnf/austinov/run-dl088r6r2-consumer-fault-evidence-MAIN-20261016-001/ACTUAL_EVIDENCE.json',bytes=15353,sha256='cc4ea59d1c90f43f0513585dc731aa53380598dd287646434a742eb8d2d5b81e')
def module(C,ref,name):
 p=C.obj_file(ref);s=importlib.util.spec_from_file_location(name,p);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
def source(C,sr):
 s=C.obj(sr);C.need(s['schema']=='deltalog.recovered-model-receiver-source/v128'and s['default_enabled']is False and s['old_model_template_ref']==OLD_TEMPLATE and s['recovery_template_ref']==R2_TEMPLATE and s['actual_fault_ref']==FAULT,'reviewed independent current receiver')
 C.need(s['files']['receiver128.py']==dict(path=str(P/'receiver128.py'),bytes=Path(__file__).stat().st_size,sha256=__import__('hashlib').sha256(Path(__file__).read_bytes()).hexdigest()),'actual executing receiver identity')
 for r in s['files'].values():C.obj_file(r)
 return s
def load_recovery(C,m,plan,reader_source):
 N=C.need
 N(plan['schema']=='deltalog.recovered-component-model-input/v128'and plan['receiver_source_ref']==reader_source and plan['old_model_template_ref']==OLD_TEMPLATE and plan['recovery_template_ref']==R2_TEMPLATE and plan['actual_fault_ref']==FAULT,'typed exact recovery plan/source')
 for k in('recovery_owner_ref','recovery_cleanup_ref','recovery_inspect_ref','component_cpu_owner_ref'):N(type(plan.get(k))is dict,'actual future recovery/CPU Ref missing: '+k)
 N(plan['component_cpu_owner_ref']==m['component_cpu_owner_ref'],'same actual original CPU/Meta owner')
 rt=C.obj(R2_TEMPLATE);V=module(C,rt['files']['provenance127.py'],'_128_exact_actual_timeout')
 e=C.obj(FAULT);s,p=V.validate(e,C.obj);refs=e['refs']
 N(m['bridge024_source_ref']==refs['source']and m['bridge024_owner_ref']==refs['owner'],'original NPU math source/failed owner never substituted')
 o=C.obj(refs['owner']);ro=C.obj(plan['recovery_owner_ref']);rs=ro['source'];reader=C.obj(rs)
 N(ro['schema']=='deltalog.fresh-bridge-owned-host/v5'and ro['target_source']==rs and ro['stage']=='cpu'and ro['steps']==16 and ro['physical']==[]and ro['NPU']is False,'distinct actual owned Devices[] recovery, not new NPU')
 N(ro['primary']is None and ro['secondary']==[]and ro['stopped_retained']is ro['resource_admitted']is True and ro['bridge_primitive_gate_pass']is ro['full_gdn_qualified']is ro['model_ready']is False,'actual recovery completed/released without promotion')
 N(reader['schema']=='deltalog.deadpayload-native-bridge-source/v024'and reader['prepared_only']is False and reader['bound']is True and reader['prepared_template']==R2_TEMPLATE and reader['files']==rt['files']and reader['root']==rt['root'],'exact reviewed127R2 actual current consumer source')
 N(reader['producer_source']==reader['original_source_ref']==refs['source']and reader['original_producer_ref']==refs['producer']and reader['original_failed_owner_ref']==refs['owner']and reader['original_strict_ref']==refs['strict']and reader['actual_fault_evidence_ref']==FAULT and reader['original_timeout_seconds']==V.TIMEOUT and reader['allowed_fault']=='exact-original-domain-TimeoutExpired-shared590','source-separated original chain and narrow fault')
 for r in reader['files'].values():C.obj_file(r)
 # This is the actual recovery's typed, fully verified data readset, never a
 # generic recursive scan of historical JSON/source identities.
 required=[refs['producer'],refs['source'],refs['owner'],refs['strict'],refs['numeric_cleanup'],refs['consumer_cleanup'],* [x['raw']for x in p['records']],*p['actual_sidecar_records']]
 N('recovery_refs'not in reader,'no embedded large recovery array')
 R=module(C,rt['files']['readset127.py'],'_128_exact_streamed_readset')
 descriptor=reader['recovery_readset_index']
 N(descriptor['index_ref']['path']==str(PurePosixPath(reader['root'])/'RECOVERY_READSET127.jsonl'),'same-source immutable index')
 wanted={r['path']:r for r in required};seen={}
 for r in R.Index(descriptor,streamed):
  streamed(r)
  if r['path']in wanted:seen[r['path']]=r
 N(all(seen.get(r['path'])==r for r in required),'all681 raw containers + original evidence in actual recovery readset')
 base=Path(plan['recovery_owner_ref']['path']).parent;N(Path(ro['result']['path'])==base/'native/result/STAGE_RESULT.json'and Path(plan['recovery_cleanup_ref']['path'])==base/'native/cleanup-verdict.json'and Path(plan['recovery_inspect_ref']['path'])==base/'native/inspect-exited.json','actual ownedCPU report/cleanup/inspect same new leaf')
 cleanup=C.obj(plan['recovery_cleanup_ref']);inspection=C.obj(plan['recovery_inspect_ref']);N(inspection['exit_code']==0,'actual new inspection read')
 values=json.loads(inspection['stdout']);N(type(values)is list and len(values)==1,'actual one new CID inspection');x=values[0];state=x['State'];hc=x['HostConfig'];env=dict(v.split('=',1)for v in x['Config']['Env'])
 N(x['Id']==cleanup['cid']and x['Image']==V.IMAGE and not x.get('ExecIDs')and state['Status']=='exited'and state['Running']is False and state['Pid']==0 and state['ExitCode']==0 and state['OOMKilled']is False,'actual newCPU CID exited0/noExec/noOOM')
 N(cleanup['errors']==cleanup['secondary_guard_cleanup']==[]and cleanup['resource_release_verified']is cleanup['stopped']is cleanup['retained']is True and cleanup['unresolved_active_cid']is None,'actual newCPU release not original release reused')
 labels=x['Config']['Labels'];N(labels['qwen36.owner']=='deltalog-anchor-consumer-recovery-new24h-MAIN-127-repair3'and labels['qwen36.stage']=='native'and labels['deltalog-fresh-bridge.owner-source-sha256']==rs['sha256'],'actual same new reader source labels')
 N(not hc.get('Devices')and not hc.get('DeviceRequests')and not hc.get('DeviceCgroupRules')and not hc['Privileged']and hc['NetworkMode']=='none'and hc['Memory']==hc['MemorySwap']==8*2**30 and hc['NanoCpus']==10**9 and 'ALL'in hc.get('CapDrop',[])and any('no-new-privileges'in v for v in hc.get('SecurityOpt',[])),'new Devices[] bounded original CPU resource contract')
 N(env.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and env.get('ASCEND_RT_VISIBLE_DEVICES')==''and all(env.get(k)=='1'for k in('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS')),'actual no-backend CPU environment')
 N(ro['authority']==o['authority'],'same fixed-window authority')
 cmd=x['Config']['Cmd'];N(cmd[:4]==['/bin/bash','-c','source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"','dldeadbridge024'],'actual ownedCPU CANN bootstrap')
 args=cmd[4:];N(len(args)==17 and args[:7]==['/usr/local/python3.12.13/bin/python3','-I','-B',reader['files']['entry.py']['path'],'--execute','--stage','cpu-preflight']and args[7::2]==['--source-ref','--authority-ref','--lifecycle-ref','--steps','--output'],'actual complete new CPU command')
 N(json.loads(args[8])==rs and json.loads(args[10])==o['authority']and json.loads(args[12])==reader['lifecycle_source_ref']and args[14]=='16'and args[16]==str(base/'native/result'),'new CPU source/authority/lifecycle/output identities')
 allrefs=R.Readset([rs,reader['prepared_template'],*reader['files'].values(),descriptor['index_ref']],descriptor,streamed)
 parents={Path(v)for v in allrefs.parents};parents.update((Path(reader['root']),Path(refs['source']['path']).parent,Path(o['authority']['path']).parent));parents={q for q in parents if not any(v!=q and v in q.parents for v in parents)}
 expected={str(q):(str(q),False)for q in parents};expected['/usr/local/Ascend/driver']=('/usr/local/Ascend/driver',False);expected[str(base/'native')]=(str(base/'native'),True)
 N({v['Destination']:(v['Source'],v['RW'])for v in x['Mounts']}==expected,'actual exact transitive RO closure and sole new owned output RW')
 V.arm(C.obj(reader['original_arm_ref']),C.obj(reader['original_device_ref']),C.obj(reader['original_handshake_ref']),reader['original_plan_ref'],C.obj(reader['original_plan_ref']),p,s,e['small_documents']['numeric_cleanup']['cid'])
 result=C.obj(ro['result']);N(result['schema']=='deltalog.anchor-consumer-CPU-recovery/v127'and result['source']==rs and result['authority']==o['authority']and result['producer_source']==refs['source']and result['actual_original_producer']==refs['producer']and result['original_failed_owner']==refs['owner']and result['preserved_original_strict']==refs['strict']and result['actual_fault_evidence']==FAULT,'actual recovered report / original chain join')
 envelope=C.obj(result['consumer_envelope']);N(envelope['schema']=='deltalog.anchor-consumer-diagnostic/v127'and envelope['consumer_source']==rs and envelope['producer_source']==refs['source']and envelope['producer']==refs['producer']and envelope['preserved_original_strict']==refs['strict']and envelope['domain']==result['domain']and envelope['original_domain_exit']==0 and envelope['NPU_reexecuted']is envelope['qualification']is envelope['model_admitted']is False,'actual separate127 execution envelope, no fake v088 pair')
 return o,p,result,dict(recovery_owner=plan['recovery_owner_ref'],consumer_source=rs,stage_ref=ro['result'],receiver_source=reader_source)
def admit_plan(C,m,plan,reader_source):
 source(C,reader_source)
 old=C.obj(OLD_TEMPLATE);raw_ref=old['files']['plugin/qwen36_deltalog_service/split_qualification.py']
 raw=C.obj_file(raw_ref).read_bytes();text=transform(raw);ns={'__name__':'_128_original_domain_reader','__file__':raw_ref['path']};exec(compile(text,raw_ref['path']+'#recovery128','exec'),ns)
 ns['C']=C;ns['META']=module(C,old['files']['plugin/qwen36_deltalog_service/build_meta051.py'],'_128_original_build_Meta');ns['RECOVERY']=lambda reader,context:load_recovery(reader,context,plan,reader_source)
 return ns['consume'](m)
def admit(C,m,plan_ref,reader_source):
 C.need(type(plan_ref)is dict and set(plan_ref)=={'path','bytes','sha256'},'actual recovery model input pending')
 return admit_plan(C,m,C.obj(plan_ref),reader_source)
def readset(C,m,plan_ref,reader_source):
 refs={}
 class Recording:
  need=staticmethod(C.need)
  @staticmethod
  def mark(r):
   C.need(type(r)is dict and set(r)=={'path','bytes','sha256'},'typed actual readset Ref3');C.need(r['path']not in refs or refs[r['path']]==r,'one source/input Ref per path');refs[r['path']]=r
  @staticmethod
  def obj(r):Recording.mark(r);return C.obj(r)
  @staticmethod
  def obj_file(r):Recording.mark(r);return C.obj_file(r)
 admit(Recording,m,plan_ref,reader_source)
 plan=C.obj(plan_ref);ro=C.obj(plan['recovery_owner_ref']);reader=C.obj(ro['source']);rt=C.obj(R2_TEMPLATE)
 R=module(C,rt['files']['readset127.py'],'_128_export_streamed_readset')
 return R.Readset([*refs.values(),reader['recovery_readset_index']['index_ref']],reader['recovery_readset_index'],streamed)
