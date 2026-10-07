#!/usr/bin/env python3
"""NEW v2 true-T2..15 Meta only. Default OFF; no native bootstrap or devices."""
from __future__ import annotations
import argparse,json,os,re,time
from pathlib import Path
import binding as b
def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
    for n in ("followup-manifest","library","build-receipt","meta-receipt"):
        p.add_argument("--"+n);p.add_argument("--"+n+"-sha256")
    p.add_argument("--output");a=p.parse_args(argv)
    if not a.execute:
        print(json.dumps(dict(status="OFF",namespace=b.NS,npu_executed=False,serving_ready=False)));return 0
    names=("followup_manifest","library","build_receipt","meta_receipt")
    b.require(all(getattr(a,n) and getattr(a,n+"_sha256") for n in names) and a.output,"actual MAIN Refs/fresh output")
    refs={n:dict(path=getattr(a,n),sha256=getattr(a,n+"_sha256")) for n in names}
    packet,gm,pins,own,_,_,_=b.sources(refs["followup_manifest"])
    ar=dict(library=refs["library"],build=refs["build_receipt"],meta=refs["meta_receipt"])
    _,oldmeta=b.artifacts(ar,gm,pins)
    before={**pins,**own};oracle=b.load_oracle(gm)
    b.require(os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD")=="0"
              and os.environ.get("PYTHONDONTWRITEBYTECODE")=="1","no-autoload/no bytecode")
    b.require(not any(re.fullmatch("davinci[0-9]+",x.name) for x in Path("/dev").iterdir()),"no compute device Meta")
    out=Path(a.output);b.require(out.is_absolute() and not out.exists() and not out.is_symlink()
                               and out.parent.is_dir(),"fresh output in existing MAIN directory")
    import torch,torch_npu
    torch.ops.load_library(ar["library"]["path"]);ops=getattr(torch.ops,b.NS);oracle.bind_candidate(ops)
    b.require(str(ops.decode.default._schema)==oldmeta["schema"]
              and str(ops.prepare.default._schema)==oldmeta["prepare_schema"],"same actual loaded v2 schema")
    mapped={}
    for line in Path("/proc/self/maps").read_text().splitlines():
        fields=line.split()
        if len(fields)>=6 and fields[-1]==ar["library"]["path"]:mapped[fields[-1]]=b.digest(b.read_file(fields[-1]))
    b.require(mapped.get(ar["library"]["path"])==ar["library"]["sha256"],"actual mapped v2 SO")
    rows=[]
    for t in range(2,16):
        x=b.meta_inputs(torch,t);prepared=ops.prepare(x[0],x[5]);y=ops.decode(*x)
        nonalias=all(y.untyped_storage()._cdata!=v.untyped_storage()._cdata for v in x)
        b.require(prepared is None and tuple(y.shape)==(t,12,128) and y.dtype==torch.bfloat16
                  and y.device.type=="meta" and nonalias,"genuine T Meta/nonalias")
        rows.append(dict(T=t,shape=list(y.shape),dtype=str(y.dtype),device=y.device.type,
                         nonalias=nonalias,prepare_return_none=prepared is None))
    _,_,p2,o2,_,_,_=b.sources(refs["followup_manifest"]);after={**p2,**o2}
    b.require(before==after,"source drift during Meta14")
    report=dict(status="actual_v2_14_positive_Meta_pass",namespace=b.NS,meta=rows,
        source_manifest=packet["v2_gate_manifest"],followup_manifest=refs["followup_manifest"],
        artifact_refs=ar,sources_before=before,sources_after=after,loaded_libraries=mapped,
        library_sha256=ar["library"]["sha256"],schema=oldmeta["schema"],prepare_schema=oldmeta["prepare_schema"],
        no_davinci_devices_observed=True,native_bootstrap_verified=False,npu_executed=False,
        serving_ready=False,graph_proven=False,physical_nd_proven=False,completed_ns=time.time_ns(),
        runtime=dict(torch=torch.__version__,torch_npu=torch_npu.__version__,
                     torch_path=str(Path(torch.__file__).resolve()),torch_npu_path=str(Path(torch_npu.__file__).resolve())))
    b.write_new(out,report)
    print(json.dumps(dict(report=b.actual_ref(out),npu_executed=False,serving_ready=False)));return 0
if __name__=="__main__":raise SystemExit(main())
