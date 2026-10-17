"""Bounded historical tree-index reader; no owner/math/admission mechanism.

Indexes remain immutable Ref3s. Every actual file is independently hashed in
full mode. Metadata mode still enumerates the COMPLETE directory and compares
all rows; no cache boolean or partial-prefix success exists.
"""
import hashlib,json,os,stat
from pathlib import Path,PurePosixPath
CHUNK=65536;MAX_VALUE=65536
def need(v,m):
 if not v:raise ValueError(m)
def identity(s):return(s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_uid,s.st_gid,s.st_nlink)
def file_ref(path):
 p=Path(path);need(p.is_absolute()and all(not q.is_symlink()for q in(p,*p.parents)),'ordinary exact source path');a=p.lstat();need(stat.S_ISREG(a.st_mode),'regular source');h=hashlib.sha256();n=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b);n+=len(b)
 need(identity(a)==identity(p.lstat())and n==a.st_size,'source stable through complete SHA');return dict(path=p.as_posix(),bytes=n,sha256=h.hexdigest())
def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and file_ref(r['path'])==r,'whole exact tree-index Ref3');return Path(r['path'])
class Parser:
 def __init__(self,f):self.f=f;self.buf='';self.eof=False;self.decoder=json.JSONDecoder()
 def fill(self):
  need(not self.eof,'truncated tree JSON');b=self.f.read(CHUNK)
  if not b:self.eof=True
  self.buf+=b
 def ws(self):
  while True:
   self.buf=self.buf.lstrip()
   if self.buf or self.eof:return
   self.fill()
 def token(self,s):
  self.ws();need(self.buf.startswith(s),'exact JSON tree delimiter '+s);self.buf=self.buf[len(s):]
 def value(self):
  self.ws()
  while True:
   try:v,n=self.decoder.raw_decode(self.buf)
   except json.JSONDecodeError:
    need(not self.eof and len(self.buf)<=MAX_VALUE,'bounded complete tree JSON value');self.fill();continue
   need(n<=MAX_VALUE,'bounded single tree JSON value');self.buf=self.buf[n:];return v
def rows(index,root):
 """Replayable by reopening; never load the full files[] array."""
 path=checked(index);before=identity(path.lstat());seen=set();actualroot=None;last=None
 with path.open('r',encoding='utf8',newline='')as f:
  p=Parser(f);p.token('{')
  while True:
   key=p.value();need(key in('root','files')and key not in seen,'only unique root/files tree fields');seen.add(key);p.token(':')
   if key=='root':actualroot=p.value();need(actualroot==str(root),'exact historical tree root')
   else:
    p.token('[');p.ws()
    if not p.buf.startswith(']'):
     while True:
      row=p.value();need(type(row)is dict and set(row)=={'relative_path','bytes','mtime_ns','inode','device','sha256'},'complete full-hash tree row schema')
      name=row['relative_path'];q=PurePosixPath(name)
      need(type(name)is str and name and not q.is_absolute()and '..'not in q.parts and q.as_posix()==name and(last is None or last<name),'ordered unique bounded relative tree path');last=name
      need(all(type(row[k])is int and row[k]>=0 for k in('bytes','mtime_ns','inode','device'))and type(row['sha256'])is str and len(row['sha256'])==64 and all(c in'0123456789abcdef'for c in row['sha256']),'strict tree metadata/SHA fields')
      yield row;p.ws()
      if p.buf.startswith(']'):break
      p.token(',')
    p.token(']')
   p.ws()
   if p.buf.startswith('}'):break
   p.token(',')
  p.token('}');p.ws();need(p.eof and not p.buf and seen=={'root','files'}and actualroot==str(root),'whole tree JSON consumed; no partial/trailing/unknown acceptance')
 need(identity(path.lstat())==before,'index stable across streaming parse')
def metadata(root):
 root=Path(root);a=root.lstat();need(stat.S_ISDIR(a.st_mode)and all(not q.is_symlink()for q in(root,*root.parents)),'ordinary complete metadata root');h=hashlib.sha256();files=0;used=0;entries=0
 def error(e):raise e
 for parent,dirs,names in os.walk(root,followlinks=False,onerror=error):
  dirs.sort();names.sort()
  for name in sorted(dirs+names):
   p=Path(parent)/name;s=p.lstat();need(s.st_dev==a.st_dev and(stat.S_ISREG(s.st_mode)or stat.S_ISDIR(s.st_mode)),'ordinary sameFS complete metadata; no links or unknown types')
   h.update((json.dumps((p.relative_to(root).as_posix(),identity(s)),separators=(',',':'))+'\n').encode());entries+=1
   if stat.S_ISREG(s.st_mode):files+=1;used+=s.st_size
 need(identity(a)==identity(root.lstat()),'metadata root stable during full walk')
 return dict(root=str(root),root_identity=identity(a),files=files,entries=entries,bytes=used,metadata_sha256=h.hexdigest())
def verify(index,root,*,full=True):
 root=Path(root);before=metadata(root);count=0;used=0
 for row in rows(index,root):
  p=root/row['relative_path'];a=p.lstat();need(stat.S_ISREG(a.st_mode)and all(not q.is_symlink()for q in(p,*p.parents)),'ordinary retained file')
  need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==tuple(row[k]for k in('device','inode','bytes','mtime_ns')),'original complete historical stat fields')
  if full:need(file_ref(p)['sha256']==row['sha256'],'original full retained data SHA')
  need(identity(a)==identity(p.lstat()),'retained row stable through validation');count+=1;used+=a.st_size
 after=metadata(root);need(before==after and count==after['files']and used==after['bytes'],'complete directory coverage and stable strong metadata before/after')
 return dict(index=index,root=str(root),files=count,bytes=used,metadata=after,full_data_hash=full,numeric_qualified=False)
