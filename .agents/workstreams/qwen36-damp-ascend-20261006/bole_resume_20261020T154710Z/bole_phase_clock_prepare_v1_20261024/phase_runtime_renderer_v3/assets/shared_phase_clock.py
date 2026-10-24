"""One host phase, inherited through exact host-write/guest-readonly custody."""
import hashlib,json,math,os,re,stat,time
from pathlib import Path
FLAG='MODEL_TUNING_PHASE_PATH'
SCHEMA='bole.shared-existing-phase/v1'
CONTRACT=dict(schema=SCHEMA,phase_seconds=3600,cleanup_seconds=180,guest_readonly=True)
_PARENT=None
def need(v,s):
 if not v:raise ValueError(s)
def ref(p,b):return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def ordinary(p):
 p=Path(p);need(p.is_absolute() and not any(x.is_symlink() for x in (p,*p.parents)),'ordinary phase path')
 return p
def raw(p,cap=8*2**20,*,published=False):
 p=ordinary(p);a=p.stat()
 need(stat.S_ISREG(a.st_mode) and a.st_nlink in ((2,)if published else(1,2)) and a.st_size<=cap,'bounded regular phase evidence')
 if published:
  need(p.name=='PHASE.json' and len(list(p.parent.iterdir()))==2,'exact original atomic publication pair')
 if a.st_nlink==2:
  # Pinned publisher retains one .<final-name>.pending-* alias; other
  # receipts may share this directory, but no third link is accepted.
  pending=list(p.parent.glob('.'+p.name+'.pending-*'))
  need(len(pending)==1,'one source-owned retained staging link')
  q=ordinary(pending[0]);s=q.stat()
  need(stat.S_ISREG(s.st_mode) and (s.st_dev,s.st_ino,s.st_nlink,s.st_size)==(a.st_dev,a.st_ino,2,a.st_size),'retained staging is exact same inode; no external links')
 b=p.read_bytes();z=p.stat()
 need((a.st_dev,a.st_ino,a.st_nlink,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(z.st_dev,z.st_ino,z.st_nlink,z.st_size,z.st_mtime_ns,z.st_ctime_ns),'stable phase evidence')
 return b
def checked(r,cap=8*2**20):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'},'exact phase Ref3')
 b=raw(r['path'],cap);need(ref(r['path'],b)==r,'whole phase evidence Ref');return json.loads(b)
def boot():return Path('/proc/sys/kernel/random/boot_id').read_text().strip()
def time_ns():return os.readlink('/proc/self/ns/time')
def proc_start():
 s=Path('/proc/self/stat').read_text();return s.rsplit(')',1)[1].split()[19]
def cid():
 text=Path('/proc/self/cgroup').read_text()
 found=set(re.findall(r'(?:/docker/|/docker-)([a-f0-9]{64})(?:[/.\n]|$)',text))
 need(len(found)<=1,'one actual container identity')
 return next(iter(found))if found else None
def clock_contract(C,m):
 need(m.get('phase_clock_contract')==CONTRACT and C.ref(__file__)==m['files']['shared_phase_clock.py'],'exact source-owned shared phase protocol')
def bind_parent(C,sr,m,start):
 global _PARENT
 clock_contract(C,m)
 need(_PARENT is None and FLAG not in os.environ and cid()is None,'fresh genuine host phase, not guest delegation')
 need(type(start)in(int,float) and math.isfinite(start) and 0<=start<=time.monotonic(),'actual parent monotonic start')
 args=[x.decode() for x in Path('/proc/self/cmdline').read_bytes().split(b'\0')if x]
 need(len(args)>=4 and args[1:3]==['-I','-B'] and args[3]==m['files']['host_service.py']['path'],'actual unchanged host service entry')
 need(args.count('--output')==1,'one actual original host output operand')
 oi=args.index('--output');need(oi+1<len(args),'actual output value')
 actual_output=args[oi+1];expected_output=m['output_root']+('-CPU'if '--cpu-only'in args else'')
 need(actual_output==expected_output,'actual CPU/model output exactly source-declared')
 import followup_source_validate as V
 authority=V.execution_window(m,clock=True,require_phase=False)
 entry_epoch=time.time()-(time.monotonic()-start)
 need(entry_epoch+3600+180<=authority['cutoff_epoch'],'original cold entry had full unchanged window')
 need(time.monotonic()-start<3600-180,'original phase not exhausted')
 _PARENT=dict(source=sr,entry=start,deadline=start+3600,cutoff=authority['cutoff_epoch'],
  host_pid=os.getpid(),host_start=proc_start(),boot=boot(),time_namespace=time_ns(),output_root=actual_output)
def parent(C,sr,ctl):
 p=_PARENT;need(type(p)is dict and p['source']==sr and p['host_pid']==os.getpid() and p['host_start']==proc_start()
  and p['boot']==boot() and p['time_namespace']==time_ns(),'same live host phase producer')
 need(ctl.created_monotonic==p['entry'] and ctl.deadline==p['deadline'] and p['deadline']==p['entry']+3600,'original controller clock exactly, no extension')
 need(min(p['deadline']-time.monotonic(),p['cutoff']-time.time())>180,'work remains inside original cleanup reserve')
 return p
def role_root(m,role,output_root=None):
 need(role in ('cpu-preflight','dense','candidate','stream-consumer'),'known original role')
 output_root=m['output_root']if output_root is None else output_root
 need(output_root in(m['output_root'],m['output_root']+'-CPU'),'exact MODEL or standalone CPU root')
 if output_root==m['output_root']+'-CPU':need(role=='cpu-preflight','standalone CPU may create only its CPU role')
 return Path(output_root)/'.phase-clock'/role
def prepare_mount(C,sr,ctl,role,mounts):
 m=C.obj(sr);clock_contract(C,m);p=parent(C,sr,ctl)
 d=role_root(m,role,p['output_root']);base=d.parent
 need(ctl.out.parent==Path(p['output_root']) and ctl.out.name==('cpu-consumer'if role=='stream-consumer'else role),'actual existing role leaf')
 ordinary(base.parent)
 if not base.exists():base.mkdir(mode=0o700)
 ordinary(base);need(base.is_dir() and not d.exists(),'fresh bounded phase role directory')
 d.mkdir(mode=0o700);mounts[str(d)]=(str(d),False)
 ctl._shared_phase_directory=str(d)
def environment(e):
 d=Path(e['mounts']['/adakv-results'][0]).parent/'.phase-clock'/e['arm']
 need(e['mounts'].get(str(d))in ((str(d),False),[str(d),False]),'source-registered narrow readonly phase mount')
 return {FLAG:str(d/'PHASE.json')}
def publish(C,sr,ctl,x,inspect_ref):
 m=C.obj(sr);p=parent(C,sr,ctl);d=role_root(m,ctl.expected['arm'],p['output_root'])
 need(getattr(ctl,'_shared_phase_directory',None)==str(d) and x['Id']==ctl.cid==ctl.expected['cid']
  and x['State']['Running']is True and x['State']['Pid']>0,'original actual inspected live owner')
 need(ctl.expected['source']==sr and x['Name']=='/'+ctl.expected['name'],'actual source and owner')
 matches=[v for v in x['Mounts']if v['Destination']==str(d)]
 need(len(matches)==1 and matches[0]['Source']==str(d) and matches[0]['RW']is False,'actual inspect readonly custody')
 owned=Path(ctl.out)/'OWNED.json';owned_ref=C.ref(owned);ov=C.obj(owned_ref)
 need(ov['cid']==ctl.cid and ov['source']==sr and ov['name']==ctl.expected['name'],'existing OWNED exact identity')
 snapshot=C.obj(inspect_ref);rows=json.loads(snapshot['stdout'])
 need(len(rows)==1 and rows[0]==x,'actual original inspect receipt')
 value=dict(schema=SCHEMA,source=sr,authority=m['qualification_authority_ref'],phase=p,
  role=ctl.expected['arm'],cid=ctl.cid,name=ctl.expected['name'],image=ctl.expected['image'],
  owned=owned_ref,inspect=inspect_ref,directory=dict(device=d.stat().st_dev,inode=d.stat().st_ino))
 need(len(json.dumps(value).encode())<=8192,'bounded original metadata custody')
 from snapshot_publication import publish as atomic_publish
 atomic_publish(d/'PHASE.json',value)
 ctl._shared_phase_ref=C.ref(d/'PHASE.json')
 return ctl._shared_phase_ref
def readonly_mount(d):
 lines=Path('/proc/self/mountinfo').read_text().splitlines()
 rows=[l.split()for l in lines if len(l.split())>6 and l.split()[4]==str(d)]
 need(len(rows)==1 and 'ro'in rows[0][5].split(','),'actual guest exact readonly phase mount')
def inherited(C,sr,m,path):
 clock_contract(C,m)
 pth=ordinary(path);need(pth.name=='PHASE.json' and pth.parent.parent in(Path(m['output_root'])/'.phase-clock',Path(m['output_root']+'-CPU')/'.phase-clock'),'exact source phase path')
 role=pth.parent.name;need(pth.parent==role_root(m,role,str(pth.parent.parent.parent)),'bounded actual role')
 readonly_mount(pth.parent);v=json.loads(raw(pth,8192,published=True))
 need(set(v)=={'schema','source','authority','phase','role','cid','name','image','owned','inspect','directory'} and v['schema']==SCHEMA
  and v['source']==sr and v['authority']==m['qualification_authority_ref'] and v['role']==role,'same immutable source/authority/role')
 actual=cid();need(actual is not None and actual==v['cid'],'actual guest CID, not environment claim')
 d=pth.parent.stat();need(v['directory']==dict(device=d.st_dev,inode=d.st_ino),'same mounted custody directory')
 own=checked(v['owned']);snap=checked(v['inspect']);rows=json.loads(snap['stdout'])
 need(len(rows)==1,'one exact original inspect');x=rows[0]
 need(own['cid']==actual and own['source']==sr and own['name']==v['name'] and own['image']==v['image']
  and x['Id']==actual and x['Name']=='/'+v['name'] and x['Image']==v['image'],'existing source/OWNED/inspect owner join')
 need(own['mounts'].get(str(pth.parent))==[str(pth.parent),False],'original OWNED readonly mount')
 matches=[q for q in x['Mounts']if q['Destination']==str(pth.parent)]
 need(len(matches)==1 and matches[0]['Source']==str(pth.parent) and matches[0]['RW']is False,'original actual mount inspection')
 p=v['phase'];need(set(p)=={'source','entry','deadline','cutoff','host_pid','host_start','boot','time_namespace','output_root'}
  and p['output_root']==str(pth.parent.parent.parent) and p['source']==sr and p['boot']==boot() and p['time_namespace']==time_ns(),'same source/boot/time domain')
 need(type(p['entry'])in(int,float) and math.isfinite(p['entry']) and type(p['deadline'])in(int,float)
  and p['deadline']==p['entry']+3600 and 0<=p['entry']<=time.monotonic(),'original single phase deadline')
 import followup_source_validate as V
 a=V.execution_window(m,clock=True,require_phase=False)
 need(p['cutoff']==a['cutoff_epoch'] and min(p['deadline']-time.monotonic(),p['cutoff']-time.time())>180,'remaining parent work and original cleanup reserve')
 return a
def admission(C,sr,m):
 if m.get('phase_clock_contract')is None:
  need(FLAG not in os.environ,'undeclared phase proof')
  import followup_source_validate as V
  return V.execution_window(m,clock=True,require_phase=True)
 clock_contract(C,m)
 path=os.environ.get(FLAG)
 if path is not None:return inherited(C,sr,m,path)
 need(cid()is None,'declared guest phase proof missing, not a cold-entry fallback')
 import followup_source_validate as V
 return V.execution_window(m,clock=True,require_phase=True)
