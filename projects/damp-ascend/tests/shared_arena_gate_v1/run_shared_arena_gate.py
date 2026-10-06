#!/usr/bin/env python3
"""Default-OFF shared-raw-arena restricted graph/eager gate. MAIN alone executes."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import sys
import time
import traceback
from contract import (BASE,PROJECT,OLD,NAMESPACE,KERNEL,LIMITS,LAYOUTS,
                      checked,sha,require,source_bindings,validate_device,new_output)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("library","source-manifest","runtime-manifest","build-receipt",
                 "device-proof","native-source-manifest"):
        parser.add_argument("--"+name,type=Path,required=True)
        parser.add_argument("--"+name+"-sha256",required=True)
    parser.add_argument("--batch",type=int,choices=(1,16),required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    parser.add_argument("--native-gdn-source",type=Path,
        default=Path("/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py"))
    parser.add_argument("--audit-only",action="store_true")
    args=parser.parse_args()
    bindings=source_bindings(args)  # Before Torch imports or library load.
    if args.audit_only:
        print(json.dumps({"status":"source_admission_only_pass","npu_executed":False,
                          "shared_arena_supported":False,"bindings":bindings}))
        return 0
    require(os.environ.get("DAMP_RUN_SHARED_ARENA_GATE_V1")=="1" and
            os.environ.get("DAMP_ENABLE_ARENA_WRAPPER_V2")=="1","two explicit NEW opt-ins")
    require(os.environ.get("ASCEND_RT_VISIBLE_DEVICES")=="0","MAIN proves one physical shard ->logical0")
    out=new_output(args.output_dir)
    report={"schema":"damp_shared_arena_restricted_graph_gate_v1","status":"running",
        "namespace":NAMESPACE,"batch":args.batch,"steps":160,"identical_repeats":8,"warmups":3,
        "limits":dict(LIMITS),"checks":[],"cases":[],"created_ns":time.time_ns(),
        "npu_executed":False,"graph_supported":False,"shared_arena_supported":False,
        "serving_ready":False,"general_sr_supported":False,"calibrated_plan_count":0,
        "bindings":bindings,
        "scope":"synthetic shared SoA B1 orB16/SR1-power2 only: two graphs+eager, "
                "adjacent/guard-gaps, independent native feedback; not actual model cache/service,"
                "T2..15/general-SR graph/final192plans/E2E/task accuracy",
        "feedback":"independent native-derived CPU packed golden, no candidate resync or persistent FP32 cache"}
    gate=None;registries=[]
    def save_plain():
        (out/"report.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    save_plain()
    try:
        # Reuse frozen protocol functions; no source rewrite, no old registry reassignment.
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
        for module,expected in ((candidate_adapter,OLD/"tests/candidate_adapter.py"),
                                (protocols,OLD/"tests/protocols.py"),
                                (graph_protocol,OLD/"graph_gate_v1/graph_protocol.py"),
                                (run_npu_gate,OLD/"tests/run_npu_gate.py"),
                                (gate_contract,OLD/"tests/gate_contract.py")):
            require(Path(module.__file__).resolve()==expected.resolve(),"unexpected imported protocol module")
        gate=Gate(out,report);gate.save()
        report["cann_environment"]=gate_contract.cann_environment_checks(bindings)
        device_path=checked(args.device_proof,args.device_proof_sha256)
        proof=json.loads(device_path.read_text());validate_device(proof,args.batch,time.time_ns())
        report["device_proof"]={"path":str(device_path),"sha256":sha(device_path),"content":proof,
                               "authority":"fresh MAIN physical4/B1 orphysical7/B16 inspection"}
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
        # Only observation/allocation/nonalias glue is replaced IN THIS PROCESS.
        # Golden fixture/update/pack/restore/functions and thresholds are untouched.
        for kind in LAYOUTS:
            for variant in (0,1):
                registry=Registry(kind,gate);registries.append(registry)
                protocols.observe=registry.observe
                protocols.storage_disjoint=storage_disjoint
                graph_protocol.observe=registry.observe
                graph_protocol.storage_disjoint=storage_disjoint
                previous=len(report["cases"])
                graph_protocol.graph_case(gate,candidate,native,registry.nd,args.batch,variant)
                require(len(report["cases"])==previous+1,"one frozen graph case expected")
                case=report["cases"][-1]
                case["shared_arena_layout"]=kind
                case["shared_arena_audit"]=registry.manifest()
                require(len(case["shared_arena_audit"]["arenas"])==4 and
                        registry.guard_count>160*3,"three independent feedback arenas and one warmup; real guards")
                case["graph_numerical_status"]="passed"
                case["status"]="running"  # Actual-overlap no-write remains part of this NEW case.
                case["actual_overlap_rejections"]=overlap_negatives(gate,candidate,registry,args.batch)
                case["status"]="passed"
                case["shared_arena_audit_after_negatives"]=registry.manifest()
                run_npu_gate.mapped_bindings(gate,args,manifest,need_reference=False)
                gate.save()
        expected={(kind,variant) for kind in LAYOUTS for variant in
                  ("SR1_perHv_permutations","power2_perHv_permutations")}
        require({(c.get("shared_arena_layout"),c.get("variant")) for c in report["cases"]}==expected and
                len(report["cases"])==4 and all(c["batch"]==args.batch and c["status"]=="passed" and
                len(c["steps"])==160 and c["identical_repeats"]==8 and c["changed_replays"]==160 and
                c["warmups"]==3 and len(c["invalid_dynamic_cases"])==(9 if args.batch==1 else 11) and
                len(c["actual_overlap_rejections"])==15 for c in report["cases"]),
                "complete registered four-case one-batch shared-arena matrix")
        # Source after check does not change any manifest; build/source identities remain exact.
        require(source_bindings(args)==bindings,"source/library/receipt drift during NPU gate")
        report.update(status="restricted_shared_arena_graph_pass",graph_supported=True,shared_arena_supported=True,
            graph_scope="only actual v2 sameSO/this batch/SR1-power2 with retained raw+views, coldprepared static plans")
        return 0
    except BaseException as error:
        if gate is not None and gate.case is not None and gate.case["status"]=="running":
            gate.case.update(status="failed",error=repr(error))
        report.update(status="failed",error=repr(error),traceback=traceback.format_exc())
        if gate is not None:
            # Do not issue a second unguarded GPU copy after a poisoned context.
            gate.retain()
        return 1
    finally:
        report["completed_ns"]=time.time_ns()
        if gate is not None:
            try:report["loaded_libraries_final"]=loaded_libraries()
            except BaseException as error:report["library_snapshot_error"]=repr(error)
            gate.save()
        else:save_plain()
        print(json.dumps({"status":report["status"],"batch":args.batch,
                          "npu_executed":report["npu_executed"],"report":str(out/"report.json")}))
if __name__=="__main__":
    raise SystemExit(main())
