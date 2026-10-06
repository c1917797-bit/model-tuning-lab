#!/usr/bin/env python3
"""New explicit candidate numerical gate; parent alone launches it."""
import argparse
import ctypes
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback
import torch
from gate_contract import (PROJECT, REPO, NAMESPACE, STEPS, LIMITS, GDN_SHA, IMAGE_ID,
    NATIVE_COMMIT, NATIVE_HEADER_SHA, SAVED_STEP45_SHA, add_identity_arguments,
    source_bindings, cann_environment_checks, checked_file, new_output, require, read_json, sha)
from candidate_adapter import (Candidate, Gate, loaded_libraries, observe, exact,
    REGIONS, packed_dict, storage_disjoint)
from protocols import (anchor_case, general_case, restricted_case, make_layout, turn,
    audit_cast, ANCHOR_VARIANTS, GENERAL_VARIANTS, OracleLayout, ValueMajorPacked,
    errors, restore_state, unpack_value_major, invoke_prepare_guard, native_step)
from general_sr_contract import validate_device_proof, assert_matrix_order
from native_call_contract import validate_native_schema
from general_sr_native_gate import REFERENCE_HASHES

def native_bindings(args, need_reference):
    path = checked_file(args.native_source_manifest,args.native_source_manifest_sha256)
    manifest = read_json(path)
    require(manifest.get("native_commit")==NATIVE_COMMIT and
            manifest.get("native_header_sha256")==NATIVE_HEADER_SHA and
            manifest.get("image_id")==IMAGE_ID and manifest.get("source_contract_passed") is True,
            "frozen ordinary DAV2201 native source/image/source-contract mismatch")
    checked_file(manifest["native_runtime_library_path"],manifest["native_runtime_library_sha256"])
    checked_file(args.native_gdn_source,GDN_SHA)
    if need_reference:
        refpath = checked_file(args.reference_library,args.reference_sha256)
        require(refpath.name=="libqwen36_damp_native_reference_ops.so" and
                manifest.get("reference_source_hashes")==REFERENCE_HASHES and
                manifest.get("reference_library_path")==str(refpath) and
                manifest.get("reference_library_sha256")==args.reference_sha256,
                "new external manifest must bind actual independent reference SO + frozen10sources")
        for name,expected in REFERENCE_HASHES.items():
            require(sha(PROJECT/"operator/reference"/name)==expected,"reference source changed "+name)
    return manifest

def mapped_bindings(gate, args, native_manifest, need_reference):
    mapped = loaded_libraries()
    expected = [(args.library,args.library_sha256),
                (Path(native_manifest["native_runtime_library_path"]),native_manifest["native_runtime_library_sha256"])]
    if need_reference: expected.append((args.reference_library,args.reference_sha256))
    for path,digest in expected:
        require(mapped.get(str(path.resolve()))==digest,"expected actual loaded native/candidate/reference library absent")
    gate.report["loaded_libraries_latest"] = mapped
    gate.save()

