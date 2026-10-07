#!/usr/bin/env python3
"""NEW no-device load/schema/Meta only. Default OFF; no native/NPU bootstrap."""
from __future__ import annotations
import argparse,json,os,re,sys,time
from pathlib import Path
from contract import (NAMESPACE,require,sha,ref,source_admission,build_artifact_identity)

def meta_inputs(torch,t):
    s=t+3
    def empty(shape,dtype):return torch.empty(shape,dtype=dtype,device="meta")
    return (
      empty((t,4,128),torch.bfloat16),empty((t,4,128),torch.bfloat16),
      empty((t,12,128),torch.bfloat16),empty((t,12),torch.float32),
      empty((t,12),torch.bfloat16),empty((s,12,128,128),torch.float32),
      empty((s,4,16,128),torch.bfloat16),empty((s,12,16,128),torch.float32),
      empty((s,12,32),torch.float32),empty((s,12,32),torch.float32),
      empty((s,12,32),torch.int32),empty((t+1,),torch.int32),empty((t,),torch.int32))

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--execute",action="store_true")
    p.add_argument("--source-manifest",type=Path);p.add_argument("--source-manifest-sha256")
    p.add_argument("--library",type=Path);p.add_argument("--library-sha256")
    p.add_argument("--build-receipt",type=Path);p.add_argument("--build-receipt-sha256")
    p.add_argument("--output",type=Path)
    a=p.parse_args(argv)
    if not a.execute:
        print(json.dumps({"default_enabled":False,"npu_executed":False,"serving_ready":False,
                          "namespace":NAMESPACE,"scope":"no-device-load-schema-Meta-only"}))
        return
    require(all((a.source_manifest,a.source_manifest_sha256,a.library,a.library_sha256,
                 a.build_receipt,a.build_receipt_sha256,a.output)),"MAIN actual NEW Refs/output")
    source_ref=ref({"path":str(a.source_manifest),"sha256":a.source_manifest_sha256})
    manifest,before=source_admission(source_ref)
    build_ref=ref({"path":str(a.build_receipt),"sha256":a.build_receipt_sha256})
    library_ref=ref({"path":str(a.library.resolve()),"sha256":a.library_sha256})
    build_artifact_identity(build_ref,library_ref,manifest)
    require(os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD")=="0" and
            os.environ.get("PYTHONDONTWRITEBYTECODE")=="1","explicit no-autoload/no-bytecode")
    devices=[str(x) for x in Path("/dev").iterdir() if re.fullmatch(r"davinci[0-9]+",x.name)]
    require(not devices,"Meta worker must not map davinci compute devices")
    out=a.output
    require(out.is_absolute() and not out.exists() and not out.is_symlink() and out.parent.is_dir(),
            "fresh explicit output in existing MAIN directory")
    import torch,torch_npu
    torch.ops.load_library(library_ref["path"])
    import oracle
    ops=getattr(torch.ops,NAMESPACE);oracle.bind_candidate(ops)
    schema=str(ops.decode.default._schema);prepare_schema=str(ops.prepare.default._schema)
    require(prepare_schema==NAMESPACE+"::prepare(Tensor query, Tensor base_state) -> ()",
            "actual prepare schema")
    loaded={}
    for line in Path("/proc/self/maps").read_text().splitlines():
        fields=line.split()
        if len(fields)>=6 and fields[-1].startswith("/") and fields[-1]==library_ref["path"]:
            loaded[fields[-1]]=sha(fields[-1])
    require(loaded.get(library_ref["path"])==library_ref["sha256"],"actual mapped NEW library")
    cases=[]
    for t in (1,16):
        inputs=meta_inputs(torch,t)
        prepared=ops.prepare(inputs[0],inputs[5])
        require(prepared is None,"prepare Meta returns None")
        y=ops.decode(*inputs)
        require(tuple(y.shape)==(t,12,128) and y.dtype==torch.bfloat16 and y.device.type=="meta",
                "actual fresh Meta shape/dtype/device")
        storage=y.untyped_storage()._cdata
        nonalias=all(storage!=x.untyped_storage()._cdata for x in inputs)
        require(nonalias,"fresh Meta output storage must not alias any input")
        cases.append({"T":t,"shape":list(y.shape),"dtype":str(y.dtype),"device":y.device.type,
                      "nonalias":nonalias,"prepare_return_none":prepared is None})
    _,after=source_admission(source_ref)
    require(before==after,"source drift during actual Meta")
    report={"status":"pass","npu_executed":False,"namespace":NAMESPACE,
            "materialization_interval":8,"storage_log_capacity":16,"schema":schema,
            "prepare_schema":prepare_schema,"meta":cases,"source_manifest":source_ref,
            "sources_before":before,"sources_after":after,"library_sha256":library_ref["sha256"],
            "build_receipt_sha256":build_ref["sha256"],"loaded_libraries":loaded,
            "loaded_candidate_sha256":loaded[library_ref["path"]],
            "no_davinci_devices_observed":True,"native_bootstrap_verified":False,
            "physical_soc_runtime_observed":False,"serving_ready":False,
            "runtime":{"torch":torch.__version__,"torch_npu":torch_npu.__version__,
                       "torch_path":str(Path(torch.__file__).resolve()),
                       "torch_npu_path":str(Path(torch_npu.__file__).resolve())},
            "completed_ns":time.time_ns(),
            "not_validated":["PrivateUse1 numerical","runtime ND/layout",
                             "dynamic metadata","graph","native bootstrap","service"]}
    with out.open("x") as stream:stream.write(json.dumps(report,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"status":"pass","report":str(out),"sha256":sha(out),"npu_executed":False}))

if __name__=="__main__":main()
