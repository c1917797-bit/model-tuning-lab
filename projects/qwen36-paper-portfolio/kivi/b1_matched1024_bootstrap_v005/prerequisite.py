"""Source-bound consumed packed3 evidence permits ONLY the registered next diagnostic.
It does not create model/numerical/performance acceptance.
"""
from pathlib import Path
import hashlib,json
FINAL_SHA="d686123d97f9856d72bd2efc4a7d3441cc0a5794250ebd8807519071af3b217d"
PRODUCER_MF="d6a151a13bd3b665eab14f25f5c1c45b1b6ab3b3b470014305977132d7643914"
HOST_MF="49ad791275d5cc9eccdf6c239ab85bc18292d0e3d849052d893dc815c7ac708f"
KERNEL_SHA="ecdae41fa1a3487beb872b01522bbb586f3546100f9fd22b9dd4159ca9c0ac2a"
def need(v,m):
    if not v:raise ValueError(m)
def consumed(ref,read):
    need(ref["sha256"]==FINAL_SHA and ref["bytes"]==2195,"actual MAIN-consumed original packed3 result")
    value=read(ref)
    need(value["schema"]=="kivi.packed3.singlecard.original-consumed/v1"
         and value["status"]=="PACKED3_OWNED_DIAGNOSTIC_CONSUMED"
         and value["MAIN_original_operation_verified"]is True
         and value["host_owned_admission_semantically_consumed"]is True
         and (value["frames"],value["output_rows"],value["kernel_calls"])==(20,24,60)
         and value["source"]["sha256"]==HOST_MF and value["producer_source"]["sha256"]==PRODUCER_MF,
         "complete actual20/24/60 original+host consumer, not a source/canary boolean")
    for name in("native_ready","model_ready","performance_ready","released_cuda_parity","ready","run_authority","whole_176"):
        need(value[name]is False,"diagnostic predecessor is not model/full176 permission")
    for name in("source","producer_source","original_result","original_terminal","independent","independent_child"):
        read(value[name])
    mf=read(value["producer_source"])
    # Exact stored algorithm identity; no mutation of a previous kernel namespace.
    need(mf["algorithm_refs"]["kernel"]["sha256"]==KERNEL_SHA,
         "actual repaired signed-cast primitive, not failed old kernel")
    return value
def owned(recipe,read,source_ref,identity):
    consumed(recipe["compiled_numeric_qualification_ref"],read)
    value=read(recipe["external_owner_authority_ref"])
    need(value["schema"]=="kivi.firstdecode.actual-owned-precondition/v1"
         and value["source"]==source_ref and value["container_id"]==recipe["container_id"]
         and recipe["container_id"]in identity["cgroup"] and value["image"]==recipe["image_id"]
         and value["physical_devices"]==[4,5,6,7]
         and value["logical_to_physical"]=={"0":4,"1":5,"2":6,"3":7}
         and value["guest_limit_bytes"]==64*1024**3
         and value["host_limit_bytes"]==512*1024**2
         and value["ordinary_initial_floor_bytes"]==73*1024**3
         and value["phase_seconds_including_cleanup"]==5400 and value["cleanup_seconds"]==90
         and value["hbm_reserve_mib_per_card"]==3072 and value["portfolio_cutoff"]==1791788425,
         "current exact MAIN-owned source/resource/mapping precondition; not new acceptance")
    for name in("owned_inspect_ref","resource_ref","mapping_ref","clock_ref","canary_ref","cpu_ref"):
        read(value[name])
    need(value["model_ready"]is value["performance_ready"]is False,
         "owned admission does not claim model correctness")
    return value
