#!/usr/bin/env python3
"""Actual load/schema/Meta only; no Ascend runtime initialization."""
import argparse,hashlib,json,os
from pathlib import Path
NS="qwen36_native_recurrent_copy_trace_v2"
def require(v,s):
    if not v:raise ValueError(s)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--library");p.add_argument("--library-sha256");p.add_argument("--output")
    a=p.parse_args()
    if not a.library:print(json.dumps({"default_enabled":False,"npu_executed":False}));return
    require(a.library_sha256 and a.output,"explicit actual inputs")
    require(os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD")=="0" and
            not list(Path("/dev").glob("davinci[0-9]*")),"no-device prerequisites")
    lib=Path(a.library);out=Path(a.output)
    require(lib.is_file() and not lib.is_symlink() and sha(lib)==a.library_sha256 and not out.exists(),"exact library/new receipt")
    import torch,torch_npu
    require(not torch_npu.npu.is_initialized(),"no initialized runtime")
    torch.ops.load_library(str(lib));ops=getattr(torch.ops,NS)
    schemas={n:str(getattr(ops,n).default._schema) for n in ("prepare","tiling_info","decode_trace")}
    require(schemas["prepare"]==NS+"::prepare(Tensor query, Tensor state) -> ()","actual prepare schema")
    require(schemas["tiling_info"]==NS+"::tiling_info(Tensor query, Tensor state) -> Tensor","actual tiling schema")
    require(schemas["decode_trace"]==NS+"::decode_trace(Tensor query, Tensor key, Tensor value, Tensor g, Tensor beta, Tensor(a!) state, Tensor actual_seq_lengths, Tensor state_indices, Tensor(b!) precast_trace, Tensor(c!) selected_state_trace) -> Tensor","actual aliases/schema")
    shapes=[(16,4,128),(16,4,128),(16,12,128),(16,12),(16,12),(19,12,128,128),
            (17,),(16,),(16,12,128),(16,12,128,128)]
    types=[torch.bfloat16,torch.bfloat16,torch.bfloat16,torch.float32,torch.bfloat16,
           torch.float32,torch.int32,torch.int32,torch.float32,torch.float32]
    args=[torch.empty(s,dtype=d,device="meta") for s,d in zip(shapes,types)]
    require(ops.prepare(args[0],args[5]) is None,"actual Meta prepare")
    info=ops.tiling_info(args[0],args[5])
    require(info.device.type=="meta" and info.dtype==torch.uint8 and tuple(info.shape)==(72,),"actual Meta tiling")
    y=ops.decode_trace(*args)
    require(y.device.type=="meta" and y.dtype==torch.bfloat16 and tuple(y.shape)==(16,12,128),"actual Meta decode")
    negatives=[]
    def reject(i,t,label):
        modified=list(args);modified[i]=t
        try:ops.decode_trace(*modified)
        except RuntimeError as e:negatives.append({"argument":i,"label":label,"error":str(e)})
        else:raise ValueError("negative admitted "+label)
    for i,(s,d) in enumerate(zip(shapes,types)):
        wrong=torch.float32 if d!=torch.float32 else torch.bfloat16
        reject(i,torch.empty(s,dtype=wrong,device="meta"),"dtype")
        wrongShape=(s[0]+1,)+s[1:]
        reject(i,torch.empty(wrongShape,dtype=d,device="meta"),"shape")
    reject(0,torch.empty((16,128,4),dtype=torch.bfloat16,device="meta").transpose(1,2),"noncontiguous query")
    reject(8,torch.empty((16,128,12),dtype=torch.float32,device="meta").transpose(1,2),"noncontiguous trace")
    maps=[l for l in Path("/proc/self/maps").read_text().splitlines() if str(lib) in l]
    require(maps and not any("(deleted)" in l for l in maps) and sha(lib)==a.library_sha256 and
            not torch_npu.npu.is_initialized(),"actual mapped bytes/no initialized NPU")
    result={"schema":"kvbp.native-recurrent-copy-trace-meta/v2","status":"actual-load-schema-meta-only",
            "library":{"path":str(lib),"sha256":a.library_sha256},"schemas_loaded":schemas,
            "positive_cases":3,"negative_cases":negatives,"mapped_library_lines":maps,
            "torch_version":torch.__version__,"torch_npu_version":torch_npu.__version__,
            "npu_executed":False,"numeric_verified":False,"serving_ready":False}
    with out.open("x") as f:f.write(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"meta_receipt":str(out),"meta_sha256":sha(out),"negative_cases":len(negatives),"npu_executed":False}))
if __name__=="__main__":main()
