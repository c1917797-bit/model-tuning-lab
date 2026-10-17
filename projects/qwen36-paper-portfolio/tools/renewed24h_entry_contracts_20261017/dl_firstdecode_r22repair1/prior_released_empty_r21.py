"""Typed sole-CPU failed attempt; old result/journal/empty inode stay immutable."""
import json,os,stat,types
from pathlib import Path
ROOT=Path('/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061')
OPT=Path('/opt/host/vnf/austinov/run-deltalog-FIRSTDECODE101R21-main-NEW24H_FIRSTDECODE101R21_001')
SOURCE={'bytes': 267633, 'path': '/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-first-real-decode-owned-renew24h-v1-101-repair21-20261017-001/SOURCE_MANIFEST.json', 'sha256': 'e5da6610109d60ae8524c08072f49f037242a096dae5ed0f72cd3c031f0b3306'}
TEMPLATE={'bytes': 243191, 'path': '/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-first-real-decode-owned-renew24h-v1-101-repair21-20261017-001/SOURCE_TEMPLATE.json', 'sha256': 'bd53c08cb9886af01c3f90940f0a1bd16bb18ef70ada7f784d4576568ab63a41'}
OWNER={'path': '/opt/host/vnf/austinov/run-deltalog-FIRSTDECODE101R21-main-NEW24H_FIRSTDECODE101R21_001/RESULT.json', 'bytes': 29961, 'sha256': 'fb1757cc7ca4bedb1989c1ef06054eb25510a162f3fffd99a8ea40e79059195c'}
JOURNAL={'path': '/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061/MODEL_SNAPSHOTS_LEDGER.R21.json', 'bytes': 5774, 'sha256': '25104323f8ac7c46434a8d461d857ea2e53d5855d89de519f4588a0e9096dac7'}
BASE={'bytes': 4169, 'path': '/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061/STORAGE_LEDGER061.23.json', 'sha256': '7bacf26df76b47d53963fc054c91b38384716c7d9901938087f329dc288c23d0'}
CLEANUP={'path': '/opt/host/vnf/austinov/run-deltalog-FIRSTDECODE101R21-main-NEW24H_FIRSTDECODE101R21_001/cpu-preflight/cleanup.json', 'bytes': 1441, 'sha256': 'e24f1f5b051216d47a715aa6e19b81a62aabc3024fee59a67e7cfe39d121ebb4'}
INSPECT={'bytes': 40925, 'path': '/opt/host/vnf/austinov/run-deltalog-FIRSTDECODE101R21-main-NEW24H_FIRSTDECODE101R21_001/cpu-preflight/inspect-1792238554768327070.json', 'sha256': '6a1303c1dde444fe71bbcbd1566429aa60fadca94bc4616d8efbb058c0fe2b27'}
CID='49ab87d0130890dab2382fca78a0b13d2f722853f83e23812dd0d798682c4646'
LEAF=Path('/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061/first-real-decode-model-snapshots-renew24h-R21-20261017-001')
PRIMARY="ValueError('original child failure retained: DL-cold-source')"
EMPTY=(64770, 6029411, 16832, 2, 4096, 1792238008548000000, 1792238008548000000)
FIELDS=('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns')

