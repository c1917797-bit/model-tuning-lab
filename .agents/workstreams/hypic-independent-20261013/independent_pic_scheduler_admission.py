"""CPU control-plane admission tied to current four-worker material receipts."""
from pathlib import Path
import json
from independent_current_material_readiness import current_materials_ready
from independent_segment_selection import select_segment,token_digest
from independent_pic_admission_plan import cap_pic_chunk

class WorkerMaterialReader:
    def __init__(self,root,manifest_sha256):
        self.root=Path(root);self.manifest=manifest_sha256
        self.cursors={};self.events=[];self.last_step=None
        if not self.root.is_absolute() or not self.root.is_dir() or self.root.is_symlink():
            raise ValueError("existing owned absolute diagnostic directory required")
    def ready(self,step,digest):
        if step!=self.last_step:
            for path in sorted(self.root.glob("compact-worker-*.jsonl")):
                if path.is_symlink() or not path.is_file():raise ValueError("unsafe worker evidence file")
                st=path.stat();offset,inode=self.cursors.get(str(path),(0,st.st_ino))
                if inode!=st.st_ino or st.st_size<offset or st.st_size>134217728:
                    raise ValueError("worker ledger identity/size drift")
                with path.open("rb") as stream:
                    stream.seek(offset);data=stream.read(134217729-offset)
                complete=data[:data.rfind(b"\n")+1]
                for line in complete.splitlines():
                    event=json.loads(line)
                    if event.get("event") in ("compact_public_state_published","compact_public_kv_published","compact_public_material_evicted"):
                        if len(self.events)>=4096:raise ValueError("material transition evidence bound exceeded")
                        self.events.append(event)
                self.cursors[str(path)]=(offset+len(complete),inode)
            self.last_step=step
        return current_materials_ready(self.events,self.manifest,digest)

class PICAdmissionCallback:
    def __init__(self,public_tokens,reader,*,emit):
        self.public=tuple(public_tokens);self.digest=token_digest(self.public)
        self.reader=reader;self.emit=emit;self.cache={}
    def __call__(self,scheduler,request,computed,proposed):
        prompt=getattr(request,"prompt_token_ids",None)
        if (not prompt or computed>=len(prompt) or getattr(request,"has_encoder_inputs",False)
            or getattr(scheduler,"use_eagle",False) or getattr(scheduler,"connector",None) is not None):
            return proposed
        rid=request.request_id
        if rid not in self.cache:
            if len(self.cache)>=128:raise ValueError("scheduler request identity bound exceeded")
            try:selection=select_segment(prompt,self.public)
            except ValueError:return proposed
            if selection.start==0:return proposed
            self.cache[rid]=(tuple(prompt),selection)
        frozen,selection=self.cache[rid]
        if tuple(prompt)!=frozen:raise ValueError("private scheduler prompt changed")
        if computed>selection.start:return proposed
        step=getattr(scheduler,"current_step",None)
        if type(step) is not int:raise ValueError("native scheduler step unavailable")
        if not self.reader.ready(step,self.digest):return proposed
        aligned=getattr(scheduler,"need_mamba_block_aligned_split",False)
        block=getattr(scheduler.cache_config,"block_size",None) if aligned else 1
        result=cap_pic_chunk(computed=computed,proposed=proposed,prompt_tokens=len(prompt),
            segment_start=selection.start,segment_end=selection.end,ready=True,block_size=block)
        if result!=proposed:
            self.emit({"event":"pic_scheduler_boundary_capped","request_id":rid,
                "step":step,"computed_tokens":computed,"native_proposed_tokens":proposed,
                "scheduled_tokens":result,"pic_start":selection.start,"pic_end":selection.end,
                "native_block_size":block,"tokens_sha256":self.digest})
        return result
