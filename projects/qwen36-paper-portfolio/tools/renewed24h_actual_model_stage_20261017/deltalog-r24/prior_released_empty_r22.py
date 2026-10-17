"""Exact real R22 sole-CPU FAIL closure; metadata freezes only at actual bind."""
import json,os,stat,types
from pathlib import Path
OPT=Path('/opt/host/vnf/austinov/run-deltalog-FIRSTDECODE101R22repair1-main-NEW24H_FIRSTDECODE101R22repair1_001')
LEAF=Path('/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061/first-real-decode-model-snapshots-renew24h-R22repair1-20261017-001')
SOURCE=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-first-real-decode-owned-renew24h-v1-101-repair22-repair1-20261017-001/SOURCE_MANIFEST.json',bytes=280513,sha256='fe1605d6bc07185e1a37792daf3c73050b129833dbff763ff121b6a78d2585ec')
OWNER=dict(path=OPT.as_posix()+'/RESULT.json',bytes=31213,sha256='f784a124c065a4ad9d44e2dc4ad8506d3ab225e85c6ebdc75df7b092d573615d')
CLEANUP=dict(path=OPT.as_posix()+'/cpu-preflight/cleanup.json',bytes=1497,sha256='729a0d85fc776b9a186e3d53226e6bc63d84df58b31a048ec803a9f329147e79')
INSPECT=dict(path=OPT.as_posix()+'/cpu-preflight/inspect-1792243801126342010.json',bytes=42737,sha256='4991fd33c553b5c773c5b67ad4ddf7f937db511e12b45bbc50b64968f6d364be')
JOURNAL=dict(path=LEAF.parent.as_posix()+'/MODEL_SNAPSHOTS_LEDGER.R22repair1.json',bytes=7751,sha256='007f37078aef0853b87a204c2255de4cfe2ed19760a05244f5b6858ae885e3dc')
CID='03aa7c4db91fa43ca71fc3f458de28a263128b599e186d8e3bd22de7b410ec80'
PRIMARY="ValueError('original child failure retained: DL-cold-source')"
FIELDS=('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns')

