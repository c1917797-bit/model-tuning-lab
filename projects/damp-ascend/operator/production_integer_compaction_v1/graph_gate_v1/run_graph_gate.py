#!/usr/bin/env python3
"""Default-OFF restricted B1/B16 operator graph/metadata gate, not serving."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import sys
import time
import traceback
from graph_contract import (BASE, PROJECT, PRIOR_REPORT_SHA, STEPS, VARIANTS,
    require, old_contract, graph_source_bindings, validate_frozen_evidence)
old=old_contract()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    old.add_identity_arguments(parser)
    for name in ("graph-runtime-manifest","eager-report","device-proof","native-source-manifest"):
        parser.add_argument("--"+name,type=Path,required=True)
        parser.add_argument("--"+name+"-sha256",required=True)
    parser.add_argument("--native-gdn-source",type=Path,
        default=Path("/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py"))
    parser.add_argument("--audit-only",action="store_true",
        help="stdlib source/receipt admission only; no Torch import/load/NPU")
    args=parser.parse_args()
    require(args.eager_report_sha256==PRIOR_REPORT_SHA,"exact prior eager report required")
    # Entire new runtime and frozen old runtime identities precede Torch imports.
    bindings=graph_source_bindings(args)
    admission=validate_frozen_evidence(args,bindings)
    if args.audit_only:
        print(json.dumps({"status":"source_admission_only_pass","npu_executed":False,
            "graph_supported":False,"bindings":bindings,"eager_admission":admission}))
        return 0
    require(os.environ.get("DAMP_RUN_GRAPH_GATE_V1")=="1" and
            os.environ.get("DAMP_ENABLE_INTEGER_COMPACTION_V1")=="1",
            "both graph diagnostic and candidate explicit opt-ins required")
    require(os.environ.get("ASCEND_RT_VISIBLE_DEVICES")=="0","parent proves physical4 -> logical0 only")
    out=old.new_output(args.output_dir)
    report={"schema":"damp_integer_compaction_graph_metadata_gate_v1","status":"running",
        "namespace":old.NAMESPACE,"steps":STEPS,"identical_repeats":8,"warmups":3,
        "limits":dict(old.LIMITS),"checks":[],"cases":[],"created_ns":time.time_ns(),
        "npu_executed":False,"graph_supported":False,"serving_ready":False,
        "general_sr_supported":False,"calibrated_plan_count":0,
        "scope":"same-SO restricted B1/B16 one-token SR1/power2 graph + malformed dynamic metadata only; "
                "not T2..15, mixed scheduling, general SR, cache manager, service/E2E/task quality",
        "bindings":bindings,"eager_admission":admission,
        "feedback":"independent native-derived packed feedback, no candidate-side golden or step resync",
        "capture":"prepare cold outside capture; separate resettable warmup arena; input sync before replay"}
    gate=None
    def save_report():
        (out/"report.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    save_report()
    try:
        import torch
        import torch_npu
        from candidate_adapter import Candidate,Gate,loaded_libraries
        from run_npu_gate import native_bindings,mapped_bindings
        from general_sr_contract import validate_device_proof
        from native_call_contract import validate_native_schema
        from graph_protocol import graph_case
        gate=Gate(out,report);gate.save()
        report["cann_environment"]=old.cann_environment_checks(bindings)
        proof_path=old.checked_file(args.device_proof,args.device_proof_sha256)
        proof=old.read_json(proof_path);validate_device_proof(proof,time.time_ns())
        report["device_proof"]={"path":str(proof_path),"sha256":old.sha(proof_path),"content":proof,
                                "authority":"fresh MAIN observations; not inferred ordinal or old eager proof"}
        manifest=native_bindings(args,need_reference=False)
        require(manifest==old.read_json(old.checked_file(args.eager_report,PRIOR_REPORT_SHA))[
                "native_source_manifest"],"new graph native provenance differs from actual eager admission")
        report["native_source_manifest"]=manifest
        torch.set_num_threads(1)
        torch_npu.npu.set_compile_mode(jit_compile=False)
        from vllm_ascend.utils import enable_custom_op
        require(enable_custom_op(),"actual native bootstrap unavailable")
        handle=ctypes.CDLL(str(args.library.resolve()),mode=ctypes.RTLD_GLOBAL)
        require(getattr(handle,old.KERNEL_SYMBOL,None) is not None,"actual launcher unresolved")
        torch.ops.load_library(str(args.library.resolve()))
        candidate=Candidate()
        report["candidate_schemas"]=candidate.schemas()
        report["candidate_meta"]=candidate.meta_gate()
        native=torch.ops._C_ascend.npu_recurrent_gated_delta_rule
        validate_native_schema(native.default._schema)
        report["native_schema"]=str(native.default._schema)
        torch.npu.set_device(0)
        require(torch.npu.get_device_name("npu:0")=="Ascend910B4","real runtime SoC mismatch")
        require(torch.__version__=="2.10.0+cpu" and torch_npu.__version__=="2.10.0.post4",
                "pinned runtime versions required")
        require(hasattr(torch.npu,"NPUGraph") and hasattr(torch.npu,"graph"),
                "actual NPUGraph API unavailable; no silent eager substitute")
        report["versions"]={"torch":torch.__version__,"torch_npu":torch_npu.__version__,
                            "actual_runtime_soc":torch.npu.get_device_name("npu:0")}
        report["npu_executed"]=True;gate.save()
        def nd(x):
            result=torch_npu.npu_format_cast(x.to("npu:0").contiguous(),2)
            require(torch_npu.get_npu_format(result)==2 and result.data_ptr()%32==0,
                    "preparation physical ND/32B pointer required")
            return result
        for batch in (1,16):
            for variant in (0,1):
                graph_case(gate,candidate,native,nd,batch,variant)
                mapped_bindings(gate,args,manifest,need_reference=False)
        require(len(report["cases"])==4 and all(c["status"]=="passed" and
            len(c["steps"])==STEPS and c["identical_repeats"]==8 and
            c["changed_replays"]==STEPS and c["warmups"]==3 and
            len(c["invalid_dynamic_cases"])==(9 if c["batch"]==1 else 11)
            for c in report["cases"]),"complete pre-registered four-case graph/metadata matrix")
        report["status"]="restricted_graph_metadata_pass"
        report["graph_supported"]=True
        report["graph_scope"]="only same SO/B1/B16/SR1-power2 with cold-prepared static plans and fixed geometry"
        return 0
    except BaseException as error:
        if gate is not None and gate.case is not None and gate.case["status"]=="running":
            gate.case.update(status="failed",error=repr(error))
        report.update(status="failed",error=repr(error),traceback=traceback.format_exc())
        if gate is not None:gate.retain()
        return 1
    finally:
        report["completed_ns"]=time.time_ns()
        try:report["loaded_libraries_final"]=loaded_libraries()
        except BaseException as error:report["library_snapshot_error"]=repr(error)
        if gate is not None:gate.save()
        else:save_report()
        print(json.dumps({"status":report["status"],"npu_executed":report["npu_executed"],
                          "report":str(out/"report.json")}))
if __name__=="__main__":
    raise SystemExit(main())
