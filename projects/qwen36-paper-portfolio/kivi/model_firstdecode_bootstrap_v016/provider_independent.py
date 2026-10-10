"""Independent physical/storage-byte check for the explicit provider.
Never imports provider, allocator, fields or quantization code.
Native FA/GDN spans remain wholly protected, not merely a chosen subrange.
"""
from math import prod

def need(value, message):
    if not value:
        raise ValueError(message)

def extent(d):
    shape, stride = d["shape"], d["stride"]
    need(type(shape) in (list, tuple) and type(stride) in (list, tuple)
         and len(shape) == len(stride) > 0 and all(type(n) is int and n > 0 for n in shape)
         and all(type(s) is int and s >= 0 for s in stride), "whole positive strided tensor")
    size, offset = d["element_size"], d["storage_offset_elements"]
    base, storage = d["storage_base"], d["storage_bytes"]
    need(all(type(x) is int for x in (size, offset, base, storage))
         and size > 0 and offset >= 0 and base > 0 and storage > 0,
         "actual storage pointer/size/offset")
    end = (offset + 1 + sum((n-1)*s for n, s in zip(shape, stride))) * size
    need(end <= storage and d["data_ptr"] == base + offset*size
         and d["logical_bytes"] == prod(shape)*size, "all strided bytes inside real parent")
    return base, base+storage

