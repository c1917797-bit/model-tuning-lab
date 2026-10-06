#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Independent eager diagnostic, not a production/graph/performance fast path."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import traceback
from cases import (GUARDS,NAMES,LUT_HASHES,lut_hashes,signed,golden,labeled_fixtures,
                   endpoint_rows,proposal_rows,chunks,lifecycle_rows)
BASE=Path(__file__).resolve().parent
SOURCE_NAMES=(
    "CMakeLists.txt","op_kernel/probe_plan.h","op_kernel/certificate_probe.h",
    "op_kernel/certificate_probe_kernel.asc","op_extension/ops.h",
    "op_extension/certificate_torch.cpp","op_extension/register.cpp",
    "cases.py","test_software_contract.py","run_certificate_gate.py",
    "../integer_certificate_ascendc.h","../integer_certificate.py",
    "../test_integer_certificate.py","../../exact_quantizer_bits.h",
    "../../test_exact_quantizer.py","../../probe_fixtures.py")
INPUT_GUARD=0x10293847
FROZEN_SOURCE_SHA={
    "../integer_certificate_ascendc.h":"e96cbd0565cdb879016e1970753342151936e3d45bafd375530d1d27cfd7b9cb",
    "../integer_certificate.py":"93a5b4f79285dd18db179b0ae83ca144ce0227332d6d2ce221613f453220f3d1",
    "../test_integer_certificate.py":"4c4521a1e023795717f852c874666dcef0370842da12e1081dd03998ff34f8f9",
    "../../exact_quantizer_bits.h":"f5d380534d34d6e4148d94fcfec35b294ca8ca38d09316d98b11e7f645ff6169",
    "../../test_exact_quantizer.py":"b1c9d10bf9e24e095fe048235693e426f5437be27a9e21b39503bd7825a50c3d",
    "../../probe_fixtures.py":"a4ce599438c7d0e325e78f7d22f51fa1c4f1133d9904dfcd12b3a48696763bf0"}
def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()

def read_json(path):
    with Path(path).open() as stream:
        return json.load(stream)

def signed(bits):
    return bits if bits < (1<<31) else bits-(1<<32)

def assert_true(condition, detail):
    if not condition:
        raise AssertionError(detail)

COMPILED_NAMES=(
    "CMakeLists.txt","op_kernel/probe_plan.h","op_kernel/certificate_probe.h",
    "op_kernel/certificate_probe_kernel.asc","op_extension/ops.h",
    "op_extension/certificate_torch.cpp","op_extension/register.cpp",
    "../integer_certificate_ascendc.h","../../exact_quantizer_bits.h")
