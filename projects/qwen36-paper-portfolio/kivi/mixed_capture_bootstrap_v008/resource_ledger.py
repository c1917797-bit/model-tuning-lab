"""Byte accounting only; no admission, telemetry substitution, quotas or cleanup."""
import math,hashlib,inspect
from pathlib import Path
FIELDS_SHA="77b678af5eea524c59405d98a3681415810e2e77b7f8cf9cde9fd241b28d4157"
CAPS=(256,1024,2,2)
ROW_MAX=(2,2,2,2,1)
def need(v,m):
    if not v:raise ValueError(m)
def from_layouts(event_refs,geometry_refs,*,fields_module,document):
    need(Path(inspect.getfile(fields_module.consume_geometry)).resolve()==Path(fields_module.__file__).resolve()
         and hashlib.sha256(Path(fields_module.__file__).read_bytes()).hexdigest()==FIELDS_SHA,
         "exact independent explicit field geometry source")
    need(len(event_refs)==4 and len(geometry_refs)==4,"all4 actual native events")
    answer=[]
    for rank,(er,gr) in enumerate(zip(event_refs,geometry_refs)):
        event=document(er);names=sorted(n for n,v in event["layers"].items() if v["kind"]=="FA")
        need(event["rank"]==rank and len(event["layers"])==64 and len(names)==16 and set(gr)==set(names),
             "all64 native layers and all16 actual FA geometry Refs per rank")
        for name in names:
            ref=gr[name];g=document(ref)
            fields_module.consume_geometry(g,event)
            need(g["layer"]==name and len(g["fields"])==9,"whole exact actual9 fields")
            captured=sum(row["descriptor"]["logical_bytes"] for row in g["fields"] if row["name"]!="shifts")
            answer.append(dict(rank=rank,layer=name,pages=g["pages"],records=g["pages"]*128,
                slots=g["slots"],bits=g["bits"],captured_bytes=captured,
                original_event_ref=er,actual_geometry_ref=ref,source_geometry_consumed=True))
    return answer
