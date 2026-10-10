"""Explicit all64/Q2Q4 real writer outputs -> compiled reader. No model launch."""
import argparse,hashlib,json,os,sys,time,traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import contract as C
import layout as L
def identity():
    root=Path("/proc/self");s=(root/"stat").read_text();raw=(root/"cmdline").read_bytes()
    return dict(pid=os.getpid(),start_ticks=int(s[s.rfind(")")+2:].split()[19]),cgroup=(root/"cgroup").read_text(),
      argv=[x.decode()for x in raw.split(b"\0")if x],cmdline_sha256=hashlib.sha256(raw).hexdigest())
def blob(x,torch):return x.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes()
def from_raw(raw,shape,dtype,torch):
    return torch.frombuffer(bytearray(raw),dtype=dtype).clone().reshape(shape).to("npu:0")
def controlled_pool(item,torch):
    dtype={"torch.float16":torch.float16,"torch.bfloat16":torch.bfloat16}[item["axes"]["K"]["original_dtype"]]
    pool={};before={}
    for axis in("K","V"):
        original=item["axes"][axis];obs=C.obj(item["writer_axes"][axis]);maps,width=L.addresses(original["layout"],item["bits"])
        after=obs["after"];dense=C.read(original["input_ref"]);edge=dense[:5*512]+dense[(4096-128)*512:]
        p=dict(payload=from_raw(C.read(after["payload"]),(1,4096,width),torch.uint8,torch),
          scales=from_raw(C.read(after["scales"]),(1,4096,4),dtype,torch),
          zero_points=from_raw(C.read(after["zero_points"]),(1,4096,4),dtype,torch),
          edges=from_raw(edge,(1,133,256),dtype,torch),
          map=torch.tensor(maps,dtype=torch.int32,device="npu:0"))
        pool[axis]=p;before[axis]={n:hashlib.sha256(blob(t,torch)).hexdigest()for n,t in p.items()}
    return pool,before,dtype
