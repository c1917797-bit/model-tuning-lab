"""Actual initialized-region and immutable owner inputs for the existing worker.
Metadata only: no allocation/controller/Torch import, no guessed PID or admission.
"""
import hashlib
import inspect
import json
import re
import time
from pathlib import Path

FIELDS_SHA="0bdc89eab1c629bf43301705e744c9baf18600b959b5f272974a81b02f8480f6"
SPANS_SHA="2eb0a604dead0181c51e4314a15efb6aca48d51436f7eeb254ef3f5ce4518831"
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
CUTOFF=1791788425

def need(value,message):
    if not value:raise ValueError(message)

def read(ref,limit=8*1024**2):
    need(type(ref)is dict and set(ref)=={"path","bytes","sha256"},"exact3 immutable Ref")
    p=Path(ref["path"])
    need(type(ref["bytes"])is int and 0<ref["bytes"]<=limit and p.is_absolute()
         and p.resolve()==p and not p.is_symlink() and p.is_file(),"ordinary bounded original")
    before=p.stat();wire=p.read_bytes();after=p.stat()
    need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==
         (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)
         and len(wire)==ref["bytes"] and hashlib.sha256(wire).hexdigest()==ref["sha256"],
         "whole stable actual Ref bytes/SHA")
    return json.loads(wire)

def pin(fn,digest):
    p=Path(inspect.getfile(inspect.unwrap(getattr(fn,"__func__",fn))))
    need(p.is_absolute() and p.resolve()==p and not p.is_symlink()
         and hashlib.sha256(p.read_bytes()).hexdigest()==digest,"actual frozen geometry source")

def merge(ranges):
    answer=[]
    for lo,hi in sorted(ranges):
        need(type(lo)is type(hi)is int and 0<=lo<hi,"positive actual interval")
        if answer and lo<=answer[-1][1]:answer[-1]=(answer[-1][0],max(hi,answer[-1][1]))
        else:answer.append((lo,hi))
    return answer

