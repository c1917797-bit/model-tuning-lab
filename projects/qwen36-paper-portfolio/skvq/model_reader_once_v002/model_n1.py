"""All4 actual tiny+full engine in source660 before ANY weights; raw before enum gates."""
import argparse,json,multiprocessing as mp,os,time,traceback
from pathlib import Path
import bridge_contract as B
def tiny(rank,sha,root):
    C,source,m=B.source(sha);dest=Path(root)/("N1-rank-%d.json"%rank)
    from numeric import identity
    before=identity();C.atomic(dest.with_name("N1-rank-%d-RAW_PRE.json"%rank),dict(source_ref=source,rank=rank,identity=before))
    try:
        import torch,torch_npu
        F=C.load("_skvq_model_actual_n1_format",C.host_bindings()["n1_format.py"])
        getter,enum,qualification=F.qualify(torch,torch_npu,source)
        torch.set_num_threads(1);torch.set_num_interop_threads(1);torch.npu.set_device(rank)
        x=torch.tensor([1.,2.],device="npu:%d"%rank);y=x+3.;torch.npu.synchronize()
        actual=y.cpu().tolist();fmt=getter(y);after=identity()
        serial,raw=F.observe_then_check(actual,fmt,enum,rank=rank,source=source,identity=before,after_identity=after,
          qualification=qualification,destination=dest.with_name("N1-rank-%d-RAW_OBSERVATION.json"%rank),publish=C.atomic)
        C.atomic(dest,dict(status="ACTUAL_TINY_CHECKED",rank=rank,source_ref=source,identity=before,after_identity=after,
          input=[1.,2.],output=actual,format=serial["normalized_nd"],actual_format=serial,original_observation_ref=raw,
          torch_origin=C.ref(torch.__file__),torch_npu_origin=C.ref(torch_npu.__file__)))
        time.sleep(30)
    except BaseException as e:
        C.atomic(dest,dict(status="FAILED",rank=rank,source_ref=source,identity=before,primary=repr(e),
          traceback=traceback.format_exc()));raise
def run(sha,cpu_ref,output):
    C,source,m=B.source(sha);cpu=C.obj(cpu_ref);dest=Path(output)
    B.need(cpu["schema"]=="skvq.model-reader.cpu/v1"and cpu["source_ref"]==source and
      cpu["status"]=="ACTUAL_READER_PROMPT_PARSER_RPC_CHECKED"and cpu["configuration"]["NPU_initialized"]is False,
      "actual same source necessary CPU prerequisite")
    B.need(os.environ.get("MAIN_OWNED_CID")and os.environ.get("ASCEND_RT_VISIBLE_DEVICES")=="0,1,2,3"and
      dest.parent.is_dir()and not dest.exists(),"MAIN owned exact four maps/new N1 sink")
    children=[mp.get_context("spawn").Process(target=tiny,args=(r,sha,str(dest.parent)))for r in range(4)]
    try:
        for child in children:child.start()
        limit=time.monotonic()+120
        for child in children:child.join(max(0,limit-time.monotonic()))
        B.need(all(not child.is_alive()and child.exitcode==0 for child in children),"actual all4 tiny completed")
        rows=[C.ref(dest.parent/("N1-rank-%d.json"%r))for r in range(4)]
        F=C.load("_skvq_model_actual_n1_format",C.host_bindings()["n1_format.py"])
        for row in rows:F.consume_row(C.obj(row),source)
        from actual_config import construct,match
        config=construct(source,full=True);match(cpu["configuration"],config)
        # The actual same-image patch representation is qualified before weights, live groups only in actual workers.
        from model_factory import capture_registry
        original=capture_registry()
        tp=__import__("tp_provider_current")
        native=tp.preweights(source,dest.parent/"N1-NATIVE-TP-RAW.json",C.atomic)
        return C.atomic(dest,dict(schema="skvq.model-reader.N1/v1",source_ref=source,cpu_ref=cpu_ref,
          rank_refs=rows,full_engine_configuration_checked=True,actual_configuration=config,
          original_native_TP_qualification=native,weights_loaded=False,**B.false_scopes()))
    finally:
        for child in children:
            if child.is_alive():child.terminate()
        for child in children:child.join(5)
def main():
    p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true");p.add_argument("--source-manifest-sha256")
    p.add_argument("--cpu-ref-json");p.add_argument("--output");a=p.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,**B.false_scopes())));return
    print(json.dumps(run(a.source_manifest_sha256,json.loads(Path(a.cpu_ref_json).read_bytes()),a.output),sort_keys=True))
if __name__=="__main__":main()
