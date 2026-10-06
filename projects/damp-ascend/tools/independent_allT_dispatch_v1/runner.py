#!/usr/bin/env python3
"""NEW default-OFF true-T restricted gate; explicit anchored rowwise native seam."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import sys
import time
import traceback
from independent_contract import (BASE,PROJECT,OLD,NAMESPACE,KERNEL,LIMITS,LAYOUTS,BATCH_GROUPS,
                      checked,sha,require,source_bindings,validate_device,new_output)

from independent_contract import source_snapshot, validate_native_anchors
from reference_seam import NativeRows, clone_graph_case

def retain_failure(gate,report,primary):
    """Frozen retain has pre-try exists/snapshot seams; never replace primary."""
    try:
        gate.retain()
        return True
    except BaseException as secondary:
        report["failure_retention_secondary_error"]=repr(secondary)
        print("secondary failure-retention error: "+repr(secondary)+
              "; original primary: "+repr(primary),file=sys.stderr,flush=True)
        return False

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("library","source-manifest","runtime-manifest","build-receipt",
                 "device-proof","native-source-manifest"):
        parser.add_argument("--"+name,type=Path,required=True)
        parser.add_argument("--"+name+"-sha256",required=True)
    parser.add_argument("--physical-card",type=int,choices=(4,5,6,7),required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    parser.add_argument("--native-gdn-source",type=Path,
        default=Path("/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py"))
    parser.add_argument("--audit-only",action="store_true")
    parser.add_argument("--packet-sha256",required=True)
    args=parser.parse_args()
    bindings=source_bindings(args)  # Before Torch imports or library load.
    if args.audit_only:
        print(json.dumps({"status":"source_admission_only_pass","npu_executed":False,
                          "shared_arena_supported":False,"bindings":bindings}))
        return 0
    require(os.environ.get("DAMP_RUN_INDEPENDENT_ALLT_V1")=="1","NEW explicit opt-in")
    require(os.environ.get("DAMP_RUN_ALL_BATCH_GATE_V1")=="1" and
            os.environ.get("DAMP_ENABLE_ALL_BATCH_WRAPPER_V3")=="1","two explicit NEW opt-ins")
    require(os.environ.get("ASCEND_RT_VISIBLE_DEVICES")=="0","MAIN proves one physical shard ->logical0")
    out=new_output(args.output_dir)
    report={"schema":"damp_all_batch_restricted_shared_graph_gate_v1","status":"running",
        "execution_packet":"damp-independent-allT-v1",
        "namespace":NAMESPACE,"physical_card":args.physical_card,
        "batches":list(BATCH_GROUPS[args.physical_card]),"steps":160,"identical_repeats":8,"warmups":3,
        "limits":dict(LIMITS),"checks":[],"cases":[],"created_ns":time.time_ns(),
        "npu_executed":False,"graph_supported":False,"shared_arena_supported":False,
        "serving_ready":False,"general_sr_supported":False,"calibrated_plan_count":0,
        "bindings":bindings,"sources_before":source_snapshot(),
        "scope":"synthetic shared SoA actual T1..16/SR1-power2, one registered four-T shard only: two graphs+eager, "
                "adjacent/guard-gaps, independent native feedback; not actual model cache/service,"
                "general-SR graph/final192plans, transitions betweenT, scheduler/cache lifecycle/E2E/task accuracy",
        "feedback":"independent native-derived CPU packed golden, no candidate resync or persistent FP32 cache"}
    gate=None;registries=[]
    def save_plain():
        (out/"report.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    save_plain()
    try:
        # Reuse frozen protocol functions; no source rewrite, no old registry reassignment.
        sys.path.insert(0,str(BASE))
        sys.path.insert(0,str(OLD/"graph_gate_v1"))
        sys.path.insert(0,str(OLD/"tests"))
        import torch
        import torch_npu
        import candidate_adapter
        from candidate_adapter import Gate,loaded_libraries
        import protocols
        import graph_protocol
        import run_npu_gate
        import gate_contract
        from native_call_contract import validate_native_schema
        from arena_adapter import Registry,Candidate,storage_disjoint,overlap_negatives
        from metadata_contract import metadata_cases,copy_bounds
        for module,expected in ((candidate_adapter,OLD/"tests/candidate_adapter.py"),
                                (protocols,OLD/"tests/protocols.py"),
                                (graph_protocol,OLD/"graph_gate_v1/graph_protocol.py"),
                                (run_npu_gate,OLD/"tests/run_npu_gate.py"),
                                (gate_contract,OLD/"tests/gate_contract.py")):
            require(Path(module.__file__).resolve()==expected.resolve(),"unexpected imported protocol module")
        gate=Gate(out,report);gate.save()
        report["cann_environment"]=gate_contract.cann_environment_checks(bindings)
        device_path=checked(args.device_proof,args.device_proof_sha256)
        proof=json.loads(device_path.read_text());validate_device(proof,args.physical_card,time.time_ns())
        report["device_proof"]={"path":str(device_path),"sha256":sha(device_path),"content":proof,
                               "authority":"fresh MAIN one physical4..7/registered realT shard inspection"}
        manifest=run_npu_gate.native_bindings(args,need_reference=False)
        report["native_source_manifest"]=manifest
        torch.set_num_threads(1)
        torch_npu.npu.set_compile_mode(jit_compile=False)
        from vllm_ascend.utils import enable_custom_op
        require(enable_custom_op(),"actual native bootstrap unavailable")
        handle=ctypes.CDLL(str(args.library.resolve()),mode=ctypes.RTLD_GLOBAL)
        require(getattr(handle,KERNEL,None) is not None,"defined actual arena launcher unresolved")
        torch.ops.load_library(str(args.library.resolve()))
        candidate=Candidate()
        report["candidate_schemas"]=candidate.schemas()
        report["candidate_meta"]=candidate.meta_gate()
        native=torch.ops._C_ascend.npu_recurrent_gated_delta_rule
        validate_native_schema(native.default._schema);report["native_schema"]=str(native.default._schema)
        torch.npu.set_device(0)
        require(torch.npu.get_device_name("npu:0")=="Ascend910B4","actual runtime SoC required")
        require(torch.__version__=="2.10.0+cpu" and torch_npu.__version__=="2.10.0.post4","pinned runtime versions")
        require(hasattr(torch.npu,"NPUGraph") and hasattr(torch.npu,"graph"),"no eager fallback for absent graph API")
        report["versions"]={"torch":torch.__version__,"torch_npu":torch_npu.__version__,
                            "actual_runtime_soc":torch.npu.get_device_name("npu:0")}
        report["npu_executed"]=True;gate.save()
        import native_compressed_golden
        run_npu_gate.mapped_bindings(gate,args,manifest,need_reference=False)
        native_rows=NativeRows(gate,protocols,native_compressed_golden,torch,torch_npu)
        native_rows.anchor(native)
        validate_native_anchors(report)
        # Private FunctionType globals inject NEW reference only; frozen files/modules unchanged.
        report["protocol_glue"]={
            "graph_case_source":str(Path(graph_protocol.__file__).resolve()),
            "metadata_fixture_source":str(BASE/"metadata_contract.py"),
            "actual_tokens":"T, not padded to16; fixture/meta slots=T+3",
            "changes":["shared SoA allocation/observation/DATA nonalias",
                       "actualT metadata negatives instead of old B1/B16 fixture restriction",
                       "NEW trueT native rows, admitted by six actual B16 split anchors"]}
        for batch in BATCH_GROUPS[args.physical_card]:
            for kind in LAYOUTS:
                for variant in (0,1):
                    registry=Registry(kind,gate);registries.append(registry)
                    case_callable=clone_graph_case(graph_protocol,protocols,native_rows,registry,
                                                   metadata_cases,storage_disjoint)
                    previous=len(report["cases"])
                    case_callable(gate,candidate,native,registry.nd,batch,variant)
                    require(len(report["cases"])==previous+1,"one unchanged frozen graph case expected")
                    case=report["cases"][-1]
                    case["shared_arena_layout"]=kind
                    case["actual_token_metadata"]=copy_bounds(batch)
                    case["shared_arena_audit"]=registry.manifest()
                    require(len(case["shared_arena_audit"]["arenas"])==4 and
                            registry.guard_count>160*3,"three independent feedback arenas and one warmup; real guards")
                    require(case["batch"]==batch and all(len(s["indices"])==batch for s in case["steps"]),
                            "every execution uses actual T metadata, no fake padding slots")
                    case["graph_numerical_status"]="passed"
                    case["status"]="running"
                    case["actual_overlap_rejections"]=overlap_negatives(gate,candidate,registry,batch)
                    case["status"]="passed"
                    case["shared_arena_audit_after_negatives"]=registry.manifest()
                    run_npu_gate.mapped_bindings(gate,args,manifest,need_reference=False)
                    gate.save()
        expected={(batch,kind,variant) for batch in BATCH_GROUPS[args.physical_card]
                  for kind in LAYOUTS for variant in
                  ("SR1_perHv_permutations","power2_perHv_permutations")}
        require({(c["batch"],c.get("shared_arena_layout"),c.get("variant")) for c in report["cases"]}==expected and
                len(report["cases"])==16 and all(c["status"]=="passed" and
                len(c["steps"])==160 and c["identical_repeats"]==8 and c["changed_replays"]==160 and
                c["warmups"]==3 and len(c["invalid_dynamic_cases"])==len(metadata_cases(c["batch"],c["batch"]+3)) and
                len(c["actual_overlap_rejections"])==15 for c in report["cases"]),
                "complete registered16-case/four-realT shared-arena shard")
        # Source after check does not change any manifest; build/source identities remain exact.
        require(source_bindings(args)==bindings,"source/library/receipt drift during NPU gate")
        validate_native_anchors(report)
        report["sources_after"]=source_snapshot()
        require(report["sources_after"]==report["sources_before"],"NEW source drift")
        report.update(status="restricted_all_batch_shared_arena_shard_pass",graph_supported=True,shared_arena_supported=True,
            graph_scope="only actual v3 sameSO/registered four realT/SR1-power2 with retained raw+views, coldprepared static plans")
        return 0
    except BaseException as error:
        if gate is not None and gate.case is not None and gate.case["status"]=="running":
            gate.case.update(status="failed",error=repr(error))
        report.update(status="failed",error=repr(error),traceback=traceback.format_exc())
        if gate is not None:
            # Do not issue a second unguarded GPU copy after a poisoned context.
            retain_failure(gate,report,error)
        return 1
    finally:
        report["completed_ns"]=time.time_ns()
        try:report["sources_after"]=source_snapshot()
        except BaseException as secondary:report["source_after_error"]=repr(secondary)
        if gate is not None:
            try:report["loaded_libraries_final"]=loaded_libraries()
            except BaseException as error:report["library_snapshot_error"]=repr(error)
            try:gate.save()
            except BaseException as secondary:print("secondary report-save error: "+repr(secondary),file=sys.stderr)
        else:
            try:save_plain()
            except BaseException as secondary:print("secondary report-save error: "+repr(secondary),file=sys.stderr)
        print(json.dumps({"status":report["status"],"batches":report["batches"],
                          "npu_executed":report["npu_executed"],"report":str(out/"report.json")}))
if __name__=="__main__":
    raise SystemExit(main())
