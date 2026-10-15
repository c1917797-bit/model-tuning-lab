"""Draft catalog admission and bounded retained-material index; not activated."""
import json
from pathlib import Path
from independent_material_readiness import materials_ready
from independent_segment_catalog import SegmentCatalog
from independent_pic_admission_plan import cap_pic_chunk
MATERIAL_EVENTS={"compact_public_state_published","compact_public_kv_published","compact_public_material_evicted"}
def make_scheduler_callback(config,raw,manifest,*,emit,request_limit=128):
 if "public_segments" in config:
  if "public_tokens" in config:raise ValueError("ambiguous scheduler catalog")
  reader=CatalogWorkerMaterialReader(raw,manifest)
  return CatalogPICAdmissionCallback(config["public_segments"],reader,emit=emit,max_requests=request_limit,boundary_tokens=config.get("boundary_tokens",8))
 from independent_pic_scheduler_admission import WorkerMaterialReader,PICAdmissionCallback
 return PICAdmissionCallback(tuple(config["public_tokens"]),WorkerMaterialReader(raw,manifest),emit=emit)
class RetainedMaterialIndex:
 def __init__(self,manifest,*,max_active=4096,max_keys=65536):
  if not isinstance(manifest,str) or not manifest or type(max_active) is not int or type(max_keys) is not int or not 1<=max_active<=4096 or not max_active<=max_keys<=65536:raise ValueError("bounded material index required")
  self.manifest=manifest;self.max_active=max_active;self.max_keys=max_keys
  self.alive={};self.latest={};self.pids={}
 def accept(self,event):
  kind=event.get("event")
  if kind not in MATERIAL_EVENTS:return
  if event.get("manifest_sha256")!=self.manifest:raise ValueError("material source drift")
  rank=event.get("rank");pid=event.get("pid");pool=event.get("pool");key=event.get("key");generation=event.get("generation")
  if type(rank) is not int or rank not in range(4) or type(pid) is not int or pid<=0 or pool not in ("linear","kv") or not isinstance(key,str) or not key or type(generation) is not int or generation<=0:raise ValueError("material identity invalid")
  if rank in self.pids and self.pids[rank]!=pid:raise ValueError("worker PID changed")
  self.pids[rank]=pid;slot=(rank,pool,key)
  if kind=="compact_public_material_evicted":
   previous=self.alive.get(slot)
   if previous is None or previous["generation"]!=generation or previous["pid"]!=pid:raise ValueError("eviction generation mismatch")
   del self.alive[slot];return
  expected="linear" if kind=="compact_public_state_published" else "kv"
  if not isinstance(event.get("layer"),str) or not event["layer"] or not isinstance(event.get("tokens_sha256"),str) or not event["tokens_sha256"]:raise ValueError("publication layer/segment identity missing")
  if pool!=expected or slot in self.alive:raise ValueError("duplicate or wrong-pool publication")
  if generation<=self.latest.get(slot,0):raise ValueError("stale publication generation")
  if slot not in self.latest and len(self.latest)>=self.max_keys:raise ValueError("material key ceiling exceeded")
  if len(self.alive)>=self.max_active:raise ValueError("retained material ceiling exceeded")
  self.latest[slot]=generation;self.alive[slot]=dict(event)
 def ready(self,digest):
  return materials_ready(self.alive.values(),self.manifest,digest)
class CatalogWorkerMaterialReader:
 def __init__(self,root,manifest,*,max_active=4096,max_keys=65536):
  self.root=Path(root)
  if not self.root.is_absolute() or not self.root.is_dir() or self.root.is_symlink():raise ValueError("owned absolute ledger directory required")
  self.index=RetainedMaterialIndex(manifest,max_active=max_active,max_keys=max_keys);self.cursors={};self.last_step=None
 def ready(self,step,digest):
  if type(step) is not int or step<0 or (self.last_step is not None and step<self.last_step):raise ValueError("monotonic scheduler step required")
  if step!=self.last_step:
   files=sorted(self.root.glob("compact-worker-*.jsonl"))
   if len(files)>4:raise ValueError("only four worker ledgers allowed")
   for path in files:
    if path.is_symlink() or not path.is_file():raise ValueError("unsafe worker ledger")
    st=path.stat();offset,inode=self.cursors.get(str(path),(0,st.st_ino))
    if inode!=st.st_ino or st.st_size<offset or st.st_size>134217728:raise ValueError("worker ledger identity/size drift")
    with path.open("rb") as stream:
     stream.seek(offset);data=stream.read(134217729-offset)
    if offset+len(data)>134217728:raise ValueError("worker ledger byte ceiling exceeded")
    complete=data[:data.rfind(b"\n")+1]
    for line in complete.splitlines():self.index.accept(json.loads(line))
    self.cursors[str(path)]=(offset+len(complete),inode)
   self.last_step=step
  return self.index.ready(digest)
class CatalogPICAdmissionCallback:
 def __init__(self,public_segments,reader,*,emit,max_requests=128,boundary_tokens=8):
  if type(max_requests) is not int or not 1<=max_requests<=4096 or not callable(emit):raise ValueError("bounded request ledger and sink required")
  self.catalog=SegmentCatalog(public_segments,boundary_tokens=boundary_tokens);self.reader=reader;self.emit=emit;self.limit=max_requests;self.cache={}
 def __call__(self,scheduler,request,computed,proposed):
  prompt=getattr(request,"prompt_token_ids",None)
  if not prompt or computed>=len(prompt) or getattr(request,"has_encoder_inputs",False) or getattr(scheduler,"use_eagle",False) or getattr(scheduler,"connector",None) is not None:return proposed
  rid=request.request_id
  if rid not in self.cache:
   try:selection=self.catalog.select_one(prompt)
   except ValueError:return proposed
   if selection.start==0:return proposed
   if len(self.cache)>=self.limit:raise ValueError("scheduler request identity ceiling exceeded")
   self.cache[rid]=(tuple(prompt),selection)
  frozen,selection=self.cache[rid]
  if tuple(prompt)!=frozen:raise ValueError("private scheduler prompt changed")
  if computed>selection.start:return proposed
  step=getattr(scheduler,"current_step",None)
  if type(step) is not int:raise ValueError("native scheduler step missing")
  if not self.reader.ready(step,selection.tokens_sha256):return proposed
  aligned=getattr(scheduler,"need_mamba_block_aligned_split",False)
  block=getattr(scheduler.cache_config,"block_size",None) if aligned else 1
  result=cap_pic_chunk(computed=computed,proposed=proposed,prompt_tokens=len(prompt),segment_start=selection.start,segment_end=selection.end,ready=True,block_size=block)
  if result!=proposed:self.emit({"event":"pic_scheduler_boundary_capped","request_id":rid,"step":step,"computed_tokens":computed,"native_proposed_tokens":proposed,"scheduled_tokens":result,"pic_start":selection.start,"pic_end":selection.end,"native_block_size":block,"tokens_sha256":selection.tokens_sha256})
  return result
