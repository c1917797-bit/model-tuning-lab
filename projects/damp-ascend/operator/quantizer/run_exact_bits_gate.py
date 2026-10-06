#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Isolated NPU exact-bits gate. Main agent alone may execute device phase.
No production state, fast certificate, GatherMask or E2E claims are included.
Every actual return is saved BEFORE numerical/guard/input assertions.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import traceback
from probe_fixtures import build_fixtures, fixture_sha, chunk_cases

BASE = Path(__file__).resolve().parent
SOURCE_NAMES = (
    "CMakeLists.txt", "exact_quantizer_bits.h", "op_extension/ops.h",
    "op_extension/register.cpp", "op_extension/quantizer_torch.cpp",
    "op_kernel/quantizer_probe_kernel.asc", "op_kernel/quantizer_probe.h",
    "test_exact_quantizer.py",
    "probe_fixtures.py", "run_exact_bits_gate.py")
CODE_GUARD, VALID_GUARD, INPUT_GUARD = 0x13579BDF, 0x2468ACE0, 0x10293847

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

def source_checks(args):
    manifest = read_json(args.source_manifest)
    assert_true(manifest.get("schema") == "damp_quantizer_sources_v1",
                "unsupported source manifest")
    expected = manifest.get("sources")
    assert_true(isinstance(expected, dict) and set(expected) == set(SOURCE_NAMES),
                "manifest must bind exact registered source list")
    actual = {}
    for relative in SOURCE_NAMES:
        actual[relative] = digest(BASE/relative)
        assert_true(actual[relative] == expected[relative], f"source hash {relative}")
    receipt = read_json(args.build_receipt)
    assert_true(receipt.get("schema") == "damp_quantizer_build_v1",
                "unsupported parent-produced build receipt")
    assert_true(receipt.get("sources") == actual and
                receipt.get("library_sha256") == args.library_sha256 and
                receipt.get("npu_arch") == "dav-2201" and
                receipt.get("soc") == "Ascend910B4" and
                receipt.get("cann_version") == "9.1.0",
                "build/source/SO/architecture binding mismatch")
    assert_true(digest(args.library) == args.library_sha256, "SO hash mismatch")
    return {"sources": actual, "build_receipt": receipt,
            "source_manifest_sha256": digest(args.source_manifest),
            "build_receipt_sha256": digest(args.build_receipt),
            "library": str(Path(args.library).resolve()),
            "library_sha256": args.library_sha256}

