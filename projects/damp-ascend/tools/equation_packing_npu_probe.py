#!/usr/bin/env python3
"""Real Ascend equation/packing gate. Not a fused kernel or E2E benchmark."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
import torch
import torch_npu

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reference import (Layout, transform_state, restore_state, transformed_inputs,
                       restore_output, pack, unpack, gdn_step, storage_bytes, risk,
                       SCALE_RECIPROCAL_FP32)

H_QK, H_V, D, STEPS = 4, 12, 128, 160
SCALE = D ** -0.5
SOURCE_HASH = "d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816"

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def rel(actual, expected):
    a, e = actual.detach().float().cpu().double(), expected.detach().float().cpu().double()
    return math.sqrt(float((a-e).square().sum()) / max(float(e.square().sum()), 1e-30))

def finite(*xs):
    return all(bool(torch.isfinite(x).all().cpu()) for x in xs)

def exact(a, b):
    return torch.equal(a.detach().cpu().contiguous().view(torch.uint8),
                       b.detach().cpu().contiguous().view(torch.uint8))

def cpu_pack_oracle(t, layout):
    # Explicit independent group loop, not reference int8_groups.
    x = t.detach().float().cpu().transpose(-1, -2).contiguous()
    high = x[:, :, :layout.khi].half()
    low = x[:, :, layout.khi:]
    codes = torch.empty_like(low, dtype=torch.int8)
    scales = torch.empty((*low.shape[:-1], low.shape[-1]//layout.group))
    for group in range(low.shape[-1]//layout.group):
        sl = slice(group*layout.group, (group+1)*layout.group)
        chunk = low[..., sl]
        maximum = chunk.abs().max(-1).values
        scale = torch.where(maximum == 0, torch.ones_like(maximum),
                            maximum*torch.tensor(SCALE_RECIPROCAL_FP32, dtype=torch.float32))
        codes[..., sl] = torch.round(chunk/scale[..., None]).clamp(-127,127).to(torch.int8)
        scales[..., group] = scale
    return high, codes, scales

def packing_gate(report):
    rng = torch.Generator().manual_seed(260827513)
    checks = []
    for dv, dk in ((96,64), (128,128)):
        state = torch.randn((1,H_V,dv,dk), generator=rng)*0.1
        state[:, :, :32, 20] = 0
        c = torch.ones((H_V,dv), device="npu:0")
        pv = torch.arange(dv).repeat(H_V,1).to("npu:0")
        pk = torch.arange(dk).repeat(H_V,1).to("npu:0")
        layout = Layout(c,pv,pk)
        device_state = state.to("npu:0")
        packed = pack(device_state,layout)
        high, codes, scales = cpu_pack_oracle(device_state, layout)
        checks.append(dict(dv=dv,dk=dk, high_exact=exact(packed.high,high),
                           codes_exact=exact(packed.codes,codes),
                           scales_exact=exact(packed.scales,scales),
                           finite=finite(packed.high,packed.scales,unpack(packed,layout)),
                           bytes_per_head=storage_bytes(packed)//H_V))
    report["packing_checks"] = checks
    ties = torch.tensor([-2.5,-1.5,-0.5,0.5,1.5,2.5]).to("npu:0")
    report["ties_to_even"] = torch.equal(torch.round(ties).cpu(), torch.tensor([-2.,-2.,0.,0.,2.,2.]))
    e = torch.tensor([[[10.,0.]],[[0.,9.]]])
    score = risk(e,torch.tensor([[1.],[101.]]),torch.tensor([0.5,0.5]))
    report["weighted_error_before_mean"] = int(score.argmax(-1)) == 1
    if not all(all(x[k] for k in ("high_exact","codes_exact","scales_exact","finite")) for x in checks):
        raise RuntimeError("NPU pack/reference mismatch: retain first failure")
    if checks[1]["bytes_per_head"] != 20224 or not report["ties_to_even"] or not report["weighted_error_before_mean"]:
        raise RuntimeError("packing layout/rounding/decay weighting gate failed")

def run_case(batch, report, save):
    rng = torch.Generator().manual_seed(260827513+batch)
    slots = batch+3
    native = (torch.randn((slots,H_V,D,D),generator=rng)*0.005).to("npu:0")
    c = torch.exp(torch.linspace(-0.3,0.3,D)).repeat(H_V,1).to("npu:0")
    pv = torch.stack([torch.randperm(D,generator=rng) for _ in range(H_V)]).to("npu:0")
    pk = torch.stack([torch.randperm(D,generator=rng) for _ in range(H_V)]).to("npu:0")
    layout = Layout(c,pv,pk)
    transformed = transform_state(native,layout)
    pointer = native.data_ptr()
    lengths = torch.cat((torch.zeros(1,dtype=torch.int32),torch.ones(batch,dtype=torch.int32))).to("npu:0")
    case = dict(batch=batch,slots=slots,steps=[],status="running")
    report["cases"].append(case)
    save()
    for step in range(STEPS):
        q = torch.nn.functional.normalize(torch.randn((batch,H_QK,D),generator=rng),dim=-1).bfloat16().to("npu:0")
        k = torch.nn.functional.normalize(torch.randn((batch,H_QK,D),generator=rng),dim=-1).bfloat16().to("npu:0")
        v = (torch.randn((batch,H_V,D),generator=rng)*0.2).bfloat16().to("npu:0")
        g = -(0.002+0.18*torch.rand((batch,H_V),generator=rng)).to("npu:0")
        beta = torch.sigmoid(torch.randn((batch,H_V),generator=rng)).bfloat16().to("npu:0")
        ids_cpu = (torch.arange(batch,dtype=torch.int32)+step)%slots
        ids = ids_cpu.to("npu:0")
        i64 = ids.long()
        untouched = [i for i in range(slots) if i not in ids_cpu.tolist()]
        before_native = native[untouched].clone()
        before_transformed = transformed[untouched].clone()
        qe, ke = q.float().repeat_interleave(3,1), k.float().repeat_interleave(3,1)
        qp,kp,vp = transformed_inputs(qe,ke,v,layout)
        updated, op = gdn_step(transformed.index_select(0,i64),qp,kp,vp,g,beta,SCALE)
        transformed.index_copy_(0,i64,updated)
        expected = torch.ops._C_ascend.npu_recurrent_gated_delta_rule(
            query=q,key=k,value=v,g=g,beta=beta,state=native,scale=SCALE,
            actual_seq_lengths=lengths,ssm_state_indices=ids)
        actual = restore_output(op,layout).bfloat16()
        restored = restore_state(transformed,layout)
        torch.npu.synchronize()
        state_error = rel(restored,native)
        output_error = rel(actual,expected)
        passed = (finite(native,transformed,actual,expected) and state_error<=1e-5
                  and output_error<=0.00303 and native.data_ptr()==pointer
                  and exact(before_native,native[untouched])
                  and exact(before_transformed,transformed[untouched]))
        case["steps"].append(dict(step=step+1,state_relative_l2=state_error,
                                  output_relative_l2=output_error,passed=passed))
        if step%8==0 or not passed:
            save()
        if not passed:
            raise RuntimeError(f"batch={batch},step={step+1}: state={state_error},output={output_error}")
    case["status"]="passed"
    save()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output-dir",type=Path,required=True)
    args=parser.parse_args()
    out=args.output_dir.resolve()
    if Path("/damp-results") not in out.parents or out.exists():
        parser.error("require a NEW output directory below /damp-results")
    if os.environ.get("ASCEND_RT_VISIBLE_DEVICES")!="0":
        parser.error("requires logical0 mapped to physical4")
    out.mkdir(parents=True)
    report=dict(schema="damp-equation-packing-npu/v1",status="running",
                created_ns=time.time_ns(),script_sha256=sha(__file__),
                reference_sha256=sha(Path(__file__).resolve().parents[1]/"reference.py"),
                cases=[],limits=dict(state_relative_l2=1e-5,output_relative_l2=0.00303),
                evidence_scope="uncompressed equation covariance and NPU pack parity only; NOT packed recurrence, graph, serving, speed or task accuracy")
    def save():
        (out/"report.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    save()
    try:
        source=Path("/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py")
        if sha(source)!=SOURCE_HASH:
            raise RuntimeError("deployed GDN source changed")
        from vllm_ascend.utils import enable_custom_op
        torch_npu.npu.set_compile_mode(jit_compile=False)
        if not enable_custom_op():
            raise RuntimeError("native operators unavailable")
        torch.npu.set_device(0)
        report["native_schema"]=str(torch.ops._C_ascend.npu_recurrent_gated_delta_rule.default._schema)
        report["versions"]={"torch":torch.__version__,"torch_npu":torch_npu.__version__}
        report["loaded_libraries"]=[]
        for name in sorted({line.split()[-1] for line in Path("/proc/self/maps").read_text().splitlines()
                            if "/" in line and any(x in line for x in ("libcust_opapi","vllm_ascend","ascendc"))}):
            if Path(name).is_file():
                report["loaded_libraries"].append({"path":name,"sha256":sha(name)})
        packing_gate(report)
        save()
        for batch in (1,16):
            run_case(batch,report,save)
        report["status"]="equation_and_packing_pass"
    except BaseException as error:
        report.update(status="failed",error=repr(error),error_type=type(error).__name__)
        raise
    finally:
        # Native opapi libraries can be loaded lazily by the first call.
        report["loaded_libraries_after_execution"] = []
        for name in sorted({line.split()[-1] for line in Path("/proc/self/maps").read_text().splitlines()
                            if "/" in line and any(x in line for x in ("libcust_opapi", "vllm_ascend", "ascendc"))}):
            if Path(name).is_file():
                report["loaded_libraries_after_execution"].append({"path": name, "sha256": sha(name)})
        report["completed_ns"]=time.time_ns()
        save()
    print(json.dumps({"status":report["status"],"report":str(out/"report.json")}))
if __name__=="__main__":
    main()