def run(expected,whole_ref,proof_ref,output):
    source=C.source(expected,device=True);whole=C.writer_whole(whole_ref);items=C.input_rows(whole)
    proof=C.proof(C.obj(proof_ref),source,whole_ref)
    C.need(os.environ.get("MAIN_SKVQ_COMPILED_READER_EXECUTE")=="1"and
      os.environ.get("MAIN_OWNED_CID")==proof["cid"]and os.environ.get("ASCEND_RT_VISIBLE_DEVICES")=="0",
      "MAIN admitted singleton logical0 only")
    out=Path(output);C.need(out.is_absolute()and out.parent.is_dir()and not out.exists(),"absent child of owned RW tree");out.mkdir()
    cache=out/"jit-cache";cache.mkdir()
    os.environ["TRITON_CACHE_DIR"]=str(cache);os.environ["TRITON_HOME"]=str(cache)
    who=identity();C.atomic(out/"RAW_BEFORE_IMPORT.json",dict(source_ref=source,writer_whole_ref=whole_ref,
      proof_ref=proof_ref,identity=who,**C.scopes()))
    result=dict(schema="skvq.compiled-reader.producer/v1",status="FAILED",source_ref=source,writer_whole_ref=whole_ref,
      proof_ref=proof_ref,identity=who,cases=[],primary=None,npu_executed=False,**C.scopes())
    started=time.monotonic()
    try:
        import torch,torch_npu,triton,triton.language as tl
        torch.set_num_threads(1);torch.set_num_interop_threads(1);torch.npu.set_device(0)
        import kernel
        W,_=C.writer_modules();F=C.load("_skvq_reader_format",W.HOST_BINDINGS["n1_format.py"])
        getter,enum,qualification=F.qualify(torch,torch_npu,W.ref(W.ROOT/"SOURCE_MANIFEST.json"))
        policy=F.policy()
        def nd(t):policy.serial(getter(t),enum)
        def qualify():C.need(C.ref(HERE/"kernel.py")==next(x for x in C.obj(source)["files"]if x["path"].endswith("/kernel.py")),"actual compiled reader source")
        props=torch.npu.get_device_properties(0)
        core=dict(num_aicore=props.num_aicore,num_vectorcore=props.num_vectorcore)
        cls=kernel.build(torch,triton,tl,device_properties=core,validate_nd=nd,qualify=qualify);reader=cls()
        for item in items:
            directory=out/("r%d-l%s-q%d"%(item["rank"],item["logical_layer"].split(".")[2],item["bits"]));directory.mkdir()
            pool,before,dtype=controlled_pool(item,torch)
            a,b=item["query_byte_slice"];query_raw=C.read(item["query_full_ref"])[a:b]
            q=from_raw(query_raw,(1,6,256),dtype,torch);controls=torch.tensor([[4096,5,3968,0]],dtype=torch.int32,device="npu:0")
            before_query=blob(q,torch);before_controls=blob(controls,torch)
            C.atomic(directory/"RAW_BEFORE_KERNEL.json",dict(input=item,identity=who,pool_hashes=before,
              query_sha256=hashlib.sha256(before_query).hexdigest(),controls_sha256=hashlib.sha256(before_controls).hexdigest(),
              actual_format_qualification=qualification,actual_core_properties=core))
            def live():
                C.need(identity()==who and C.ref(item["event_ref"]["path"])==item["event_ref"],"same actual process/input/live binding")
            output_tensor,scores,prob=reader(q,pool,controls,bits=item["bits"],capacity=4096,assert_live=live)
            torch.npu.synchronize()
            actual={name:C.atomic(directory/(name+".bin"),blob(t,torch),binary=True)for name,t in
              (("output",output_tensor),("scores",scores),("probabilities",prob))}
            after={axis:{n:hashlib.sha256(blob(t,torch)).hexdigest()for n,t in p.items()}for axis,p in pool.items()}
            case=dict(rank=item["rank"],logical_layer=item["logical_layer"],bits=item["bits"],input=item,actual=actual,
              pool_before_sha256=before,pool_after_sha256=after,query_unchanged=blob(q,torch)==before_query,
              controls_unchanged=blob(controls,torch)==before_controls,identity=identity(),actual_calls=3)
            case_ref=C.atomic(directory/"CASE.json",case);result["cases"].append(case_ref)
            C.need(before==after and case["query_unchanged"]is True and case["controls_unchanged"]is True,
              "complete original payload/SS/low/edge/map/query/control immutable")
            del pool,q,controls,output_tensor,scores,prob
        C.need(len(result["cases"])==128,"all64/Q2Q4 actual compiled reader output")
        cache_reader=C.load("_skvq_reader_actual_budget",C.BUDGET);cache_raw=cache_reader.scan(cache)
        C.need(cache_reader.consume(cache_raw,cache)<=512*2**20,"actual compilecache snapshot512MiB included in output1GiB")
        result.update(status="ALL64_Q2Q4_COMPILED_READER_RAW_PENDING_INDEPENDENT",npu_executed=True,actual_cases=128,
          actual_kernel_calls=384,actual_context=4096,physical_card=4,logical_device=0,owned_cid=proof["cid"])
        result["jit_cache_snapshot"]=cache_raw;result["jit_cache_cap_bytes"]=512*2**20
    except BaseException as e:result["primary"]=dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc())
    result["elapsed_seconds"]=time.monotonic()-started;result["identity_at_terminal"]=identity()
    row=C.atomic(out/"RESULT.json",result);C.need(result["primary"]is None,"compiled reader failed; keep raw/first fault");return row
def main():
    p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true");p.add_argument("--source-manifest-sha256")
    p.add_argument("--writer-whole-ref-json");p.add_argument("--device-proof-ref-json");p.add_argument("--output");a=p.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,**C.scopes())));return
    C.need(a.writer_whole_ref_json and a.device_proof_ref_json and a.output,"whole/proof/new output required")
    print(json.dumps(run(a.source_manifest_sha256,json.loads(Path(a.writer_whole_ref_json).read_bytes()),
      json.loads(Path(a.device_proof_ref_json).read_bytes()),a.output),sort_keys=True))
if __name__=="__main__":main()