def preflight_checks(args):
    proof = read_json(args.preflight)
    assert_true(proof.get("schema") == "damp_quantizer_preflight_v1" and
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
    records = []
    for count in (64,1792):
        x, scale = [torch.empty(count, dtype=torch.int32, device="meta") for _ in range(2)]
        torch.ops.qwen36_damp_quantizer.prepare(x, scale)
        outputs = torch.ops.qwen36_damp_quantizer.exact_bits(x, scale)
        assert_true(len(outputs) == 2 and all(t.shape == (count+16,) and
                    t.dtype == torch.int32 and t.device.type == "meta" for t in outputs),
                    "Meta output contract")
        records.append({"count":count,"shape":[count+16],"dtype":"int32"})
    for count in (0,63,65,1793):
        x, scale = [torch.empty(count,dtype=torch.int32,device="meta") for _ in range(2)]
        for name in ("prepare","exact_bits"):
            try:
                getattr(torch.ops.qwen36_damp_quantizer,name)(x,scale)
            except RuntimeError:
                continue
            raise AssertionError(f"Meta {name} accepted bad count {count}")
    x = torch.empty(64,device="meta",dtype=torch.float32)
    try:
        torch.ops.qwen36_damp_quantizer.prepare(x,x.clone())
    except RuntimeError:
        pass
    else:
        raise AssertionError("Meta accepted wrong dtype")
    return {"passed":True,"records":records,
            "scope":"shape/dtype/count only; no physical ND/SoC/alias/graph proof"}

def actual_gate(torch, torch_npu, args, outdir, rows, progress):
    device = f"npu:{args.logical_device}"
    torch.npu.set_device(args.logical_device)
    assert_true(torch.npu.get_device_name(device) == "Ascend910B4", "actual SoC mismatch")
    assert_true(torch.__version__ == "2.10.0+cpu" and
                torch_npu.__version__ == "2.10.0.post4", "deployed Torch/TorchNPU mismatch")
    provenance = {"torch":torch.__version__,"torch_npu":torch_npu.__version__,
                  "device_name":torch.npu.get_device_name(device),
                  "ascend_home_path":os.environ.get("ASCEND_HOME_PATH"),
                  "ascend_visible_devices":os.environ.get("ASCEND_RT_VISIBLE_DEVICES")}
    def nd(t):
        result = torch_npu.npu_format_cast(t.to(device).contiguous(),2)
        assert_true(torch_npu.get_npu_format(result) == 2, "input physical ND")
        return result
    def span(t):
        begin = t.data_ptr()
        return begin, begin+t.numel()*t.element_size()
    def disjoint(a,b):
        ab,ae=span(a); bb,be=span(b)
        return ae <= bb or be <= ab
    records = []
    progress.update({"passed":False,"records":records,"provenance":provenance})
    for case_no, (name, chunk, useful) in enumerate(chunk_cases(rows)):
        count = len(chunk)
        x_cpu = torch.tensor([INPUT_GUARD]*8 + [signed(r["x_bits"]) for r in chunk] +
                             [INPUT_GUARD]*8,dtype=torch.int32)
        s_cpu = torch.tensor([INPUT_GUARD]*8 + [signed(r["scale_bits"]) for r in chunk] +
                             [INPUT_GUARD]*8,dtype=torch.int32)
        x_root, s_root = nd(x_cpu), nd(s_cpu)
        x, scale = x_root[8:8+count], s_root[8:8+count]
        golden_code = torch.tensor([r["code"] for r in chunk],dtype=torch.int32)
        golden_valid = torch.tensor([r["valid"] for r in chunk],dtype=torch.int32)
        before_x, before_s = x_root.cpu().clone(),s_root.cpu().clone()
        torch.ops.qwen36_damp_quantizer.prepare(x,scale)
        torch.npu.synchronize()
        after_prepare_x,after_prepare_s=x_root.cpu().clone(),s_root.cpu().clone()
        # Save raw prepare results before invariant assertions.
        torch.save({"x_before":before_x,"s_before":before_s,
                    "x_after_prepare":after_prepare_x,"s_after_prepare":after_prepare_s},
                   outdir/f"{case_no:03d}-prepare.pt")
        assert_true(torch.equal(before_x,after_prepare_x) and
                    torch.equal(before_s,after_prepare_s), "prepare mutated full inputs")
        input_pointers=(x_root.data_ptr(),s_root.data_ptr(),x.data_ptr(),scale.data_ptr())
        for repeat in range(args.repeats):
            codes,valid = torch.ops.qwen36_damp_quantizer.exact_bits(x,scale)
            torch.npu.synchronize()
            code_cpu,valid_cpu=codes.cpu().clone(),valid.cpu().clone()
            after_x,after_s=x_root.cpu().clone(),s_root.cpu().clone()
            artifact=outdir/f"{case_no:03d}-repeat{repeat:02d}.pt"
            torch.save({"labels":[r["label"] for r in chunk], "useful":useful,
                        "x_before":before_x,"s_before":before_s,
                        "x_after":after_x,"s_after":after_s,
                        "codes_full":code_cpu,"valid_full":valid_cpu,
                        "golden_code":golden_code,"golden_valid":golden_valid},artifact)
            # Raw outputs/input-after saved above, including any failure.
            assert_true(codes.dtype==valid.dtype==torch.int32 and
                        codes.shape==valid.shape==(count+16,), "actual output shape/dtype")
            assert_true(torch_npu.get_npu_format(codes)==torch_npu.get_npu_format(valid)==2,
                        "actual output physical ND")
            assert_true(all(disjoint(output,inp) for output in (codes,valid)
                            for inp in (x_root,s_root)) and disjoint(codes,valid),
                        "output/input storage alias")
            assert_true(torch.equal(code_cpu[:8],torch.full((8,),CODE_GUARD,dtype=torch.int32)) and
                        torch.equal(code_cpu[-8:],torch.full((8,),CODE_GUARD,dtype=torch.int32)) and
                        torch.equal(valid_cpu[:8],torch.full((8,),VALID_GUARD,dtype=torch.int32)) and
                        torch.equal(valid_cpu[-8:],torch.full((8,),VALID_GUARD,dtype=torch.int32)),
                        "output guard corruption")
            assert_true(torch.equal(code_cpu[8:-8],golden_code) and
                        torch.equal(valid_cpu[8:-8],golden_valid), "bitwise code/valid mismatch")
            assert_true(torch.equal(before_x,after_x) and torch.equal(before_s,after_s),
                        "complete guarded input mutated")
            assert_true(input_pointers==(x_root.data_ptr(),s_root.data_ptr(),
                        x.data_ptr(),scale.data_ptr()), "input storage pointer changed")
            records.append({"case":name,"count":count,"useful":useful,"repeat":repeat,
                            "artifact":artifact.name,"artifact_sha256":digest(artifact)})
    # Wrapper admission negatives; snapshot every raw input before/after on exception.
    negatives=[]
    progress["admission_negatives"]=negatives
    for label in ("N0","N63","N65","N1793","wrongdtype","noncontiguous","misaligned","alias","scale_CPU","CPU"):
        if label.startswith("N"):
            count=int(label[1:]); a_root=nd(torch.ones(count,dtype=torch.int32)); b_root=nd(torch.ones(count,dtype=torch.int32))
            a,b=a_root,b_root
        elif label=="wrongdtype":
            a_root=nd(torch.ones(64,dtype=torch.float32)); b_root=a_root.clone();a,b=a_root,b_root
        elif label=="noncontiguous":
            a_root=nd(torch.ones(128,dtype=torch.int32));b_root=nd(torch.ones(64,dtype=torch.int32));a,b=a_root[::2],b_root
        elif label=="misaligned":
            a_root=nd(torch.ones(65,dtype=torch.int32));b_root=nd(torch.ones(64,dtype=torch.int32));a,b=a_root[1:],b_root
        elif label=="alias":
            a_root=nd(torch.ones(64,dtype=torch.int32));b_root=a_root;a,b=a_root,b_root
        elif label=="scale_CPU":
            a_root=nd(torch.ones(64,dtype=torch.int32));b_root=torch.ones(64,dtype=torch.int32);a,b=a_root,b_root
        else:
            a_root=torch.ones(64,dtype=torch.int32);b_root=a_root.clone();a,b=a_root,b_root
        before_a,before_b=a_root.cpu().clone(),b_root.cpu().clone()
        for opname in ("prepare","exact_bits"):
            error=None
            try:
                getattr(torch.ops.qwen36_damp_quantizer,opname)(a,b)
                torch.npu.synchronize()
            except Exception as exc:
                error=repr(exc)
            after_a,after_b=a_root.cpu().clone(),b_root.cpu().clone()
            artifact=outdir/f"negative-{label}-{opname}.pt"
            torch.save({"input_before":[before_a,before_b],"input_after":[after_a,after_b],
                        "error":error},artifact)
            assert_true(error is not None, f"negative {label}/{opname} accepted")
            assert_true(torch.equal(before_a,after_a) and torch.equal(before_b,after_b),
                        f"negative {label}/{opname} mutated inputs")
            negatives.append({"label":label,"op":opname,"error":error,
                              "artifact":artifact.name,"artifact_sha256":digest(artifact)})
    return {"passed":True,"records":records,"admission_negatives":negatives,
            "provenance":provenance,"loaded_libraries":loaded_libraries()}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--software-only",action="store_true")
    p.add_argument("--meta-only",action="store_true")
    p.add_argument("--library");p.add_argument("--library-sha256")
    p.add_argument("--source-manifest");p.add_argument("--build-receipt")
    p.add_argument("--preflight");p.add_argument("--output-dir")
    p.add_argument("--logical-device",type=int,default=0)
    p.add_argument("--repeats",type=int,default=20)
    p.add_argument("--random-count",type=int,default=2048)
    args=p.parse_args()
    rows=build_fixtures(args.random_count)
    if args.software_only:
        from test_exact_quantizer import exact_bin_model
        for row in rows:
            assert_true(exact_bin_model(row["x_bits"],row["scale_bits"]) ==
                        (bool(row["valid"]),row["code"]), "software exact model mismatch")
        print(json.dumps({"status":"pass","scope":"new fixture mathematics only",
              "fixtures":len(rows),"fixture_sha256":fixture_sha(rows),
              "cases":len(chunk_cases(rows)),"npu_executed":False},sort_keys=True))
        return
    assert_true(not args.software_only and args.repeats>=20,"at least20 lifecycle repeats")
    for field in ("library","library_sha256","source_manifest","build_receipt","output_dir"):
        assert_true(getattr(args,field), f"missing --{field.replace('_','-')}")
    assert_true(Path(args.output_dir).is_absolute(),"output directory must be absolute")
    # Any failure before device initialization is reportable and does not start NPU.
    bindings=source_checks(args)
    if not args.meta_only:
        assert_true(args.preflight,"NPU phase requires fresh parent preflight")
        bindings.update(preflight_checks(args))
    outdir=Path(args.output_dir)
    outdir.mkdir(parents=False,exist_ok=False)
    result={"status":"running","scope":"isolated quantizer only","fast_enabled":False,
            "production_integrated":False,"npu_executed":False,
            "fixture_sha256":fixture_sha(rows),"fixture_count":len(rows),**bindings}
    try:
        import torch
        import torch_npu
        torch.ops.load_library(str(Path(args.library).resolve()))
        result["operator_schema"]=str(torch.ops.qwen36_damp_quantizer.exact_bits.default._schema)
        result["prepare_schema"]=str(torch.ops.qwen36_damp_quantizer.prepare.default._schema)
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
        # Dedicated new output folder; no overwriting old experiments.
        with (outdir/"report.json").open("x") as stream:
            json.dump(result,stream,indent=2,sort_keys=True)
        print(json.dumps({"status":result["status"],"scope":result["scope"],
              "npu_executed":result["npu_executed"],"report":str(outdir/"report.json")},
              sort_keys=True))
if __name__=="__main__":
    main()
