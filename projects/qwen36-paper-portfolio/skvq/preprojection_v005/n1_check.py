"""MAIN-owned all4 tiny native canary plus actual EngineArgs configuration; no weights."""
import argparse,hashlib,inspect,json,multiprocessing as mp,os,sys,time,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import current_contract as C
from model_kwargs import kwargs
BASE=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-calibration-capture-chain-v1-001")
sys.path.insert(0,str(BASE))
from io_contract import publish_json,reference
ARG_SHA="3ade2488897d08b5c1fd4ddb815eb5743169907d59741a47867185caab7f250d"
def identity():
    p=Path("/proc/self");raw=(p/"stat").read_text();start=int(raw[raw.rfind(")")+2:].split()[19])
    cmd=(p/"cmdline").read_bytes()
    return {"pid":os.getpid(),"start_ticks":start,"cgroup":(p/"cgroup").read_text(),
        "cmdline_sha256":hashlib.sha256(cmd).hexdigest(),"argv":[x.decode()for x in cmd.split(b"\0")if x]}
def tiny(rank,source,destination):
    C.configure(source);dest=Path(destination)/("N1-rank-%d.json"%rank)
    before=identity()
    publish_json(dest.with_name("N1-rank-%d-RAW_PRE.json"%rank),{"source_ref":C.source(),"rank":rank,"identity":before})
    try:
        import torch,torch_npu
        torch.set_num_threads(1);torch.set_num_interop_threads(1);torch.npu.set_device(rank)
        x=torch.tensor([1.,2.],device="npu:%d"%rank);y=x+3.;torch.npu.synchronize()
        actual=y.cpu().tolist();fmt=torch_npu.get_npu_format(y)
        C.require(actual==[4.,5.]and type(fmt)is int and fmt==2,"actual tiny tensor/sync/getter ND2")
        publish_json(dest,{"status":"ACTUAL_TINY_CHECKED","rank":rank,"source_ref":C.source(),"identity":before,
            "after_identity":identity(),"input":[1.,2.],"output":actual,"format":fmt,
            "torch_origin":reference(torch.__file__),"torch_npu_origin":reference(torch_npu.__file__)})
        time.sleep(30)
    except BaseException as e:
        publish_json(dest,{"status":"FAILED","rank":rank,"source_ref":C.source(),
            "primary":repr(e),"traceback":traceback.format_exc(),"identity":before});raise
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
    p.add_argument("--source-manifest-sha256");p.add_argument("--output",type=Path);p.add_argument("--cpu-config-ref-json",type=Path);a=p.parse_args()
    if not a.execute:print(json.dumps({"default_enabled":False,"model_launched":False}));return
    source=C.configure(a.source_manifest_sha256);C.fit(180)
    C.require(a.output.is_absolute()and a.output.parent.is_dir()and not a.output.exists(),"exact new owned N1 output")
    C.require(os.environ.get("MAIN_OWNED_CID")and os.environ.get("ASCEND_RT_VISIBLE_DEVICES")=="0,1,2,3",
        "actual owned CID and singleton logical maps")
    cpu_ref=json.loads(a.cpu_config_ref_json.read_bytes());C.checked(cpu_ref)
    prior=json.loads(Path(cpu_ref["path"]).read_bytes())
    C.require(prior["status"]=="ACTUAL_DECLARED_SCHEDULER_CONFIG_CHECKED"and prior["source_ref"]==source and
        prior["full_engine_config_verified"]is False and prior["model_config_constructed"]is False and prior["NPU_initialized"]is False,
        "honest actual partial Devices[] config before ANY NPU")
    ctx=mp.get_context("spawn");children=[ctx.Process(target=tiny,args=(r,a.source_manifest_sha256,str(a.output.parent)))for r in range(4)]
    for child in children:child.start()
    limit=time.monotonic()+120
    try:
        for child in children:child.join(max(0,limit-time.monotonic()))
        C.require(all(not child.is_alive()and child.exitcode==0 for child in children),"actual all4 tiny completed")
        rows=[reference(a.output.parent/("N1-rank-%d.json"%r))for r in range(4)]
        for rank,row in enumerate(rows):
            x=json.loads(Path(row["path"]).read_bytes())
            C.require(x["status"]=="ACTUAL_TINY_CHECKED"and x["rank"]==rank and x["source_ref"]==source,"all4 original N1 results")
        # Full original platform config is allowed only after actual all4 tiny, still before weights.
        from engine_config import construct,match_partial
        effective=construct(full=True);match_partial(prior,effective,source)
        raw=publish_json(a.output.parent/"N1-ACTUAL-CONFIG.json",effective)
        publish_json(a.output,{"status":"SKVQ_ALL4_TINY_N1_CHECKED","source_ref":source,"ranks":rows,
            "actual_configuration_ref":raw,"effective_capture_configuration_checked":True,
            "model_ready":False,"native_ready":False})
    finally:
        for child in children:
            if child.is_alive():child.terminate()
        for child in children:child.join(5)
if __name__=="__main__":main()
