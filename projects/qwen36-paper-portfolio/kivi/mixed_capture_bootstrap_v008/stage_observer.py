"""Thin staged raw sink around existing publishers/RawSink. Diagnostic only.
No CPU oracle inside a Torch worker, no subprocess, no wait/cleanup controller.
Original before-write inputs and native-before/merged-after output are immutable.
"""
import copy
import hashlib
import json
from pathlib import Path

def need(v,m):
    if not v:raise ValueError(m)

class Observer:
    def __init__(self,schedule,*,torch,producer,callback,root,identity,publish,sequence=None):
        self.schedule=schedule;self.t=torch;self.producer=producer;self.callback=callback
        self.root=root;self.identity=identity;self.ident=dict(identity());self.original_publish=publish
        self.context=None;self.native={};self.indices=[];self.raw_inputs=[]
        self.sequence=sequence;self.stage_ref=None;self.last_update_ref=None;self.retirement_refs={}
        self.progress_frame=None;self.progress_returns=set();self.ready=set()
    def publish_wire(self,label,row):
        """Preserve original JSON bytes, without changing producer-owned values.
        The unchanged scalar journal still publishes exactly once and verifies
        the complete original Ref/bytes/SHA; only tuple/list JSON semantics differ.
        """
        need(self.identity()==self.ident,"same actual worker before wire publication")
        wire=json.loads(json.dumps(row,sort_keys=True,separators=(",",":"),allow_nan=False))
        return self.original_publish(label,wire)
    def publish(self,label,row):
        ref=self.publish_wire(label,row)
        if row.get("schema")=="kivi.actual-packed-qwen-update/v1":self.last_update_ref=ref
        if row.get("schema")=="kivi.actual-packed-qwen-retire/v1":
            rid=row["request_id"]
            need(rid in self.schedule.retirements and rid not in self.retirement_refs
                 and self.last_update_ref is not None,"source-bound native update before original release")
            self.retirement_refs[rid]=dict(update_ref=self.last_update_ref,retire_ref=ref)
            if rid==self.schedule.ids["holder0"]:
                self.progress("HOLDER0-RETIRED",dict(self.retirement_refs[rid],request_id=rid))
            if set(self.retirement_refs)==set(self.schedule.ids.values()):self.stage_ref=self.finish()
        if row.get("schema")=="kivi.actual-packed-qwen-output/v1" and self.sequence is not None:
            frame=self.progress_frame
            need(frame is not None and row["frame_ref"]==frame["ref"] and row["layer"] in self.sequence.layers
                 and row["layer"] not in self.progress_returns,"complete source-bound FA return set")
            self.progress_returns.add(row["layer"])
            if self.progress_returns==set(self.sequence.layers):
                f=frame["frame"];actual=dict(zip(f["req_ids"],zip(f["computed_tokens"],f["scheduled_counts"])))
                for role,label in (("holder0","HOLDER0-DECODE-READY"),("holder1","HOLDER1-DECODE-READY")):
                    rid=self.schedule.ids[role]
                    if actual.get(rid)==(32768,1) and label not in self.ready:
                        self.progress(label,dict(frame_ref=frame["ref"],request_id=rid,positions=actual,
                            all16_actual_FA_output_returns=sorted(self.progress_returns)))
        if row.get("schema")=="kivi.actual-packed-qkav-frame/v1":
            need(self.context is not None and self.context["capture"] is True
                 and self.schedule.active is not None,"only registered selected full frame")
            point=self.schedule.published(ref);point["native_prefill"]=copy.deepcopy(self.native)
            self.indices.append(point)
            self.context["published_point"]=point
        return ref
    def progress(self,label,body):
        need(label not in self.ready,"one actual stage transition event")
        ref=self.publish_wire("MATRIX-s%02d-r%d-%s"%(self.schedule.stage,self.schedule.rank,label),
            dict(body,schema="kivi.actual-mixed-stage-progress/v1",stage=self.schedule.stage,rank=self.schedule.rank,
                identity=self.ident,plan_ref=self.schedule.plan_ref,label=label,
                observer_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                model_ready=False,run_authority=False))
        self.ready.add(label);return ref
    def start(self,layer,frame,frame_ref,states):
        need(self.identity()==self.ident,"same actual worker at raw stage boundary")
        if self.sequence is not None:
            following=self.sequence.for_frame(frame,self.schedule,self.stage_ref)
            if following is not self.schedule:
                self.schedule=following;self.context=None;self.native={};self.indices=[];self.raw_inputs=[]
                self.stage_ref=None;self.retirement_refs={};self.ready=set()
        if self.progress_frame is None or self.progress_frame["frame"]["epoch"]!=frame["epoch"]:
            self.progress_frame=dict(frame=copy.deepcopy(frame),ref=copy.deepcopy(frame_ref));self.progress_returns=set()
        if not self.schedule.selected(layer):
            self.context=None;return
        selected=self.schedule.choose(layer,frame,frame_ref,states)
        self.context=dict(layer=layer,frame=frame,frame_ref=frame_ref,states=states,
            capture=selected is not None,native_support=self.schedule.needs_native_support(frame,states),published_point=None)
        self.native={}
    def needs_prefill(self,layer,rid):
        return self.schedule.prefill(layer,rid)
    def original_prefill(self,layer,rid,ref):
        need(self.schedule.selected(layer),"only selected original-prefill sink")
        self.schedule.original_prefill(rid,ref)
    def sink(self,label):
        need(self.context is not None,"actual selected FA context")
        f=self.context["frame"]
        return self.producer.RawSink(self.root,self.t,self.callback,
            "s%02d-r%d-%s-e%06d-%s"%(self.schedule.stage,self.schedule.rank,self.schedule.layer.replace(".","-"),f["epoch"],label))
    def native_input(self,row,q,k,v):
        if self.context is None or not (self.context["capture"] or self.context["native_support"]):return
        allowed=(self.schedule.active["prefill_ids"] if self.context["capture"] else [self.schedule.ids["replacement"]])
        need(row["request_id"] in allowed
             and row["computed"]==0 and row["scheduled"]==32768,"actual whole selected new prefill")
        self.t.npu.synchronize()
        sink=self.sink("NATIVE-"+str(row["batch_index"]))
        blobs={name:sink.tensor(name,tensor.contiguous()) for name,tensor in (("Q",q),("K",k),("V",v))}
        self.native[row["request_id"]]=dict(row=copy.deepcopy(row),before_native_input=blobs)
    def native_output(self,row,piece):
        if self.context is None or not (self.context["capture"] or self.context["native_support"]):return
        self.t.npu.synchronize()
        need(tuple(piece.shape)==(32768,1536),"entire actual original native output, no chosen channel/token")
        self.native[row["request_id"]]["original_native_output"]=self.sink("NATIVE-"+str(row["batch_index"])).tensor("BEFORE-OUTPUT",piece.contiguous())
    def append_inputs(self,layer,plan,q,k,v,states):
        if not self.schedule.selected(layer):return
        need(self.context is not None and self.context["layer"]==layer and self.identity()==self.ident,
             "same selected FA actual prewrite context")
        rows=plan["decode"];need(rows,"actual full decode subset")
        self.t.npu.synchronize()
        for i,row in enumerate(rows):
            rid=row["request_id"];state=states[rid]
            start,stop=row["start"],row["stop"]
            need(stop-start==1,"one original full-frame decode input before subset packing")
            sink=self.sink("APPEND-i%02d"%i)
            key=sink.tensor("K",k[start:stop].contiguous())
            value=sink.tensor("V",v[start:stop].contiguous())
            query=(sink.tensor("Q",q[start:stop].contiguous()) if self.context["capture"] else None)
            body=dict(schema="kivi.actual-original-append/v1",stage=self.schedule.stage,rank=self.schedule.rank,identity=self.ident,
                layer=layer,frame_ref=self.context["frame_ref"],request_id=rid,computed=row["computed"],
                slot=state["slot"],slot_epoch=state["epoch"],decode_index=i,decode_count=len(rows),
                original_batch_index=row["batch_index"],token_start=start,token_stop=stop,
                key_ref=key,value_ref=value,query_ref=query,before_candidate_write=True,
                input_origin="original-forward-QKV-before-packed-subset",
                observer_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                model_ready=False,run_authority=False)
            ref=self.publish_wire("RAW-APPEND-s%02d-r%d-%s-e%06d-i%02d"%(self.schedule.stage,self.schedule.rank,
                layer.replace(".","-"),self.context["frame"]["epoch"],i),body)
            self.schedule.append(layer,rid,row["computed"],state["slot"],state["epoch"],ref)
            self.raw_inputs.append(ref)
    def capture_decode(self,layer):
        return bool(self.schedule.selected(layer) and self.context is not None and self.context["capture"])
    def merged_output(self,layer,output,plan):
        if not self.schedule.selected(layer) or self.context is None or not (self.context["capture"] or self.context["native_support"]):return
        if self.context["capture"]:
            need(self.context["published_point"] is not None,"same real completed packed publication before merged output")
        for row in plan["prefill"]:
            self.t.npu.synchronize()
            final=output[row["start"]:row["stop"]]
            need(tuple(final.shape)==(32768,1536),"whole actual final native-prefill output region")
            self.native[row["request_id"]]["merged_native_output"]=self.sink("NATIVE-"+str(row["batch_index"])).tensor("AFTER-OUTPUT",final.contiguous())
        if self.context["native_support"]:
            body=dict(schema="kivi.actual-reuse-prefill-support/v1",stage=self.schedule.stage,rank=self.schedule.rank,identity=self.ident,
                layer=layer,frame_ref=self.context["frame_ref"],native_prefill=copy.deepcopy(self.native),
                retired_holder0=self.schedule.retired,replacement_state=copy.deepcopy(self.context["states"][self.schedule.ids["replacement"]]),
                model_ready=False,run_authority=False)
            self.schedule.reuse_prefill_ref=self.publish_wire("MATRIX-REUSE-PREFILL-s%02d-r%d"%(self.schedule.stage,self.schedule.rank),body)
            if not self.context["capture"]:return
        point=self.context["published_point"];point["native_prefill"]=copy.deepcopy(self.native)
        # Packed outputs are also frozen after scatter to prove original frame
        # indices, independently of the producer's pre-scatter output snapshot.
        self.t.npu.synchronize();sink=self.sink("MERGED")
        point["merged_decode_output_refs"]=[sink.tensor("DECODE-%02d"%i,
            output[row["start"]:row["stop"]].contiguous()) for i,row in enumerate(plan["decode"])]
        ref=self.publish_wire("MATRIX-POINT-s%02d-r%d-%s"%(self.schedule.stage,self.schedule.rank,point["point"]),
            dict(point,schema="kivi.actual-mixed-numeric-point/v1",identity=self.ident,
                observer_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                model_ready=False,performance_ready=False,run_authority=False))
        self.schedule.points[point["point"]]["complete_point_ref"]=ref
    def retire(self,rid,slot,epoch,length):
        self.schedule.retired_owner(rid,slot,epoch,length)
    def finish(self):
        result=self.schedule.finish()
        need(all("complete_point_ref" in p for p in result["points"].values()),"complete merged output for each point")
        need(set(self.retirement_refs)==set(self.schedule.ids.values()),"all four original native release/update Refs")
        result["identity"]=self.ident
        result["retirement_refs"]=copy.deepcopy(self.retirement_refs)
        result["observer_source_sha256"]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        return self.publish_wire("MATRIX-s%02d-r%d-STAGE-FINAL"%(self.schedule.stage,self.schedule.rank),result)

