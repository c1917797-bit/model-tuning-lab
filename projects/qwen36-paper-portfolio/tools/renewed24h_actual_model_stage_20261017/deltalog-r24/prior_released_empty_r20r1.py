"""Typed sole-CPU failed attempt; old result/journal/empty inode stay immutable."""
import json,os,stat,types
from pathlib import Path
ROOT=Path('/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061')
OPT=Path('/opt/host/vnf/austinov/run-deltalog-FIRSTDECODE101R20R1-main-NEW24H_FIRSTDECODE101R20R1_001')
SOURCE=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-first-real-decode-owned-renew24h-v1-101-repair20-repair1-20261017-001/SOURCE_MANIFEST.json',bytes=259665,sha256='86e6dfdc1c691abf271106472095c192744f788c1b2821106624f584338f9df9')
TEMPLATE=dict(path=SOURCE['path'].replace('SOURCE_MANIFEST','SOURCE_TEMPLATE'),bytes=240387,sha256='44cce9e384f74bb630ddf22f1b28e85b2be389d88ddf5bb16301c335775b1b4e')
OWNER=dict(path=(OPT/'RESULT.json').as_posix(),bytes=29572,sha256='b6166077731e1661d16b29a938932cfb80503f37a8bf6a6b6b507f1d45dd433b')
JOURNAL=dict(path=(ROOT/'MODEL_SNAPSHOTS_LEDGER.R20repair1.json').as_posix(),bytes=3807,sha256='aa1f760e8efbcff4c2ff421e4bd3967d5077f2bb96f2c2afc0e79c2db97bb295')
BASE=dict(path=(ROOT/'STORAGE_LEDGER061.23.json').as_posix(),bytes=4169,sha256='7bacf26df76b47d53963fc054c91b38384716c7d9901938087f329dc288c23d0')
CLEANUP=dict(path=(OPT/'cpu-preflight/cleanup.json').as_posix(),bytes=1457,sha256='bdc08aa5aef687ee2cb37bc85d410b852edaf73b2417a3e89c0fd61252c9bcd4')
INSPECT=dict(path=(OPT/'cpu-preflight/inspect-1792234662622791260.json').as_posix(),bytes=40187,sha256='13e3cc13e2c2e8a6967c2547a15153f7a94663fd4bd9c60a72969f29494121f8')
CID='d91f6408599362a8e733953579b5a35730a608026f524d138c234ccee5005b96'
LEAF=ROOT/'first-real-decode-model-snapshots-renew24h-R20repair1-20261017-001'
PRIMARY="ValueError('original child failure retained: DL-cold-source')"
EMPTY=(64770,6029410,16832,2,4096,1792234138768000000,1792234138768000000)
FIELDS=('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns')

