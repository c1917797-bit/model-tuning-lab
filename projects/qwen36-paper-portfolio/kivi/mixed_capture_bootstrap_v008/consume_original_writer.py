"""Sequential original-input writer oracle for mixed/later eager snapshots.
No candidate imports or reuse of candidate pack/control computations.
The pinned stdlib reference codec defines quantization; host time is unmeasured.
"""
import hashlib,importlib.util,json,re,sys
from pathlib import Path
from contextlib import ExitStack

HELPER_SHA="3e4a100be9225c3ec464e1d256761a780648fad3dfd4b1dc79db8f883fd092f1"
KERNEL_SHA="ecdae41fa1a3487beb872b01522bbb586f3546100f9fd22b9dd4159ca9c0ac2a"
def need(v,m):
    if not v:raise ValueError(m)
def helper_module(ref):
    need(type(ref) is dict and set(ref)=={"path","bytes","sha256"} and ref["sha256"]==HELPER_SHA,
         "exact independent original geometry/streaming helper")
    p=Path(ref["path"])
    need(p.is_absolute() and p.resolve()==p and not p.is_symlink(),"ordinary helper source")
    blob=p.read_bytes();need(len(blob)==ref["bytes"] and hashlib.sha256(blob).hexdigest()==HELPER_SHA,"helper full source bytes")
    spec=importlib.util.spec_from_file_location("_kivi_mixed_original_stream_geometry",p)
    h=importlib.util.module_from_spec(spec);sys.modules[spec.name]=h
    exec(compile(blob,str(p),"exec"),h.__dict__);return h

