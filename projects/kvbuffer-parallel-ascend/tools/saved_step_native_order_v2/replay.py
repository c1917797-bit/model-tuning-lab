#!/usr/bin/env python3
"""Opt-in saved B1 failure replay. Diagnostic only, never matrix/E2E/accuracy authority."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,os,sys,time
from pathlib import Path

ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab")
PROJECT=ROOT/"projects/kvbuffer-parallel-ascend"
NEW=PROJECT/"tools/split_gate_v2"
MANIFEST_SHA="508ff442ede945b8fb5930f79ee597ec1dba07e5d4e778d9abc85aafda6ce9c9"
REPORT=Path("/cache/cch/qwen36-kvbuffer-parallel-20261006/split-dispatch-native-20261007-0830/b1/results/gate/report.json")
REPORT_SHA="759b8978ee44503fbe2a57df9b2956d0bbefe2b7e53170a678a3bc2bb07a4d03"
RAW_SHA="c53ef1f5263de0a058664d075b7e185fa1b33f06c05481dd0943d5796375a47a"
OLD_ORACLE=PROJECT/"tools/native_oracle_probe.py"
OLD_ORACLE_SHA="caa65dd94506edbd68a5600e9f813d93711ba162a8a2fc0565e7e00ede4414dd"
OLD_NAMESPACE="qwen36_kvbuffer_parallel_fp32"
OLD_LIBRARY=Path("/cache/cch/qwen36-kvbuffer-parallel-20261006/build-p1-v1/libqwen36_gdn_kvbuffer_parallel_ops.so")
OLD_LIBRARY_SHA="0e7c64b53314f1e822a27b5f373376d82d3f73c01264a384cf58ee4bc6e3477b"
NATIVE_PATH="/vllm-workspace/vllm-ascend/vllm_ascend/vllm_ascend_C.cpython-312-aarch64-linux-gnu.so"
NATIVE_SHA="eaa9457a21a45e2cb027c1345ee670b59d10fcd6f4a8be8b0b1bf2fde1d2232a"

def require(value,why):
    if not value:raise ValueError(why)

def sha(path):
    p=Path(path);require(p.is_file() and not p.is_symlink(),"ordinary exact file required")
    return hashlib.sha256(p.read_bytes()).hexdigest()

def frozen_module(path,digest,name):
    require(sha(path)==digest,"frozen module source drift")
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod
    spec.loader.exec_module(mod);return mod

def raw_ref():
    require(sha(REPORT)==REPORT_SHA,"original failed report changed")
    report=json.loads(REPORT.read_bytes())
    require(report["schema"]=="kvbp.split-native-gate/v1" and report["status"]=="failed",
            "original failed report is not a promoted PASS")
    case=next(c for c in report["cases"] if (c["batch"],c["mode"],c["trial"])==(1,"graph",2))
    row=next(s for s in case["steps"] if s["step"]==104)
    r=row["raw_step"];name=Path(r["file"])
    require(len(name.parts)==1 and name.name=="raw-step-b1-graph-t2-step104.pt" and
            row["passed"] is False and row["output_error"]>.00303 and
            r["retained"] is True and r["sha256"]==RAW_SHA and r["bytes"]==20819413,
            "exact original failure/raw identity")
    raw=REPORT.parent/name
    require(sha(raw)==RAW_SHA and raw.stat().st_size==r["bytes"],"original raw bytes drift")
    return raw,row

def bitwise(torch,a,b):
    if (a.shape,a.dtype)!=(b.shape,b.dtype):return False
    aa=a.detach().cpu().contiguous().view(torch.uint8)
    bb=b.detach().cpu().contiguous().view(torch.uint8)
    return bool(torch.equal(aa,bb))

def mapped(required):
    observed={}
    for line in Path("/proc/self/maps").read_text().splitlines():
        fields=line.split()
        if len(fields)>=6 and fields[-1] in required:
            observed[fields[-1]]=sha(fields[-1])
    require(observed==required,"actual mapped library bytes do not match required libraries")
    return observed

def collect(torch,helper,state,guards,native,x,y,expected):
    # Independent nullable copies preserve original dispatch errors if context is poisoned.
    errors={}
    def copy(label,t):
        if t is None:return None
        try:return t.detach().cpu().clone()
        except BaseException as e:errors[label]=repr(e);return None
    values={"after":{n:copy("after."+n,t) for n,t in state.items()},
            "guards":{n:copy("guards."+n,t) for n,t in guards.items()},
            "inputs":{n:copy("inputs."+n,t) for n,t in x.items()},
            "native":copy("native",native),"actual":copy("actual",y),
            "expected":copy("expected",expected)}
    try:pointers=helper.all_pointers(state,guards,native,x,y,expected)
    except BaseException as e:pointers=None;errors["pointers_after"]=repr(e)
    values.update(pointers_after=pointers,copy_errors=errors);return values

def allocate_from_fixture(torch,helper,fixture):
    # Complete guarded allocation identical to original oracle's layout.
    state,guards=helper.allocate(helper.nd(fixture["before"]["base"].to("npu:0")))
    for n in helper.NAMES:guards[n].copy_(fixture["guards_before"][n].to("npu:0"))
    require(all(bitwise(torch,state[n],fixture["before"][n]) for n in helper.NAMES),
            "full before/log/guard source restoration differs")
    native=helper.nd(fixture["native_before"].to("npu:0").clone())
    x={n:helper.nd(t.to("npu:0").clone()) for n,t in fixture["inputs"].items()}
    return state,guards,native,x

def step(torch,helper,fixture,ops,output,mode,label):
    state,guards,native,x=allocate_from_fixture(torch,helper,fixture)
    before={n:t.clone() for n,t in state.items()};immutable={n:t.clone() for n,t in x.items()}
    pointers=helper.all_pointers(state,guards,native,x)
    y=expected=None;original=None
    # prepare/capture and diagnostic failures use the same raw preservation path.
    try:
        ops.prepare(x["query"],state["base"]);torch.npu.synchronize()
        if mode=="graph":
            warm,warm_guards,_,warm_x=allocate_from_fixture(torch,helper,fixture)
            for _ in range(3):
                ops.decode(warm_x["query"],warm_x["key"],warm_x["value"],warm_x["g"],warm_x["beta"],
                           warm["base"],warm["k_log"],warm["u_log"],warm["lambda_log"],
                           warm["decay"],warm["length"],warm_x["seq"],warm_x["indices"])
                torch.npu.synchronize()
            graph=torch.npu.NPUGraph()
            with torch.npu.graph(graph):
                y=ops.decode(x["query"],x["key"],x["value"],x["g"],x["beta"],state["base"],
                             state["k_log"],state["u_log"],state["lambda_log"],state["decay"],
                             state["length"],x["seq"],x["indices"])
            torch.npu.synchronize()
            for n in helper.NAMES:guards[n].copy_(fixture["guards_before"][n].to("npu:0"))
            torch.npu.synchronize()
        # Original order: native mutation first, candidate operation second.
        expected=helper.native(native,x)
        if mode=="graph":
            torch.npu.synchronize();graph.replay()
        else:
            y=ops.decode(x["query"],x["key"],x["value"],x["g"],x["beta"],state["base"],
                         state["k_log"],state["u_log"],state["lambda_log"],state["decay"],
                         state["length"],x["seq"],x["indices"])
        torch.npu.synchronize()
    except BaseException as e:original=e
    raw=collect(torch,helper,state,guards,native,x,y,expected)
    raw.update(schema="kvbp.saved-replay-raw/v1",label=label,mode=mode,
               before=fixture["before"],native_before=fixture["native_before"],
               input_before=fixture["input_before"],guards_before=fixture["guards_before"],
               pointers_before=pointers,original_dispatch_error=repr(original) if original else None,
               updated_S_fp32_export="pending: no production kernel export",
               precast_readout_fp32_export="pending: no production kernel export")
    raw_path=output/(label+"-raw.pt")
    try:
        require(not raw_path.exists(),"raw evidence cannot overwrite")
        torch.save(raw,raw_path) # before metrics, logical reconstruction or any assertion.
    except BaseException as secondary:
        print(json.dumps({"primary":repr(original) if original else None,
                          "raw_save_error":repr(secondary),"raw_path":str(raw_path)}))
        if original is not None:raise original
        raise
    if original is not None:raise original
    require(not raw["copy_errors"],"raw D2H/pointer observations incomplete; original evidence retained")
    return state,guards,native,x,y,expected,before,immutable,pointers,raw_path

def metrics(torch,helper,state,guards,native,x,y,expected,before,immutable,pointers):
    # Exactly reuse the original helper equations; no pre-cast CPU proxy.
    complete=helper.logical(state)
    eout=helper.output_error(y,expected)
    estate=helper.rel(complete,native)
    ehead=max(helper.rel(complete[s,h],native[s,h]) for s in range(4) for h in range(12))
    ids=x["indices"].cpu().tolist();unused=[s for s in range(4) if s not in ids]
    checks={"untouched_slots_bitwise":all(bitwise(torch,state[n][unused],before[n][unused])
                                         for n in helper.NAMES),
            "nonflush_base_bitwise":all(bitwise(torch,state["base"][s],before["base"][s])
                                       for s in ids if int(before["length"][s,0,0])!=15),
            "all_logs_bitwise_outside_new_U":helper.check_logs(state,before,x,1),
            "guards":all(bool(torch.all(t[:64]==7).cpu()) and bool(torch.all(t[-64:]==7).cpu())
                         for t in guards.values()),
            "pointers":helper.all_pointers(state,guards,native,x)==pointers,
            "input_immutable":all(bitwise(torch,x[n],immutable[n]) for n in x),
            "zero_length_output_zero":True}
    finite=all(bool(torch.isfinite(t).all().cpu()) for t in
               [*state.values(),y,expected,complete,native])
    metric_finite=all(__import__("math").isfinite(v) for v in (eout,estate,ehead))
    passed=(eout<=helper.OUT_LIMIT and estate<=helper.STATE_LIMIT and ehead<=helper.STATE_LIMIT and
            finite and metric_finite and all(v for n,v in checks.items() if
                                           n!="all_logs_bitwise_outside_new_U") and
            all(checks["all_logs_bitwise_outside_new_U"].values()))
    return {"output_error":eout,"complete_state_l2":estate,"max_per_head_l2":ehead,
            **checks,"finite":finite,"metric_finite":metric_finite,"passed":passed}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--execute",action="store_true");p.add_argument("--script-sha256")
    p.add_argument("--source-manifest",type=Path);p.add_argument("--source-manifest-sha256")
    p.add_argument("--library",type=Path);p.add_argument("--library-sha256")
    p.add_argument("--build-receipt",type=Path);p.add_argument("--build-receipt-sha256")
    p.add_argument("--meta-receipt",type=Path);p.add_argument("--meta-receipt-sha256")
    p.add_argument("--identity",type=Path);p.add_argument("--output-dir",type=Path)
    a=p.parse_args(argv)
    if not a.execute:
        print(json.dumps({"default_enabled":False,"npu_executed":False,"serving_ready":False,
                          "scope":"one saved B1 failure replay only","precast_updated_S":"pending"}))
        return
    require(all((a.script_sha256,a.source_manifest,a.source_manifest_sha256,a.library,
                 a.library_sha256,a.build_receipt,a.build_receipt_sha256,a.meta_receipt,
                 a.meta_receipt_sha256,a.identity,a.output_dir)),"MAIN exact actual Refs")
    require(sha(__file__)==a.script_sha256,"MAIN expected NEW diagnostic source drift")
    require(a.source_manifest_sha256==MANIFEST_SHA,"frozen16 manifest required")
    sys.path.insert(0,str(NEW))
    import contract
    source_ref=contract.ref({"path":str(a.source_manifest),"sha256":a.source_manifest_sha256})
    manifest,sources=contract.source_admission(source_ref)
    refs={k:contract.ref({"path":str(path),"sha256":digest}) for k,path,digest in
          (("library",a.library,a.library_sha256),("build",a.build_receipt,a.build_receipt_sha256),
           ("meta",a.meta_receipt,a.meta_receipt_sha256))}
    contract.artifacts(refs,manifest)
    ident=json.loads(a.identity.read_bytes())
    contract.validate_identity(ident,1,5,source_ref,manifest,sources,refs)
    require(ident.get("diagnostic_script")=={"path":str(Path(__file__).resolve()),
                                            "sha256":a.script_sha256},
            "MAIN explicitly bound diagnostic, not an untracked script")
    require(os.environ.get("ASCEND_RT_VISIBLE_DEVICES")=="0" and
            os.environ.get("PYTHONDONTWRITEBYTECODE")=="1" and
            os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD")=="0",
            "single logical0/no bytecode/no backend autoload before durable CPU evidence")
    cg=contract.legacy().cgroup_limit()
    raw_path,original_row=raw_ref()
    require(sha(OLD_ORACLE)==OLD_ORACLE_SHA and sha(OLD_LIBRARY)==OLD_LIBRARY_SHA,
            "actual frozen original oracle/production SO")
    require(a.library.resolve()!=OLD_LIBRARY.resolve(),"new SO must not alias original SO")
    native_pins=contract.legacy().NATIVE_PINS
    require({n:sha(n) for n in native_pins}==native_pins,"actual native source pins")
    out=a.output_dir.resolve()
    require(Path("/kvbuffer-results") in out.parents and not out.exists(),
            "fresh diagnostic output directory")
    out.mkdir(parents=True,exist_ok=False)
    report={"schema":"kvbp.saved-native-order-diagnostic/v2","status":"running",
            "script_sha256":a.script_sha256,"source_manifest":source_ref,"sources_before":sources,
            "identity_sha256":sha(a.identity),"cgroup":cg,"original_report_sha256":REPORT_SHA,
            "original_raw":{"path":str(raw_path),"sha256":RAW_SHA},"original_row":original_row,
            "artifact_refs":refs,"old_library_sha256":OLD_LIBRARY_SHA,
            "precast_updated_S":"pending: no production export, no CPU proxy",
            "matrix_verified":False,"graph_matrix_verified":False,"matched_e2e_verified":False,
            "accuracy_verified":False,"serving_ready":False}
    def save():
        value=new_oracle.finite_json(report) if new_oracle is not None else report
        (out/"report.json").write_text(json.dumps(value,indent=2,allow_nan=False)+"\n")
    old_oracle=new_oracle=None;primary=None
    save()
    try:
        import torch
        # Hash-bound weights-only CPU payload; never execute arbitrary pickle globals.
        fixture=torch.load(raw_path,map_location="cpu",weights_only=True)
        require((fixture["schema"],fixture["batch"],fixture["mode"],fixture["trial"],
                 fixture["step"],fixture["active"])==("kvbp.raw-step/v1",1,"graph",2,104,1),
                "saved fixture scope")
        require(set(fixture["before"])==set(("base","k_log","u_log","lambda_log","decay","length"))
                and all(bitwise(torch,fixture["inputs"][n],fixture["input_before"][n])
                        for n in fixture["inputs"]),"complete original before/input fixture")
        # Durable CPU before evidence exists before any device import/bootstrap/dispatch.
        torch.save({"fixture":fixture,"original_report":str(REPORT),"original_report_sha256":REPORT_SHA,
                    "original_raw_sha256":RAW_SHA},out/"before.pt")
        import torch_npu
        from vllm_ascend.utils import enable_custom_op
        from vllm_ascend.ops.triton.triton_utils import init_device_properties_triton
        torch_npu.npu.set_compile_mode(jit_compile=False);torch.npu.set_device(0)
        require(torch.npu.device_count()==1 and torch.npu.get_device_name(0)=="Ascend910B4",
                "actual single logical0 910B4")
        require(enable_custom_op(),"actual native op available");init_device_properties_triton()
        old_oracle=frozen_module(OLD_ORACLE,OLD_ORACLE_SHA,"_kv_saved_old_oracle")
        new_oracle=frozen_module(NEW/"oracle.py",manifest["files"]["oracle.py"],"_kv_saved_new_oracle")
        for helper in (old_oracle,new_oracle):helper.torch=torch;helper.torch_npu=torch_npu
        torch.ops.load_library(str(OLD_LIBRARY))
        old_ops=getattr(torch.ops,OLD_NAMESPACE)
        require(str(old_ops.decode.default._schema)==old_oracle.EXPECTED_SCHEMA,"old production schema")
        report["old_mapped_libraries"]=mapped({str(OLD_LIBRARY):OLD_LIBRARY_SHA,NATIVE_PATH:NATIVE_SHA})
        old=step(torch,old_oracle,fixture,old_ops,out,"graph","old-production")
        state,guards,native,x,y,expected,before,immutable,pointers,raw_out=old
        reproduction={"after":all(bitwise(torch,state[n],fixture["after"][n]) for n in old_oracle.NAMES),
                      "actual":bitwise(torch,y,fixture["actual"]),
                      "native":bitwise(torch,native,fixture["native"]),
                      "expected":bitwise(torch,expected,fixture["expected"]),
                      "guards":all(bitwise(torch,guards[n],fixture["guards"][n]) for n in guards),
                      "inputs":all(bitwise(torch,x[n],fixture["inputs"][n]) for n in x)}
        report["old_reproduction"]=reproduction
        report["old_raw"]={"path":str(raw_out),"sha256":sha(raw_out)}
        save()
        require(all(reproduction.values()),"old production does not reproduce saved bytes; STOP before NEW")
        report["old_metrics"]=metrics(torch,old_oracle,*old[:9])
        require(report["old_metrics"]["passed"] is False and
                report["old_metrics"]["output_error"]==original_row["output_error"],
                "original failure must still fail original frozen gate")
        save()
        torch.ops.load_library(str(a.library.resolve()))
        new_ops=getattr(torch.ops,contract.NAMESPACE);new_oracle.bind_candidate(new_ops)
        report["new_mapped_libraries"]=mapped({str(a.library.resolve()):a.library_sha256,NATIVE_PATH:NATIVE_SHA})
        current=step(torch,new_oracle,fixture,new_ops,out,"eager","new-native-order")
        report["new_raw"]={"path":str(current[-1]),"sha256":sha(current[-1])}
        save() # actual complete new tensors are durable before metrics.
        report["new_native_reproduces_saved"]=bitwise(torch,current[2],fixture["native"])
        report["new_expected_reproduces_saved"]=bitwise(torch,current[5],fixture["expected"])
        require(report["new_native_reproduces_saved"] and report["new_expected_reproduces_saved"],
                "independent native single step changed")
        report["new_metrics"]=metrics(torch,new_oracle,*current[:9])
        report["status"]="new_single_step_numerical_pass" if report["new_metrics"]["passed"] else "failed"
        save()
        require(report["new_metrics"]["passed"],"new saved single-step numerical gate failed; retain")
    except BaseException as error:
        primary=error;report.update(status="failed",original_error=repr(error));raise
    finally:
        report["completed_ns"]=time.time_ns()
        try:
            _,after=contract.source_admission(source_ref)
            report["sources_after"]=after;require(after==sources,"frozen source drift during diagnostic")
            require(sha(__file__)==a.script_sha256 and sha(REPORT)==REPORT_SHA and sha(raw_path)==RAW_SHA,
                    "source/original evidence drift")
            save()
        except BaseException as secondary:
            if primary is None:
                report.update(status="failed",original_error=repr(secondary))
                try:save()
                except BaseException as save_error:
                    print(json.dumps({"primary":repr(secondary),"save_error":repr(save_error)}))
                raise
            report["secondary_finalize_error"]=repr(secondary)
            try:save()
            except BaseException as save_error:
                print(json.dumps({"primary":repr(primary),"secondary":repr(secondary),
                                  "save_error":repr(save_error)}))

if __name__=="__main__":main()
