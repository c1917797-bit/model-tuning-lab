"""Source-owned two-large-index storage ABI adapter. No math/clock changes."""
import hashlib,inspect,types,json,os,weakref
from dataclasses import dataclass
from pathlib import Path,PurePosixPath
import stat
import stream_closed_tree as S
@dataclass(frozen=True)
class ExpectedRows:
 index:dict
 root:str
 count:int
 def __iter__(self):return S.rows(self.index,Path(self.root))
 def __len__(self):return self.count
@dataclass(frozen=True)
class ActualRows:
 root:str
 full:bool
 def __eq__(self,other):
  if isinstance(other,ExpectedRows):
   S.need(other.root==self.root,'same historical streamed root');S.verify(other.index,self.root,full=self.full);return True
  if type(other)is list:
   # Compatibility only for original metadata comprehension, not a cached PASS.
   S.need(not self.full,'full comparison requires complete indexed SHA source')
   before=S.metadata(self.root);last=None;used=0
   for row in other:
    S.need(set(row)=={'relative_path','bytes','mtime_ns','inode','device'}and(last is None or last<row['relative_path']),'original ordered metadata schema')
    last=row['relative_path'];rel=PurePosixPath(last);S.need(not rel.is_absolute()and '..'not in rel.parts and rel.as_posix()==last,'exact ordinary relative row')
    p=Path(self.root)/last;a=p.lstat();S.need(stat.S_ISREG(a.st_mode)and all(not q.is_symlink()for q in(p,*p.parents)),'ordinary exact retained metadata file')
    S.need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==tuple(row[k]for k in('device','inode','bytes','mtime_ns')),'original retained stat equality');used+=a.st_size
   S.need(before==S.metadata(self.root)and len(other)==before['files']and used==before['bytes'],'complete metadata comparison coverage');return True
  return NotImplemented
def install(seal,original_ref):
 S.need(S.file_ref(seal.__file__)==original_ref,'exact original sealed reader source')
 original_canonical=seal.canonical;original_read_tree=seal.read_tree
 # Verify actual historical function body before replacing its storage reader.
 text=Path(seal.__file__).read_text(encoding='utf8')
 S.need(inspect.getsource(original_read_tree)in text,'original read_tree complete source body')
 roots={Path(seal.OUT)/('tree-'+str(n)+'.json'):Path(root)for n,root in zip((16,160),seal.LEAVES)}
 def read_tree(K,r):
  path=Path(r['path']);S.need(path.parent==seal.OUT and path in roots and 0<r['bytes']<49*2**20 and K.ref(path)==r,'same bounded exact historical tree container')
  count=sum(1 for _ in S.rows(r,roots[path]))
  return dict(root=str(roots[path]),files=ExpectedRows(dict(r),str(roots[path]),count))
 def canonical(sr):
  K,m=original_canonical(sr);original_tree=K.tree
  def tree(path,full):
   return ActualRows(str(path),full)if Path(path)in seal.LEAVES else original_tree(path,full)
  K.tree=tree;return K,m
 seal.read_tree=read_tree;seal.canonical=canonical
 return seal

class AuthenticatedMetadata:
 """One Lease/PID-bound immutable baseline, not an external certificate.

 Must be built around successful ORIGINAL full validation under the original
 shared lock. Every comparison walks ALL files+directories. Ordinary local
 VFS/nonprivileged-writer threat model only; not a raw-device/root defense.
 """
 def __init__(self,lease,roots,before,after,rows,index_identities):
  S.need(before==after and len(roots)==len(set(roots))==15,'atomic fifteen metadata/fullhash/metadata window')
  self.lease=weakref.ref(lease);self.pid=os.getpid();self.fd=lease.fd;self.fd_identity=S.identity(os.fstat(lease.fd));self.source=json.dumps(lease.model_sr,sort_keys=True)
  self.roots=tuple(roots);self.baseline=types.MappingProxyType({k:types.MappingProxyType(dict(v))for k,v in after.items()});self.rows=types.MappingProxyType({r['leaf']:json.dumps(r,sort_keys=True)for r in rows});self.index_identities=types.MappingProxyType(dict(index_identities))
  S.need(len(self.rows)==13 and set(self.rows)<=set(roots),'exact original13 rows; new2 separate')
 def _index(self,r):
  lease=self.lease();S.need(os.getpid()==self.pid and lease is not None and lease.fd==self.fd and S.identity(os.fstat(self.fd))==self.fd_identity and json.dumps(lease.model_sr,sort_keys=True)==self.source,'same current PID/source/held storage lock instance')
  S.need(r['path']in self.index_identities and S.identity(Path(r['path']).lstat())==self.index_identities[r['path']],'authenticated index inode/mode/size/mtime/ctime unchanged')
 def check_leaf(self,leaf,r):
  self._index(r);S.need(leaf in self.baseline and S.metadata(leaf)==self.baseline[leaf],'complete strong retained metadata unchanged; no rebaseline')
 def closed_stat(self,unused,row):
  S.need(row['leaf']in self.rows and json.dumps(row,sort_keys=True)==self.rows[row['leaf']],'exact originally full-validated closed row')
  self.check_leaf(row['leaf'],row['tree_ref'])
 def original_commitment(self,original):
  # Clone the exact function CODE/closure; substitute only its private imported
  # module's closed_stat, not globals in the frozen/public original module.
  module=original.__globals__['original'];proxy=types.SimpleNamespace(**vars(module));proxy.closed_stat=self.closed_stat
  scope=dict(original.__globals__,original=proxy)
  made=types.FunctionType(original.__code__,scope,original.__name__,original.__defaults__,original.__closure__)
  S.need(made.__code__ is original.__code__,'original commitment body byte-identical')
  return made
