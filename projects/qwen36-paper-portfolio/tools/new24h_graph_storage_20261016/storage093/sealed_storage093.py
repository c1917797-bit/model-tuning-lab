"""Second explicit retained seal. Storage evidence only; never numerical promotion."""
import hashlib,importlib.util,json,os,sys
from pathlib import Path
ROOT=Path('/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061')
GIB=2**30
BASE={'path':ROOT.as_posix()+'/STORAGE_LEDGER061.7.json','bytes':2005,'sha256':'cf2771c6dd1f4621e3ee597207a1b87f02111eb2ac2567fb9a89c143c8d0055c'}
OLD={'path':'/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-split-scale-numeric-new24h-v1-069-repair1/sealed_storage069.py','bytes':10617,'sha256':'897999182145efb9088855c2059a94d9ae0fcc28e6666d842fec65013aef9304'}
SOURCE={'path':'/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-split-scale-numeric-new24h-v1-069-repair1/SOURCE_MANIFEST.json','bytes':52969,'sha256':'b9cb456d960072d8e6730bb5307dcabfc83b3ad7bffd9d3476d9b92220048f21'}
NAMES=tuple('run-'+s+'-MAIN-20261016-NEW24H-069-repair1-001'for s in('cpu','numeric16','numeric160'))
CIDS=(('d18c0b2a72c94acc19d6905d26b4dd56a9957c91dd171c601bf42e70a69473b5',),('3ad8b0e22b0476b0d36f296fec930387022ad7ca14e5b207560a573bb4a6da32','83f11b18404864b9f2d93083ad72466bad2513dcc469de2cdacdeafe0b32ed34'),('337f3b695e881874b23f1c173eaed46fe3994c7bb41db9c6c64cb86cdf60e642','c840b0455fe2e58b1a56ad3c4f36d75254c40a9ca338d1a4110ccf715f724e91'))
EXITS=((0,),(0,0),(1,0))
OWNER_PINS=((1386,'54e38927342aa9c4e443cbde798768e46a421afc3fb1ba7c8e220aa3842ed3cd'),(1620,'e98523737a3b87244625bb1a9241a8d92fb6695d0b5f059751e4a9a7b441a8f9'),(1469,'412680c3460d4921f32edd3a0cf467186f8639d16e07ee0a1b5e89cdfed513e1'))
OPERATIONS=('exec-0000000000000a40','exec-0000000000000a49','exec-0000000000000a58')
def need(x,m):
 if not x:raise ValueError(m)
def old():
 p=Path(OLD['path']);need(ref(p)==OLD,'exact original seal implementation')
 key='_sealed069_original093'
 if key not in sys.modules:
  m=importlib.util.module_from_spec(s:=importlib.util.spec_from_file_location(key,p));sys.modules[key]=m;s.loader.exec_module(m)
 return sys.modules[key]
def ref(p):
 p=Path(p);need(p.is_absolute()and p.is_file()and all(not x.is_symlink()for x in(p,*p.parents)),'ordinary absolute exact file');a=p.stat();h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 z=p.stat();need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns),'stable reference')
 return dict(path=str(p),bytes=z.st_size,sha256=h.hexdigest())
def read(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and ref(r['path'])==r,'exact Ref3');return json.loads(Path(r['path']).read_bytes())
def unavailable(r):
 vv=read(r);need(type(vv)is list and len(vv)==3,'actual three unavailable observations')
 for i,v in enumerate(vv):
  q=v['snapshot'];need(v['operationId']==q['operationId']==OPERATIONS[i]and q['schema']=='agentweb.operation/v1'and q['found']is False and q['status']==q['phase']=='not_found'and q['retryable']is False and q['result']is None and q['operation']['routeDecision']=='peer_direct'and q['operation']['targetPeerId']=='lgw_a6109c51076a4a2c9d2674ca5a8704a0','actual correct-peer not_found, not completed operation')
 return vv
def no_writers():
 O=old();O.no_old_commands();count=0
 prefix=str(Path(SOURCE['path']).parent)+'/'
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  count+=1;need(count<=16384,'bounded full proc scan')
  try:
   with(p/'cmdline').open('rb')as f:b=f.read(65537)
  except FileNotFoundError:continue
  need(len(b)<=65536 and not any(t.startswith(prefix.encode())or any(n.encode()in t for n in NAMES)for t in b.split(b'\0')),'no active original069 source/run command')
 return True
def rows(ledger):
 rr=ledger['reservations'];need(type(rr)is list and len({x['leaf']for x in rr})==len(rr),'unique historical rows')
 for x in rr:need(set(x)=={'leaf','stage','budget_bytes'}and x['stage']in('cpu','numeric')and type(x['budget_bytes'])is int and x['budget_bytes']==(1 if x['stage']=='cpu'else 33)*GIB and Path(x['leaf']).parent==ROOT,'unchanged reservation allocation')
 return rr
