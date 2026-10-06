#!/usr/bin/env python3
"""Isolate FP32 constant-division lowering; not an algorithm success gate."""
import argparse, hashlib, json, os
from pathlib import Path
import torch, torch_npu
p=argparse.ArgumentParser()
p.add_argument("--output-dir",type=Path,required=True)
a=p.parse_args()
out=a.output_dir.resolve()
if Path("/damp-results") not in out.parents or out.exists():
    p.error("fresh /damp-results output required")
if os.environ.get("ASCEND_RT_VISIBLE_DEVICES")!="0":
    p.error("require logical0/physical4")
out.mkdir(parents=True)
report={"scope":"isolated FP32 max/127 versus reciprocal multiplication","status":"running",
        "script_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"cases":[]}
def metrics(x,y):
    x,y=x.detach().cpu().contiguous(),y.detach().cpu().contiguous()
    d=(x-y).abs()
    return {"bitwise":torch.equal(x.view(torch.uint8),y.view(torch.uint8)),
            "mismatches":int((x.view(torch.int32)!=y.view(torch.int32)).sum()),
            "max_abs":float(d.max()),"max_relative":float((d/y.abs().clamp_min(1e-30)).max()),
            "max_ulp":int((x.view(torch.int32).long()-y.view(torch.int32).long()).abs().max())}
try:
    torch.npu.set_device(0)
    generator=torch.Generator().manual_seed(260827513)
    reciprocal=torch.tensor(1.0/127,dtype=torch.float32)
    for dv,dk in ((96,64),(128,128)):
        s=torch.randn((1,12,dv,dk),generator=generator)*0.1
        s[:,:,:32,20]=0
        x=s.transpose(-1,-2).contiguous()[:,:,16:].reshape(1,12,dk-16,dv//32,32)
        cpu_max=x.abs().max(-1).values
        npu_max=x.to("npu:0").abs().amax(-1)
        npu_div=npu_max/127
        npu_mul=npu_max*reciprocal.to("npu:0")
        cpu_div=cpu_max/127
        cpu_mul=cpu_max*reciprocal
        # No changing candidate from these metrics; this diagnostic only identifies lowering.
        report["cases"].append({"dv":dv,"dk":dk,
            "max_reduction":metrics(npu_max,cpu_max),
            "division_vs_division":metrics(npu_div,cpu_div),
            "division_vs_reciprocal":metrics(npu_div,cpu_mul),
            "reciprocal_vs_reciprocal":metrics(npu_mul,cpu_mul),
            "cpu_division_vs_reciprocal":metrics(cpu_div,cpu_mul)})
    report["status"]="diagnostic_complete"
except BaseException as error:
    report.update(status="failed",error=repr(error))
    raise
finally:
    (out/"report.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
print(json.dumps(report))
