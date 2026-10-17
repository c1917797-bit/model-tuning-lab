"""R23 created CPU+candidate, failed parser; never reinterpret as no-CID/PASS."""
import json,os,stat,types
from pathlib import Path
OPT=Path('/opt/host/vnf/austinov/run-deltalog-FIRSTDECODE101R23payloadcontract-main-NEW24H_FIRSTDECODE101R23payloadcontract_001')
LEAF=Path('/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061/first-real-decode-model-snapshots-renew24h-R23payloadcontract-20261017-001')
ROOT='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-first-real-decode-owned-renew24h-v1-101-repair23-payload-contract-20261017-001'
TEMPLATE=dict(path=ROOT+'/SOURCE_TEMPLATE.json',bytes=257617,sha256='620b0941bc85a6736348f5d95073af287ddcebbfc8fb343dd7fb91d6c045dad6')
COMMANDS=dict(path=ROOT+'/COMMANDS_FINAL.json',bytes=8761,sha256='3c521d5818c2165a4c67e132126eda5e1e3c8dfda65d98c644cbdb8fb8b8b0bc')
PAYLOAD=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-selected-firstdecode-renew24h-20261017-001-test-contract-repair1/SOURCE_MANIFEST.json',bytes=18758,sha256='91f89a435b47a40f25b97d3a6852e45f2fdb29909a5c70f20be9b1a91868c81c')
PRIMARY="ValueError('original child failure retained: DL-four-canary')"
FIELDS=('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns')
def documents(O,er):
 O.need(type(er)is dict and set(er)=={'path','bytes','sha256'},'actual R23 terminal original Ref bundle pending; no candidate absence shortcut')
 e=O.obj(er);O.need(set(e)=={'schema','source','owner','journal','cleanups'}and e['schema']=='deltalog.actual-r23-terminal-readset/v1','typed original R23 terminal references only')
 source=O.obj(e['source']);template=O.obj(TEMPLATE);owner=O.obj(e['owner']);journal=O.obj(e['journal'])
 O.need(e['source']['path']==ROOT+'/SOURCE_MANIFEST.json'and source['prepared_template']==TEMPLATE and source['prepared_only']is False and source['root']==ROOT and source['output_root']==OPT.as_posix(),'original actual bound R23 source/template/root')
 O.need(source['files']==dict(template['files'],**{'COMMANDS_FINAL.json':COMMANDS})and source['firstdecode_contract']['payload_source']==PAYLOAD,'original exact R23 own code and payload, not a replacement source')
 O.need(e['owner']['path']==(OPT/'RESULT.json').as_posix()and owner['schema']=='deltalog.actual-owned-dispatch-smoke/v025'and owner['source']==e['source']and owner['status']=='failed'and owner['primary']==PRIMARY and owner['secondary']==[]and owner['all_created_containers_release_verified']is True,'original R23 parser FAIL retained, not numeric success')
 rows=owner['owned_containers'];O.need(len(rows)==2 and [r['stage']for r in rows]==[(OPT/'cpu-preflight').as_posix(),(OPT/'candidate').as_posix()]and all(r['exact_owned_release_verified']is True for r in rows)and len({r['cid']for r in rows})==2,'actually created CPU and candidate, both released')
 O.need(all(owner[k]is False for k in('model_numeric_qualified','long_history_160_qualified','production_admitted','performance_ready','task_accuracy')),'all original R23 qualification flags false')
 p=owner['post_work_verification'];O.need(p['source_after']is p['metadata_after_hash']is True and p['registered_cap_seconds']==900 and 0<p['actual_cap_seconds']<=900 and 0<=p['elapsed_seconds']<=900 and 0<=owner['elapsed']<=3600 and 0<=owner['cleanup_seconds']<=270,'actual complete original source/data/clock/release fences')
 post_states=p['current_owned_inspects'];O.need(len(post_states)==2 and{v['Id']for v in post_states}=={r['cid']for r in rows},'both actual independent posthash stopped inspections')
 O.need(set(e['cleanups'])=={'cpu-preflight','candidate'},'both original cleanup records required');cids=[]
 for row,stage in zip(rows,('cpu-preflight','candidate')):
  rr=e['cleanups'][stage];O.need(rr['path']==(OPT/stage/'cleanup.json').as_posix(),'original exact stage cleanup path');c=O.obj(rr)
  O.need(c['container']==row['cid']and c['stopped']is c['retained']is True and c['deleted']is False and c['errors']==[],'original stop/retain, no cleanup rewrite')
  receipt=O.obj(c['after_inspect']);O.need(receipt['exit_code']==0 and receipt['requested_argv']==['/usr/bin/docker','inspect',row['cid']],'original actual after-inspect command')
  values=json.loads(receipt['stdout']);O.need(len(values)==1,'one original CID inspect');v=values[0];s=v['State'];h=v['HostConfig']
  O.need(v['Id']==row['cid']and v['Image']=='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'and not v.get('ExecIDs')and s['Status']=='exited'and s['Running']is False and s['Pid']==0 and s['OOMKilled']is False,'actual original stopped/noExec/noOOM image660 CID')
  O.need(h['Memory']==h['MemorySwap']==(8 if stage=='cpu-preflight'else 32)*2**30 and h['ReadonlyRootfs']is True,'original actual CPU8/model32 scope')
  later=next(z for z in post_states if z['Id']==row['cid']);O.need(later['State']==s and later.get('ExecIDs')==v.get('ExecIDs'),'same original posthash release state, not a stale cleanup alone')
  if stage=='cpu-preflight':O.need(h['Devices']==[]and not h.get('DeviceRequests'),'original CPU Devices[]')
  labels=v['Config']['Labels'];O.need(labels['model-tuning-lab.owner']=='NEW24H_FIRSTDECODE101R23payloadcontract_001'and labels['model-tuning-lab.arm']==stage and labels['model-tuning-lab.source-manifest-sha256']==e['source']['sha256'],'actual original source/owner/stage labels')
  cids.append(row['cid'])
 O.need(e['journal']['path']==(LEAF.parent/'MODEL_SNAPSHOTS_LEDGER.R23payloadcontract.json').as_posix()and journal['source']==e['source']and journal['payload_source']==PAYLOAD and journal['leaf']==LEAF.as_posix()and journal['combined_opt_root']==OPT.as_posix(),'same exact original R23 snapshot journal')
 O.need(p['storage']['model_snapshots_reservation_ref']==e['journal'],'same final original journal Ref')
 O.need((journal['budget_bytes'],journal['payload_total_cap_bytes'],journal['opt_total_cap_bytes'],journal['allocated_worker_cap_bytes'])==(32*2**30,30*2**30,2*2**30,15*2**29)and journal['legacy_ledger_written']is journal['numeric_qualified']is False,'old budget/ledger/qualification untouched')
 return dict(schema='deltalog.released-empty-r23-created-candidate/v1',original_refs=e,original_primary=PRIMARY,created_cids=cids,candidate_created=True,prior_lease_terminal=True,numeric_qualified=False,old_journal_not_rewritten=True)
