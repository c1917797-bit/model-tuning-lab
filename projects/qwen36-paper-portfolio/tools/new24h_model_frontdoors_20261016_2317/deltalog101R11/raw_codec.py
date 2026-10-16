"""Lossless tensor bytes; content-addressed first-axis chunks, never compression.

Only the newly owned raw directory is readable. The ordinary torch loader is
retained for trusted original source inputs; encoded raw independently checks
every chunk's path/size/SHA/dtype/shape before reconstruction.
"""
import hashlib
from pathlib import Path

TAG='deltalog.lossless-raw-chunks/v043'
def digest(p):
 h=hashlib.sha256();n=0
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b);n+=len(b)
 return dict(path=str(Path(p)),bytes=n,sha256=h.hexdigest())
class Store:
 def __init__(self,torch,root,cap):
  self.torch=torch;self.root=Path(root).resolve();self.blobs=self.root/'tensor-blobs';self.blobs.mkdir();self.cap=cap;self.used=0;self.original=torch.load
 def write(self,path,value):
  def encode(v):
   if isinstance(v,self.torch.Tensor):
    t=v.detach().cpu().contiguous();flat=t.reshape(-1).view(self.torch.uint8).reshape(-1);chunks=[]
    # Slot boundaries permit exact reuse of inactive state across lifecycle.
    width=t[0].numel()*t.element_size() if t.ndim and t.shape[0] else max(flat.numel(),1)
    width=max(1,min(width,4*1024*1024))
    for i in range(0,flat.numel(),width):
     b=flat[i:i+width].numpy().tobytes();key=hashlib.sha256(b).hexdigest();p=self.blobs/(key+'.bin')
     if not p.exists():
      if self.used+len(b)+2097152>self.cap:raise ValueError('actual unique-byte raw cap before write')
      with p.open('xb')as f:f.write(b)
      self.used+=len(b)
     r=digest(p)
     if r['sha256']!=key or r['bytes']!=len(b):raise ValueError('existing blob content drift')
     chunks.append(r)
    return {'__tensor043__':True,'dtype':str(t.dtype),'shape':list(t.shape),'chunks':chunks}
   if isinstance(v,dict):return {k:encode(x)for k,x in v.items()}
   if isinstance(v,list):return [encode(x)for x in v]
   if isinstance(v,tuple):return {'__tuple043__':[encode(x)for x in v]}
   return v
  value={'schema':TAG,'root':str(self.root),'payload':encode(value)}
  p=Path(path)
  with p.open('xb')as f:self.torch.save(value,f)
  r=digest(p)
  if self.used+r['bytes']>self.cap:raise ValueError('raw container cap')
  self.used+=r['bytes'];return r
def install(torch):
 original=torch.load
 def load(path,*a,**kw):
  v=original(path,*a,**kw)
  if not isinstance(v,dict)or v.get('schema')!=TAG:return v
  root=Path(v['root']).resolve();p=Path(path).resolve()
  if p.parent!=root or p.is_symlink():raise ValueError('encoded raw same owned root')
  def decode(x):
   if isinstance(x,dict)and x.get('__tensor043__')is True:
    if set(x)!={'__tensor043__','dtype','shape','chunks'}:raise ValueError('exact tensor descriptor')
    dt=getattr(torch,x['dtype'].removeprefix('torch.'));parts=[]
    for r in x['chunks']:
     q=Path(r['path'])
     if q.parent!=root/'tensor-blobs' or q.is_symlink()or digest(q)!=r:raise ValueError('exact immutable blob Ref3')
     parts.append(q.read_bytes())
    b=b''.join(parts);count=1
    for d in x['shape']:
     if type(d)is not int or d<0:raise ValueError('tensor shape')
     count*=d
    if len(b)!=count*torch.empty((),dtype=dt).element_size():raise ValueError('tensor byte geometry')
    return torch.frombuffer(bytearray(b),dtype=dt).clone().reshape(x['shape']) if b else torch.empty(x['shape'],dtype=dt)
   if isinstance(x,dict)and set(x)=={'__tuple043__'}:return tuple(decode(z)for z in x['__tuple043__'])
   if isinstance(x,dict):return {k:decode(z)for k,z in x.items()}
   if isinstance(x,list):return [decode(z)for z in x]
   return x
  return decode(v['payload'])
 torch.load=load
 return original
