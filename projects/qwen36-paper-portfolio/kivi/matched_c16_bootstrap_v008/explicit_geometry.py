"""Explicit compact geometry; scalar evidence, no candidate math or allocator."""
import hashlib,inspect,json
from pathlib import Path
import provider_independent as independent
import kivi_layout_consumer as layout
import provider_zeroer as zeroer_source

INDEPENDENT_SHA="332b222442ace7ba90a2ed41cae66f0806dec3639d8711cac86609955afe6f9c"
def sources():
    for value,digest in ((independent.consume,INDEPENDENT_SHA),(zeroer_source.snapshot_zeroer,
                         "2eb0a604dead0181c51e4314a15efb6aca48d51436f7eeb254ef3f5ce4518831")):
        p=Path(inspect.getfile(value)).resolve()
        need(not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==digest,
             "exact independent geometry and live zeroer sources")

def need(v,m):
    if not v:raise ValueError(m)
def document(ref):
    need(type(ref)is dict and set(ref)=={"path","bytes","sha256"} and type(ref["bytes"])is int
         and 0<ref["bytes"]<=8*1024**2,"exact bounded actual3Ref")
    p=Path(ref["path"]);need(p.is_absolute() and p.resolve()==p and p.is_file() and not p.is_symlink(),"actual ordinary Ref")
    a=p.stat();wire=p.read_bytes();b=p.stat()
    need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(b.st_dev,b.st_ino,b.st_size,b.st_mtime_ns)
         and len(wire)==ref["bytes"] and hashlib.sha256(wire).hexdigest()==ref["sha256"],"whole stable bytes/SHA")
    return json.loads(wire)
def post_native_allocated(worker,state):
    need(worker._kivi_explicit_provider is state and state["state"]=="native_initialized"
         and len(state["arenas"])==16 and len(state["native_raw"])==64
         and all(not a.active for a in state["arenas"].values()),"actual initialized empty explicit arenas")
def receipts(plan_ref,allocation_ref,event):
    sources()
    p=document(plan_ref);a=document(allocation_ref)
    need(p["rank"]==a["rank"]==event["rank"] and p["identity"]==a["identity"]==event["identity"]
         and p["source_ref"]==a["source_ref"] and p["recipe_ref"]==a["recipe_ref"]
         and a["plan_ref"]==plan_ref and a["initialized_compact"] is True
         and a["native_original_mapping_returned"] is True
         and a["model_ready"]is a["run_authority"]is False,"same-source rank provider and original event")
    native={d["storage_base"]:d for d in a["native"]}
    need(len(native)==len(a["native"])==16,"exact all16 original native roots")
    need(independent.consume(p,native,a["compact"])==a["independent"],"independent allocation replay")
    return p,a,native
def consume_rank(owner,event,compact,zero):
    p,a,native=receipts(owner["explicit_plan_ref"],owner["explicit_allocation_ref"],event)
    need(compact==a["compact"],"all live fields match original explicit storage receipt")
    return independent.validate_native_event(p,event,native,compact,zero,layout_consumer=layout)
def consume_geometry(g,event):
    need(g["schema"]=="kivi.actual-explicit-field-geometry/v1"
         and g["rank"]==event["rank"] and g["identity"]==event["identity"]
         and g["layer"]in event["layers"] and event["layers"][g["layer"]]["kind"]=="FA",
         "same actual explicit geometry owner/rank/FA")
    p,a,native=receipts(g["plan_ref"],g["allocation_ref"],event)
    need(g["bits"]==p["bits"] and g["pages"]==p["pages"] and g["slots"]==16
         and g["allocation_replaced"] is False and g["original_dense_storage_still_live"] is True
         and g["native_capacity_reduced"] is True and g["compact_new_allocation_explicit"] is True
         and all(g[n] is False for n in("packing_checked","reader_checked","native_ready","model_ready","run_authority")),
         "honest explicit allocation geometry, not native padding")
    expected=independent.expected_fields(g["pages"],g["bits"])
    need([f["name"] for f in g["fields"]]==[x[0] for x in expected],"all9 ordered explicit fields")
    fields={f["name"]:f["descriptor"] for f in g["fields"]}
    need(fields==a["compact"][g["layer"]] and g["dtype"]==fields["key_scales"]["dtype"]
         and g["newly_allocated_device_bytes"]==sum(d["logical_bytes"] for d in fields.values()),
         "whole separately allocated fields and bytes")
    return fields
