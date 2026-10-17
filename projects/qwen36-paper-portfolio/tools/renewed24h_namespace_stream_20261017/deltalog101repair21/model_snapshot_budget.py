"""One explicit model_snapshots journal, holding the shared061 lifecycle lock.

The reviewed two-leaf validator is mandatory. Original061 generations remain
immutable; the new commitment only substitutes proved closed retained bytes.
"""
import hashlib,json,os,shutil,stat,inspect,types
import stream_closed_tree as STREAM
from stream_seal_adapter import AuthenticatedMetadata
from pathlib import Path
ROOT=Path('/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061')
LEAF=ROOT/'first-real-decode-model-snapshots-renew24h-R21-20261017-001'
JOURNAL=ROOT/'MODEL_SNAPSHOTS_LEDGER.R21.json'
G=2**30;CAP=32*G;PAYLOAD_CAP=30*G;OPT_CAP=2*G;TERMINAL_RESERVE=64*2**20;LIMIT=80*G;FREE=100*G
def need(v,m):
 if not v:raise ValueError(m)
def ref(p):
 p=Path(p);a=p.stat();h=hashlib.sha256();n=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b);n+=len(b)
 z=p.stat();need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns),'stable resource source')
 return dict(path=p.as_posix(),bytes=n,sha256=h.hexdigest())
def obj(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and Path(r['path']).is_absolute()and ref(r['path'])==r,'exact immutable resource Ref3')
 return json.loads(Path(r['path']).read_bytes())
def scan(root):
 root=Path(root);a=root.lstat();need(stat.S_ISDIR(a.st_mode)and all(not p.is_symlink()for p in(root,*root.parents)),'ordinary resource root');total=0
 def error(e):raise e
 for parent,dirs,files in os.walk(root,followlinks=False,onerror=error):
  for name in dirs+files:
   s=(Path(parent)/name).lstat();need(s.st_dev==a.st_dev and(stat.S_ISDIR(s.st_mode)or stat.S_ISREG(s.st_mode)),'ordinary sameFS complete resource scan')
   if stat.S_ISREG(s.st_mode):total+=s.st_size
 z=root.lstat();need((a.st_dev,a.st_ino,a.st_mode)==(z.st_dev,z.st_ino,z.st_mode),'resource root not replaced');return total
def adjusted(total,old_committed,closed,rows,payload_bytes,opt_bytes):
 need(type(payload_bytes)is int and type(opt_bytes)is int and min(payload_bytes,opt_bytes)>=0 and payload_bytes+opt_bytes<=CAP,'opt plus P one32GiB cap')
 need(payload_bytes<=PAYLOAD_CAP and opt_bytes<=OPT_CAP,'actual P30GiB and combined opt2GiB partitions')
 savings=0;seen=set()
 for phase in closed:
  leaf=phase['leaf'];need(leaf not in seen,'distinct closed leaf');seen.add(leaf);rr=[x for x in rows if x['leaf']==leaf]
  need(len(rr)==1 and rr[0]['stage']=='numeric'and rr[0]['budget_bytes']==33*G,'only exact original numeric33 rows')
  frozen=phase['frozen_bytes'];need(type(frozen)is int and 0<=frozen<=33*G,'full frozen bytes');savings+=33*G-frozen
 need(len(seen)==2,'only N16 and N160 reduced')
 committed=old_committed-savings+max(0,CAP-payload_bytes)
 need(total>=payload_bytes and committed>=total and total<=LIMIT and committed<=LIMIT,'combined80 actual and commitments');return committed
