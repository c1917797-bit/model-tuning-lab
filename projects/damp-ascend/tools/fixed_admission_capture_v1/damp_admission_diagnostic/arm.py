"""MAIN-only actual mapped-image arm. Canary then the unchanged frozen offline runner."""
from __future__ import annotations
import argparse
import os
import runpy
from pathlib import Path
import sys
from diag_contract import ARMS,COLLECTOR,source_contract,runtime_environment,write_new
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest",required=True);p.add_argument("--output-dir",required=True)
    p.add_argument("--arm",choices=ARMS,required=True)
    a=p.parse_args()
    source_contract()
    write_new(Path(a.output_dir).parent/(a.arm+"-environment.json"),
              runtime_environment(Path(a.output_dir).parent))
    # Canary is explicit, on only inspected logical0..3, before loading weights.
    import torch
    import torch_npu  # noqa:F401
    assert os.environ.get("ASCEND_RT_VISIBLE_DEVICES")=="0,1,2,3"
    assert torch.npu.device_count()==4
    for logical in range(4):
        torch.npu.set_device(logical)
        assert torch.ones(16,device="npu").sum().cpu().item()==16
        torch.npu.synchronize()
    torch.npu.set_device(0)
    os.environ["DAMP_ADMISSION_TRACE_ENABLE"]="1"
    os.environ["DAMP_ADMISSION_ARM"]=a.arm
    sys.argv=["damp_capture.run","--manifest",a.manifest,"--output-dir",a.output_dir,
        "--capture","on" if a.arm=="on" else "off","--batch-size","1","--memory-utilization","0.80"]
    runpy.run_module("damp_capture.run",run_name="__main__")
if __name__=="__main__":
    main()
