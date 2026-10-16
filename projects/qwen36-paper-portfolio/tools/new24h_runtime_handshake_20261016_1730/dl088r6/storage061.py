"""One experiment tree, one retained reservation ledger; no service/FS changes."""
import json,os,shutil,stat
from pathlib import Path
ROOT=Path('/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061')
GIB=1024**3;LIMIT=80*GIB;FREE=100*GIB
def need(x,m):
 if not x:raise ValueError(m)
def authority(r,read):
 from window056 import AUTH
 a=read(r)
 need(set(r)=={'path','bytes','sha256'}and a['schema']=='ascend.paper-experiment.storage-authority/v1'and a['output_root']==str(ROOT)and type(a['max_total_bytes'])is int and a['max_total_bytes']==LIMIT and type(a['min_free_bytes'])is int and a['min_free_bytes']==FREE and a['current_authority_ref']==AUTH,'exact explicit user storage authorization')
 return a
def scan(root,phase_roots=()):
 root=Path(root);need(root.is_dir()and all(not p.is_symlink()for p in(root,*root.parents)),'real nonsymlink experiment root');dev=root.stat().st_dev;total=0;amounts=[0 for _ in phase_roots]
 for parent,dirs,files in os.walk(root,followlinks=False):
  for name in dirs+files:
   p=Path(parent)/name;s=p.lstat();need(not stat.S_ISLNK(s.st_mode)and s.st_dev==dev,'no symlink/other filesystem in experiment tree')
   if stat.S_ISREG(s.st_mode):
    total+=s.st_size
    for i,phase in enumerate(phase_roots):
     if p.is_relative_to(phase):amounts[i]+=s.st_size
   else:need(stat.S_ISDIR(s.st_mode),'ordinary experiment files only')
 return total,amounts
def usage(root):return scan(root)[0]
def check(root=ROOT,*,free=None):
 available=shutil.disk_usage(root).free if free is None else free
 generations=list(Path(root).glob('STORAGE_LEDGER061.*.json'));generations.sort(key=lambda p:int(p.name.split('.')[1]))
 ledger=json.loads(generations[-1].read_bytes())if generations else dict(reservations=[])
 used,committed=commitment(root,ledger)
 need(used<=LIMIT and committed<=LIMIT and available>=FREE,'experiment total/commitment80GiB/live filesystem free100GiB')
 return dict(root=str(root),used_bytes=used,committed_bytes=committed,max_total_bytes=LIMIT,filesystem_free_bytes=available,min_free_bytes=FREE,scope='application-observed, not kernel filesystem quota')
def reserved(ledger):
 rows=ledger['reservations'];need(type(rows)is list,'reservation rows');seen=set();total=0
 for row in rows:
  need(set(row)=={'leaf','stage','budget_bytes'}and row['stage']in('cpu','numeric')and Path(row['leaf']).parent==ROOT and row['leaf']not in seen,'exact unique owned reservation')
  expected=(33 if row['stage']=='numeric'else 1)*GIB
  need(type(row['budget_bytes'])is int and row['budget_bytes']==expected,'fixed stage allocation');seen.add(row['leaf']);total+=expected
 need(total<=LIMIT,'combined reservations80GiB');return total
def committed_bytes(total,phase_actual,budgets):
 need(type(total)is int and total>=0 and len(phase_actual)==len(budgets)and all(type(x)is int and x>=0 for x in phase_actual+budgets),'nonnegative actual/budget byte counts')
 untracked=total-sum(phase_actual);need(untracked>=0,'one whole-root snapshot covers every unique phase')
 return untracked+sum(max(a,b)for a,b in zip(phase_actual,budgets))
def commitment(root,ledger):
 reserved(ledger);rows=ledger['reservations'];total,amounts=scan(root,[Path(r['leaf'])for r in rows])
 return total,committed_bytes(total,amounts,[r['budget_bytes']for r in rows])
def reserve(root,leaf,stage,read,auth_ref,*,free=None):
 authority(auth_ref,read);root=Path(root);need(root==ROOT and Path(leaf).parent==root and not Path(leaf).exists(),'one exact new authorized root/leaf')
 import fcntl
 lock=root/'.storage061.lock'
 fd=os.open(lock,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
 try:
  fcntl.flock(fd,fcntl.LOCK_EX);proof=check(root,free=free);generations=list(root.glob('STORAGE_LEDGER061.*.json'))
  generations.sort(key=lambda p:int(p.name.split('.')[1]));p=generations[-1]if generations else None
  if p is not None:
   need(not p.is_symlink(),'ledger regular');ledger=json.loads(p.read_bytes());need(ledger['authority_ref']==auth_ref and ledger['root']==str(ROOT),'same immutable storage authority/root')
  else:ledger=dict(schema='deltalog.storage-reservations/v061',root=str(ROOT),authority_ref=auth_ref,reservations=[])
  budget=(33 if stage=='numeric'else 1)*GIB
  need(stage in('numeric','cpu')and not any(x['leaf']==str(leaf)for x in ledger['reservations']),'one retained phase reservation')
  need(commitment(root,ledger)[1]+budget<=LIMIT,'untracked actual plus cumulative phase commitments80GiB')
  need(proof['filesystem_free_bytes']>=FREE+budget,'preserve100GiB after full phase allocation')
  ledger['reservations'].append(dict(leaf=str(leaf),stage=stage,budget_bytes=budget))
  # Immutable retained generations; partial writes reject, never overwrite/release.
  generation=root/('STORAGE_LEDGER061.%d.json'%(max([int(x.name.split('.')[1])for x in root.glob('STORAGE_LEDGER061.*.json')],default=0)+1))
  need('_seal_context'in globals(),'explicit069 seal context before reservation')
  import sealed_storage069 as seal069
  ledger.update(previous_ledger_ref=seal069.ref(p),storage069_template_ref=_seal_context['template_ref'],sealed_evidence_ref=_seal_context['evidence_ref'])
  data=json.dumps(ledger,sort_keys=True).encode();need(commitment(root,ledger)[1]+len(data)<=LIMIT,'new retained ledger bytes included in total commitment')
  with generation.open('xb')as f:f.write(data);f.flush();os.fsync(f.fileno())
  d=os.open(root,os.O_RDONLY);os.fsync(d);os.close(d)
  return dict(proof,reservation=ledger['reservations'][-1],reserved_total_bytes=sum(x['budget_bytes']for x in ledger['reservations']))
 finally:os.close(fd)
