"""Explicit third retained-storage seal. Never numerical promotion."""
import argparse,hashlib,importlib.util,json,os,stat,subprocess,sys,time
from pathlib import Path
ROOT=Path('/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061');G=2**30
BASE=dict(path=str(ROOT/'STORAGE_LEDGER061.11.json'),bytes=2480,sha256='b751253b285b5e2890aafe0beda89ddf17bdcc69f03db70f03c655c1ff98e2b4')
SOURCE=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-sameinitial-native-contract-new24h-v1-088-repair2/SOURCE_MANIFEST.json',bytes=56939,sha256='78c1c11ef1781a86c6a5a9d1f8d7c2b4d62dbf66754f264fa03e96b654bd9ec5')
PRIOR=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-closed-storage-new24h-v1-093/SOURCE_MANIFEST.json',bytes=5812,sha256='d0cb8fef914cb8a077a691ec19f23724dadc92d0a2a2dd1284f09321edcb1e88')
PHASES=('cpu','numeric16','numeric160')
CIDS=(('aeb0a1cdd31cb56b43585fcb78f951ccf0104739d3efa3152caaca95c755a071',),('43304f726fe9e55b6b4bd91bf318392c19bc5f9844e43dc04497953bcaffe1c6','fe8b1054b420f325e09cf6120e4eccb04c2e4f9d6cc3a7ca937f4c00c232e516'),('a936ea75ee468c39f1ddfebe77b0481c1c06eddad54a778828d39fcd2f33d8aa',))
OWNERS=((1402,'6a989d81dda695cb00bbfe20baea2075aaa9914ec5b147c5e59578eb07b9359a'),(1635,'27bf8c6234ec3b0f7d82e6340708768e8c3345eaba1e76fcf205b7f442138b71'),(1404,'46bd79009ff3373a5003651a887378f6ac98f6d35c35022402f0792717644b3a'))
def need(v,m):
 if not v:raise ValueError(m)
def leaf(i):return ROOT/('run-'+PHASES[i]+'-MAIN-20261016-NEW24H-088-repair2-001')
def ref(p):
 p=Path(p);need(p.is_file()and all(not x.is_symlink()for x in(p,*p.parents)),'ordinary exact input');a=p.stat();h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 z=p.stat();need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns),'stable streamed input');return dict(path=str(p),bytes=z.st_size,sha256=h.hexdigest())
def read(r):
 need(ref(r['path'])==r,'exact Ref3');need(r['bytes']<16*2**20,'bounded JSON metadata');return json.loads(Path(r['path']).read_bytes())
def write(p,v):
 b=(json.dumps(v,sort_keys=True,allow_nan=False)+'\n').encode();need(len(b)<50*2**20,'bounded evidence')
 with Path(p).open('xb')as f:f.write(b);f.flush();os.fsync(f.fileno())
 return ref(p)
def load(r,n):
 read_guard=ref(r['path']);need(read_guard==r,'exact helper');s=importlib.util.spec_from_file_location(n,r['path']);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def prior():
 m=read(PRIOR);S=load(m['files']['sealed_storage093.py'],'_actual_prior093_119');base=read(BASE);e,b,closed=S.validate(base['sealed_evidence_ref'],base['authority_ref'],True)
 before=S.BASE;previous=read(before)
 for n in range(8,12):
  rr=ref(ROOT/('STORAGE_LEDGER061.%d.json'%n));v=read(rr);need(v['previous_ledger_ref']==before and v['storage069_template_ref']==PRIOR and v['sealed_evidence_ref']==base['sealed_evidence_ref'],'exact retained093 prefix');need(v['reservations'][:len(previous['reservations'])]==previous['reservations'],'append-only reservations');before=rr;previous=v
 need(before==BASE,'exact ledger11 prefix');return S,base,closed