def expected_fields(pages, bits):
    lanes = 32 // bits
    return [
        ("key_codes", [pages,128//lanes,256], "torch.int32", 4),
        ("key_scales", [pages,4,256], None, 2),
        ("key_minima", [pages,4,256], None, 2),
        ("value_codes", [pages*128,256//lanes], "torch.int32", 4),
        ("value_scales", [pages*128,8], None, 2),
        ("value_minima", [pages*128,8], None, 2),
        ("key_residual", [16,128,256], None, 2),
        ("value_residual", [16,129,256], None, 2),
        ("shifts", [lanes], "torch.int32", 4),
    ]

def disjoint(intervals):
    ordered = sorted(intervals)
    for (_, prev_end, prev_name), (start, _, name) in zip(ordered, ordered[1:]):
        need(prev_end <= start, "overlapping whole storage: %s / %s" % (prev_name,name))

def consume(plan, native, compact):
    need(plan["schema"] == "kivi.explicit-same-budget-plan/v1"
         and plan["total_budget_bytes"] == 10*1024**3
         and plan["slots"] == 16 and type(plan["bits"]) is int and plan["bits"] in (2,4)
         and plan["max_length"] == 33792 and plan["model_ready"] is False
         and plan["performance_ready"] is False and plan["run_authority"] is False
         and plan["allocation_replaced"] is False
         and plan["compact_new_allocation_explicit"] is True,
         "exact explicit allocation scope, no permission promotion")
    groups = plan["native"]["groups"]
    fa = [g for g in groups if g["kind"] == "FA"]
    need(len(groups) == 4 and len(fa) == 1 and len(fa[0]["names"]) == 16
         and sorted(g["kind"] for g in groups) == ["FA","GDN","GDN","GDN"]
         and all(len(g["names"]) == 16 for g in groups)
         and len({n for g in groups for n in g["names"]}) == 64,
         "entire FA16/GDN48 group membership")
    blocks = plan["native"]["num_blocks"]
    pages = (blocks * fa[0]["block_size"] + 127)//128
    need(type(blocks) is int and blocks > 0 and plan["pages"] == pages
         and type(native) is dict and len(native) == 16 and set(compact) == set(fa[0]["names"]),
         "actual physical capacity and all16 compact planes")
    intervals=[];native_storage=0;native_logical=0
    for base,d in native.items():
        lo,hi=extent(d)
        need(int(base)==lo and d["contiguous"] is True and d["storage_offset_elements"]==0
             and d["dtype"] in ("torch.int8","torch.uint8") and d["observed_format_code"]==2,
             "native initialized entire byte parent descriptor")
        need(d["logical_bytes"] == groups[0]["page_bytes"]*blocks,
             "source-derived actual native physical pool capacity")
        intervals.append((lo,hi,"native:"+str(base)))
        native_storage+=hi-lo;native_logical+=d["logical_bytes"]
    compact_storage=0;compact_logical=0;dtype=None;device=None
    field_spec=expected_fields(pages,plan["bits"])
    for layer, fields in compact.items():
        need(set(fields)=={r[0] for r in field_spec},"all9 explicit allocated fields")
        for name, shape, expected_dtype, item in field_spec:
            d=fields[name];lo,hi=extent(d)
            if expected_dtype is None:
                need(d["dtype"] in ("torch.float16","torch.bfloat16"),"actual A16 compact")
                dtype=d["dtype"] if dtype is None else dtype
                need(d["dtype"]==dtype,"one actual compact dtype")
            else:need(d["dtype"]==expected_dtype,"actual compact field dtype")
            device=d["device"] if device is None else device
            need(d["device"]==device and all(n["device"]==device for n in native.values()),
                 "same physical worker device, no host/different-rank storage")
            expected_stride=[];step=1
            for n in reversed(shape):
                expected_stride.insert(0,step);step*=n
            need(list(d["shape"])==shape and list(d["stride"])==expected_stride
                 and d["element_size"]==item and d["contiguous"] is True
                 and d["storage_offset_elements"]==0 and d["observed_format_code"]==2,
                 "whole exact contiguous ND2 field, not an unreported subview")
            intervals.append((lo,hi,layer+":"+name))
            compact_storage+=hi-lo;compact_logical+=prod(shape)*item
    disjoint(intervals)  # compares WHOLE storages across all native/GDN and compact
    need(native_logical==plan["native"]["native_bytes"]==plan["native_budget_returned_bytes"]
         and compact_logical==plan["compact_logical_bytes"],"independent full byte arithmetic")
    overhead=plan["overhead"]
    exact_meta=16*16*(264+33792+4)*8
    exact_prefill=2*32768*256*2*2
    exact_packed=16*6*33792*2*2+16*6*256*2
    need(set(overhead)=={"persistent_metadata_bytes","full_prefill_gather_peak_bytes",
                        "packed_score_probability_result_bytes","allocation_margin_bytes"}
         and overhead["persistent_metadata_bytes"]==exact_meta
         and overhead["full_prefill_gather_peak_bytes"]==exact_prefill
         and overhead["packed_score_probability_result_bytes"]==exact_packed
         and type(overhead["allocation_margin_bytes"]) is int
         and overhead["allocation_margin_bytes"]>0,"all named overheads independently recomputed")
    logical_charge=native_logical+compact_logical+sum(overhead.values())
    extra_storage=native_storage+compact_storage-native_logical-compact_logical
    need(extra_storage>=0 and extra_storage<=overhead["allocation_margin_bytes"]
         and logical_charge==plan["charged_total_bytes"]
         and logical_charge<=plan["total_budget_bytes"]
         and plan["unassigned_bytes"]==plan["total_budget_bytes"]-logical_charge,
         "same total10GiB, rounding uses charged margin rather than extra memory")
    need(plan["original_native_all64_preserved"] is True and plan["native_capacity_reduced"] is True
         and plan["scheduler_preemption_supported"] is False
         and plan["allocator_peak_checked"] is False,"unproved runtime scopes remain explicit")
    return dict(schema="kivi.explicit-cache-storage-check/v1",
                native_logical_bytes=native_logical,native_storage_bytes=native_storage,
                compact_logical_bytes=compact_logical,compact_storage_bytes=compact_storage,
                actual_storage_rounding_bytes=extra_storage,
                remaining_margin_bytes=overhead["allocation_margin_bytes"]-extra_storage,
                native_all64_whole_pools_excluded=True,fields=144,
                all_device_storages_checked=True,allocator_peak_checked=False,
                zeroer_after_initialize_checked=False,numerical_checked=False,
                model_ready=False,run_authority=False)

def validate_native_event(plan, event, native, compact, zeroer, *, layout_consumer):
    """Run AFTER original reshape/bind/zeroer; requires its actual full event.
    This does not replace the original layout consumer/source qualification.
    Protecting entire native allocations excludes ANY in-pool zeroer range.
    """
    import hashlib, inspect
    from pathlib import Path
    path=Path(inspect.getfile(layout_consumer.consume_rank))
    need(path.is_absolute() and not path.is_symlink() and hashlib.sha256(path.read_bytes()).hexdigest()==
         "71f45ada3acf89b68b0338a74897cbb68ab5cc980a3788aa6c4afd282d823927",
         "original independent whole-native layout consumer source")
    layout_consumer.consume_rank(event,bits=plan["bits"],slots=16)
    # Its old hypothetical padding proposals are deliberately not used.
    need(event["num_blocks"]==plan["native"]["num_blocks"] and len(event["layers"])==64,
         "same actually initialized full native config")
    expected={n:g["kind"] for g in plan["native"]["groups"] for n in g["names"]}
    need(set(event["layers"])==set(expected),"no lost native FA/GDN layer")
    actual={}
    for pool in event["pools"]:
        d=pool["raw"];lo,hi=extent(d)
        need(lo not in actual and lo in {int(b) for b in native},"all actual initialized original roots")
        original=native.get(lo,native.get(str(lo)))
        need(extent(original)==(lo,hi) and d["logical_bytes"]==original["logical_bytes"],
             "native allocation unchanged through reshape")
        actual[lo]=pool
    need(len(actual)==len(native)==16,"all16 initialized native roots")
    for name,row in event["layers"].items():
        need(row["kind"]==expected[name],"actual layer kind preserved")
        for d in row["views"]:
            lo,hi=extent(d)
            need(lo in actual and hi==extent(actual[lo]["raw"])[1]
                 and name in actual[lo]["shared_by"],"whole original strided view remains in native parent")
    need(zeroer["schema"]=="kivi.actual-ascend-zeroer-writer/v1"
         and zeroer["identity"]==event["identity"] and zeroer["rank"]==event["rank"]
         and zeroer["num_blocks"]==event["num_blocks"]
         and type(zeroer["initialized"]) is bool
         and zeroer["source_sha256"]=="e75651c8742650f1bac7dddb5f39b9a636f289b4785864c984837ec12dcdae75"
         and zeroer["runner_source_sha256"]=="94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968"
         and zeroer["segment_table_before"]==zeroer["segment_table_after"],
         "same actual source-qualified zeroer snapshot")
    if zeroer["initialized"]:
        width=zeroer["page_size_el"]*4*event["num_blocks"]
        need(type(width) is int and width>0 and len(set(zeroer["segments"]))==len(zeroer["segments"])==zeroer["n_segs"],
             "all full-stride zeroer segments")
        for address in zeroer["segments"]:
            need(sum(lo<=address and address+width<=extent(p["raw"])[1] for lo,p in actual.items())==1,
                 "zeroer cannot target explicit compact or outside original native")
    else:
        need(zeroer["speculative_config_is_none"] is True and zeroer["segments"]==[]
             and zeroer["n_segs"]==zeroer["page_size_el"]==zeroer["block_size_el"]==0
             and zeroer["segment_table_before"] is None
             and zeroer["absent_guarded_noop_source_sha256"]=="6250ca0670c4593aa2f7c4567c9c71d6cb3d8182624a985d4d4e33d5bf054666"
             and zeroer["native_initializer_source_sha256"]=="c392da56095b255d47fe5ad7ffdfbedd269fe69851690e89a8d2ed44c073f6c3",
             "source-qualified absent zeroer; no guessed empty writes")
    proof=consume(plan,native,compact)
    proof["zeroer_after_initialize_checked"]=True
    return proof

