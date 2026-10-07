#!/usr/bin/env python3
"""Real dlopen/schema/Meta only. Does not initialize or execute an NPU."""
import argparse,hashlib,json,os,sys
from pathlib import Path
def require(v,s):
    if not v:raise ValueError(s)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--library");p.add_argument("--library-sha256");p.add_argument("--output");a=p.parse_args()
    if not a.library:
        print(json.dumps({"default_enabled":False,"npu_executed":False}));return
    require(a.library_sha256 and a.output,"actual source-bound explicit inputs")
    require(os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD")=="0" and not list(Path("/dev").glob("davinci[0-9]*")),"no-device prerequisite")
    lib=Path(a.library);out=Path(a.output)
    require(lib.is_file() and not lib.is_symlink() and sha(lib)==a.library_sha256 and not out.exists(),"exact library/new receipt")
    import torch,torch_npu
    sys.path.insert(0,str(Path(__file__).resolve().parent));import protocol
    protocol.source_admission("e970dca058a7e7d01e964c85b9580a5dde00b5929e5ae16ea064f34b07557cdf")
    torch.ops.load_library(str(lib))
    ops=getattr(torch.ops,protocol.NAMESPACE)
    schema=str(ops.decode_trace.default._schema);require(schema==protocol.SCHEMA,"actual trace schema")
    tensors=[
       torch.empty((16,4,128),dtype=torch.bfloat16,device="meta"),
       torch.empty((16,4,128),dtype=torch.bfloat16,device="meta"),
       torch.empty((16,12,128),dtype=torch.bfloat16,device="meta"),
       torch.empty((16,12),dtype=torch.float32,device="meta"),
       torch.empty((16,12),dtype=torch.bfloat16,device="meta"),
       torch.empty((19,12,128,128),dtype=torch.float32,device="meta"),
       torch.empty((19,4,16,128),dtype=torch.bfloat16,device="meta"),
       torch.empty((19,12,16,128),dtype=torch.float32,device="meta"),
       torch.empty((19,12,32),dtype=torch.float32,device="meta"),
       torch.empty((19,12,32),dtype=torch.float32,device="meta"),
       torch.empty((19,12,32),dtype=torch.int32,device="meta"),
       torch.empty((17,),dtype=torch.int32,device="meta"),
       torch.empty((16,),dtype=torch.int32,device="meta"),
       torch.empty((3,32,128),dtype=torch.float32,device="meta"),
       torch.empty((32,),dtype=torch.float32,device="meta"),
       torch.empty((16,),dtype=torch.int32,device="meta")]
    require(ops.prepare(tensors[0],tensors[5]) is None,"prepare Meta")
    y=ops.decode_trace(*tensors)
    require(tuple(y.shape)==(16,12,128) and y.dtype==torch.bfloat16 and y.device.type=="meta","positive output")
    negatives=[]
    for i,shape,dtype in [(0,(1,4,128),torch.bfloat16),(0,(16,4,128),torch.float32),(1,(16,4,127),torch.bfloat16),
                         (5,(4,12,128,128),torch.float32),(6,(19,4,15,128),torch.bfloat16),
                         (8,(19,12,16),torch.float32),(10,(19,12,32),torch.int64),(11,(16,),torch.int32),
                         (12,(17,),torch.int32),(13,(2,32,128),torch.float32),(14,(32,),torch.bfloat16),(15,(17,),torch.int32)]:
        args=list(tensors);args[i]=torch.empty(shape,dtype=dtype,device="meta")
        try:ops.decode_trace(*args)
        except RuntimeError as e:negatives.append({"argument":i,"shape":shape,"dtype":str(dtype),"error":str(e)})
        else:raise ValueError("negative Meta incorrectly admitted")
    mapping=[l for l in Path("/proc/self/maps").read_text().splitlines() if str(lib) in l]
    require(mapping and not any("(deleted)" in l for l in mapping) and sha(lib)==a.library_sha256,"actual mapped bytes")
    result={"schema":"kvbp.candidate-ub-trace-meta/v1","status":"actual-load-schema-meta-only",
      "library":{"path":str(lib),"sha256":a.library_sha256},"schema_loaded":schema,"positive_cases":2,
      "negative_cases":negatives,"mapped_library_lines":mapping,"torch_version":torch.__version__,
      "torch_npu_version":torch_npu.__version__,"source_manifest_sha256":protocol.sha(protocol.HERE/"SOURCE_MANIFEST.json"),
      "npu_executed":False,"numeric_verified":False,"serving_ready":False}
    with out.open("x") as f:f.write(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"meta_receipt":str(out),"meta_sha256":sha(out),"negative_cases":len(negatives),"npu_executed":False}))
if __name__=="__main__":main()