def documents(O):
 source,owner,journal,base,cleanup,receipt=[O.obj(r)for r in(SOURCE,OWNER,JOURNAL,BASE,CLEANUP,INSPECT)]
 O.need(source['prepared_template']==TEMPLATE and source['prepared_only']is False and source['output_root']==OPT.as_posix(),'actual R21 source/template/output')
 O.need(owner['schema']=='deltalog.actual-owned-dispatch-smoke/v025'and owner['source']==SOURCE and owner['status']=='failed'and owner['primary']==PRIMARY and owner['secondary']==[]and owner['all_created_containers_release_verified']is True,'exact original R21 FAIL retained, not numeric PASS')
 O.need(owner['owned_containers']==[dict(stage=(OPT/'cpu-preflight').as_posix(),cid=CID,exact_owned_release_verified=True)],'sole released CPU, not R19 noCID or missing model proof')
 p=owner['post_work_verification']
 O.need(p['source_after']is True and p['metadata_after_hash']is True and p['registered_cap_seconds']==900 and 0<p['actual_cap_seconds']<=900 and 0<=p['elapsed_seconds']<=900 and 0<=owner['elapsed']<=3600 and 0<=owner['cleanup_seconds']<=270,'original complete source/hash/metadata fence and clocks')
 O.need(all(owner[k]is False for k in('model_numeric_qualified','long_history_160_qualified','production_admitted','performance_ready','task_accuracy')),'original qualification flags remain false')
 O.need(journal['schema']=='deltalog.model-snapshots-reservation/v1'and journal['source']==SOURCE and journal['leaf']==LEAF.as_posix()and journal['combined_opt_root']==OPT.as_posix()and journal['core_ledger_ref']==BASE and journal['legacy_ledger_written']is journal['numeric_qualified']is False,'exact old empty reservation/core ledger')
 O.need((journal['budget_bytes'],journal['payload_total_cap_bytes'],journal['opt_total_cap_bytes'],journal['allocated_worker_cap_bytes'])==(32*2**30,30*2**30,2*2**30,15*2**29),'old combined budget unchanged')
 O.need(cleanup['container']==CID and cleanup['stopped']is cleanup['retained']is True and cleanup['deleted']is False and cleanup['errors']==[]and cleanup['primary_error']==PRIMARY and cleanup['after_inspect']==INSPECT,'actual cleanup join, never synthesize success')
 O.need(receipt['exit_code']==0 and receipt['requested_argv']==['/usr/bin/docker','inspect',CID],'actual inspect command')
 values=json.loads(receipt['stdout']);O.need(len(values)==1,'sole original inspect');v=values[0];s=v['State'];h=v['HostConfig'];labels=v['Config']['Labels']
 O.need(v['Id']==CID and not v.get('ExecIDs')and s['Status']=='exited'and s['Running']is False and s['Pid']==0 and s['OOMKilled']is False,'original CPU independently stopped/noExec/noOOM')
 O.need(h['Devices']==[]and not h.get('DeviceRequests')and not h.get('DeviceCgroupRules')and h['Memory']==h['MemorySwap']==8*2**30 and h['NanoCpus']==10**9 and h['ReadonlyRootfs']is True,'original CPU Devices[]/memory/cpu/RO')
 O.need(labels['model-tuning-lab.owner']=='NEW24H_FIRSTDECODE101R21_001'and labels['model-tuning-lab.arm']=='cpu-preflight'and labels['model-tuning-lab.source-manifest-sha256']==SOURCE['sha256'],'original CPU owner/source/arm')
 states=p['current_owned_inspects'];O.need(len(states)==1 and states[0]['Id']==CID and states[0]['State']==s and states[0].get('ExecIDs')==v.get('ExecIDs'),'posthash independent release joined')
 return dict(schema='deltalog.closed-released-empty-attempt/v021',owner=OWNER,source=SOURCE,journal=JOURNAL,cleanup=CLEANUP,inspect=INSPECT,core_ledger_ref=BASE,leaf=LEAF.as_posix(),original_primary=PRIMARY,sole_released_cpu=CID,candidate_created=False,actual_payload_bytes=0,original_nominal_budget_bytes=32*2**30,prior_lease_terminal=True,old_journal_not_rewritten=True,numeric_qualified=False)

def refs(O):
 cleanup=O.obj(CLEANUP)
 return[SOURCE,TEMPLATE,OWNER,JOURNAL,BASE,CLEANUP,INSPECT,*[cleanup[k]for k in('before_inspect','stop_receipt','release_smi')]]

def empty(O):
 st=LEAF.lstat();O.need(stat.S_ISDIR(st.st_mode)and tuple(getattr(st,k)for k in FIELDS)==EMPTY and not any(LEAF.iterdir())and not any(x.is_symlink()for x in(LEAF,*LEAF.parents)),'actual same empty R21 inode/all metadata')
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
