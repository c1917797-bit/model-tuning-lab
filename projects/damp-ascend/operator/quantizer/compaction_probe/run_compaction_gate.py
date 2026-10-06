#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed real-NPU eager seam gate. Never starts Docker or selects host cards.
No production cache/recurrence, no graph, no performance claims.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import traceback
from cases import EXACT_SHA,ORACLE_SHA,fixtures,software_gate

COMPILED=("CMakeLists.txt","op_kernel/probe_plan.h","op_kernel/compaction_probe.h",
          "op_kernel/compaction_probe_kernel.asc","op_extension/ops.h",
          "op_extension/register.cpp","op_extension/compaction_torch.cpp",
          "../exact_quantizer_bits.h")
RUNTIME=COMPILED+("../test_exact_quantizer.py","cases.py","run_compaction_gate.py",
                  "test_software.py","README.md")
def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):h.update(block)
    return h.hexdigest()
def write_json(p,obj):
    p.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+"\n")
def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()
def verify_sources(receipt):
    root=Path(__file__).resolve().parent
    manifest=json.loads(Path(receipt).read_text())
    if set(manifest["compiled_files"])!=set(COMPILED):
        raise RuntimeError("receipt compiled source set mismatch")
    actual={name:sha(root/name) for name in RUNTIME}
    for name,digest in actual.items():
        if manifest["files"].get(name)!=digest:
            raise RuntimeError("source receipt mismatch: "+name)
    if actual["../exact_quantizer_bits.h"]!=EXACT_SHA or actual["../test_exact_quantizer.py"]!=ORACLE_SHA:
        raise RuntimeError("frozen exact/independent oracle identity mismatch")
    return actual
def proof_gate(path,physical):
    p=json.loads(Path(path).read_text())
    if not(p.get("physical_device")==physical==4 and p.get("logical_device")==0
           and p.get("privileged") is False and p.get("container") and p.get("image_id")):
        raise RuntimeError("MAIN-provided fresh nonprivileged physical4->logical0 proof required")
    if "/dev/davinci4" not in p.get("host_device_paths",[]):
        raise RuntimeError("device proof does not include physical davinci4")
    when=datetime.datetime.fromisoformat(p["checked_utc"].replace("Z","+00:00"))
    if when.tzinfo is None:raise RuntimeError("device proof must have UTC offset")
    age=(datetime.datetime.now(datetime.timezone.utc)-when).total_seconds()
    if not 0<=age<=900:raise RuntimeError("device proof stale or future")
    return p
def tensor_identity(t):
    return {"data_ptr":t.data_ptr(),"storage_ptr":t.untyped_storage().data_ptr(),
            "storage_bytes":t.untyped_storage().nbytes(),"shape":list(t.shape),
            "dtype":str(t.dtype),"device":str(t.device)}