def prefix_chain(base):
 O=old();e,baseline=O.validate_evidence(base['sealed_evidence_ref'],ROOT,base['authority_ref'],full=True)
 items=O.generations(ROOT);start=items.index(O.exact_ref(e['baseline_ledger_ref']));end=items.index(O.exact_ref(BASE));before=e['baseline_ledger_ref'];need(end>start,'existing original seal generation')
 for p in items[start+1:end+1]:
  v=read(ref(p));need(v['previous_ledger_ref']==before and v['sealed_evidence_ref']==base['sealed_evidence_ref']and v['storage069_template_ref']==base['storage069_template_ref'],'retain original seal prefix exactly');rows(v);need(v['reservations'][:len(baseline['reservations'])]==baseline['reservations'],'old rows unchanged');before=ref(p)
 return e
def verify_terminal(p,i):
 O=old();need(p['leaf']==(ROOT/NAMES[i]).as_posix(),'exact completed069 leaf');need(p['owner_ref']==dict(path=(ROOT/NAMES[i]/'RESULT.json').as_posix(),bytes=OWNER_PINS[i][0],sha256=OWNER_PINS[i][1]),'exact observed original owner');o=read(p['owner_ref']);need(o['schema']=='deltalog.diagnostic-owned-host/v035'and o['source']==SOURCE and o['target_source']==SOURCE and o['stopped_retained']is True and not o['secondary'],'actual same-source released owner')
 stages=('native',)if i==0 else('native','numeric')
 need([r['path']for r in p['cleanup_refs']]==[(ROOT/NAMES[i]/stage/'cleanup-verdict.json').as_posix()for stage in stages],'each exact original stage cleanup, no omission/duplicate')
 need(o['stage']==('cpu'if i==0 else'numeric')and o['steps']==(160 if i==2 else 16)and((o['primary']is None)==(i!=2)),'preserve actual owner stage and original consumer failure')
 for r in p['cleanup_refs']:
  v=read(r);need(v['resource_release_verified']is v['stopped']is v['retained']is True and not v['errors']and v['unresolved_active_cid']is None,'all created containers retained/released')
 need(len(p['cleanup_refs'])==len(CIDS[i]),'all stage cleanup receipts')
 actual=[]
 for j,stage in enumerate(('native',)if i==0 else('native','numeric')):
  c=read(p['create_refs'][j]);need(p['create_refs'][j]['path']==(ROOT/NAMES[i]/stage/'create-receipt.json').as_posix()and c['stdout'].strip()==CIDS[i][j],'exact source-created CID')
 for rr in p['container_state_refs']:
  for v in read(rr):
   cid=v['Id'];need(cid in CIDS[i]and cid not in actual,'no foreign/duplicate inspect');j=CIDS[i].index(cid);s=v['State'];need(s['Status']=='exited'and s['Running']is False and s['Pid']==0 and s['ExitCode']==EXITS[i][j]and s.get('OOMKilled',False)is False and not v.get('ExecIDs'),'exact quiescent container; consumer exit1 remains failure');actual.append(cid)
 need(sorted(actual)==sorted(CIDS[i]),'complete exact CID closure')
 if p.get('operation_terminal_ref')is None:
  q=read(p['quiescent_ref']);need(q['schema']=='deltalog.actual-quiescent-closure/v093'and q['source']==SOURCE and q['leaf']==p['leaf']and q['owner_ref']==p['owner_ref']and q['historical_operation_receipt_unavailable']is True and q['historical_operation_exit_claimed']is False and q['no_original_commands']is True and q['no_open_write_fds_or_shared_writable_maps']is True and q['two_full_hashes_equal']is True,'explicit new quiescent scope, never fabricated historical terminal')
  unavailable(q['operation_unavailable_ref']);need(q['unavailable_operation_id']==OPERATIONS[i],'exact missing operation association');snap=read(p['tree_ref']);need(q['first_tree_ref']==p['tree_ref']and read(q['second_tree_ref'])==snap,'two independent complete stable tree hashes');no_writers();return True
 t=read(p['operation_terminal_ref']);need(t['schema']=='ascend.actual-operation-terminal-observation/v1','real original operation terminal required, no projected substitute');q=t['operation_snapshot'];op=q['operation'];r=op['result']['record'];code=(0,0,3)[i]
 need(q['found']is q['terminal']is True and q['status']=='completed'and q['kind']=='exec'and op['ok']is True and op['routeDecision']=='peer_direct'and op['targetPeerId']==O.TARGET,'actual cached completed operation')
 need(r['state']=='completed'and r['exitCode']==code and q['ok']is(code==0)and not r['timedOut']and not r['cancelled']and r['command']=='/usr/bin/python3','preserved original operation exit')
 a=r['args'];need(a[:3]==['-I','-B',str(Path(SOURCE['path']).parent/'run052.py')]and a.count('--phase')==1 and a[a.index('--phase')+1]==('cpu','numeric16','numeric160')[i],'actual original069 CLI phase')
 lines=[x.split('MAIN_DLLIFECYCLE002_OWNER ',1)[1]for x in r['stdout'].splitlines()if x.startswith('MAIN_DLLIFECYCLE002_OWNER ')];need(len(lines)==1 and json.loads(lines[0])==p['owner_ref']and((o['primary']is None)==(code==0)),'exact published owner and preserved failure')
 no_writers();return True