def ledger(geometries,*,long_row_seconds=19.758,existing_task_output_bytes=None):
    need(existing_task_output_bytes is None or type(existing_task_output_bytes) is int
         and existing_task_output_bytes>=0,"existing retained output measured or explicitly unknown")
    need(type(long_row_seconds) in (int,float) and math.isfinite(long_row_seconds) and long_row_seconds>0,
         "one actual positive reference cost, not fit authority")
    need(type(geometries) is list and len(geometries)==64,
         "actual source-qualified sixteen FA geometries for each of four ranks")
    fields=[];names=set()
    for g in geometries:
        rank,layer,pages,bits=g["rank"],g["layer"],g["pages"],g["bits"]
        need(type(rank) is int and rank in range(4) and (rank,layer) not in names
             and type(pages) is int and pages>0 and type(bits) is int and bits in (2,4),"whole distinct actual physical geometry")
        names.add((rank,layer))
        n=pages*(8192*bits+8192)+16*257*256*2
        need(n<=192*1024**2,"unchanged full-pool192MiB cap, no native quota shrink")
        need(g["captured_bytes"]==n and g["slots"]==16 and g["records"]==pages*128,
             "independently consumed all8 field extent")
        fields.append(n)
    need(all(sum(r==rank for r,layer in names)==16 for rank in range(4)),"all64 FA rank/ordinal pairs")
    rows=sum(ROW_MAX)*64;frames=5*64
    original=4*64*32768*256*2*2
    append=64*sum(n-1 for n in CAPS)*256*2*2
    native_qkv=2*64*32768*(1536+256+256)*2
    native_output=2*64*2*32768*1536*2
    query_original=rows*1536*2
    producer_qkv=rows*(1536+256+256)*2
    output_pre_post=rows*1536*2*2
    packed=5*sum(fields)
    raw=original+append+native_qkv+native_output+query_original+producer_qkv+output_pre_post+packed
    # The capture selector can retain an invalid extra holder row before the
    # independent predicate rejects it. Preserve/charge that failed evidence too:
    # selected decode upper by source = 2,3,3,2,3, vs valid matrix2,2,2,2,1.
    failed_extra_rows=(13-sum(ROW_MAX))*64
    failed_row_margin=failed_extra_rows*(1536*2+(1536+256+256)*2+1536*2*2)
    raw_upper=raw+failed_row_margin
    # No stage raw is released, consumed or deleted while NPU capture is active.
    # Whole raw accumulates through all16 phases and remains after stop-retain.
    # Every output consumer reads one full pool. Writer VerifiedFile hashes it,
    # then seeks compared original-prefix regions. Extra metadata/path IO is NOT
    # guessed here and must be timed/charged from actual immutable source logs.
    full_pool_reads=2*packed
    original_prefix_read_hash_and_compare=2*rows*32768*256*2*2
    native_support_reads=2*64*(96+2*32+2*32+4*96)*1024**2
    writer_seek_upper=rows*(33791*256*4//8*2+33791*256//32*2*2*2+257*256*2)
    history_payload_read_upper=2*rows*1023*256*2*2+2*append
    scalar_reserved=16*2*1024**3
    output_estimate=rows*long_row_seconds
    return dict(schema="kivi.mixed-numeric-resource-accounting/v1",phases=16,
        model_load_intent="one existing loaded worker set and lease; no helper load/restore",
        captured_frames=frames,full_1536_reference_rows_max=rows,
        source_qualified_geometry_required=True,
        raw_written_bytes=dict(packed_pool=packed,original_prefill=original,original_append=append,
            native_QKV=native_qkv,native_before_after_outputs=native_output,
            original_selected_queries=query_original,producer_QKV=producer_qkv,
            packed_before_after_outputs=output_pre_post,total=raw),
        raw_retained_peak_bytes=raw,
        raw_payload_formula_upper_including_failed_extra_rows_bytes=raw_upper,
        raw_payload_global192MiB_pool_cap_upper_bytes=raw-packed+320*192*1024**2+failed_row_margin,
        failed_extra_row_capture_reserved_bytes=failed_row_margin,
        cpu_numeric_phase="separate Devices[] CPU8 only after actual TP4 stop-retain",
        cpu_numeric_wait_inside_NPU_phase=False,
        retained_scalar_log_reserved_bytes=scalar_reserved,
        retained_independent_audit_reserved_bytes=16*16*1024**2,
        other_metadata_and_source_reserved_bytes=8*1024**3,
        proposed_new_workspace_ceiling_bytes=160*1024**3,
        retained_payload_and_declared_additional_bytes=raw_upper+scalar_reserved+16*16*1024**2+8*1024**3,
        disk_free_reserve_bytes=8*1024**3+512*1024**2,
        historical_free_space_bytes_not_admission=498*1024**3,
        existing_task_output_bytes=existing_task_output_bytes,
        proposed_complete_ceiling_with_existing_bytes=None if existing_task_output_bytes is None
            else 160*1024**3+existing_task_output_bytes,
        proposed_initial_free_floor_for_new_workspace_bytes=168*1024**3+512*1024**2,
        fresh_disk_and_existing_logs_accounting_required=True,
        proposed_quota_requires_new_existing_scanner_contract=True,
        reserves_are_not_measured_metadata_high_water=True,
        portfolio_cutoff_epoch=1791788425,
        known_read_byte_accounting=dict(full_pool=full_pool_reads,original_prefix=original_prefix_read_hash_and_compare,
            native_support=native_support_reads,writer_region_seek_upper=writer_seek_upper,
            original_append_upper=history_payload_read_upper),
        uncounted_or_unmeasured=["actual filesystem throughput/fsync and metadata reads",
            "raw source SHA/hash CPU cost","scalar codec writer CPU time","source/journal qualification IO",
            "model prefill/decode and TP timing","guest/host RSS high-water","existing logs and retained failed raw",
            "actual per-stage cleanup/audit overhead"],
        independent_output_CPU_seconds_estimate=output_estimate,
        estimate_note="576 rows times one measured32769-row19.758s; not a measured total or safe upper bound",
        old5400second_host_deadline_sufficient=False,
        additional_resident_NPU_dense_cache_bytes=0,
        diagnostic_contiguous_snapshot_transient_NPU_upper_per_worker_bytes=96*1024**2,
        independent_writer_dense_resident_copy=False,
        cleanup_implemented=False,resource_fit_measured=False,model_ready=False,performance_ready=False,run_authority=False)

