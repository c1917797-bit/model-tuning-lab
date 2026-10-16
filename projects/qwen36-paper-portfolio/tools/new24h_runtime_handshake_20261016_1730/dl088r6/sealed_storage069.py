"""Source-bound closed-phase storage evidence; never deletes old data/ledgers."""
import hashlib,json,os,stat
from pathlib import Path
EXPECTED=('run-cpu-MAIN-20261016-NEW24H-001','run-numeric16-MAIN-20261016-NEW24H-001','run-recovery066-MAIN-20261016-NEW24H-001')
TARGET='lgw_a6109c51076a4a2c9d2674ca5a8704a0'
OLDROOT='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-split-scale-numeric-new24h-v1-061'
RECOVERYROOT='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog061-runtime-source-recovery-new24h-v1-066'
def need(x,m):
 if not x:raise ValueError(m)
def exact_ref(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'},'exactRef3');p=Path(r['path']);need(p.is_absolute()and all(not x.is_symlink()for x in(p,*p.parents))and p.is_file(),'ordinary reference');a=p.stat();h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 z=p.stat();need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns)and z.st_size==r['bytes']and h.hexdigest()==r['sha256'],'stable exact reference');return p
def read(r):return json.loads(exact_ref(r).read_bytes())
def ref(p):
 p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def tree(root,full):
 root=Path(root);need(root.is_dir()and all(not x.is_symlink()for x in(root,*root.parents)),'closed real phase');dev=root.stat().st_dev;rows=[]
 for parent,dirs,files in os.walk(root,followlinks=False):
  for n in sorted(dirs+files):
   p=Path(parent)/n;s=p.lstat();need(not stat.S_ISLNK(s.st_mode)and s.st_dev==dev,'closed tree no symlink/FS escape')
   if p.is_dir():continue
   need(stat.S_ISREG(s.st_mode),'ordinary closed evidence only');row=dict(relative_path=p.relative_to(root).as_posix(),bytes=s.st_size,mtime_ns=s.st_mtime_ns,inode=s.st_ino,device=s.st_dev)
   if full:
    r=ref(p);exact_ref(r);row['sha256']=r['sha256']
   rows.append(row)
 return sorted(rows,key=lambda x:x['relative_path'])
def verify_closed(row,full=False):
 snap=read(row['tree_ref']);need(snap['root']==row['leaf']and type(snap['files'])is list,'exact closed tree snapshot')
 actual=tree(row['leaf'],full)
 expected=snap['files']if full else[{k:v for k,v in r.items()if k!='sha256'}for r in snap['files']]
 need(actual==expected and sum(x['bytes']for x in actual)==row['frozen_bytes'],'closed phase changed: stop retain, no credit')
 return row['frozen_bytes']
def no_old_commands():
 found=[];count=0
 for proc in Path('/proc').iterdir():
  if not proc.name.isdigit():continue
  count+=1;need(count<=16384,'bounded complete process scan')
  try:
   with(proc/'cmdline').open('rb')as f:raw=f.read(65537)
  except FileNotFoundError:continue
  need(len(raw)<=65536,'bounded process command proof')
  tokens=raw.split(b'\0')
  if any(t.startswith((OLDROOT+'/').encode())or t.startswith((RECOVERYROOT+'/').encode())for t in tokens):found.append(int(proc.name))
 need(not found,'old061/066 phase command still active; no writer seal')
 return dict(complete_scan=True,matched_owned_commands=[],processes_examined=count,foreign_command_values_retained=False)
def verify_terminal(phase,read_json=read):
 owner=read_json(phase['owner_ref']);need(owner['stopped_retained']is True and not owner['secondary'],'actual owner terminal/release')
 releases=[read_json(r)for r in phase['cleanup_refs']];need(releases,'actual cleanup evidence')
 for c in releases:need(c['resource_release_verified']is c['stopped']is c['retained']is True and not c['errors']and c['unresolved_active_cid']is None,'actual all created containers stop retain release')
 name=Path(phase['leaf']).name
 need(name in EXPECTED,'only exact authorized closed phase names')
 expected=[]
 for relative in(('numeric/create-receipt.json','native/create-receipt.json')if name==EXPECTED[1]else('native/create-receipt.json',)):
  value=json.loads((Path(phase['leaf'])/relative).read_bytes());cid=value['stdout'].strip();need(len(cid)==64 and all(x in'0123456789abcdef'for x in cid),'actual source-owned create CID');expected.append(cid)
 states=[]
 for rr in phase['container_state_refs']:
  value=read_json(rr);rows=json.loads(value['stdout'])if type(value)is dict and 'stdout'in value else value
  need(type(rows)is list,'actual docker inspect list')
  for row in rows:
   st=row['State'];need(row['Id']in expected and not row.get('ExecIDs')and st['Running']is False and st['Pid']==0 and st['ExitCode']==0 and st.get('OOMKilled',False)is False and st['Status']=='exited','every original source-created container terminal, not live/reused/unresolved')
   states.append(row['Id'])
 need(len(set(expected))==len(expected)and sorted(states)==sorted(expected),'all original created CIDs, no omitted/extra inspect')
 if phase.get('operation_terminal_ref')is None:
  need(name==EXPECTED[0]and phase['owner_ref']['bytes']==1357 and phase['owner_ref']['sha256']=='649feda29cd60da14dc2c133be4ebcee4b8119177f0cd84d54ee43503a344f45'and owner['primary']is None,'only actual CPU09bc missing cached operation has explicit owner+cleanup+fresh no-command compensation')
 else:
  t=read_json(phase['operation_terminal_ref']);need(t['schema']=='ascend.actual-operation-terminal-observation/v1','actual cached tool terminal observation schema');q=t['operation_snapshot'];op=q['operation'];record=op['result']['record']
  expected_exit=3 if name==EXPECTED[1]else 0
  need(q['found']is q['terminal']is True and q['status']=='completed'and q['kind']=='exec'and op['ok']is True and op['routeDecision']=='peer_direct'and op['targetPeerId']==TARGET,'actual completed peer-direct transport, not command success or fresh not_found')
  need(record['state']=='completed'and type(record['exitCode'])is int and record['exitCode']==expected_exit and q['ok']is(expected_exit==0)and not record['timedOut']and not record['cancelled']and record['command']=='/usr/bin/python3','exact old phase exit3 failure or exit0 CPU terminal record; no success relabel')
  need((owner['primary']is not None)if expected_exit else(owner['primary']is None),'actual owner failure/success agrees with preserved command exit')
  args=record['args'];script=RECOVERYROOT+'/run_recovery.py'if name==EXPECTED[2]else OLDROOT+'/run052.py';kind='numeric16'if name==EXPECTED[1]else'cpu'
  need(args[:3]==['-I','-B',script]and args.count('--phase')==1 and args[args.index('--phase')+1]==kind,'exact actual owner entry and phase')
  lines=[line.split('MAIN_DLLIFECYCLE002_OWNER ',1)[1]for line in record['stdout'].splitlines()if line.startswith('MAIN_DLLIFECYCLE002_OWNER ')];need(len(lines)==1 and json.loads(lines[0])==phase['owner_ref'],'actual operation output joins exact owner Ref')
 no_old_commands()
 return True
def validate_evidence(r,root,authority_ref,*,full=True):
 e=read(r);need(e['schema']=='deltalog.closed-phase-storage-evidence/v069'and e['root']==str(root)and e['authority_ref']==authority_ref,'exact authorized storage evidence')
 ledger=read(e['baseline_ledger_ref']);need(ledger['root']==str(root)and ledger['authority_ref']==authority_ref,'same historical ledger authority')
 need([Path(x['leaf']).name for x in e['phases']]==list(EXPECTED),'only three explicitly authorized completed phases')
 for row in e['phases']:
  need(Path(row['leaf']).parent==root and any(r['leaf']==row['leaf']for r in ledger['reservations']),'closed phase was actually reserved')
  verify_terminal(row);verify_closed(row,full)
 return e,ledger
def generations(root):
 rows=list(Path(root).glob('STORAGE_LEDGER061.*.json'));rows.sort(key=lambda p:int(p.name.split('.')[1]));return rows
def seal_generation(evidence_ref,root,authority_ref,template_ref):
 import fcntl
 e,ledger=validate_evidence(evidence_ref,root,authority_ref,full=True);fd=os.open(root/'.storage061.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
 try:
  fcntl.flock(fd,fcntl.LOCK_EX);items=generations(root);need(items and ref(items[-1])==e['baseline_ledger_ref'],'latest old ledger unchanged before seal')
  value=dict(ledger,sealed_evidence_ref=evidence_ref,storage069_template_ref=template_ref,previous_ledger_ref=e['baseline_ledger_ref'])
  target=root/('STORAGE_LEDGER061.%d.json'%(int(items[-1].name.split('.')[1])+1));data=(json.dumps(value,sort_keys=True)+'\n').encode()
  with target.open('xb')as f:f.write(data);f.flush();os.fsync(f.fileno())
  d=os.open(root,os.O_RDONLY);os.fsync(d);os.close(d);return ref(target)
 finally:os.close(fd)
def chain(root,e,template_ref,evidence_ref):
 items=generations(root);baseline=exact_ref(e['baseline_ledger_ref']);need(baseline in items,'historical baseline retained');before=e['baseline_ledger_ref'];start=items.index(baseline)
 for p in items[start+1:]:
  v=json.loads(p.read_bytes());need(v['previous_ledger_ref']==before and v['storage069_template_ref']==template_ref and v['sealed_evidence_ref']==evidence_ref,'no unknown/old-helper ledger advancement after seal');before=ref(p)
 need(len(items)>start+1,'actual separate seal generation required');return before
def install(storage,r,authority_ref,source_ref):
 e,baseline=validate_evidence(r,storage.ROOT,authority_ref,full=True)
 chain(storage.ROOT,e,source_ref,r);storage._seal_context=dict(template_ref=source_ref,evidence_ref=r)
 original_reserved=storage.reserved
 def historical_rows(ledger):
  rows=ledger['reservations'];need(type(rows)is list and len({x['leaf']for x in rows})==len(rows),'unique historical reservation rows')
  for x in rows:need(set(x)=={'leaf','stage','budget_bytes'}and x['stage']in('cpu','numeric')and x['budget_bytes']==(33 if x['stage']=='numeric'else 1)*storage.GIB and type(x['budget_bytes'])is int and Path(x['leaf']).parent==storage.ROOT,'unchanged historical fixed phase budget')
  return sum(x['budget_bytes']for x in rows)
 def effective(root,ledger):
  chain(root,e,source_ref,r)
  historical_rows(ledger);rows=ledger['reservations'];need(rows[:len(baseline['reservations'])]==baseline['reservations'],'historical ledger rows never edited')
  for phase in e['phases']:verify_closed(phase,False)
  total,amounts=storage.scan(root,[Path(x['leaf'])for x in rows]);closed={x['leaf']:x['frozen_bytes']for x in e['phases']}
  budgets=[closed.get(x['leaf'],x['budget_bytes'])for x in rows]
  return total,storage.committed_bytes(total,amounts,budgets)
 storage.reserved=historical_rows;storage.commitment=effective
 return dict(schema='deltalog.storage-seal-runtime/v069',evidence_ref=r,baseline_ledger_ref=e['baseline_ledger_ref'],source=source_ref,full_initial_hash_verified=True,old_ledger_unchanged=True)
def final_verify(evidence_ref):
 e=read(evidence_ref)
 for row in e['phases']:verify_terminal(row);verify_closed(row,True)
 return True
