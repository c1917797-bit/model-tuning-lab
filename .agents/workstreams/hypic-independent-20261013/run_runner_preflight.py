"""Guarded bounded numeric probe controller; exact owned container only."""
import json,time,subprocess,hashlib
from pathlib import Path
import native_tp4_smoke as n
HERE=Path(__file__).resolve().parent
ROOT=Path("/cache/cch/hypic-independent-20261013/runner-preflight-r1")
NAME="hypic-independent-runner-preflight-r1"
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
def main():
    assert not ROOT.exists(),"immutable root exists"
    first=n.snapshot();assert not first["foreign"],"physical0–3 busy"
    n.port_free(26491)
    ROOT.mkdir();journal=n.DurableJournal(ROOT/"events.jsonl")
    cid=None;result={"valid":False};samples=[];error=None
    try:
        journal.append({"event":"preflight","snapshot":first})
        args=["docker","create","--name",NAME,"--network","host","--label","model-tuning-lab.task="+n.TASK,"--entrypoint","python3"]
        for d in ["/dev/davinci0","/dev/davinci_manager","/dev/hisi_hdc","/dev/devmm_svm"]:
            if Path(d).exists():args+=["--device",d]
        for src,dst in [(str(HERE),"/probe"),("/cache/efim/Qwen3.6-27B","/model"),("/usr/local/Ascend/driver","/usr/local/Ascend/driver"),("/usr/local/Ascend/firmware","/usr/local/Ascend/firmware"),("/usr/local/dcmi","/usr/local/dcmi"),("/etc/ascend_install.info","/etc/ascend_install.info")]:
            if Path(src).exists():args+=["-v",src+":"+dst+":ro"]
        args+=["-e","ASCEND_RT_VISIBLE_DEVICES=0","-e","PYTHONDONTWRITEBYTECODE=1",IMAGE,"-B","/probe/independent_runner_npu_preflight.py"]
        journal.append({"event":"launch","argv":args,"sources":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.glob("independent*.py")}})
        cid=n.command(args).strip();n.command(["docker","start",cid])
        deadline=time.monotonic()+240
        while True:
            snap=n.snapshot(cid);samples.append(snap);journal.append({"event":"isolation","snapshot":snap})
            if snap["foreign"]:raise RuntimeError("foreign physical process")
            state=n.inspect(cid)["State"]
            if not state["Running"]:
                result={"valid":state["ExitCode"]==0,"exit_code":state["ExitCode"],"npu_observed":any(x["processes"] for x in samples)}
                break
            if time.monotonic()>deadline:raise TimeoutError("bounded240s")
            time.sleep(2)
    except Exception as e:error={"type":type(e).__name__,"message":str(e)}
    finally:
        result["error"]=error
        if cid:
            meta=n.inspect(cid);assert meta["Config"]["Labels"].get("model-tuning-lab.task")==n.TASK
            (ROOT/"stdout.log").write_text(n.command(["docker","logs",cid],20))
            if meta["State"]["Running"]:n.command(["docker","stop","-t","5",cid],20)
            n.command(["docker","rm",cid],20)
            result["exact_removed_container"]=cid
        result["final_snapshot"]=n.snapshot();result["samples"]=len(samples)
        n.write(ROOT,"result.json",result);journal.append({"event":"terminal","result":result});journal.close()
        print(json.dumps(result),flush=True)
    if not result["valid"]:raise SystemExit(1)
if __name__=="__main__":main()