class Lease:
 def __init__(self,seal,seal_sr,evidence_ref,model_sr,payload_sr,opt_root,opt_usage):
  self.seal,self.seal_sr,self.er=seal,seal_sr,evidence_ref;self.model_sr,self.payload_sr=model_sr,payload_sr;self.opt=Path(opt_root);self.opt_usage=opt_usage;self.extra_opt=None;self.fd=None;self.terminal=False
 def opt_bytes(self):
  return sum(self.opt_usage(p)for p in(self.opt,self.extra_opt)if p is not None and p.exists())
 def prewrite(self,path,n):
  p=Path(path);need(type(n)is int and n>=0 and any(root==p or root in p.parents for root in(self.opt,self.extra_opt)if root is not None),'only own opt controlled write')
  reserve=0 if self.terminal else TERMINAL_RESERVE
  need(self.opt_bytes()+n+reserve<=OPT_CAP,'own opt write retains combined2GiB/terminal64MiB')
  need(not LEAF.exists()or scan(LEAF)<=PAYLOAD_CAP,'observed payload30GiB')
 def wrap_writer(self,c):
  original=c.write
  def write(path,value):
   # A conservative upper bound; original serialization/result Ref is unchanged.
   size=len(json.dumps(value,sort_keys=True,indent=2,ensure_ascii=True).encode())+65536
   self.prewrite(path,size);return original(path,value)
  c.write=write
 def open(self,existing=False):
  import fcntl
  need(self.fd is None,'one whole lifecycle storage lease');fd=os.open(ROOT/'.storage061.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
  try:
   fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);self.fd=fd
   self.K,_=self.seal.canonical(self.seal_sr);self.e=self.K.read(self.er);self.base=self.e['baseline_ledger_ref'];self.ledger=obj(self.base)
   import prior_empty_r19
   self.prior_failed_attempt=prior_empty_r19.validate(types.SimpleNamespace(obj=obj,need=need),self.K)
   import prior_released_empty_r20r1
   self.prior_released_attempt=prior_released_empty_r20r1.validate(types.SimpleNamespace(obj=obj,need=need),self.K)
   bound=obj(self.model_sr)['firstdecode_contract']['closed_readset']
   roots=tuple(bound['retained_tree_roots']);need(len(roots)==len(set(roots))==15,'bound exact fifteen closed roots')
   self._metadata_guard=None
   baseline_before={p:STREAM.metadata(p)for p in roots}
   index_before={r['path']:STREAM.identity(Path(r['path']).lstat())for r in bound['refs']}
   need(len(index_before)==len(bound['refs']),'unique source-bound immutable metadata dependency paths')
   self.K.no_writers();need(self.K.inspect_all()==self.e['states_after']and self.seal.latest(self.K)==self.base,'prehash exact stopped/no-writer/ledger fences')
   need((LEAF.is_dir()and JOURNAL.is_file())if existing else(not LEAF.exists()and not JOURNAL.exists()),'exact new or retained payload/journal')
   # Capture the already-reviewed original full13 final verifier, not a new
   # successful boolean. This whole-function inverse adds only its handle.
   def patch_policy(S):
    self._validated_policy=S
    original=S.commitment
    self._original_commitment=original
    original_closed=inspect.getclosurevars(original).nonlocals['closed']
    need(len(original_closed)==13,'exact original13 commitment closure')
    self._original_closed=original_closed
    def commitment(root,ledger):
     need(self.seal.latest(self.K)==self.base and ledger==self.ledger,'old highest/prefix unchanged under shared lock')
     self.K.no_writers();need(self.K.inspect_all()==self.e['states_after'],'closed CIDs independently stopped')
     for phase in self.e['phases']:
      if self._metadata_guard is None:STREAM.verify(phase['tree_ref'],phase['leaf'],full=False)
      else:self._metadata_guard.check_leaf(phase['leaf'],phase['tree_ref'])
     active=original if self._metadata_guard is None else self._authenticated_commitment
     total,committed=active(root,ledger);payload=scan(LEAF)if LEAF.exists()else 0;opt=self.opt_bytes()
     return total,adjusted(total,committed,self.e['phases'],ledger['reservations'],payload,opt)
    S.commitment=commitment
   raw=inspect.getsource(self.seal.prior_policy)
   pairs=[('B.install(C,m,S)','_final=B.install(C,m,S);S._firstdecode_final_verify=_final.final_verify'),('proof=S.check()','_firstdecode_patch(S);proof=S.check()')]
   changed=raw
   for old,new in pairs:need(changed.count(old)==1,'exact prior-policy source seam');changed=changed.replace(old,new)
   inverse=changed
   for old,new in reversed(pairs):inverse=inverse.replace(new,old)
   need(inverse==raw,'whole prior-policy inverse');scope=dict(self.seal.__dict__,_firstdecode_patch=patch_policy)
   exec(compile(changed,self.seal.__file__+'#model-snapshot-commitment','exec'),scope)
   # Only this new source-bound invocation uses the new accounting. The
   # canonical frozen module/global function is not monkeypatched.
   validate=types.FunctionType(self.seal.validate.__code__,scope,'validate',self.seal.validate.__defaults__)
   checked_e,proof=validate(self.er,self.seal_sr);need(checked_e==self.e,'full original typed overlay validation')
   self.policy=self._validated_policy
   baseline_after={p:STREAM.metadata(p)for p in roots}
   need(index_before=={r['path']:STREAM.identity(Path(r['path']).lstat())for r in bound['refs']},'all bound immutable indices stable around original full validation')
   self.K.no_writers();need(self.K.inspect_all()==self.e['states_after']and self.seal.latest(self.K)==self.base,'posthash exact stopped/no-writer/ledger fences')
   self._metadata_guard=AuthenticatedMetadata(self,roots,baseline_before,baseline_after,self._original_closed,index_before)
   self._authenticated_commitment=self._metadata_guard.original_commitment(self._original_commitment)
   payload_scope=dict(self.K.__dict__,PHASES=('payload',),leaf=lambda i:LEAF)
   self.payload_no_writers=types.FunctionType(self.K.no_writers.__code__,payload_scope,'no_writers')
   self.payload_baseline=None
   if existing:
    self.payload_no_writers();self.payload_baseline=self.K.tree(LEAF,True);self.payload_no_writers()
   if not existing:need(proof['filesystem_free_bytes']>=FREE+CAP,'initial32 preserves100GiB')
   from renewed_closed_reader101r19 import check as renewed_check
   renewed=renewed_check()
   prior_record={k:v for k,v in self.prior_failed_attempt.items()if k!='current_no_writers'}
   prior_released_record={k:v for k,v in self.prior_released_attempt.items()if not k.startswith('current_')}
   j=dict(prior_failed_empty_attempt=prior_record,renewal_validation=renewed,schema='deltalog.model-snapshots-reservation/v1',stage='model_snapshots',source=self.model_sr,payload_source=self.payload_sr,closed_overlay_ref=self.er,closed_source_ref=self.seal_sr,core_ledger_ref=self.base,leaf=LEAF.as_posix(),budget_bytes=CAP,payload_total_cap_bytes=PAYLOAD_CAP,opt_total_cap_bytes=OPT_CAP,allocated_worker_cap_bytes=15*G//2,combined_opt_root=self.opt.as_posix(),legacy_ledger_written=False,numeric_qualified=False)
   j['prior_released_empty_attempt']=prior_released_record
   if existing:need(obj(ref(JOURNAL))==j,'retained exact same-source journal; no new reservation')
   else:
    body=(json.dumps(j,sort_keys=True)+'\n').encode();need(proof['committed_bytes']+len(body)<=LIMIT,'journal charged before write')
    with JOURNAL.open('xb')as f:f.write(body);f.flush();os.fsync(f.fileno())
    LEAF.mkdir(mode=0o700)
   self.journal=ref(JOURNAL);self.check();return self
  except BaseException:os.close(fd);self.fd=None;raise
 def check(self):
  need(self.fd is not None and ref(JOURNAL)==self.journal,'live exclusive lease/exact journal')
  import prior_empty_r19
  prior_empty_r19.validate(types.SimpleNamespace(obj=obj,need=need),self.K)
  import prior_released_empty_r20r1
  prior_released_empty_r20r1.validate(types.SimpleNamespace(obj=obj,need=need),self.K)
  proof=self.policy.check();need(shutil.disk_usage(self.opt.parent).free>=int(8.5*G),'separate opt8.5 reserve')
  return dict(proof,model_snapshots_reservation_ref=self.journal,closed_overlay_ref=self.er,combined_actual_bytes=self.opt_bytes()+scan(LEAF),combined_cap_bytes=CAP,ledger_advanced=False)
 def metadata(self):
  roots=obj(self.model_sr)['firstdecode_contract']['closed_readset']['retained_tree_roots']
  need(len(roots)==15 and len(set(roots))==15,'exact validated fifteen closed roots')
  out={}
  for p in roots+[LEAF.as_posix()]:
   a=Path(p).lstat();value=self.seal.inventory(Path(p));z=Path(p).lstat()
   identity=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_mtime_ns,s.st_ctime_ns)
   need(identity(a)==identity(z),'closed root inode/mtime/ctime stable')
   out[p]=dict(inventory=value,root_stat=identity(z))
  return out
 def close(self,released):
  need(self.fd is not None,'active lease')
  need(released is True,'all current owned CIDs released before post-work full hashing')
  self.payload_no_writers();before=self.metadata()
  final=self.check();self.policy._firstdecode_final_verify(None)
  for phase in self.e['phases']:
   tree=self.seal.read_tree(self.K,phase['tree_ref']);need(self.K.tree(phase['leaf'],True)==tree['files'],'final full closed2 source/data hash fence')
  self.payload_no_writers()
  payload=self.K.tree(LEAF,True)
  if self.payload_baseline is not None:need(payload==self.payload_baseline,'full new payload unchanged before and after independent CPU consumer')
  self.hash_end_metadata=self.metadata();need(self.hash_end_metadata==before,'inode/mtime/ctime stable through complete data hashing')
  self.final_metadata();return final
 def final_metadata(self):
  need(self.metadata()==self.hash_end_metadata,'posthash fresh inode/mtime/ctime complete fence')
  import prior_empty_r19
  prior_empty_r19.validate(types.SimpleNamespace(obj=obj,need=need),self.K)
  import prior_released_empty_r20r1
  prior_released_empty_r20r1.validate(types.SimpleNamespace(obj=obj,need=need),self.K)
  self.payload_no_writers();self.K.no_writers();need(self.K.inspect_all()==self.e['states_after']and self.seal.latest(self.K)==self.base,'final exact stoppedCID/ledger fence')
 def release(self):
  # Called only in the final RESULT write's finally: retain the lock through
  # source-after, terminal budget guard and the durable owner receipt itself.
  if self.fd is not None:os.close(self.fd);self.fd=None