def initialized_regions(event,zeroer,fields,spans,*,bits=2):
    """First-fit disjoint ORIGINAL pool padding only; fail if unavailable.
    Every logical native view and full initialized zeroer stride stays live.
    Actual physical/kernel capacity is used, not scheduler1536 or fixture4224.
    """
    pin(fields.check_region,FIELDS_SHA);pin(spans.span,SPANS_SHA)
    need(type(bits)is int and bits in(2,4) and len(event["layers"])==64
         and type(event["num_blocks"])is int and event["num_blocks"]>0,
         "complete actual initialized64 cache event")
    blocks=event["num_blocks"];pools={};native=[];fa=[]
    for pool in event["pools"]:
        base,lo,hi,size=spans.span(pool["raw"])
        need(lo==0 and hi==size==pool["size"] and base not in pools,"unique entire physical pool")
        pools[base]={"pool":pool,"size":size,"blocked":[]}
    for name,row in sorted(event["layers"].items()):
        index=int(name.split(".layers.",1)[1].split(".",1)[0])
        need(row["kind"]==("FA" if index%4==3 else "GDN"),"true64 layer membership")
        need(type(row["views"])is list and row["views"],"all actual typed views")
        if row["kind"]=="FA":fa.append(name)
        for desc in row["views"]:
            base,lo,hi,size=spans.span(desc)
            need(base in pools and size==pools[base]["size"]
                 and name in pools[base]["pool"]["shared_by"],"actual shared_by physical alias")
            pools[base]["blocked"].append((lo,hi));native.append((base,lo,hi))
    need(len(fa)==16 and sorted(int(n.split(".layers.",1)[1].split(".",1)[0])
         for n in event["layers"])==list(range(64)),"whole64/all16 once")
    need(zeroer["schema"]=="kivi.actual-ascend-zeroer-writer/v1"
         and zeroer["identity"]==event["identity"] and zeroer["rank"]==event["rank"]
         and zeroer["num_blocks"]==blocks and zeroer["source_sha256"]==spans.ZERO_SHA
         and zeroer["runner_source_sha256"]==spans.RUNNER_SHA
         and type(zeroer["initialized"])is bool
         and zeroer["segment_table_before"]==zeroer["segment_table_after"],"same actual zeroer source/frame")
    if zeroer["initialized"]:
        width=zeroer["page_size_el"]*4
        need(type(zeroer["page_size_el"])is int and width>0
             and len(zeroer["segments"])==zeroer["n_segs"]
             and len(set(zeroer["segments"]))==zeroer["n_segs"],"actual initialized whole-page writes")
        for address in zeroer["segments"]:
            matches=[(base,p)for base,p in pools.items()
                     if base<=address and address+blocks*width<=base+p["size"]]
            need(len(matches)==1,"each complete zeroer range lies in one actual physical pool")
            base,p=matches[0];p["blocked"].append((address-base,address-base+blocks*width))
    else:
        need(zeroer["segments"]==[] and zeroer["n_segs"]==zeroer["page_size_el"]==
             zeroer["block_size_el"]==0 and zeroer["segment_table_before"]is None
             and zeroer["absent_guarded_noop_source_sha256"]==spans.GPU_SHA
             and zeroer["native_initializer_source_sha256"]==spans.WORKER_SHA
             and zeroer["speculative_config_is_none"]is True,"source-qualified absent zeroer only")
    regions={};needed=0
    for name in fa:
        row=event["layers"][name]
        own=[(base,p)for base,p in pools.items()if name in p["pool"]["shared_by"]]
        need(len(own)==1,"one initialized pool per actual FA")
        base,p=own[0];pages=(blocks*row["block_size"]+127)//128
        _,size=fields.field_oracle(pages,16,bits);cursor=0;start=None
        for lo,hi in merge(p["blocked"])+[(p["size"],p["size"]+1)]:
            aligned=(cursor+3)//4*4
            if aligned+size<=lo:start=aligned;break
            cursor=max(cursor,hi)
        need(start is not None,"no disjoint initialized compact capacity for "+name+
             "; do not allocate a hidden shadow pool or discard native/GDN/zeroer spans")
        stop=start+size
        fields.check_region(event,name,start,stop,pages,16,bits)
        regions[name]=dict(pages=pages,bits=bits,start=start,stop=stop)
        p["blocked"].append((start,stop));needed+=size
    return dict(regions=regions,compact_physical_bytes=needed,
                actual_native_tokens={n:blocks*event["layers"][n]["block_size"]for n in fa},
                source_event_identity=event["identity"],actual_blocks=blocks,
                new_device_allocation_bytes=0,all_native64_writers_preserved=True,
                model_ready=False,run_authority=False)

def layout_input(recipe,ident,rank,source_sha):
    need(recipe["schema"]=="kivi.firstdecode-bootstrap-recipe/v1"
         and recipe["image_id"]==IMAGE and type(rank)is int and rank in range(4)
         and re.fullmatch("[0-9a-f]{64}",recipe["container_id"])
         and recipe["container_id"]in ident["cgroup"] and time.time()<CUTOFF,
         "actual owned identity and unchanged portfolio clock")
    read(recipe["external_owner_authority_ref"]);read(recipe["compiled_numeric_qualification_ref"])
    root=Path(recipe["diagnostic_root"])
    need(root.is_absolute() and root.resolve()==root and not root.is_symlink() and root.is_dir()
         and root.name=="run-kivi-owned-layout-"+recipe["run_id"],"existing owned diagnostic root")
    return dict(schema="kivi.owned-before-bind-input/v1",
                adapter_source_manifest_sha256=source_sha,run_id=recipe["run_id"],
                container_id=recipe["container_id"],image_id=IMAGE,
                physical_devices=[4,5,6,7],logical_to_physical={"0":4,"1":5,"2":6,"3":7},
                diagnostic_root=str(root),native_format_binding=recipe["native_format_binding"],
                external_owner_authority_ref=recipe["external_owner_authority_ref"],
                scope="unchanged-native-layout-only",run_authority=False)

