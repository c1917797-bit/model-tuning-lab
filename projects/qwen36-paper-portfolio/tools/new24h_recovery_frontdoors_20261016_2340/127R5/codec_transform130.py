"""Exact reversible IO-only transform; no tensor math, cache, or owner admission."""
import hashlib,importlib.util,sys,types
from pathlib import Path
BYTES=3592
SHA='4eb6bb0d5488cd1dfc3f2cb6c0f063d11b83ce07dbf594010c1d7554d844cd0e'
HELPER='''
def _single_read_chunk130(q,r):
 # A single file handle supplies BOTH authenticated bytes and tensor payload.
 # No cache: every logical chunk access still verifies its complete Ref.
 if type(r)is not dict or set(r)!={'path','bytes','sha256'} or r['path']!=str(q) or type(r['bytes'])is not int or r['bytes']<0:
  raise ValueError('exact immutable blob Ref3')
 if any(p.is_symlink()for p in(q,*q.parents)):
  raise ValueError('ordinary immutable blob path')
 sig=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
 path_before=q.lstat();parts=[];h=hashlib.sha256();size=0
 with q.open('rb')as f:
  before=os.fstat(f.fileno())
  if not stat.S_ISREG(before.st_mode) or sig(path_before)!=sig(before):
   raise ValueError('blob identity before read')
  for block in iter(lambda:f.read(1048576),b''):
   h.update(block);size+=len(block)
   if size>r['bytes']:raise ValueError('blob larger than exact Ref')
   parts.append(block)
  after=os.fstat(f.fileno())
 if sig(before)!=sig(after) or sig(after)!=sig(q.lstat()):
  raise ValueError('blob changed during single read')
 if (size,h.hexdigest())!=(r['bytes'],r['sha256']):
  raise ValueError('exact immutable blob Ref3')
 return b''.join(parts)
'''
OLD="     if q.parent!=root/'tensor-blobs' or q.is_symlink()or digest(q)!=r:raise ValueError('exact immutable blob Ref3')\n     parts.append(q.read_bytes())"
NEW="     if q.parent!=root/'tensor-blobs' or q.is_symlink():raise ValueError('exact immutable blob Ref3')\n     parts.append(_single_read_chunk130(q,r))"
TAG="TAG='deltalog.lossless-raw-chunks/v043'\n"

def transform(raw):
 if len(raw)!=BYTES or hashlib.sha256(raw).hexdigest()!=SHA:raise ValueError('exact original043 codec source')
 text=raw.decode('utf8')
 for old,new in (('import hashlib\n','import hashlib,os,stat\n'),(TAG,TAG+HELPER),(OLD,NEW)):
  if text.count(old)!=1:raise ValueError('one exact codec IO edit')
  text=text.replace(old,new)
 if inverse(text)!=raw:raise ValueError('whole codec inverse')
 return text

def inverse(text):
 for old,new in reversed((('import hashlib\n','import hashlib,os,stat\n'),(TAG,TAG+HELPER),(OLD,NEW))):
  if text.count(new)!=1:raise ValueError('one exact codec inverse')
  text=text.replace(new,old)
 return text.encode('utf8')

def install(torch,original_ref,checked):
 """Install BEFORE any original codec wrapper, in a fresh owned CPU process.

 The unchanged domain main may install its original wrapper later. Its inner
 call then receives already decoded data, and does not double-read blobs.
 """
 p=Path(checked(original_ref));raw=p.read_bytes()
 if original_ref['bytes']!=BYTES or original_ref['sha256']!=SHA:raise ValueError('reviewed original codec Ref')
 if getattr(torch.load,'__module__','')!='torch.serialization':raise ValueError('fresh original torch.load required; never silently wrap a prior codec')
 module=types.ModuleType('_actual_single_read_codec130');module.__file__=str(p)
 exec(compile(transform(raw),str(p)+'#single-open130','exec'),module.__dict__)
 original=module.install(torch)
 return module,original