def nullable_copies(tensors):
    copied,errors=[],[]
    for index,t in enumerate(tensors):
        try:copied.append(t.detach().cpu().clone())
        except Exception as exc:
            copied.append(None);errors.append({"index":index,"error":repr(exc)})
    return copied,errors
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--software-only",action="store_true")
    ap.add_argument("--meta-only",action="store_true")
    ap.add_argument("--output-dir")
    ap.add_argument("--library");ap.add_argument("--library-sha256")
    ap.add_argument("--source-receipt");ap.add_argument("--device-proof")
    ap.add_argument("--physical-device",type=int,default=4)
    args=ap.parse_args()
    if args.software_only:
        print(json.dumps(software_gate(),sort_keys=True,allow_nan=False));return
    if not all((args.output_dir,args.library,args.library_sha256,args.source_receipt)):
        ap.error("fresh output-dir, library/SHA and source receipt are required")
    output=Path(args.output_dir)
    output.mkdir(parents=True,exist_ok=False)
    report={"status":"running","started_utc":utc(),"scope":"independent eager compaction/scatter ONLY",
            "production_integrated":False,"recurrence_executed":False,"graph_executed":False,
            "performance_measured":False,"npu_executed":False,"rows":[]}
    torch=None; current=None; device_out=[]; device_roots=[]; previous=[]
    raw_before=None; previous_cpu=[]; first_failure_written=False
    def save_failure(exc):
        nonlocal first_failure_written
        if first_failure_written:return
        first_failure_written=True
        # Nullable, separately attempted copies: a broken D2H must not prevent
        # original CPU raw-before/error/partial output preservation.
        copied,copy_errors=nullable_copies(device_roots+device_out+previous) if torch else ([],[])
        fixture={"case":current,"raw_before":raw_before,
                 "copies":copied,"copy_errors":copy_errors,"error":repr(exc),
                 "traceback":traceback.format_exc(),"output_names":["codes","indices","retained","valid"]}
        if torch:
            try:torch.save(fixture,output/"first_failure.pt")
            except Exception as save_exc:report["fixture_save_error"]=repr(save_exc)
        report.update(status="fail",finished_utc=utc(),error=repr(exc),
                      traceback=traceback.format_exc(),first_failure=current,
                      nullable_copy_errors=copy_errors)
        write_json(output/"report.json",report)
    try:
        report["sources"]=verify_sources(args.source_receipt)
        library=Path(args.library).resolve()
        if sha(library)!=args.library_sha256:raise RuntimeError("candidate library SHA mismatch")
        report["library"]={"path":str(library),"sha256":args.library_sha256}
        import torch as imported_torch
        import torch_npu
        torch=imported_torch
        torch.ops.load_library(str(library))  # actual dlopen; unresolved host stubs fail here
        op=torch.ops.qwen36_damp_compaction_probe
        report["schemas"]={"prepare":str(op.prepare.default._schema),
                           "compact":str(op.compact.default._schema)}
        report["versions"]={"torch":torch.__version__,"torch_npu":torch_npu.__version__,
                            "ASCEND_HOME_PATH":os.environ.get("ASCEND_HOME_PATH")}
        if args.meta_only:
            for n in (64,448,896):
                m=[torch.empty(n,dtype=torch.int32,device="meta") for _ in range(4)]
                assert op.prepare(*m) is None
                out=op.compact(*m)
                assert len(out)==4 and all(t.shape==(n+16,) and t.dtype==torch.int32 for t in out)
            report.update(status="pass",finished_utc=utc(),scope="Meta shape/dtype ONLY")
            write_json(output/"report.json",report);print(json.dumps(report,sort_keys=True));return
        if not args.device_proof:raise RuntimeError("explicit MAIN physical mapping proof required")
        report["device_proof"]=proof_gate(args.device_proof,args.physical_device)
        if os.environ.get("ASCEND_RT_VISIBLE_DEVICES")!="0":
            raise RuntimeError("probe process must see container logical0 only")
        torch.npu.set_device(0)
        report["device"]={"logical":0,"physical":4,"name":torch.npu.get_device_name(0)}
        report["npu_executed"]=True
        maps=Path("/proc/self/maps").read_text().splitlines()
        libraries=sorted({line.split()[-1] for line in maps
            if line.split()[-1].startswith("/") and
            ("libtorch_npu" in line.split()[-1] or str(library)==line.split()[-1])})
        report["loaded_libraries"]=[{"path":p,"sha256":sha(p)} for p in libraries]
        last_n=None; stable=[]; previous_cpu=[]
        for case in fixtures():
            current={"n":case["n"],"turn":case["turn"],"name":case["name"]}
            n=case["n"]
            device_out=[] # dispatch failure cannot relabel previous outputs as current
            cpu_roots=[torch.tensor(v,dtype=torch.int32) for v in case["roots"]]
            raw_before={"case":current,"roots":cpu_roots,
                "inputs":[t.clone() for t in (v[8:8+n] for v in cpu_roots)],
                "expected":[torch.tensor(v,dtype=torch.int32) for v in case["outputs"]],
                "input_identity":stable if n==last_n else None}
            # Preserve current raw CPU fixture even allocation/H2D/sync fails.
            torch.save(raw_before,output/("raw-before-n%d-turn%02d.pt"%(n,case["turn"])))
            if n!=last_n:
                device_roots=[torch_npu.npu_format_cast(
                    torch.full((n+16,),0,dtype=torch.int32,device="npu:0"),2) for _ in range(4)]
                inputs=[t[8:8+n] for t in device_roots]
                stable=[tensor_identity(t) for t in device_roots+inputs]
                previous=[];previous_cpu=[];last_n=n
            raw_before["input_identity"]=stable
            for dest,source in zip(device_roots,cpu_roots):dest.copy_(source)
            torch.npu.synchronize() # changed static buffers really committed before call
            assert [tensor_identity(t) for t in device_roots+inputs]==stable
            assert all(torch_npu.get_npu_format(t)==2 for t in device_roots+inputs)
            if case["turn"]==0:
                # New process/library cache: count not prepared. Reject without launch.
                rejected=False
                try:op.compact(*inputs)
                except RuntimeError as exc:rejected="explicit prepare required" in str(exc)
                if not rejected:raise AssertionError("unprepared call not synchronously rejected")
                op.prepare(*inputs);torch.npu.synchronize()
            elif case["turn"]==3:
                op.prepare(*inputs) # cached plan, but fresh0/1/proposal admission still required
            device_out=list(op.compact(*inputs))
            torch.npu.synchronize()
            after,copy_errors=nullable_copies(device_roots+device_out+previous)
            if copy_errors:raise RuntimeError("D2H failed: "+repr(copy_errors))
            if not all(torch.equal(a,b) for a,b in zip(after[:4],cpu_roots)):
                raise AssertionError("complete input/guard changed")
            if [tensor_identity(t) for t in device_roots+inputs]!=stable:
                raise AssertionError("same input storage pointer changed")
            actual=after[4:8]
            for j,(a,e) in enumerate(zip(actual,raw_before["expected"])):
                if not torch.equal(a,e):raise AssertionError("full guarded output mismatch "+str(j))
            retained=int(actual[2][8])
            selected=actual[1][8:8+retained].tolist()
            if not(0<=retained<=n and selected==sorted(set(selected))
                   and selected==case["rejected"] and all(0<=v<n for v in selected)):
                raise AssertionError("retained/order/unique/indexrange failed")
            if previous and not all(torch.equal(a,b) for a,b in zip(after[8:],previous_cpu)):
                raise AssertionError("previous outputs changed by same-buffer replay")
            out_id=[tensor_identity(t) for t in device_out]
            intervals=[(d["storage_ptr"],d["storage_ptr"]+d["storage_bytes"])
                       for d in stable[:4]+out_id]
            for i,(begin,end) in enumerate(intervals):
                if any(not(end<=b or e<=begin) for b,e in intervals[:i]):
                    raise AssertionError("backing storage alias")
            assert all(torch_npu.get_npu_format(t)==2 for t in device_out)
            report["rows"].append({**current,"status":"pass","retained":retained,
                "same_input_pointers":True,"input_guards":True,"all_output_guards":True,
                "retained_order_unique_range":True,"previous_output_unchanged":True,
                "output_identity":out_id})
            previous=device_out;previous_cpu=[t.clone() for t in actual]
            write_json(output/"report.json",report)
        # Rejection guards are checked on both prepare and actual dispatch. No
        # unsupported blocked-format allocation is guessed on this image.
        report["admission"]=[]
        for label,argidx,value in (("flag_negative",0,-1),("flag_two",0,2),
                                   ("magnitude_negative",3,-1),("magnitude128",3,128)):
            invalid=[t.clone() for t in inputs]
            invalid[argidx][0]=value;torch.npu.synchronize()
            prior,errors=nullable_copies(invalid)
            if errors:raise RuntimeError(repr(errors))
            for method in (op.prepare,op.compact):
                caught=False
                try:method(*invalid)
                except RuntimeError:caught=True
                if not caught:raise AssertionError("bad actual values admitted: "+label)
            post,errors=nullable_copies(invalid)
            if errors or not all(torch.equal(a,b) for a,b in zip(prior,post)):
                raise AssertionError("invalid admission input changed")
            report["admission"].append({"name":label,"prepare_rejected":True,"dispatch_rejected":True})
        alias_rejected=False
        try:op.compact(inputs[0],inputs[0],inputs[2],inputs[3])
        except RuntimeError:alias_rejected=True
        if not alias_rejected:raise AssertionError("backing alias accepted")
        report["admission"].append({"name":"backing_alias","dispatch_rejected":True})
        report.update(status="pass",finished_utc=utc(),cases=len(report["rows"]),
            same_buffers_changed_masks=True,physical_format="ND2",
            limits=["flag/proposal admission copies CPU: eager diagnostic only",
                    "accepted magnitudes pre-certified by Fraction fixtures, not certificate integration",
                    "no production state/cache, recurrence, graph or performance validation"])
        write_json(output/"report.json",report)
        print(json.dumps({"status":"pass","cases":len(report["rows"]),
                          "report":str(output/"report.json"),"scope":report["scope"]},sort_keys=True))
    except Exception as exc:
        save_failure(exc)
        raise
if __name__=="__main__":main()
