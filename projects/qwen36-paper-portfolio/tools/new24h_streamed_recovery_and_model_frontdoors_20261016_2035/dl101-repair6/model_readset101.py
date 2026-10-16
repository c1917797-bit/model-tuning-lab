"""Replayable explicit recovered readset; compact real parent mount anchors."""
from pathlib import Path
import importlib.util
_p=Path(__file__).resolve().parent/'stream_io101.py';_s=importlib.util.spec_from_file_location('_101R6_exact_stream_io',_p);IO=importlib.util.module_from_spec(_s);_s.loader.exec_module(IO)
class Readset:
 def __init__(self,base,recovered):
  IO.need(type(base)in(list,tuple)and len(base)<4096,'small explicit model/source base closure')
  IO.need(hasattr(recovered,'__len__')and hasattr(recovered,'parents')and iter(recovered)is not recovered,'source-bound replayable readset, not an exhausted generator')
  self.base=tuple(base);self.recovered=recovered
  self.descriptor=getattr(recovered,'descriptor',None)
  parents={str(Path(r['path']).parent)for r in self.base}
  for p in recovered.parents:
   IO.need(type(p)is str and Path(p).is_absolute(),'exact explicit recovered parent')
   parents.add(p)
  self.parents=tuple(sorted(parents));self._length=len(self.base)+len(recovered)
 def __len__(self):return self._length
 def __iter__(self):
  yield from self.base
  yield from self.recovered
 def parent_anchors(self):
  """Full Ref verification; only one REAL smallest file retained per parent.

  Passing these anchors to original017.bind produces exactly the same RO
  parent set as the full closure, without retaining135k Path/Ref objects.
  """
  anchors={};count=0
  for r in self:
   IO.obj_file(r);count+=1;p=str(Path(r['path']).parent)
   if p not in anchors or r['bytes']<anchors[p]['bytes']:anchors[p]=dict(r)
  IO.need(count==len(self)and set(anchors)==set(self.parents),'complete source/index/readset count and exact declared parents, no omitted scope')
  return tuple(anchors[p]for p in self.parents)
 def verify(self):
  count=0;parents=set()
  for r in self:IO.obj_file(r);count+=1;parents.add(str(Path(r['path']).parent))
  IO.need(count==len(self)and parents==set(self.parents),'full stable source-bound replay verification, no consumed generator')
  return dict(entries=count,parent_count=len(parents),streamed=True)
def bind_original(H,sr,pr,readset):
 anchors=readset.parent_anchors();h,pairs=H.bind(sr,pr,anchors)
 expected={Path(p)for p in readset.parents}|{H.DONOR};expected={p for p in expected if not any(q!=p and q in p.parents for q in expected)}
 IO.need(h._READ_MOUNTS=={str(p):(str(p),False)for p in expected},'unchanged original017 compact RO parent calculation covers full actual readset')
 previous=h.frozen_directory
 def frozen(root,digest):
  result=previous(root,digest)
  if root==h.HERE:readset.verify()
  return result
 h.frozen_directory=frozen
 return h,pairs