EXPECTED_IMAGE_ID="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
def source_checks(args):
    # The actual parent build manifest has ONLY9 compiled dependencies, no
    # schema field. Runtime16 dependencies are separately source-bound.
    compiled_manifest=read_json(args.source_manifest)
    compiled=compiled_manifest.get("sources")
    assert_true(isinstance(compiled,dict) and set(compiled)==set(COMPILED_NAMES),
                "compiled manifest must bind exact9 compile dependencies")
    runtime_manifest=read_json(args.runtime_manifest)
    assert_true(runtime_manifest.get("schema")=="damp_integer_certificate_runtime_sources_v1",
                "unsupported separate runtime manifest")
    runtime=runtime_manifest.get("sources")
    assert_true(isinstance(runtime,dict) and set(runtime)==set(SOURCE_NAMES),
                "runtime manifest must bind exact16 runtime dependencies")
    actual={}
    for relative in SOURCE_NAMES:
        actual[relative]=digest(BASE/relative)
        assert_true(actual[relative]==runtime[relative],"runtime source hash "+relative)
    actual_compiled={name:actual[name] for name in COMPILED_NAMES}
    assert_true(compiled==actual_compiled,"compiled/runtime subset mismatch")
    receipt=read_json(args.build_receipt)
    commands=receipt.get("commands")
    assert_true(receipt.get("schema")=="damp_integer_certificate_build_v1" and
                receipt.get("status")=="compiled_no_device" and
                receipt.get("npu_executed") is False and
                receipt.get("physical_soc_runtime_observed") is False,
                "require successful actual no-device receipt, not failed/SoC declaration")
    assert_true(isinstance(commands,list) and len(commands)>=2 and
                all(c.get("exit_code")==0 and c.get("command") and
                    isinstance(c.get("log_sha256"),str) and len(c["log_sha256"])==64
                    for c in commands),"compiler/configuration command did not succeed")
    assert_true(receipt.get("sources")==actual_compiled and
                receipt.get("library_sha256")==args.library_sha256 and
                receipt.get("npu_arch")=="dav-2201" and
                receipt.get("image_id")==EXPECTED_IMAGE_ID,
                "compiled source/SO/architecture/immutable image mismatch")
    cann=receipt.get("cann_identity")
    assert_true(isinstance(cann,dict) and cann.get("version")=="9.1.0" and
                cann.get("component")=="opp" and
                isinstance(cann.get("version_info_path"),str) and
                Path(cann["version_info_path"]).is_absolute() and
                isinstance(cann.get("version_info_sha256"),str) and
                len(cann["version_info_sha256"])==64,
                "actual CANN OPP version.info build identity required")
    assert_true(digest(args.library)==args.library_sha256,"SO hash mismatch")
    return {"compiled_sources":actual_compiled,"runtime_sources":actual,
            "build_receipt":receipt,
            "source_manifest_sha256":digest(args.source_manifest),
            "runtime_manifest_sha256":digest(args.runtime_manifest),
            "build_receipt_sha256":digest(args.build_receipt),
            "library":str(Path(args.library).resolve()),
            "library_sha256":args.library_sha256}

def cann_environment_checks(bindings):
    # Same-image Meta and NPU phases verify actual config bytes, not a fake
    # target SoC on a no-device compiler receipt. MAIN captures opp/version.info.
    identity=bindings["build_receipt"]["cann_identity"]
    configured=os.environ.get("ASCEND_HOME_PATH")
    assert_true(configured is not None,"ASCEND_HOME_PATH missing")
    home=Path(configured).resolve()
    assert_true(home==Path("/usr/local/Ascend/cann-9.1.0").resolve(),
                "actual CANN home mismatch")
    cfg=Path(identity["version_info_path"])
    assert_true(cfg.resolve()==(home/"opp/version.info").resolve() and cfg.is_file(),
                "CANN config is not inside actual configured toolkit")
    assert_true(digest(cfg)==identity["version_info_sha256"],
                "actual runtime CANN config bytes differ from build")
    version_text=cfg.read_text()
    assert_true("Version=9.1.0" in version_text.splitlines(),
                "actual OPP version.info does not identify9.1.0")
    return {"component":"opp","scope":"OPP component identity, not all SDK packages",
            "configured_home":configured,"version_info_path":str(cfg.resolve()),
            "version_info_sha256":digest(cfg),"version_info_text":version_text,
            "declared_build_version":identity["version"],
            "physical_soc_runtime_observed":False}

def safe_cpu_snapshot(tensors):
    if tensors is None:
        return None,[]
    result=[]; errors=[]
    for index,tensor in enumerate(tensors):
        try: result.append(tensor.cpu().clone())
        except Exception as exc:
            result.append(None); errors.append({"index":index,"error":repr(exc)})
    return result,errors

def save_observation(save,path,*,returns,roots,dispatch_error,**context):
    # D2H can itself fail after a poisoned device context. Keep dispatcherror
    # distinct, preserve nullable copies, and save CPU before/rows/golden first
    # in this record before any assertion or exception rethrow.
    cpu_out,output_copy_errors=safe_cpu_snapshot(returns)
    after,input_copy_errors=safe_cpu_snapshot(roots)
    observation={**context,"outputs_full":cpu_out,"after":after,
                 "dispatch_error":dispatch_error,
                 "output_copy_errors":output_copy_errors,
                 "input_copy_errors":input_copy_errors}
    save(observation,path)
    return observation