def tree(p,full):
 p=Path(p);dev=p.stat().st_dev;rows=[]
 for d,ds,fs in os.walk(p,followlinks=False):
  for n in sorted(ds+fs):
   q=Path(d)/n;s=q.lstat();need(s.st_dev==dev and not stat.S_ISLNK(s.st_mode),'no links/filesystem escape')
   if stat.S_ISDIR(s.st_mode):continue
   need(stat.S_ISREG(s.st_mode),'ordinary retained files');r=dict(relative_path=q.relative_to(p).as_posix(),bytes=s.st_size,mtime_ns=s.st_mtime_ns,inode=s.st_ino,device=s.st_dev)
   if full:r['sha256']=ref(q)['sha256']
   rows.append(r)
 return sorted(rows,key=lambda r:r['relative_path'])
def no_writers():
 examined=0;prefix=str(Path(SOURCE['path']).parent).encode();paths=[str(leaf(i))for i in range(3)]
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  examined+=1;need(examined<=16384,'bounded full proc inventory')
  try:
   b=(p/'cmdline').read_bytes();need(len(b)<=65536,'bounded command')
   need(not any(t.startswith(prefix+b'/')or any(x.encode()in t for x in paths)for t in b.split(b'\0')),'original088 command still active')
   for fd in(p/'fd').iterdir():
    try:
     target=os.readlink(fd);info=(p/'fdinfo'/fd.name).read_text();flags=int(next(x.split()[1]for x in info.splitlines()if x.startswith('flags:')),8)
    except(FileNotFoundError,ProcessLookupError):continue
    need(not(any(target==x or target.startswith(x+'/')for x in paths)and flags&os.O_ACCMODE in(os.O_WRONLY,os.O_RDWR)),'open retained-tree write FD')
   for line in(p/'maps').read_text().splitlines():
    fields=line.split(maxsplit=5)
    if len(fields)==6:need(not('w'in fields[1]and fields[1].endswith('s')and any(fields[5]==x or fields[5].startswith(x+'/')for x in paths)),'shared writable retained-tree mapping')
  except(FileNotFoundError,ProcessLookupError):continue
  # Permission failures deliberately propagate, not interpreted as absence.
 return dict(processes_examined=examined,no_original_commands=True,no_open_write_FDs_or_shared_writable_maps=True)
def inspect_all():
 ids=[x for row in CIDS for x in row];argv=['/usr/bin/prlimit','--as=unlimited','--','/usr/bin/docker','inspect',*ids]
 r=subprocess.run(argv,capture_output=True,timeout=20);need(r.returncode==0 and len(r.stdout)<=2**20 and len(r.stderr)<=65536,'bounded actual Docker read');values=json.loads(r.stdout);out=[]
 need(len(values)==len(ids)and{v['Id']for v in values}==set(ids),'exact four original CIDs')
 for v in values:
  s=v['State'];need(not v.get('ExecIDs')and s['Status']=='exited'and s['Running']is False and s['Pid']==0 and s.get('OOMKilled')is False,'fresh independently stopped/noExec/noOOM original CID')
  out.append(dict(Id=v['Id'],State=s,ExecIDs=v.get('ExecIDs')))
 return sorted(out,key=lambda v:v['Id'])
def original_receipts():
 result=[]
 for i in range(3):
  p=leaf(i);owner=dict(path=str(p/'RESULT.json'),bytes=OWNERS[i][0],sha256=OWNERS[i][1]);o=read(owner);need(o['source']==o['target_source']==SOURCE and o['stopped_retained']is True and o['steps']==(160 if i==2 else 16),'unchanged exact owner')
  rr=[]
  for j,s in enumerate(('native',)if i==0 else('numeric','native')if i==1 else('numeric',)):
   cr=ref(p/s/'create-receipt.json');need(read(cr)['stdout'].strip()==CIDS[i][j],'actual source-created CID');cl=ref(p/s/'cleanup-verdict.json');c=read(cl);need(c['cid']==CIDS[i][j]and c['stopped']is True and c['retained']is True and c['unresolved_active_cid']is None,'own container stopped, never rewrite old release false')
   rr.append(dict(create_ref=cr,cleanup_ref=cl))
  result.append(dict(leaf=str(p),owner_ref=owner,receipts=rr,old_owner_primary=o['primary'],old_owner_secondary=o['secondary']))
 return result
