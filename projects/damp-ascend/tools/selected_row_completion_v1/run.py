#!/usr/bin/env python3
"""Default-OFF genuine missing complete cases; frozen numerical code objects."""
import argparse, ctypes, importlib.util, json, os, sys, time, traceback
from pathlib import Path
import validator as v
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def report_save(out,report):
    (out/"report.json").write_text(json.dumps(report,allow_nan=False,indent=2)+"\n")
def secondary(report,where,error,primary):
    report.setdefault("secondary_errors",[]).append({"where":where,"error":repr(error)})
    print("secondary "+where+": "+repr(error)+"; primary="+repr(primary),file=sys.stderr,flush=True)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ("library","source-manifest","runtime-manifest","build-receipt","device-proof",
        "native-source-manifest","original-authority","completion-source-manifest","case-plan"):
        p.add_argument("--"+n,type=Path,required=True);p.add_argument("--"+n+"-sha256",required=True)
    p.add_argument("--native-gdn-source",type=Path,default=Path("/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py"))
    p.add_argument("--physical-card",type=int,choices=(4,5,6,7),required=True)
    p.add_argument("--batches",type=int,nargs="+",required=True)
    p.add_argument("--packet-sha256",default=v.OLD_PIN)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--audit-only",action="store_true")
    a=p.parse_args();c=v.context()
    source_ref={"path":str(a.completion_source_manifest),"sha256":a.completion_source_manifest_sha256}
    sources=v.source_manifest(source_ref,c)
    old_ref={"path":str(a.original_authority),"sha256":a.original_authority_sha256}
    base=v.original(old_ref,c)
    plan=v.json_ref({"path":str(a.case_plan),"sha256":a.case_plan_sha256})
    v.need(plan.get("schema")=="damp-selected-row-completion-case-plan/v1" and
        plan.get("original_authority")==old_ref and plan.get("physical_card")==a.physical_card and
        plan.get("deadline_utc")=="2026-10-07T08:48:03Z","actual terminal-derived missing-case plan")
    chosen=v.selected_keys(plan["cases"],base,a.physical_card)
    v.need(tuple(a.batches)==v.GROUPS[a.physical_card] and a.packet_sha256==v.OLD_PIN,
        "original group/source admission, true-T case subset separate")
    bindings=c.source_bindings(a)
    bindings["completion_source_manifest"]=source_ref
    if a.audit_only:
        print(json.dumps({"schema":"damp-selected-row-completion-source-audit/v1",
            "cases":[list(k) for k in chosen],"original_status":"failed-timeout",
            "npu_executed":False,"launchable":False,"bindings":bindings},allow_nan=False));return 0
    v.need(os.environ.get("DAMP_RUN_SELECTED_ROW_COMPLETION_V1")=="1","NEW explicit opt-in")
    v.need(all(os.environ.get(n)=="1" for n in ("DAMP_RUN_SELECTED_ROW_DISPATCH_V1",
        "DAMP_RUN_INDEPENDENT_ALLT_V1","DAMP_RUN_ALL_BATCH_GATE_V1","DAMP_ENABLE_ALL_BATCH_WRAPPER_V3")),
        "all original explicit device opt-ins")
    v.need(os.environ.get("ASCEND_RT_VISIBLE_DEVICES")=="0","MAIN single physical shard -> logical0")
    # Budget/release/fresh resources/canary remain MAIN's host producer, never invented here.
    from datetime import datetime,timezone
    left=(datetime.fromisoformat("2026-10-07T08:48:03+00:00")-datetime.now(timezone.utc)).total_seconds()
    v.need(left>180,"unchanged deadline cleanup reserve")
    out=c.new_output(a.output_dir)
    report={"schema":"damp-selected-row-missing-cases/v1","status":"running","namespace":c.NAMESPACE,
        "physical_card":a.physical_card,"batches":a.batches,"steps":160,"identical_repeats":8,"warmups":3,
        "limits":dict(c.LIMITS),"created_ns":time.time_ns(),"checks":[],"cases":[],
        "npu_executed":False,"graph_supported":False,"shared_arena_supported":False,
        "general_sr_supported":False,"serving_ready":False,"calibrated_plan_count":0,
        "performance_claim":False,"task_accuracy_claim":False,"secondary_errors":[],
        "bindings":bindings,"argv":list(sys.argv),"original_authority":old_ref,
        "completion_source_manifest":source_ref,"case_plan":{"path":str(a.case_plan),"sha256":a.case_plan_sha256},
        "selected_case_keys":[list(k) for k in chosen],"sources_before":sources,
        "reused_reference":{"fresh_anchor_execution":False,"original_operation_id":v.OP,
            "original_report":base["authority"]["reports"][str(a.physical_card)],
            "pairs":48,"anchors":6,"scope":"terminal/source/original-journal-bound reuse; NOT NEW NPU anchors"}}
    gate=None;primary=None;r=None;return_code=1
    report_save(out,report)
    try:
        # Original bootstrap and imported module owners retained; only selected case loop differs.
        sys.path.insert(0,str(c.OLD_DIR))
        r=load("_completion_frozen_runner",v.OLD/"runner.py")
        sys.path.insert(0,str(c.BASE));sys.path.insert(0,str(c.NUMERICAL_OLD/"graph_gate_v1"))
        sys.path.insert(0,str(c.NUMERICAL_OLD/"tests"))
        import torch,torch_npu,candidate_adapter,protocols,graph_protocol,run_npu_gate,gate_contract
        from native_call_contract import validate_native_schema
        from arena_adapter import Registry,Candidate,storage_disjoint,overlap_negatives
        from metadata_contract import metadata_cases,copy_bounds
        from reference_seam import clone_graph_case
        for m,e in ((candidate_adapter,c.NUMERICAL_OLD/"tests/candidate_adapter.py"),
            (protocols,c.NUMERICAL_OLD/"tests/protocols.py"),
            (graph_protocol,c.NUMERICAL_OLD/"graph_gate_v1/graph_protocol.py"),
            (run_npu_gate,c.NUMERICAL_OLD/"tests/run_npu_gate.py"),
            (gate_contract,c.NUMERICAL_OLD/"tests/gate_contract.py")):
            v.need(Path(m.__file__).resolve()==e.resolve(),"actual frozen import owner")
        Gate=r.journal_gate(candidate_adapter.Gate,candidate_adapter.safe_json)
        gate=Gate(out,report);gate.save()
        report["cann_environment"]=gate_contract.cann_environment_checks(bindings)
        proof=v.json_ref({"path":str(a.device_proof),"sha256":a.device_proof_sha256})
        c.validate_device(proof,a.physical_card,time.time_ns())
        report["device_proof"]={"path":str(a.device_proof),"sha256":a.device_proof_sha256,"content":proof}
        manifest=run_npu_gate.native_bindings(a,need_reference=False)
        report["native_source_manifest"]=manifest
        torch.set_num_threads(1);torch_npu.npu.set_compile_mode(jit_compile=False)
        from vllm_ascend.utils import enable_custom_op
        v.need(enable_custom_op(),"actual native bootstrap")
        handle=ctypes.CDLL(str(a.library.resolve()),mode=ctypes.RTLD_GLOBAL)
        v.need(getattr(handle,c.KERNEL,None) is not None,"defined actual launcher")
        torch.ops.load_library(str(a.library.resolve()));candidate=Candidate()
        report["candidate_schemas"]=candidate.schemas();report["candidate_meta"]=candidate.meta_gate()
        native=torch.ops._C_ascend.npu_recurrent_gated_delta_rule
        validate_native_schema(native.default._schema);report["native_schema"]=str(native.default._schema)
        torch.npu.set_device(0)
        v.need(torch.npu.get_device_name("npu:0")=="Ascend910B4" and torch.__version__=="2.10.0+cpu" and
            torch_npu.__version__=="2.10.0.post4","actual SoC/pinned runtime")
        v.need(hasattr(torch.npu,"NPUGraph") and hasattr(torch.npu,"graph"),"no eager fallback")
        report["versions"]={"torch":torch.__version__,"torch_npu":torch_npu.__version__,
            "actual_runtime_soc":torch.npu.get_device_name("npu:0")}
        import native_compressed_golden
        run_npu_gate.mapped_bindings(gate,a,manifest,need_reference=False)
        seam=c.load("_completion_actual_selected_seam",c.SELECTED_DIR/"seam.py")
        rows=seam.build_reference(gate,protocols,native_compressed_golden,torch,torch_npu,
            v.REPO,c.SELECTED_SHA,enabled=True)
        # Restore ONLY the checked original reference capability; no reference result copied as NEW.
        v.need(base["reports"][a.physical_card]["native_source_manifest"]==manifest,
            "same exact native source manifest as admitted original")
        rows.anchored=True;rows.local_equivalence_passed=True;rows.equivalence_batches=tuple(a.batches)
        report["native_row_reference"].update(anchors_reused_from=report["reused_reference"],
            anchors_passed=False) # False = NOT new anchor execution. Explicit reuse is separate.
        report["npu_executed"]=True;gate.save()
        for batch,kind,name in chosen:
            variant=v.VARS.index(name);registry=Registry(kind,gate)
            fn=clone_graph_case(graph_protocol,protocols,rows,registry,metadata_cases,storage_disjoint)
            previous=len(report["cases"]);started_ns=time.time_ns();started=time.monotonic();calls_before=rows.calls
            fn(gate,candidate,native,registry.nd,batch,variant)
            v.need(len(report["cases"])==previous+1,"one frozen complete case")
            case=report["cases"][-1]
            case.update(shared_arena_layout=kind,actual_token_metadata=copy_bounds(batch),
                shared_arena_audit=registry.manifest(),graph_numerical_status="passed",status="running")
            v.need(len(case["shared_arena_audit"]["arenas"])==4 and registry.guard_count>480,
                "original full arena/guard admission")
            case["actual_overlap_rejections"]=overlap_negatives(gate,candidate,registry,batch)
            case["shared_arena_audit_after_negatives"]=registry.manifest()
            case.update(status="passed",audit_started_ns=started_ns,audit_completed_ns=time.time_ns(),
                audit_elapsed_seconds=time.monotonic()-started,actual_native_calls=rows.calls-calls_before,
                timing_scope="correctness harness elapsed; NOT performance measurement")
            v.valid_case(case,metadata_cases)
            run_npu_gate.mapped_bindings(gate,a,manifest,need_reference=False);gate.save()
        v.need({v.key(x) for x in report["cases"]}==set(chosen) and len(report["cases"])==len(chosen),
            "complete selected subset")
        v.need(c.source_bindings(a)=={k:z for k,z in bindings.items() if k!="completion_source_manifest"},
            "frozen source/library/build drift")
        report["sources_after"]=v.source_manifest(source_ref,c)
        v.need(report["sources_after"]==sources,"NEW+old52 source drift")
        report.update(status="missing_cases_pass",graph_supported=True,shared_arena_supported=True)
        return_code=0
    except BaseException as error:
        primary=error
        if gate is not None and gate.case is not None and gate.case.get("status")=="running":
            gate.case.update(status="failed",error=repr(error))
        report.update(status="failed",error=repr(error),traceback=traceback.format_exc())
        if gate is not None:r.retain_failure(gate,report,error)
    finally:
        report["completed_ns"]=time.time_ns()
        for where,fn in (("source_after",lambda:v.source_manifest(source_ref,c)),
                         ("loaded_libraries_final",lambda:candidate_adapter.loaded_libraries())):
            try:report["sources_after" if where=="source_after" else where]=fn()
            except BaseException as error:secondary(report,where,error,primary);return_code=1
        try:
            if gate is not None:gate.save();gate.close()
            else:report_save(out,report)
        except BaseException as error:secondary(report,"final_evidence",error,primary);return_code=1
        if return_code!=0:report["status"]="failed"
        # A final close/save error is stderr+exit failure even if the last report cannot be updated.
        print(json.dumps({"schema":"damp-selected-row-completion-result/v1","status":report["status"],
            "report":str(out/"report.json"),"cases":len(report["cases"]),"npu_executed":report["npu_executed"],
            "serving_ready":False},allow_nan=False),flush=True)
    return return_code
if __name__=="__main__":raise SystemExit(main())