def step45_case(gate,candidate,native,nd,torch_npu,args):
    fixture = checked_file(args.step45_fixture,SAVED_STEP45_SHA)
    source = checked_file(args.step45_source_report,args.step45_source_report_sha256)
    source_report = read_json(source)
    require(source_report.get("schema")=="damp-restricted-native-compressed-golden/v1" and
            source_report.get("first_failure_fixture",{}).get("sha256")==SAVED_STEP45_SHA,
            "saved restricted failure report/fixture binding")
    module_path = PROJECT/"operator/diagnostic/run_saved_step45_trace.py"
    spec = importlib.util.spec_from_file_location("damp_saved_failure_fixture_audit",module_path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    frozen = torch.load(fixture,map_location="cpu",weights_only=True)
    require(frozen.get("stage")=="closed_loop" and frozen.get("batch")==1 and
            frozen.get("variant")==0 and frozen.get("step")==45,"exact B1 restricted step45 required")
    audit = module.audit_fixture(frozen,source_report)
    layout = OracleLayout(frozen["layout"]["c"],frozen["layout"]["pv"],frozen["layout"]["pk"])
    before = ValueMajorPacked(*(frozen["actual_before"][n] for n in REGIONS))
    expected = ValueMajorPacked(*(frozen["golden_after"][n] for n in REGIONS))
    arena = [nd(getattr(before,n)) for n in REGIONS]
    plans = [nd(x.int()) for x in (layout.pk,layout.pv,layout.pv.argsort(1))]
    sr = nd(layout.c); lengths = nd(torch.tensor([0,1],dtype=torch.int32))
    inputs = [nd(frozen[n]) for n in ("q","k","v","g","beta")]
    indices = nd(frozen["indices"])
    gate.start_case("saved_step45",1,"exact_frozen_repair")
    gate.fixture = {"stage":"saved_step45","fixture_sha256":SAVED_STEP45_SHA,"saved":frozen,
                    "audit":audit,"candidate_before":packed_dict(before)}
    # Re-establish the saved actual native golden on this SAME immutable input.
    current_native, cpu_native, _ = observe(gate,"saved_step45_native",
        lambda: native_step(before,layout,*(frozen[n] for n in ("q","k","v","g","beta")),
                            frozen["indices"],native,"npu:0"),[])
    require(all(exact(getattr(current_native["packed"],n),getattr(expected,n)) for n in REGIONS) and
            exact(current_native["original_output_bf16"],frozen["native_evidence"]["original_output_bf16"]),
            "current loaded native differs from the source-bound saved golden")
    gate.fixture["current_native"] = cpu_native
    invoke_prepare_guard(gate,candidate.prepare,[inputs[0],arena[0],*plans,sr],arena)
    output,cpu_output,after = observe(gate,"candidate_decode",
        lambda: candidate.decode(*inputs,*arena,*plans,sr,lengths,indices),
        inputs+arena+plans+[sr,lengths,indices])
    actual = ValueMajorPacked(*after[5:8])
    ids = frozen["indices"].long()
    untouched = [s for s in range(4) if s not in ids.tolist()]
    metric = errors(restore_state(unpack_value_major(actual,layout),layout),
                    restore_state(unpack_value_major(expected,layout),layout))
    record = gate.fixture["candidate_decode"]
    guards = {
        "all_three_complete_packed_regions_bitwise":all(exact(getattr(actual,n),getattr(expected,n)) for n in REGIONS),
        "output_vs_saved_native_bitwise":exact(cpu_output,frozen["native_evidence"]["original_output_bf16"]),
        "untouched_slots_bitwise":all(exact(getattr(actual,n)[untouched],getattr(before,n)[untouched]) for n in REGIONS),
        "immutable_inputs_bitwise":all(exact(record["before"][i],after[i])
                                      for i in list(range(5))+list(range(8,14))),
        "all_pointers_stable":record["pointers_before"]==record["pointers_after"],
        "output_ABI":tuple(output.shape)==(1,12,128) and output.dtype==torch.bfloat16,
        "output_ND":torch_npu.get_npu_format(output)==2,
        "output_nonalias":all(storage_disjoint(output,x) for x in inputs+arena+plans+[sr,lengths,indices]),
    }
    gate.fixture.update(candidate_after=packed_dict(actual),candidate_output=cpu_output)
    # Exact quantizer repair receipt: not a replacement for the160step gates.
    target = gate.out/"saved-step45-actual.pt"
    torch.save(gate.fixture,target)
    gate.report["saved_step45_artifact"] = {"path":str(target),"sha256":sha(target)}
    gate.step({"step":45,"passed":all(guards.values()) and metric["finite"],
               "guards":guards,"complete_state":metric,"scope":"single saved failure repair only"})
    gate.end_case()

def reference_schema(ref):
    schema = ref.default._schema
    require([x.name for x in schema.arguments] ==
            ["q","k","v","g","beta","state_selected","pk","pv","inv_pv","sr"] and
            len(schema.returns)==3 and not any(x.alias_info for x in schema.arguments) and
            not any(x.alias_info for x in schema.returns),"independent reference readonly/fresh-output schema")
    return str(schema)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_identity_arguments(parser)
    parser.add_argument("--stage",choices=("restricted","anchors","general","step45","all"),required=True)
    parser.add_argument("--steps",type=int,default=STEPS)
    for name in ("device-proof","native-source-manifest","step45-source-report"):
        parser.add_argument("--"+name,type=Path)
        parser.add_argument("--"+name+"-sha256")
    parser.add_argument("--native-gdn-source",type=Path,
                        default=Path("/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py"))
    parser.add_argument("--reference-library",type=Path)
    parser.add_argument("--reference-sha256")
    parser.add_argument("--step45-fixture",type=Path)
    args = parser.parse_args()
    require(1<=args.steps<=STEPS,"steps1..160; shorter receipts are smoke-only")
    require(os.environ.get("ASCEND_RT_VISIBLE_DEVICES")=="0","logical0 only, parent proves physical4")
    require(os.environ.get("DAMP_ENABLE_INTEGER_COMPACTION_V1")=="1","new candidate explicit opt-in required")
    need_reference = args.stage in ("anchors","general","all")
    need_step45 = args.stage in ("step45","all")
    if need_reference:
        require(os.environ.get("DAMP_ENABLE_NATIVE_REFERENCE")=="1","test-only independent reference opt-in required")
        require(args.reference_library and args.reference_sha256,"independent reference library/hash required")
    require(args.device_proof and args.device_proof_sha256 and
            args.native_source_manifest and args.native_source_manifest_sha256,"fresh device/native identities required")
    if need_step45:
        require(args.step45_fixture and args.step45_source_report and args.step45_source_report_sha256,
                "exact saved fixture + source failure report/hash required")
    out = new_output(args.output_dir)
    report = {"schema":"damp_integer_compaction_npu_gate_v1","status":"running","namespace":NAMESPACE,
              "stage":args.stage,"steps":args.steps,"matrix_class":"full-160" if args.steps==STEPS else "smoke-only",
              "limits":LIMITS,"checks":[],"cases":[],"created_ns":time.time_ns(),"npu_executed":False,
              "graph_supported":False,"serving_ready":False,"calibrated_plan_count":0,
              "scope":"synthetic eager B1/B16 one-token numerical gates only; no TP4 cache/graph/service, E2E speed or task accuracy",
              "feedback":"two independently compressed trajectories, no step resync or production FP32 sidecar"}
    gate = Gate(out,report)
    try:
        report["bindings"] = source_bindings(args)
        report["cann_environment"] = cann_environment_checks(report["bindings"])
        device_path = checked_file(args.device_proof,args.device_proof_sha256)
        device = read_json(device_path); validate_device_proof(device,time.time_ns())
        report["device_proof"] = {"path":str(device_path),"sha256":sha(device_path),"content":device,
                                 "authority":"fresh external MAIN inspection, not inferred logical ordinal"}
        native_manifest = native_bindings(args,need_reference)
        report["native_source_manifest"] = native_manifest
        torch.set_num_threads(1)
        import torch_npu
        from vllm_ascend.utils import enable_custom_op
        torch_npu.npu.set_compile_mode(jit_compile=False)
        require(enable_custom_op(),"actual native bootstrap unavailable")
        handle = ctypes.CDLL(str(args.library.resolve()),mode=ctypes.RTLD_GLOBAL)
        require(getattr(handle,"qwen36_gdn_damp_integer_compaction_v1_decode_kernel",None) is not None,
                "actual host launcher unresolved")
        torch.ops.load_library(str(args.library.resolve()))
        candidate = Candidate()
        report["candidate_schemas"] = candidate.schemas()
        report["candidate_meta"] = candidate.meta_gate()
        if need_reference:
            torch.ops.load_library(str(args.reference_library.resolve()))
            ref = torch.ops.qwen36_damp_reference.decode
            report["reference_schema"] = reference_schema(ref)
        native = torch.ops._C_ascend.npu_recurrent_gated_delta_rule
        report["native_schema"] = str(native.default._schema)
        validate_native_schema(native.default._schema)
        torch.npu.set_device(0)
        require(torch.npu.get_device_name("npu:0")=="Ascend910B4","actual runtime SoC mismatch")
        require(torch.__version__=="2.10.0+cpu" and torch_npu.__version__=="2.10.0.post4",
                "frozen deployed Torch/TorchNPU mismatch")
        report["versions"] = {"torch":torch.__version__,"torch_npu":torch_npu.__version__,
                              "actual_runtime_soc":torch.npu.get_device_name("npu:0")}
        report["npu_executed"] = True; gate.save()
        def nd(x):
            result = torch_npu.npu_format_cast(x.to("npu:0").contiguous(),2)
            require(torch_npu.get_npu_format(result)==2 and result.data_ptr()%32==0,
                    "explicit test preparation requires physical ND /32B pointer")
            return result
        if need_step45:
            step45_case(gate,candidate,native,nd,torch_npu,args)
            mapped_bindings(gate,args,native_manifest,need_reference=False)
        if args.stage in ("restricted","all"):
            for batch in (1,16):
                for variant in (0,1):
                    restricted_case(gate,candidate,native,nd,torch_npu,batch,variant,args.steps)
                    mapped_bindings(gate,args,native_manifest,need_reference=False)
        if need_reference:
            # ALL six NEW strict bitwise anchors finish before ANY general-SR.
            for batch in (1,16):
                for variant in range(len(ANCHOR_VARIANTS)):
                    anchor_case(gate,native,ref,nd,torch_npu,batch,variant,args.steps)
                    mapped_bindings(gate,args,native_manifest,need_reference=True)
            anchored = [x for x in report["cases"] if x["stage"] in ("anchor","general")]
            assert_matrix_order(anchored,require_complete_anchor=True)
            gate.require("all_six_new_reference_native_anchors_bitwise_passed",all(x["status"]=="passed" for x in anchored))
            if args.stage in ("general","all"):
                for batch in (1,16):
                    for variant in range(len(GENERAL_VARIANTS)):
                        general_case(gate,candidate,ref,nd,torch_npu,batch,variant,args.steps)
                        mapped_bindings(gate,args,native_manifest,need_reference=True)
                assert_matrix_order([x for x in report["cases"] if x["stage"] in ("anchor","general")],
                                    require_complete_anchor=True)
        report["status"] = (args.stage+"_numerical_pass" if args.steps==STEPS else args.stage+"_smoke_only_pass")
        if args.stage=="step45": report["status"]="saved_step45_bitwise_repair_pass"
        return 0
    except BaseException as error:
        if gate.case is not None and gate.case["status"]=="running": gate.case.update(status="failed",error=repr(error))
        report.update(status="failed",error=repr(error),traceback=traceback.format_exc())
        gate.retain()
        return 1
    finally:
        report["completed_ns"] = time.time_ns()
        try: report["loaded_libraries_final"] = loaded_libraries()
        except BaseException as error: report["library_snapshot_error"]=repr(error)
        gate.save()
        print(json.dumps({"status":report["status"],"stage":args.stage,"npu_executed":report["npu_executed"],
                          "report":str(out/"report.json")}))
if __name__=="__main__":
    raise SystemExit(main())