def validate(evidence,auth,full=True):
 e=read(evidence);need(e['schema']=='deltalog.closed-phase-storage-evidence/v093'and e['root']==str(ROOT)and e['authority_ref']==auth and e['baseline_ledger_ref']==BASE,'exact second-seal baseline/auth')
 source=read(e['source_manifest_ref']);need(source['schema']=='deltalog.closed-storage-source/v093'and source['files']['sealed_storage093.py']==ref(__file__),'actual collector source manifest joins helper')
 base=read(BASE);need(base['authority_ref']==auth and len(rows(base))==6,'exact six historical reservations');prior=prefix_chain(base);need(e['prior_evidence_ref']==base['sealed_evidence_ref'],'prior seal retained')
 need([p['leaf']for p in e['phases']]==[str(ROOT/n)for n in NAMES],'only three new finished phases')
 for i,p in enumerate(e['phases']):verify_terminal(p,i);old().verify_closed(p,full)
 need([p['leaf']for p in prior['phases']+e['phases']]==[r['leaf']for r in base['reservations']],'all six phases covered without edit')
 return e,base,prior['phases']+e['phases']
def chain(e,template,evidence):
 O=old();items=O.generations(ROOT);idx=items.index(O.exact_ref(BASE));before=BASE;previous=read(BASE);need(len(items)>idx+1,'separate actual093 seal required')
 for ordinal,p in enumerate(items[idx+1:],8):
  need(p.name=='STORAGE_LEDGER061.%d.json'%ordinal,'no missing/unknown ledger generation')
  v=read(ref(p));need(v['previous_ledger_ref']==before and v['sealed_evidence_ref']==evidence and v['storage069_template_ref']==template,'no unknown generation or writer advance');rr=rows(v);prior=rows(previous);need(rr[:len(prior)]==prior and len(rr)in(len(prior),len(prior)+1),'append-only historical rows');need(v['root']==previous['root']and v['authority_ref']==previous['authority_ref'],'same root/authority');before=ref(p);previous=v
 return before
def seal_generation(evidence,root,auth,template):
 import fcntl
 source=read(template);need(source['schema']=='deltalog.closed-storage-source/v093'and source['files']['sealed_storage093.py']==ref(__file__),'reviewed exact093 helper source');need(Path(root)==ROOT,'exact storage root');fd=os.open(ROOT/'.storage061.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
 try:
  fcntl.flock(fd,fcntl.LOCK_EX);e,base,_=validate(evidence,auth,True);need(e['source_manifest_ref']==template,'same reviewed collector/seal source');items=old().generations(ROOT);need(ref(items[-1])==BASE,'only fresh ledger7 may seal');v=dict(base,previous_ledger_ref=BASE,sealed_evidence_ref=evidence,storage069_template_ref=template);data=(json.dumps(v,sort_keys=True)+'\n').encode();p=ROOT/('STORAGE_LEDGER061.%d.json'%(int(items[-1].name.split('.')[1])+1))
  import shutil
  used=sum(x['bytes']for x in old().tree(ROOT,False));need(used+len(data)<=80*GIB and shutil.disk_usage(ROOT).free>=100*GIB+len(data),'retained seal bytes charged80/free100')
  with p.open('xb')as f:f.write(data);f.flush();os.fsync(f.fileno())
  d=os.open(ROOT,os.O_RDONLY);os.fsync(d);os.close(d);return ref(p)
 finally:os.close(fd)
def install(storage,evidence,auth,template):
 source=read(template);need(source['schema']=='deltalog.closed-storage-source/v093'and source['files']['sealed_storage093.py']==ref(__file__),'reviewed exact093 helper source');need(storage.ROOT==ROOT and storage.LIMIT==80*GIB and storage.FREE==100*GIB,'original80/100 unchanged');e,base,closed=validate(evidence,auth,True);need(e['source_manifest_ref']==template,'same reviewed collector/runtime seal source');chain(e,template,evidence);storage._seal_context=dict(template_ref=template,evidence_ref=evidence)
 def historical(ledger):return sum(x['budget_bytes']for x in rows(ledger))
 def commitment(root,ledger):
  need(Path(root)==ROOT,'same filesystem scope');chain(e,template,evidence);rr=rows(ledger);need(rr[:6]==base['reservations'],'six old rows never edited')
  for p in closed:old().verify_closed(p,False)
  total,actual=storage.scan(root,[Path(x['leaf'])for x in rr]);frozen={p['leaf']:p['frozen_bytes']for p in closed};return total,storage.committed_bytes(total,actual,[frozen.get(x['leaf'],x['budget_bytes'])for x in rr])
 storage.reserved=historical;storage.commitment=commitment
 return dict(schema='deltalog.storage-seal-runtime/v093',source=template,evidence_ref=evidence,baseline_ledger_ref=BASE,closed_phase_count=6,numerical_qualification=False)
def final_verify(evidence):
 e=read(evidence);validate(evidence,e['authority_ref'],True);chain(e,e['source_manifest_ref'],evidence);return True