def post_input(recipe,bindings,event,event_ref,layout_final_ref,zeroer,fields,spans,publish,*,provider_state):
    ident=event["identity"];rank=event["rank"]
    need(bindings.owner["container_id"]==recipe["container_id"]
         and bindings.owner["rank_bindings"][str(rank)]==ident,"actual all4 independently bound workers")
    read(event_ref);read(layout_final_ref);read(recipe["actual_input_protocol_ref"])
    plan=read(bindings.plan_ref)
    need(len(plan["rows"])==3 and len(bindings.expected)==3
         and all(len(v["prompt"])==32768 for v in bindings.expected.values())
         and recipe["algorithm_arm"]=="candidate" and recipe["screen_output_counts"]==[2,2,129],
         "exact three sequential full32768 owners: two decode warmups then cost129")
    need(provider_state["state"]=="consumer_installed"
         and len(provider_state["arenas"])==16,"source-qualified completed explicit provider")
    proposal=provider_state["plan"]
    need(proposal["requested_max_num_seqs"]==1 and proposal["bits"]==recipe["bits"]
         and proposal["native"]["num_blocks"]==event["num_blocks"],"actual B1 planned native geometry")
    allocation=read(provider_state["allocation_ref"])
    need(allocation["plan_ref"]==provider_state["plan_ref"],"actual same immutable allocation plan")
    compact=allocation["compact"]
    scalar_owner=dict(explicit_plan_ref=provider_state["plan_ref"],
                      explicit_allocation_ref=provider_state["allocation_ref"])
    fields.consume_rank(scalar_owner,event,compact,zeroer)
    names={n for n,l in event["layers"].items()if l["kind"]=="FA"}
    need(names==set(provider_state["arenas"])==set(compact),"all16 actual explicit arenas")
    geometry=dict(regions={n:dict(pages=proposal["pages"],bits=proposal["bits"],
                       allocation_ref=provider_state["allocation_ref"])for n in names},
        compact_physical_bytes=allocation["independent"]["compact_storage_bytes"],
        actual_native_tokens={n:event["num_blocks"]*event["layers"][n]["block_size"]for n in names},
        source_event_identity=event["identity"],actual_blocks=event["num_blocks"],
        new_device_allocation_bytes=proposal["compact_logical_bytes"],
        all_native64_writers_preserved=True,native_capacity_reduced=True,
        compact_new_allocation_explicit=True,allocation_replaced=False,
        model_ready=False,run_authority=False)
    need(all(tokens>=32768+1024 for tokens in geometry["actual_native_tokens"].values()),
         "actual initialized full33792 capacity before fixed1024 screening")
    capacity=publish("PACKED-QWEN-r%d-INITIALIZED-CAPACITY"%rank,
        dict(schema="kivi.actual-firstdecode-capacity/v1",rank=rank,identity=ident,
             event_ref=event_ref,geometry=geometry,required_prompt=32768,maximum_output=1024,
             layout_final_ref=layout_final_ref,model_ready=False,run_authority=False))
    owner=dict(schema="kivi.packed-qwen-install-input/v1",run_id=recipe["run_id"],
        container_id=recipe["container_id"],image_id=IMAGE,physical_devices=[4,5,6,7],
        logical_to_physical={"0":4,"1":5,"2":6,"3":7},rank_bindings=bindings.owner["rank_bindings"],
        diagnostic_root=recipe["diagnostic_root"],native_format_binding=recipe["native_format_binding"],
        actual_input_protocol_ref=recipe["actual_input_protocol_ref"],
        actual_assignment_protocol_ref=bindings.plan_ref,declared_ingress_plan_ref=bindings.plan_ref,
        actual_frontend_binding_ref=bindings.frontend_binding_ref,
        actual_rank_bindings_ref=bindings.rank_bindings_ref,
        declared_passed_request_ids=list(bindings.expected),
        prompt_lengths={r:len(v["prompt"])for r,v in bindings.expected.items()},
        external_owner_authority_ref=recipe["external_owner_authority_ref"],
        compiled_numeric_qualification_ref=recipe["compiled_numeric_qualification_ref"],
        capacity_receipt_ref=capacity,regions=geometry["regions"],
        explicit_plan_ref=provider_state["plan_ref"],explicit_allocation_ref=provider_state["allocation_ref"],
        native_capacity_reduced=True,compact_new_allocation_explicit=True,allocation_replaced=False,
        model_ready=False,run_authority=False)
    return owner,publish("PACKED-QWEN-r%d-ACTUAL-INSTALL-INPUT"%rank,owner)
