"""Replayable SHA-bound JSONL readset: O(one Ref + small parent set) memory."""
import hashlib,json,os,re,sqlite3
from pathlib import Path,PurePosixPath
SCHEMA='deltalog.exact-streamed-readset/v127-repair3'
MAX_LINE=16384
def need(v,m):
 if not v:raise ValueError(m)
def validate_ref(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'},'strict indexed Ref3')
 p=r['path'];need(type(p)is str and p.startswith('/')and p!='/'and not p.startswith('//')and '\\'not in p and len(p.encode('utf8'))<8192 and not any(x in('.','..')for x in p.split('/')[1:])and PurePosixPath(p).is_absolute()and str(PurePosixPath(p))==p,'canonical absolute POSIX indexed path')
 need(type(r['bytes'])is int and r['bytes']>=0 and type(r['sha256'])is str and re.fullmatch('[0-9a-f]{64}',r['sha256'])is not None,'indexed size/hash types')
 return r
def encoded(r):return(json.dumps(validate_ref(r),sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode('utf8')
def signature(s):return(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def container_ref(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and Path(r['path']).is_absolute()and type(r['bytes'])is int and r['bytes']>=0 and type(r['sha256'])is str and re.fullmatch('[0-9a-f]{64}',r['sha256'])is not None,'absolute current-platform index container Ref')
class Index:
 def __init__(self,description,checked):
  need(type(description)is dict and set(description)=={'schema','index_ref','entries','parents','parent_count'}and description['schema']==SCHEMA,'exact index descriptor')
  container_ref(description['index_ref']);need(type(description['entries'])is int and description['entries']>0,'positive exact index count')
  parents=description['parents'];need(type(parents)is list and all(type(p)is str for p in parents)and parents==sorted(set(parents))and description['parent_count']==len(parents)and len(parents)<=4096,'bounded sorted unique parent metadata')
  self.description=description;self.checked=checked
 def __len__(self):return self.description['entries']
 def __iter__(self):
  d=self.description;r=d['index_ref'];p=Path(self.checked(r));h=hashlib.sha256();count=0;size=0;last=None;parents=set()
  with p.open('rb')as f:
   before=os.fstat(f.fileno());need(before.st_size==r['bytes'],'index exact size before stream')
   while True:
    line=f.readline(MAX_LINE+1)
    if not line:break
    need(len(line)<=MAX_LINE and line.endswith(b'\n')and b'\r'not in line,'bounded complete LF index row')
    v=json.loads(line);validate_ref(v);need(encoded(v)==line,'canonical index row encoding')
    need(last is None or last<v['path'],'strict sorted unique readset paths');last=v['path'];count+=1;size+=len(line);h.update(line);parents.add(str(PurePosixPath(v['path']).parent))
    need(count<=d['entries']and len(parents)<=4096,'index count/parent bound during stream')
    yield v
   after=os.fstat(f.fileno())
  need(signature(before)==signature(after)==signature(p.stat()),'index unchanged during complete iteration')
  need(count==d['entries']and size==r['bytes']and h.hexdigest()==r['sha256']and sorted(parents)==d['parents'],'complete exact index SHA/count/parents')
class Readset:
 def __init__(self,base,description,checked):
  self.base=tuple(base);self.index=Index(description,checked)
 def __len__(self):return len(self.base)+len(self.index)
 def __iter__(self):
  yield from self.base
  yield from self.index
 @property
 def parents(self):
  # Authenticate declared count/parents against the full immutable index before
  # exporting them. No blobs or Ref dictionaries are retained by this pass.
  for _ in self.index:pass
  return tuple(sorted(set(self.index.description['parents'])|{str(PurePosixPath(r['path']).parent)for r in self.base}))
 @property
 def descriptor(self):return self.index.description
 def extend(self,values):raise ValueError('immutable CPU-only readset; no numeric extension')
class Writer:
 def __init__(self,path,checked):
  self.path=Path(path);self.checked=checked
  # Own new artifact only. Never opens an old DB or overwrites a failed binder.
  with self.path.open('xb'):pass
  self.db=sqlite3.connect(str(self.path));self.db.execute('PRAGMA cache_size=-1024');self.db.execute('PRAGMA temp_store=FILE')
  self.db.execute('CREATE TABLE refs(path TEXT PRIMARY KEY, bytes INTEGER NOT NULL, sha TEXT NOT NULL) WITHOUT ROWID')
 def add(self,r):
  validate_ref(r);row=self.db.execute('SELECT bytes,sha FROM refs WHERE path=?',(r['path'],)).fetchone()
  if row is None:self.checked(r);self.db.execute('INSERT INTO refs VALUES(?,?,?)',(r['path'],r['bytes'],r['sha256']))
  else:need(row==(r['bytes'],r['sha256']),'conflicting duplicate exact Ref')
  return Path(r['path'])
 def get(self,path):
  row=self.db.execute('SELECT bytes,sha FROM refs WHERE path=?',(path,)).fetchone();need(row is not None,'existing indexed Ref')
  return dict(path=path,bytes=row[0],sha256=row[1])
 def emit(self,path):
  self.db.commit();path=Path(path);h=hashlib.sha256();size=0;count=0;parents=set()
  with path.open('xb')as f:
   for p,n,sha in self.db.execute('SELECT path,bytes,sha FROM refs ORDER BY path'):
    b=encoded(dict(path=p,bytes=n,sha256=sha));need(len(b)<=MAX_LINE,'bounded exported Ref');f.write(b);h.update(b);size+=len(b);count+=1;parents.add(str(PurePosixPath(p).parent));need(len(parents)<=4096,'bounded source parent inventory')
   f.flush();os.fsync(f.fileno())
  need(count>0,'nonempty complete readset');directory=os.open(str(path.parent),os.O_RDONLY)if os.name!='nt'else None
  if directory is not None:
   try:os.fsync(directory)
   finally:os.close(directory)
  return dict(schema=SCHEMA,index_ref=dict(path=path.as_posix(),bytes=size,sha256=h.hexdigest()),entries=count,parents=sorted(parents),parent_count=len(parents))
 def close(self):self.db.close()