def refs(O,er):
 proof=documents(O,er);e=proof['original_refs'];out=[er,e['source'],TEMPLATE,COMMANDS,e['owner'],e['journal'],*e['cleanups'].values()]
 for r in e['cleanups'].values():
  c=O.obj(r);out.extend(c[k]for k in('before_inspect','stop_receipt','after_inspect','release_smi'))
 return out
def empty(O):
 a=LEAF.lstat();O.need(stat.S_ISDIR(a.st_mode)and a.st_nlink==2 and not any(LEAF.iterdir())and not any(p.is_symlink()for p in(LEAF,*LEAF.parents)),'actual ordinary R23 payload EMPTY; no firstdecode captured')
 O.need((OPT/'candidate').is_dir()and not(OPT/'candidate').is_symlink(),'R23 candidate actually existed; do not assert no-candidate')
 return list(getattr(a,k)for k in FIELDS)
def observe(O,K,er,expected=None):
 proof=documents(O,er);a=empty(O)
 if expected is not None:O.need(expected==dict(proof,empty_metadata=a,actual_payload_bytes=0),'same original bind-frozen R23 EMPTY identity')
 ns=dict(K.__dict__,SOURCE=proof['original_refs']['source'],PHASES=('payload','control'),leaf=lambda i:(LEAF,OPT)[i]);scan=types.FunctionType(K.no_writers.__code__,ns,'no_writers',K.no_writers.__defaults__,K.no_writers.__closure__);scan()
 inspect=types.FunctionType(K.inspect_all.__code__,dict(K.__dict__,CIDS=(tuple(proof['created_cids']),)),'inspect_all',K.inspect_all.__defaults__,K.inspect_all.__closure__);states=inspect();O.need({r['Id']for r in states}==set(proof['created_cids'])and empty(O)==a,'fresh both stopped CIDs and unchanged ordinary EMPTY payload')
 return dict(proof,empty_metadata=a,actual_payload_bytes=0)
def bind(O,K,er):return observe(O,K,er)
def validate(O,K,er,expected):return observe(O,K,er,expected)