def preflight_checks(args):
    proof = read_json(args.preflight)
    assert_true(proof.get("schema") == "damp_integer_certificate_preflight_v1" and
                proof.get("passed") is True and proof.get("mapping_proven") is True and
                proof.get("no_external_npu_processes") is True,
                "fresh main-owned preflight did not pass")
    cards = proof.get("physical_devices")
    assert_true(isinstance(cards, list) and len(cards) == 1 and cards[0] in (4,5,6,7),
                "isolated gate permits exactly one proved physical NPU4-7")
    assert_true(proof.get("logical_device") == args.logical_device and
                proof.get("soc") == "Ascend910B4",
                "preflight logical mapping / SoC mismatch")
    checked = datetime.datetime.fromisoformat(proof["checked_at_utc"].replace("Z","+00:00"))
    assert_true(checked.tzinfo is not None, "preflight time requires timezone")
    age = (datetime.datetime.now(datetime.timezone.utc)-checked).total_seconds()
    assert_true(0 <= age <= 300, "preflight is not within five minutes before launch")
    return {"preflight": proof, "preflight_sha256": digest(args.preflight)}

def loaded_libraries():
    result = {}
    for line in Path("/proc/self/maps").read_text().splitlines():
        fields = line.split()
        if len(fields) < 6:
            continue
        candidate = fields[-1]
        if candidate.startswith("/") and ".so" in candidate and (
                "Ascend" in candidate or "torch" in candidate or "qwen36_damp" in candidate):
            path = Path(candidate)
            if path.is_file() and candidate not in result:
                result[candidate] = digest(path)
    return result


def meta_gate(torch):
    records=[]
    for count in (64,896):
        inputs=[torch.empty(count,dtype=torch.int32,device="meta") for _ in range(3)]
        torch.ops.qwen36_damp_integer_probe.prepare(*inputs)
        outs=torch.ops.qwen36_damp_integer_probe.certify_bits(*inputs)
        assert_true(len(outs)==7 and all(t.shape==(count+16,) and t.dtype==torch.int32 and
                    t.device.type=="meta" for t in outs),"Meta full seven-output contract")
        records.append({"count":count,"outputs":7,"shape":[count+16],"dtype":"int32"})
    for count in (0,63,65,897,1792):
        inputs=[torch.empty(count,dtype=torch.int32,device="meta") for _ in range(3)]
        for name in ("prepare","certify_bits"):
            try: getattr(torch.ops.qwen36_damp_integer_probe,name)(*inputs)
            except RuntimeError: continue
            raise AssertionError(f"Meta accepted bad count {count}/{name}")
    for label in ("wrongdtype","shape","noncontiguous","misaligned","device"):
        a=torch.empty(64,dtype=torch.int32,device="meta")
        b=a.clone(); n=a.clone()
        if label=="wrongdtype": n=torch.empty(64,dtype=torch.float32,device="meta")
        elif label=="shape": n=torch.empty(63,dtype=torch.int32,device="meta")
        elif label=="noncontiguous": n=torch.empty(128,dtype=torch.int32,device="meta")[::2]
        elif label=="misaligned": n=torch.empty(65,dtype=torch.int32,device="meta")[1:]
        else: n=torch.empty(64,dtype=torch.int32)
        for name in ("prepare","certify_bits"):
            try: getattr(torch.ops.qwen36_damp_integer_probe,name)(a,b,n)
            except RuntimeError: continue
            raise AssertionError(f"Meta accepted {label}/{name}")
    return {"passed":True,"records":records,
            "scope":"shape/dtype/count/offset; no value range/physical ND/alias/graph proof"}

