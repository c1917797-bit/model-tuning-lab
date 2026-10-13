"""Recover only the exact orphan native r2; never promote missing historical isolation."""
import json,threading,time
from pathlib import Path
import native_tp4_smoke as n
ROOT=Path("/cache/cch/hypic-independent-20261013/native-smoke-r2")
CID="1fe9f605ffc0de544c4b4af8059a8c9329cd86a5ca55259e7eedcd1661d0947d"
def main():
    assert not ROOT.joinpath("result.json").exists()
    meta=n.inspect(CID)
    assert meta["Id"]==CID
    assert meta["Name"]=="/hypic-independent-native-smoke-r2-20261013"
    assert meta["Config"]["Labels"].get("model-tuning-lab.task")==n.TASK
    assert meta["Image"]=="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
    out=ROOT/"recovery-1";out.mkdir(exist_ok=False)
    samples=[];responses=[];errors=[];stop=threading.Event()
    def guard():
        while not stop.is_set():
            try:
                x=n.snapshot(CID);samples.append(x)
                if x["foreign"]:raise RuntimeError("foreign process")
            except Exception as e:errors.append(str(e));return
            stop.wait(3)
    thread=threading.Thread(target=guard,daemon=True);thread.start()
    release={};error=None
    try:
        assert n.request(8233)==200
        for i in range(3):
            x=n.snapshot(CID);samples.append(x)
            assert not x["foreign"] and not errors
            payload={"model":"qwen3.5","messages":[{"role":"user","content":"Calculate 2 + 2. Reply with only the integer."}],"temperature":0,"seed":0,"max_tokens":32,"chat_template_kwargs":{"enable_thinking":False}}
            response=n.request(8233,payload)
            responses.append({"index":i,"payload":payload,"response":response})
            assert not errors
        texts=[r["response"]["choices"][0]["message"]["content"].strip() for r in responses]
        assert all(t.rstrip(".")=="4" for t in texts) and len(set(texts))==1
    except Exception as e:error=str(e)
    finally:
        stop.set();thread.join(20)
        n.write(out,"responses.json",responses);n.write(out,"isolation.json",samples)
        (out/"service.log").write_text(n.command(["docker","logs",CID],20))
        check=n.inspect(CID)
        assert check["Id"]==CID and check["Config"]["Labels"].get("model-tuning-lab.task")==n.TASK
        n.command(["docker","stop","-t","10",CID],30)
        n.command(["docker","rm",CID],30)
        n.port_free(8233)
        release={"exact_container_removed":CID,"port_free":True,"final":n.snapshot()}
        n.write(out,"release.json",release)
        result={"historical_r2_valid":False,"historical_gap":"controller lost; continuous isolation missing before recovery","recovery_responses":len(responses),"recovery_error":error,"guard_errors":errors,"recovery_semantic_pass":error is None and not errors,"released":True}
        n.write(out,"result.json",result);print(json.dumps(result),flush=True)
if __name__=="__main__":main()

