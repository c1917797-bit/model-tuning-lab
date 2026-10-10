"""Only MAIN-owned physical4/logical0 tiny; records raw BEFORE exact enum gate."""
import argparse,json,os,sys,time,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import contract as C
from numeric import identity
def run(expected,whole_ref,prior_ref,output):
    source=C.source(expected,device=True);prior=C.obj(prior_ref)
    C.need(prior["source_ref"]==source and prior["writer_whole_ref"]==whole_ref and
      prior["status"]=="ACTUAL_WRITER128_AND_NUMPY12_CHECKED"and
      os.environ.get("MAIN_OWNED_CID")and os.environ.get("ASCEND_RT_VISIBLE_DEVICES")=="0",
      "real CPU prerequisite and single mapped current owned NPU")
    path=Path(output);C.need(not path.exists()and path.parent.is_dir(),"new owned canary sink")
    before=identity();result=dict(schema="skvq.compiled-reader.canary/v1",status="FAILED",source_ref=source,
      writer_whole_ref=whole_ref,cpu_ref=prior_ref,owned_cid=os.environ["MAIN_OWNED_CID"],
      physical_card=4,logical_device=0,identity=before,primary=None,**C.scopes())
    try:
        import torch,torch_npu
        F=C.load("_skvq_writer_actual_format",C.host_bindings()["n1_format.py"])
        getter,enum,qualification=F.qualify(torch,torch_npu,source)
        torch.set_num_threads(1);torch.set_num_interop_threads(1);torch.npu.set_device(0)
        x=torch.tensor([1.,2.],device="npu:0");y=x+3.;torch.npu.synchronize()
        actual=y.cpu().tolist();fmt=getter(y);after=identity()
        serial,raw=F.observe_then_check(actual,fmt,enum,rank=0,source=source,identity=before,
          after_identity=after,qualification=qualification,destination=path.with_name("CANARY_RAW.json"),publish=C.atomic)
        result.update(status="ACTUAL_SINGLE4_TINY_CHECKED",input=[1.,2.],output=actual,format=serial["normalized_nd"],
          actual_format=serial,original_observation_ref=raw,after_identity=after)
    except BaseException as e:result["primary"]=dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc())
    row=C.atomic(path,result)
    C.need(result["primary"]is None,"real original canary failure retained, no retry")
    time.sleep(30) # permits real host PID/start/mapping observation; charged to1800
    return row
def main():
    p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true");p.add_argument("--source-manifest-sha256")
    p.add_argument("--writer-whole-ref-json");p.add_argument("--cpu-ref-json");p.add_argument("--output");a=p.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,**C.scopes())));return
    C.need(a.writer_whole_ref_json and a.cpu_ref_json and a.output,"actual descriptor paths/new sink")
    print(json.dumps(run(a.source_manifest_sha256,json.loads(Path(a.writer_whole_ref_json).read_bytes()),
      json.loads(Path(a.cpu_ref_json).read_bytes()),a.output),sort_keys=True))
if __name__=="__main__":main()