def geometry(state,event,event_ref,zero_ref,layer):
    p,a,native=receipts(state["plan_ref"],state["allocation_ref"],event);fields=a["compact"][layer]
    result=dict(schema="kivi.actual-explicit-field-geometry/v1",rank=event["rank"],identity=event["identity"],
        layer=layer,dtype=fields["key_scales"]["dtype"],pages=p["pages"],bits=p["bits"],slots=16,
        plan_ref=state["plan_ref"],allocation_ref=state["allocation_ref"],event_ref=event_ref,zeroer_ref=zero_ref,
        fields=[dict(name=n,descriptor=fields[n]) for n,*unused in independent.expected_fields(p["pages"],p["bits"])],
        newly_allocated_device_bytes=sum(d["logical_bytes"] for d in fields.values()),
        native_capacity_reduced=True,compact_new_allocation_explicit=True,
        original_dense_storage_still_live=True,allocation_replaced=False,packing_checked=False,
        reader_checked=False,native_ready=False,model_ready=False,run_authority=False)
    consume_geometry(result,event);return result
def guard_current(torch,callback,identity,rank,runner,event,contexts,zero_ref):
    state=runner._kivi_explicit_provider
    need(event["identity"]==identity() and event["rank"]==rank
         and state["state"]=="consumer_installed","same actual initialized provider/worker")
    zero=document(zero_ref)
    actual=zeroer_source.snapshot_zeroer(torch,runner,event,callback,identity,rank)
    need(actual==zero,"same actual live zeroer metadata/owner, never a stale snapshot")
    compact={}
    for name,ctx in contexts.items():
        need(ctx["arena"]is state["arenas"][name],"actual original explicit arena identity")
        compact[name]={}
        for key,value in ctx["arena"].pool.items():
            if key in("allocated_bytes","dense_shadow_bytes"):continue
            before=callback.scalar_tensor(value);code=ctx["packed_batch"].format(value)
            need(before==callback.scalar_tensor(value),"format read must not mutate explicit field")
            compact[name][key]=dict(before,layout="ND_CONTIGUOUS",observed_format_code=code)
    native={d["storage_base"]:d for d in document(state["allocation_ref"])["native"]}
    for raw in state["native_raw"].values():
        before=callback.scalar_tensor(raw);original=native[before["storage_base"]]
        need(all(original[k]==v for k,v in before.items()),"native raw roots stay unchanged")
    return consume_rank(dict(explicit_plan_ref=state["plan_ref"],explicit_allocation_ref=state["allocation_ref"]),
                        event,compact,zero)
def writer_geometry(frame,provenance,owner,event,g,tensor_extent,fields_order):
    # Outer unchanged consumer has checked original native inputs/prompt/position.
    actual=consume_geometry(g,event)
    need(g["event_ref"]==provenance["event_ref"] and g["layer"]==owner["layer"]
         and g["rank"]==owner["rank"] and g["identity"]==owner["identity"],"original prefill geometry")
    p,a,native=receipts(g["plan_ref"],g["allocation_ref"],event)
    independent.validate_native_event(p,event,native,a["compact"],document(g["zeroer_ref"]),layout_consumer=layout)
    need(set(frame["pool_fields"])==set(fields_order)
         and set(frame["live_alias_descriptors_before_snapshot"])==set(fields_order),"whole8 raw fields")
    dtype="torch."+frame["dtype"];sizes={}
    for name,shape,field_dtype,item in independent.expected_fields(g["pages"],g["bits"]):
        field_dtype=field_dtype or dtype;d=actual[name];physical=tensor_extent(d,shape,field_dtype,nd=True)
        if name in fields_order:
            live=frame["live_alias_descriptors_before_snapshot"][name]
            need(tensor_extent(live,shape,field_dtype)==physical and all(d[k]==v for k,v in live.items()),
                 "exact live explicit field before original snapshot")
            sizes[name]=item
            for n in shape:sizes[name]*=n
            need(frame["pool_fields"][name]["bytes"]==sizes[name],"whole raw field byte count")
    need(sum(sizes.values())<=192*1024**2,"unchanged compact capture envelope")
    return dict(pages=g["pages"],records=g["pages"]*128,slots=16,
       native_capacity=event["num_blocks"]*event["layers"][g["layer"]]["block_size"],
       logical_capacity_per_owner=33792,sizes=sizes,captured_bytes=sum(sizes.values()),
       event_ref=provenance["event_ref"],geometry_ref=provenance["geometry_ref"],layer=g["layer"])
