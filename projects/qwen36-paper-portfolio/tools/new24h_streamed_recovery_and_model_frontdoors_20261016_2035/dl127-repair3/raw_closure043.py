"""Read tensor-free043 torch archive metadata with NO torch/backend import."""
import io,pickle,zipfile
from pathlib import Path
class PrimitiveOnly(pickle.Unpickler):
 def find_class(self,module,name):raise ValueError('no pickle globals in tensor-free raw metadata')
 def persistent_load(self,pid):raise ValueError('no hidden tensor storages in043 metadata')
def metadata(r,checked):
 p=checked(r)
 with zipfile.ZipFile(p)as z:
  names=[n for n in z.namelist()if n.endswith('/data.pkl')];
  if len(names)!=1 or z.getinfo(names[0]).file_size>4*1024**2:raise ValueError('bounded one tensor-free metadata record')
  v=PrimitiveOnly(io.BytesIO(z.read(names[0]))).load()
 if v.get('schema')!='deltalog.lossless-raw-chunks/v043'or Path(v['root'])!=p.parent:raise ValueError('actual043 same owned raw root')
 return v['payload']
def closure(r,checked):
 p=checked(r);payload=metadata(r,checked);refs={}
 def visit(x):
  if isinstance(x,dict):
   if x.get('__tensor043__')is True:
    for rr in x['chunks']:
     q=Path(rr['path'])
     if q.parent!=p.parent/'tensor-blobs':raise ValueError('only exact same043 blob root')
     checked(rr)
     if q in refs and refs[q]!=rr:raise ValueError('conflicting blob identity')
     refs[q]=rr
   else:
    for a in x.values():visit(a)
  elif isinstance(x,(tuple,list)):
   for a in x:visit(a)
 visit(payload);return list(refs.values())