def capture(out,sr):
 need(not out.exists()and out.parent==ROOT and out.name=='seal-evidence119-MAIN-001','unique authorized evidence leaf');S,base,closed=prior();read(SOURCE);receipts=original_receipts();f=os.statvfs(ROOT);need(sum(x['bytes']for x in tree(ROOT,False))+50*2**20<=80*G and f.f_bavail*f.f_frsize>=100*G+50*2**20,'evidence charged80/free100');out.mkdir();before=no_writers();states1=inspect_all();phases=[]
 for i in range(3):
  a=tree(leaf(i),True);b=tree(leaf(i),True);need(a==b,'two complete independent streamed tree hashes equal');r=write(out/('tree-'+PHASES[i]+'.json'),dict(root=str(leaf(i)),files=a));phases.append(dict(receipts[i],tree_ref=r,frozen_bytes=sum(x['bytes']for x in a)))
 states2=inspect_all();need(states1==states2,'independent stopped states stable');after=no_writers();need(ref(BASE['path'])==BASE,'ledger unchanged')
 return write(out/'EVIDENCE119.json',dict(schema='deltalog.closed-phase-storage-evidence/v119',source_manifest_ref=sr,root=str(ROOT),baseline_ledger_ref=BASE,authority_ref=base['authority_ref'],prior_source_ref=PRIOR,prior_evidence_ref=base['sealed_evidence_ref'],phases=phases,states_before=states1,states_after=states2,no_writer_before=before,no_writer_after=after,old_cleanup_failures_preserved=True,numerical_qualification=False))
def validate(er,sr):
 e=read(er);need(e['schema']=='deltalog.closed-phase-storage-evidence/v119'and e['source_manifest_ref']==sr and e['baseline_ledger_ref']==BASE and e['prior_source_ref']==PRIOR,'exact119 evidence');S,base,closed=prior();need(e['prior_evidence_ref']==base['sealed_evidence_ref']and e['authority_ref']==base['authority_ref'],'exact prior seal/auth');need(e['phases']and len(e['phases'])==3,'all three phases');receipts=original_receipts()
 for i,p in enumerate(e['phases']):
  need(all(p[k]==v for k,v in receipts[i].items()),'original failure receipts intact');t=read(p['tree_ref']);need(t['root']==str(leaf(i))and tree(leaf(i),True)==t['files']and p['frozen_bytes']==sum(x['bytes']for x in t['files']),'full retained tree unchanged')
 need(inspect_all()==e['states_before']==e['states_after'],'fresh independent stopped CID proof');no_writers();return e,base,closed+e['phases']
def seal(er,sr):
 import fcntl,shutil
 fd=os.open(ROOT/'.storage061.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
 try:
  fcntl.flock(fd,fcntl.LOCK_EX);e,base,closed=validate(er,sr);need(ref(sorted(ROOT.glob('STORAGE_LEDGER061.*.json'),key=lambda p:int(p.name.split('.')[1]))[-1])==BASE,'latest11 only; no racing reservation')
  v=dict(base,previous_ledger_ref=BASE,sealed_evidence_ref=er,storage069_template_ref=sr);need(sum(x['bytes']for x in tree(ROOT,False))+65536<=80*G and shutil.disk_usage(ROOT).free>=100*G+65536,'80hard/100free unchanged');return write(ROOT/'STORAGE_LEDGER061.12.json',v)
 finally:os.close(fd)
def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--mode',choices=['capture','validate','seal']);p.add_argument('--source-ref');p.add_argument('--evidence-ref');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return
 sr=json.loads(a.source_ref);m=read(sr);need(m['files']['sealed119.py']==ref(__file__),'actual119 sourcebound helper');need(1792134133<=time.time()<1792220533,'unchanged new24h window')
 if a.mode=='capture':r=capture(ROOT/'seal-evidence119-MAIN-001',sr)
 elif a.mode=='validate':e,b,c=validate(json.loads(a.evidence_ref),sr);r=dict(closed=len(c),numeric_qualified=False)
 else:r=seal(json.loads(a.evidence_ref),sr)
 print(json.dumps(r))
if __name__=='__main__':main()