def control(row):
    c=row["computed"]
    need(type(c) is int and 32768<=c<=33790,"actual fixed1024 original position")
    expected=[c+1,c//128*128,c-128,row["slot"]]
    need(row["controls"]==expected and all(type(x) is int for x in row["controls"])
         and type(row["slot"]) is int and 0<=row["slot"]<16
         and type(row["epoch"]) is int and row["epoch"]>0
         and type(row["generation"]) is int and row["generation"]==c-32768+1,
         "independent pending control K128/V129 and generation")
    return expected

class Original:
    """Bounded original prefix tiles plus original prewrite append bytes only."""
    def __init__(self,h,provenance,history,owner,point,observer_sha):
        self.h=h;self.provenance=provenance;self.owner=owner
        self.append={"key":bytearray(),"value":bytearray()};self.cache={}
        tiles=provenance["tiles"]
        need(type(tiles) is list and len(tiles)==256,"all original32768 tiles")
        paths=[]
        for i,tile in enumerate(tiles):
            need(tile["start"]==i*128 and tile["stop"]==(i+1)*128,"ordered complete original tiles")
            for axis in self.append:
                need(tile[axis+"_ref"]["bytes"]==65536,"whole original128/D256/A16 tile")
                paths.append(tile[axis+"_ref"]["path"])
        need(len(set(paths))==512,"nonalias original tile evidence")
        need(type(history) is list and len(history)==owner["computed"]-32768+1,
             "complete before-write sequence through current append")
        previous_epoch=provenance["frame_ref"]
        previous_epoch=h.document(previous_epoch)["epoch"]
        for offset,item in enumerate(history):
            c=32768+offset;data=h.document(item["ref"])
            need(item["computed"]==c and item["slot"]==owner["slot"] and item["slot_epoch"]==owner["epoch"]
                 and data["schema"]=="kivi.actual-original-append/v1"
                 and data["stage"]==point["stage"] and data["rank"]==owner["rank"]
                 and data["identity"]==owner["identity"] and data["layer"]==owner["layer"]
                 and data["request_id"]==owner["request_id"] and data["computed"]==c
                 and data["slot"]==owner["slot"] and data["slot_epoch"]==owner["epoch"]
                 and data["before_candidate_write"] is True and data["observer_source_sha256"]==observer_sha
                 and data["input_origin"]=="original-forward-QKV-before-packed-subset"
                 and data["model_ready"] is False and data["run_authority"] is False,
                 "same actual original append origin, source and owner epoch")
            actual=h.document(data["frame_ref"]);ids=actual["req_ids"]
            counts=actual["scheduled_counts"];computed=actual["computed_tokens"]
            need(actual["rank"]==owner["rank"] and actual["identity"]==owner["identity"]
                 and actual["epoch"]>previous_epoch,"ordered real original frames")
            previous_epoch=actual["epoch"]
            dec=[rid for rid,pos,n in zip(ids,computed,counts) if pos>=32768 and n==1]
            i=data["decode_index"];n=data["decode_count"]
            need(type(i) is int and type(n) is int and n==len(dec) and 0<=i<n
                 and dec[i]==owner["request_id"] and computed[ids.index(dec[i])]==c,
                 "actual per-request row belonging to whole decode subset")
            batch=ids.index(dec[i]);starts=actual["query_start_loc"]
            need(data["original_batch_index"]==batch and data["token_start"]==starts[batch]
                 and data["token_stop"]==starts[batch+1] and starts[batch+1]-starts[batch]==1,
                 "original full-frame token span independently matches native partition")
            for axis in self.append:
                blob=h.raw(data[axis+"_ref"],512)
                need(len(blob)==512,"whole original D256 input extent")
                self.append[axis].extend(blob)
        need(history[-1]["ref"]==point["append_history"][owner["request_id"]][-1]["ref"],
             "point owns complete original history")
        need(data["frame_ref"]==point["frame_ref"],"current original append is same captured actual frame")
        self.current_query_ref=data["query_ref"]
    def read(self,axis,start,stop):
        need(axis in self.append and type(start) is int and type(stop) is int
             and 0<=start<stop<=32768+len(self.append[axis])//512 and stop-start<=128,
             "bounded original-input tile request")
        pieces=[]
        while start<stop:
            if start<32768:
                tile=start//128;end=min(stop,(tile+1)*128)
                key=(axis,tile)
                if key not in self.cache:
                    self.cache.clear()
                    self.cache[key]=self.h.raw(self.provenance["tiles"][tile][axis+"_ref"],65536)
                blob=self.cache[key];need(len(blob)==65536,"entire original tile bytes")
                pieces.append(blob[(start%128)*512:((start%128)+end-start)*512])
            else:
                end=stop;pieces.append(self.append[axis][(start-32768)*512:(end-32768)*512])
            start=end
        return b"".join(pieces)

def consume(point_ref,*,helper_ref,codec_ref,installer_sha256,capture_sha256,observer_sha256):
    need("torch" not in sys.modules and "torch_npu" not in sys.modules,"independent no-Torch consumer")
    need(all(type(s) is str and re.fullmatch("[0-9a-f]{64}",s) for s in
        (installer_sha256,capture_sha256,observer_sha256)),"exact reviewed new source identities")
    h=helper_module(helper_ref);point=h.document(point_ref)
    need(point["schema"]=="kivi.actual-mixed-numeric-point/v1"
         and point["observer_source_sha256"]==observer_sha256 and point["model_ready"] is False
         and point["run_authority"] is False,"actual selected mixed point, not numerical permission")
    frame_ref=point["packed_frame_ref"];frame=h.document(frame_ref);rows=frame["rows"]
    need(frame["schema"]=="kivi.actual-packed-qkav-frame/v1"
         and frame["kernel_source_sha256"]==KERNEL_SHA and frame["snapshot_is_live_alias"] is False
         and frame["model_ready"] is False and frame["run_authority"] is False
         and type(rows) is list and 1<=len(rows)<=3,"whole real selected decode subset")
    bits,dtype=frame["bits"],frame["dtype"];codec=h.codec_module(codec_ref)
    first=h.document(rows[0]["identity_refs"]["slot_owner"])
    physical=h.source_geometry(frame,h.document(first["original_prefill_ref"]),first)
    expected_ids=[r["request_id"] for r in rows]
    need(point["decode_ids"]==expected_ids and point["decode_positions"]==[r["computed"] for r in rows]
         and set(point["append_history"])==set(expected_ids),"whole captured per-request ordering")
    current=h.document(point["frame_ref"])
    need(current["schema"]=="kivi.actual-packed-qwen-frame/v1" and current["kind"] in ("decode","mixed")
         and current["rank"]==point["rank"] and current["epoch"]==point["frame_epoch"],
         "actual mixed/decode frame, not synthetic pure decode")
    decoded=[r for r,c,n in zip(current["req_ids"],current["computed_tokens"],current["scheduled_counts"]) if c>=32768 and n==1]
    need(decoded==expected_ids,"full actual decode partition")
    seen={"kp":set(),"vp":set(),"slots":set(),"owners":set()};results=[]
    with ExitStack() as stack:
        fields={name:stack.enter_context(h.VerifiedFile(frame["pool_fields"][name],192*1024**2)) for name in h.FIELDS}
        need(all(fields[n].size==physical["sizes"][n] for n in h.FIELDS),"whole source-derived field bytes")
        inputs=frame["whole_prewrite_input_refs"]
        need(set(inputs)=={"query","key","value"},"original producer full QKV before write")
        raw_inputs={axis:h.raw(ref,16*3072) for axis,ref in inputs.items()}
        need(len(raw_inputs["query"])==len(rows)*3072 and len(raw_inputs["key"])==len(raw_inputs["value"])==len(rows)*512,
             "whole producer original inputs")
        def equal(name,offset,blob):
            need(fields[name].read(offset,len(blob))==blob,"independent original writer byte mismatch "+name)
        for i,row in enumerate(rows):
            length,k_length,v_length,slot=control(row);c=row["computed"]
            kp,vp=row["kp"],row["vp"]
            for axis,seq,limit in (("kp",kp,physical["pages"]),("vp",vp,physical["records"])):
                need(len(seq)==(k_length//128 if axis=="kp" else v_length)
                     and len(set(seq))==len(seq) and all(type(p) is int and 0<=p<limit for p in seq),
                     "exact complete physical original prefix remap")
            for key,values in (("kp",kp),("vp",vp),("slots",[slot]),("owners",[row["request_id"]])):
                need(not seen[key].intersection(values),"nonalias actual live owners");seen[key].update(values)
            owner=h.document(row["identity_refs"]["slot_owner"]);pref=h.document(owner["original_prefill_ref"])
            need(owner["schema"]=="kivi.actual-qwen-slot-owner/v1" and owner["request_id"]==row["request_id"]
                 and owner["slot"]==slot and owner["epoch"]==row["epoch"] and owner["generation"]==row["generation"]
                 and owner["computed"]==c and owner["frame_ref"]==point["frame_ref"]
                 and owner["identity"]==point["identity"] and owner["rank"]==point["rank"] and owner["layer"]==point["layer"],
                 "same source-bound current owner epoch and complete frame")
            need(pref["schema"]=="kivi.actual-original-prefill/v1" and pref["status"]=="ORIGINAL_PREFILL_CAPTURED"
                 and pref["request_id"]==row["request_id"] and pref["slot"]==slot and pref["slot_epoch"]==row["epoch"]
                 and pref["dtype"]==dtype and pref["bits"]==bits and pref["prompt_length"]==32768
                 and pref["original_bytes"]==33554432 and pref["original_attention_calls"]==1
                 and pref["installer_source_sha256"]==installer_sha256 and pref["capture_source_sha256"]==capture_sha256
                 and all(pref[k]==v for k,v in h.PINS.items())
                 and all(pref[k] is False for k in ("allocation_replaced","graph_checked","model_ready",
                     "performance_ready","run_authority","writer_arithmetic_checked")),"whole original native prefill provenance")
            need(h.source_geometry(frame,pref,owner)==physical,"same independently proven native geometry for every owner")
            pre=h.document(pref["frame_ref"]);p=pre["req_ids"].index(row["request_id"])
            need(pre["kind"] in ("prefill","mixed") and pre["computed_tokens"][p]==0
                 and pre["scheduled_counts"][p]==32768 and pre["epoch"]<current["epoch"]
                 and pre["rank"]==owner["rank"] and pre["identity"]==owner["identity"],"actual full native prefill predecessor")
            source=Original(h,pref,point["append_history"][row["request_id"]],owner,point,observer_sha256)
            original_query=h.raw(source.current_query_ref,3072)
            need(len(original_query)==3072 and original_query==raw_inputs["query"][i*3072:(i+1)*3072]
                 and original_query==h.raw(row["query_ref"],3072),
                 "whole original Q6D256 row equals packed subset and true kernel query")
            for axis in ("key","value"):
                need(source.read(axis,c,c+1)==raw_inputs[axis][i*512:(i+1)*512],"current input independently frozen before candidate write")
            for start in range(0,k_length,128):
                blob=source.read("key",start,start+128);xs=codec.scalars(blob,dtype)
                packed=codec.pack((xs[t*256:(t+1)*256] for t in range(128)),"K",bits,dtype)
                page=kp[start//128]
                equal("key_codes",page*128*256*bits//8,packed.payload)
                equal("key_scales",page*2048,packed.scales);equal("key_minima",page*2048,packed.minima)
            for start in range(0,v_length,128):
                end=min(start+128,v_length);xs=codec.scalars(source.read("value",start,end),dtype)
                packed=codec.pack((xs[t*256:(t+1)*256] for t in range(end-start)),"V",bits,dtype)
                width=256*bits//8
                for j,record in enumerate(vp[start:end]):
                    equal("value_codes",record*width,packed.payload[j*width:(j+1)*width])
                    equal("value_scales",record*16,packed.scales[j*16:(j+1)*16])
                    equal("value_minima",record*16,packed.minima[j*16:(j+1)*16])
            equal("key_residual",slot*128*512,source.read("key",k_length,length))
            # V pending residual is129 rows: maintain bounded<=128 reads.
            for offset in range(v_length,length,128):
                equal("value_residual",(slot*129+offset-v_length)*512,source.read("value",offset,min(offset+128,length)))
            results.append(dict(request_id=row["request_id"],slot=slot,epoch=row["epoch"],computed=c,
                original_prefill_ref=owner["original_prefill_ref"],original_append_count=c-32768+1,
                exact_code_scale_minimum_and_residual_bytes=True))
    need("torch" not in sys.modules and "torch_npu" not in sys.modules,"consumer remained independent")
    return dict(schema="kivi.actual-mixed-original-writer-consumed/v1",status="ORIGINAL_WRITER_BYTES_CONSUMED",
        point_ref=point_ref,frame_ref=frame_ref,rows=results,physical_geometry=physical,
        independent_helper_ref=helper_ref,independent_codec_ref=codec_ref,
        consumer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        full_original_input_history_checked=True,output_arithmetic_checked=False,
        unused_writer_bytes_checked=False,lifecycle_checked=False,full_model_coverage_checked=False,
        graph_checked=False,model_ready=False,performance_ready=False,run_authority=False)