def documents(O):
 owner,cleanup,receipt,journal=[O.obj(r)for r in(OWNER,CLEANUP,INSPECT,JOURNAL)]
 O.need(owner['schema']=='deltalog.actual-owned-dispatch-smoke/v025'and owner['source']==SOURCE and owner['status']=='failed'and owner['primary']==PRIMARY and owner['secondary']==[]and owner['all_created_containers_release_verified']is True,'exact R22 FAIL retained')
 O.need(owner['owned_containers']==[dict(stage=OPT.as_posix()+'/cpu-preflight',cid=CID,exact_owned_release_verified=True)],'sole released CPU; no candidate/NPU success inferred')
 p=owner['post_work_verification'];O.need(p['source_after']is p['metadata_after_hash']is True and p['registered_cap_seconds']==900 and 0<p['actual_cap_seconds']<=900 and 0<=p['elapsed_seconds']<=900 and 0<=owner['elapsed']<=3600 and 0<=owner['cleanup_seconds']<=270,'original full source/hash and deadline fences retained')
 O.need(all(owner[k]is False for k in('model_numeric_qualified','long_history_160_qualified','production_admitted','performance_ready','task_accuracy')),'original no qualifications')
 O.need(cleanup['container']==CID and cleanup['stopped']is cleanup['retained']is True and cleanup['deleted']is False and cleanup['errors']==[]and cleanup['primary_error']==PRIMARY and cleanup['after_inspect']==INSPECT,'actual retained CPU cleanup join')
 O.need(receipt['exit_code']==0 and receipt['requested_argv']==['/usr/bin/docker','inspect',CID],'actual exact final inspect command')
 values=json.loads(receipt['stdout']);O.need(len(values)==1,'one actual stopped CID');v=values[0];s=v['State'];h=v['HostConfig']
 O.need(v['Id']==CID and not v.get('ExecIDs')and s['Status']=='exited'and s['Running']is False and s['Pid']==0 and s['ExitCode']==137 and s['OOMKilled']is False,'original retained stopped CPU Exit137 is not natural PASS')
 O.need(h['Devices']==[]and not h.get('DeviceRequests')and not h.get('DeviceCgroupRules')and h['Memory']==h['MemorySwap']==8*2**30 and h['NanoCpus']==10**9 and h['ReadonlyRootfs']is True,'actual original CPU scope')
 labels=v['Config']['Labels'];O.need(labels['model-tuning-lab.owner']=='NEW24H_FIRSTDECODE101R22repair1_001'and labels['model-tuning-lab.arm']=='cpu-preflight'and labels['model-tuning-lab.source-manifest-sha256']==SOURCE['sha256'],'actual original CPU source/owner labels')
 states=p['current_owned_inspects'];O.need(len(states)==1 and states[0]['Id']==CID and states[0]['State']==s and states[0].get('ExecIDs')==v.get('ExecIDs'),'posthash independent stop proof')
 O.need(journal['schema']=='deltalog.model-snapshots-reservation/v1'and journal['source']==SOURCE and journal['leaf']==LEAF.as_posix()and journal['combined_opt_root']==OPT.as_posix()and journal['legacy_ledger_written']is journal['numeric_qualified']is False,'exact immutable old reservation')
 from prior_released_empty_r21 import BASE
 O.need(journal['core_ledger_ref']==BASE,'unchanged exact original highest23 base')
 O.need((journal['budget_bytes'],journal['payload_total_cap_bytes'],journal['opt_total_cap_bytes'],journal['allocated_worker_cap_bytes'])==(32*2**30,30*2**30,2*2**30,15*2**29),'old2+30 budget unchanged')
 return dict(schema='deltalog.released-empty-r22-bind-observation/v1',source=SOURCE,owner=OWNER,cleanup=CLEANUP,inspect=INSPECT,journal=JOURNAL,leaf=LEAF.as_posix(),original_primary=PRIMARY,sole_released_cpu=CID,prior_lease_terminal=True,numeric_qualified=False,old_journal_not_rewritten=True)

def refs(O):
 cleanup=O.obj(CLEANUP)
 return[SOURCE,OWNER,CLEANUP,INSPECT,JOURNAL,*[cleanup[k]for k in('before_inspect','stop_receipt','release_smi')]]

def empty(O):
 st=LEAF.lstat();O.need(stat.S_ISDIR(st.st_mode)and st.st_nlink==2 and not any(LEAF.iterdir())and not any(x.is_symlink()for x in(LEAF,*LEAF.parents)),'actual complete ordinary R22 EMPTY directory')
 O.need(not os.path.lexists(OPT/'candidate'),'actual candidate never created, not batch absence')
 return list(getattr(st,k)for k in FIELDS)

def observe(O,K,expected=None):
 O.obj(SOURCE) # Exact complete old source SHA as well as the encoded owner Ref.
 proof=documents(O);before=empty(O)
 if expected is not None:O.need(expected==dict(proof,empty_metadata=before,actual_payload_bytes=0,candidate_created=False),'same bind-frozen original R22 proof/EMPTY identity')
 ns=dict(K.__dict__,SOURCE=SOURCE,PHASES=('payload','control'),leaf=lambda i:(LEAF,OPT)[i])
 check=types.FunctionType(K.no_writers.__code__,ns,'no_writers',K.no_writers.__defaults__,K.no_writers.__closure__)
 scan=types.FunctionType(K.inspect_all.__code__,dict(K.__dict__,CIDS=((CID,),)),'inspect_all',K.inspect_all.__defaults__,K.inspect_all.__closure__)
 check();states=scan();O.need(len(states)==1 and states[0]['Id']==CID and empty(O)==before,'fresh stopped sole CID/EMPTY unchanged')
 return dict(proof,empty_metadata=before,actual_payload_bytes=0,candidate_created=False)

def bind(O,K):return observe(O,K)
def validate(O,K,expected):return observe(O,K,expected)