def actual_gate(torch,torch_npu,args,outdir,rows,progress):
    device=f"npu:{args.logical_device}"
    torch.npu.set_device(args.logical_device)
    assert_true(torch.npu.get_device_name(device)=="Ascend910B4","actual SoC mismatch")
    assert_true(torch.__version__=="2.10.0+cpu" and
                torch_npu.__version__=="2.10.0.post4","deployed Torch/TorchNPU mismatch")
    provenance={"torch":torch.__version__,"torch_npu":torch_npu.__version__,
                "device_name":torch.npu.get_device_name(device),
                "ascend_home_path":os.environ.get("ASCEND_HOME_PATH"),
                "ascend_visible_devices":os.environ.get("ASCEND_RT_VISIBLE_DEVICES")}
    def nd(t):
        r=torch_npu.npu_format_cast(t.to(device).contiguous(),2)
        assert_true(torch_npu.get_npu_format(r)==2,"input physical ND")
        return r
    def span(t):
        s=t.untyped_storage(); return s.data_ptr(),s.data_ptr()+s.nbytes()
    def disjoint(a,b):
        ab,ae=span(a); bb,be=span(b); return ae<=bb or be<=ab
    def make_inputs(chunk):
        roots=[]
        for field in ("x_bits","scale_bits","proposal"):
            values=[signed(r[field]) if field!="proposal" else r[field] for r in chunk]
            roots.append(nd(torch.tensor([INPUT_GUARD]*8+values+[INPUT_GUARD]*8,dtype=torch.int32)))
        return roots,[t[8:-8] for t in roots]
    records=[]; negative=[]
    progress.update({"passed":False,"records":records,"admission_negatives":negative,
                     "provenance":provenance,"gather_mask_compaction_implemented":False})
    case_no=0; accepted_count=0; lane_count=0
    def reject(label,roots,inputs,opname):
        before=[t.cpu().clone() for t in roots]; error=None; outs=None
        try:
            value=getattr(torch.ops.qwen36_damp_integer_probe,opname)(*inputs)
            if opname=="certify_bits": outs=value
            torch.npu.synchronize()
        except Exception as exc: error=repr(exc)
        artifact=outdir/f"negative-{label}-{opname}.pt"
        observation=save_observation(torch.save,artifact,returns=outs,roots=roots,
            dispatch_error=error,before=before,label=label,op=opname,
            input_pointers=[t.data_ptr() for t in roots])
        negative.append({"label":label,"op":opname,"dispatch_error":error,
                         "artifact":artifact.name,"artifact_sha256":digest(artifact)})
        assert_true(error is not None,f"negative {label}/{opname} accepted")
        assert_true(not observation["output_copy_errors"] and
                    not observation["input_copy_errors"],
                    f"negative {label}/{opname} after-copy failed (raw record saved)")
        assert_true(all(torch.equal(a,b) for a,b in zip(before,observation["after"])),
                    f"negative {label}/{opname} changed input")
    # Fresh process/library has no NPU prepared plan. Meta prepare does not cache.
    smoke=lifecycle_rows(rows,64,0); roots,inputs=make_inputs(smoke)
    reject("not_prepared",roots,inputs,"certify_bits")
    def one(name,chunk,useful):
        nonlocal case_no,accepted_count,lane_count
        count=len(chunk); roots,inputs=make_inputs(chunk)
        expected=[golden(r) for r in chunk]
        gold=[torch.tensor([r[i] for r in expected],dtype=torch.int32) for i in range(7)]
        before=[t.cpu().clone() for t in roots]
        ptrs=[t.data_ptr() for t in roots]+[t.data_ptr() for t in inputs]
        def observe_prepare(label):
            error=None; after_prepare=None
            try:
                torch.ops.qwen36_damp_integer_probe.prepare(*inputs)
                torch.npu.synchronize()
            except Exception as exc:
                error=repr(exc)
            try:
                after_prepare=[t.cpu().clone() for t in roots]
            except Exception as exc:
                error=(error or "")+"; input-after-copy: "+repr(exc)
            prep=outdir/f"{case_no:04d}-{label}.pt"
            torch.save({"before":before,"after":after_prepare,"pointers":ptrs,
                        "error":error},prep)  # preserve unexpected failure before assertions
            assert_true(error is None and after_prepare is not None,
                        label+" failed: "+str(error))
            assert_true(all(torch.equal(a,b) for a,b in zip(before,after_prepare)),
                        label+" changed complete input roots")
            assert_true(ptrs==[t.data_ptr() for t in roots]+[t.data_ptr() for t in inputs],
                        label+" changed input storage pointer")
            return prep
        prep=observe_prepare("prepare")
        # Observe a second cached prepare, never just cold initialization.
        cached=observe_prepare("prepare-cached")
        outs=None; error=None
        try:
            outs=torch.ops.qwen36_damp_integer_probe.certify_bits(*inputs)
            torch.npu.synchronize()
        except Exception as exc: error=repr(exc)
        artifact=outdir/f"{case_no:04d}-{name}.pt"
        # Keep original dispatch failure even when subsequent D2H also fails.
        observation=save_observation(torch.save,artifact,returns=outs,roots=roots,
            dispatch_error=error,labels=[r["label"] for r in chunk],useful=useful,
            rows=chunk,before=before,golden_interiors=gold,input_pointers=ptrs,
            output_pointers=None if outs is None else [t.data_ptr() for t in outs])
        assert_true(error is None and outs is not None,"certify dispatch failed: "+str(error))
        assert_true(not observation["output_copy_errors"] and
                    not observation["input_copy_errors"],
                    "certify D2H failed (nullable raw record already saved)")
        cpu_out=observation["outputs_full"];after=observation["after"]
        assert_true(len(outs)==7,"actual output arity")
        assert_true(all(t.dtype==torch.int32 and t.shape==(count+16,) and
                    torch_npu.get_npu_format(t)==2 and t.data_ptr()%32==0 for t in outs),
                    "output dtype/shape/physical ND/alignment")
        assert_true(all(disjoint(o,r) for o in outs for r in roots) and
                    all(disjoint(outs[i],outs[j]) for i in range(7) for j in range(i)),
                    "full backing storage aliases")
        for i,out in enumerate(cpu_out):
            guard=torch.full((8,),GUARDS[i],dtype=torch.int32)
            assert_true(torch.equal(out[:8],guard) and torch.equal(out[-8:],guard),
                        f"{NAMES[i]} guard corruption")
            assert_true(torch.equal(out[8:-8],gold[i]),f"bitwise {NAMES[i]} mismatch")
        assert_true(all(torch.equal(a,b) for a,b in zip(before,after)),"input-root mutation")
        assert_true(ptrs==[t.data_ptr() for t in roots]+[t.data_ptr() for t in inputs],
                    "input storage pointer changed")
        accepted_count+=int(gold[0][:useful].sum());lane_count+=useful
        records.append({"case":name,"count":count,"useful":useful,"artifact":artifact.name,
                        "artifact_sha256":digest(artifact),"prepare_sha256":digest(prep),
                        "prepare_cached_sha256":digest(cached)})
        case_no+=1
    for count in (64,896):
        for repeat in range(args.repeats):
            one(f"N{count}_lifecycle{repeat}",lifecycle_rows(rows,count,repeat),count)
    for name,chunk,useful in chunks(endpoint_rows(),"all_endpoints"): one(name,chunk,useful)
    for name,chunk,useful in chunks(proposal_rows(rows),"all_proposals"): one(name,chunk,useful)
    # Negative guards execute BEFORE Gather, including n128/n129 despite old
    # helper precondition. Read full roots even if a view is malformed.
    for label in ("N0","N63","N65","N897","N1792","wrongdtype","shape",
                  "noncontiguous","misaligned","alias","overlap_storage",
                  "proposal_CPU","CPU","n_minus1","n128","n129","nINTMIN","nINTMAX"):
        roots,inputs=make_inputs(lifecycle_rows(rows,64,1))
        if label.startswith("N"):
            count=int(label[1:])
            roots=[nd(torch.ones(count,dtype=torch.int32)) for _ in range(3)];inputs=roots
        elif label=="wrongdtype": roots[2]=nd(torch.ones(64,dtype=torch.float32));inputs[2]=roots[2]
        elif label=="shape": roots[2]=nd(torch.ones(63,dtype=torch.int32));inputs[2]=roots[2]
        elif label=="noncontiguous":
            roots[2]=nd(torch.ones(128,dtype=torch.int32));inputs[2]=roots[2][::2]
        elif label=="misaligned":
            roots[2]=nd(torch.ones(65,dtype=torch.int32));inputs[2]=roots[2][1:]
        elif label=="alias": roots[2]=roots[0];inputs[2]=inputs[0]
        elif label=="overlap_storage":
            root=nd(torch.ones(128,dtype=torch.int32))
            roots=[root,root,roots[2]];inputs=[root[:64],root[64:],inputs[2]]
        elif label=="proposal_CPU":
            roots[2]=torch.ones(64,dtype=torch.int32);inputs[2]=roots[2]
        elif label=="CPU": roots=[torch.ones(64,dtype=torch.int32) for _ in range(3)];inputs=roots
        else:
            value={"n_minus1":-1,"n128":128,"n129":129,
                   "nINTMIN":-(1<<31),"nINTMAX":(1<<31)-1}[label]
            roots[2]=nd(torch.tensor([INPUT_GUARD]*8+[0]*63+[value]+[INPUT_GUARD]*8,
                                    dtype=torch.int32));inputs[2]=roots[2][8:-8]
        for opname in ("prepare","certify_bits"): reject(label,roots,inputs,opname)
    return {"passed":True,"records":records,"admission_negatives":negative,
            "provenance":provenance,"accepted_lanes":accepted_count,"useful_lanes":lane_count,
            "fallback_fraction_is_diagnostic_not_throughput":True,
            "gather_mask_compaction_implemented":False,"graph_supported":False,
            "loaded_libraries":loaded_libraries()}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--software-only",action="store_true")
    p.add_argument("--meta-only",action="store_true")
    for field in ("library","library-sha256","source-manifest","runtime-manifest","build-receipt","preflight","output-dir"):
        p.add_argument("--"+field)
    p.add_argument("--logical-device",type=int,default=0)
    p.add_argument("--repeats",type=int,default=20)
    args=p.parse_args()
    assert_true(lut_hashes()==LUT_HASHES,"fixed C/F table hashes")
    for relative,sha in FROZEN_SOURCE_SHA.items():
        assert_true(digest(BASE/relative)==sha,"frozen dependency hash "+relative)
    if args.software_only:
        from test_software_contract import run
        run(); return
    assert_true(args.repeats>=20,"N64 and896 require at least20 changed-input calls")
    for field in ("library","library_sha256","source_manifest","runtime_manifest","build_receipt","output_dir"):
        assert_true(getattr(args,field),"missing --"+field.replace("_","-"))
    assert_true(Path(args.output_dir).is_absolute(),"absolute nonoverwriting output directory required")
    bindings=source_checks(args)
    if not args.meta_only:
        assert_true(args.preflight,"fresh parent preflight required")
        bindings.update(preflight_checks(args))
    outdir=Path(args.output_dir);outdir.mkdir(parents=False,exist_ok=False)
    rows=labeled_fixtures()
    result={"status":"running","scope":"isolated integer certificate plus exact fallback",
            "production_integrated":False,"graph_supported":False,"npu_executed":False,
            "fixture_count":len(rows),"lut_hashes":LUT_HASHES,**bindings}
    try:
        result["cann_environment"]=cann_environment_checks(bindings)
        import torch
        import torch_npu
        torch.ops.load_library(str(Path(args.library).resolve()))
        result["schema"]=str(torch.ops.qwen36_damp_integer_probe.certify_bits.default._schema)
        result["prepare_schema"]=str(torch.ops.qwen36_damp_integer_probe.prepare.default._schema)
        result["meta"]=meta_gate(torch)
        if not args.meta_only:
            result["npu_executed"]=True
            result["actual"]=actual_gate(torch,torch_npu,args,outdir,rows,result.setdefault("actual",{}))
        result["status"]="pass"
    except Exception as exc:
        result["status"]="fail";result["error"]=repr(exc);result["traceback"]=traceback.format_exc()
        raise
    finally:
        result["loaded_libraries"]=loaded_libraries()
        with (outdir/"report.json").open("x") as stream: json.dump(result,stream,indent=2,sort_keys=True)
        print(json.dumps({"status":result["status"],"scope":result["scope"],
                         "npu_executed":result["npu_executed"],"report":str(outdir/"report.json")},sort_keys=True))
if __name__=="__main__": main()