def documents(O):
 source,owner,journal,base,cleanup,receipt=[O.obj(r)for r in(SOURCE,OWNER,JOURNAL,BASE,CLEANUP,INSPECT)]
 O.need(source['prepared_template']==TEMPLATE and source['prepared_only']is False and source['output_root']==OPT.as_posix(),'actual R20r1 source/template/output')
 O.need(owner['schema']=='deltalog.actual-owned-dispatch-smoke/v025'and owner['source']==SOURCE and owner['status']=='failed'and owner['primary']==PRIMARY and owner['secondary']==[]and owner['all_created_containers_release_verified']is True,'exact original R20r1 FAIL retained, not numeric PASS')
 O.need(owner['owned_containers']==[dict(stage=(OPT/'cpu-preflight').as_posix(),cid=CID,exact_owned_release_verified=True)],'sole released CPU, not R19 noCID or missing model proof')
 p=owner['post_work_verification']
 O.need(p['source_after']is True and p['metadata_after_hash']is True and p['registered_cap_seconds']==900 and 0<p['actual_cap_seconds']<=900 and 0<=p['elapsed_seconds']<=900 and 0<=owner['elapsed']<=2700 and 0<=owner['cleanup_seconds']<=270,'original complete source/hash/metadata fence and clocks')
 O.need(all(owner[k]is False for k in('model_numeric_qualified','long_history_160_qualified','production_admitted','performance_ready','task_accuracy')),'original qualification flags remain false')
 O.need(journal['schema']=='deltalog.model-snapshots-reservation/v1'and journal['source']==SOURCE and journal['leaf']==LEAF.as_posix()and journal['combined_opt_root']==OPT.as_posix()and journal['core_ledger_ref']==BASE and journal['legacy_ledger_written']is journal['numeric_qualified']is False,'exact old empty reservation/core ledger')
 O.need((journal['budget_bytes'],journal['payload_total_cap_bytes'],journal['opt_total_cap_bytes'],journal['allocated_worker_cap_bytes'])==(32*2**30,30*2**30,2*2**30,15*2**29),'old combined budget unchanged')
 O.need(cleanup['container']==CID and cleanup['stopped']is cleanup['retained']is True and cleanup['deleted']is False and cleanup['errors']==[]and cleanup['primary_error']==PRIMARY and cleanup['after_inspect']==INSPECT,'actual cleanup join, never synthesize success')
 O.need(receipt['exit_code']==0 and receipt['requested_argv']==['/usr/bin/docker','inspect',CID],'actual inspect command')
 values=json.loads(receipt['stdout']);O.need(len(values)==1,'sole original inspect');v=values[0];s=v['State'];h=v['HostConfig'];labels=v['Config']['Labels']
 O.need(v['Id']==CID and not v.get('ExecIDs')and s['Status']=='exited'and s['Running']is False and s['Pid']==0 and s['OOMKilled']is False,'original CPU independently stopped/noExec/noOOM')
 O.need(h['Devices']==[]and not h.get('DeviceRequests')and not h.get('DeviceCgroupRules')and h['Memory']==h['MemorySwap']==8*2**30 and h['NanoCpus']==10**9 and h['ReadonlyRootfs']is True,'original CPU Devices[]/memory/cpu/RO')
 O.need(labels['model-tuning-lab.owner']=='NEW24H_FIRSTDECODE101R20R1_001'and labels['model-tuning-lab.arm']=='cpu-preflight'and labels['model-tuning-lab.source-manifest-sha256']==SOURCE['sha256'],'original CPU owner/source/arm')
 states=p['current_owned_inspects'];O.need(len(states)==1 and states[0]['Id']==CID and states[0]['State']==s and states[0].get('ExecIDs')==v.get('ExecIDs'),'posthash independent release joined')
 return dict(schema='deltalog.closed-released-empty-attempt/v021',owner=OWNER,source=SOURCE,journal=JOURNAL,cleanup=CLEANUP,inspect=INSPECT,core_ledger_ref=BASE,leaf=LEAF.as_posix(),original_primary=PRIMARY,sole_released_cpu=CID,candidate_created=False,actual_payload_bytes=0,original_nominal_budget_bytes=32*2**30,prior_lease_terminal=True,old_journal_not_rewritten=True,numeric_qualified=False)

def refs(O):
 cleanup=O.obj(CLEANUP)
 return[SOURCE,TEMPLATE,OWNER,JOURNAL,BASE,CLEANUP,INSPECT,*[cleanup[k]for k in('before_inspect','stop_receipt','release_smi')]]

def empty(O):
 st=LEAF.lstat();O.need(stat.S_ISDIR(st.st_mode)and tuple(getattr(st,k)for k in FIELDS)==EMPTY and not any(LEAF.iterdir())and not any(x.is_symlink()for x in(LEAF,*LEAF.parents)),'actual same empty R20r1 inode/all metadata')
 O.need(not os.path.lexists(OPT/'candidate'),'no candidate ever created; dangling aliases reject')
 return tuple(getattr(st,k)for k in FIELDS)

def validate(O,K):
 proof=documents(O);before=empty(O)
 # Same exact source-bound proc FD/maps scanner, no PID exemption and no
 # absence-as-retirement. Both old opt and old P roots remain protected.
 ns=dict(K.__dict__,SOURCE=SOURCE,PHASES=('payload','control'),leaf=lambda i:(LEAF,OPT)[i])
 no_writers=types.FunctionType(K.no_writers.__code__,ns,'no_writers',K.no_writers.__defaults__,K.no_writers.__closure__)
 inspect_scope=dict(K.__dict__,CIDS=((CID,),))
 fresh=types.FunctionType(K.inspect_all.__code__,inspect_scope,'inspect_all',K.inspect_all.__defaults__,K.inspect_all.__closure__)
 writers=no_writers();states=fresh()
 O.need(len(states)==1 and states[0]['Id']==CID and empty(O)==before,'fresh sole CPU stopped and empty tree unchanged')
 return dict(proof,current_no_writers=writers,current_stopped_cpu=states)
