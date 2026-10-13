"""Native-only TP4 smoke controller. No HYPIC package is installed or mounted."""
import argparse
import hashlib
import json
import os
import re
import socket
import subprocess
import time
import threading
import urllib.error
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
CONTRACT = HERE / "NATIVE_SMOKE_CONTRACT.json"
TASK = "hypic-independent-20261013"

class DurableJournal:
    """Exclusive append-only evidence, synced before returning to device work."""
    def __init__(self,path):
        self.file=Path(path).open("x",encoding="utf-8")
        self.lock=threading.Lock()
    def append(self,event):
        with self.lock:
            self.file.write(json.dumps(event,ensure_ascii=False)+"\n")
            self.file.flush()
            os.fsync(self.file.fileno())
    def close(self):
        with self.lock:self.file.close()

def command(args, timeout=30):
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT, timeout=timeout)

class ProcessTableError(ValueError):
    def __init__(self,message,raw):
        super().__init__(message)
        self.raw=raw

def processes(text):
    marker = "Process id"
    if marker not in text:
        raise ProcessTableError("NPU process table unavailable",text)
    tail = text.split(marker, 1)[1]
    rows = []
    seen = set()
    for line in tail.splitlines():
        if "No running processes found in NPU" in line:
            m = re.search(r"NPU\s+(\d+)", line)
            if m: seen.add(int(m.group(1)))
        columns = [c.strip() for c in line.split("|")]
        combined = columns[1].split() if len(columns)>=5 else []
        if len(combined)==2 and all(x.isdigit() for x in combined) and columns[2].isdigit():
            npu,pid=int(combined[0]),int(columns[2])
            rows.append((npu,pid));seen.add(npu)
            continue
        if len(columns) >= 6 and columns[1].isdigit() and columns[2].isdigit() and columns[3].isdigit():
            npu, pid = int(columns[1]), int(columns[3])
            rows.append((npu,pid)); seen.add(npu)
    if not set(range(4)) <= seen:
        raise ProcessTableError("Incomplete physical0-3 process table",text)
    return rows

def inspect(cid):
    return json.loads(command(["docker","inspect",cid]))[0]

def snapshot(cid=None):
    text = command(["npu-smi","info"],timeout=15)
    rows = processes(text)
    target = [(n,p) for n,p in rows if n in range(4)]
    foreign = [];owners=[]
    for n,pid in target:
        try:
            cgroup = Path("/proc",str(pid),"cgroup").read_text()
        except OSError:
            cgroup = "owner_unverified"
        if not cid or cid not in cgroup:
            foreign.append({"npu":n,"pid":pid,"cgroup":cgroup})
        owners.append({"npu":n,"pid":pid,"cgroup":cgroup,"owned":bool(cid and cid in cgroup)})
    return {"utc":datetime.now(timezone.utc).isoformat(),"processes":target,"owners":owners,"foreign":foreign,"raw":text}

def port_free(port):
    with socket.socket() as s:
        s.bind(("0.0.0.0",port))

def write(root,name,data):
    path=root/name
    with path.open("x",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)
        f.flush()

def request(port,payload=None):
    path="/health" if payload is None else "/v1/chat/completions"
    data=None if payload is None else json.dumps(payload).encode()
    req=urllib.request.Request("http://127.0.0.1:"+str(port)+path,data=data,headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=60 if data else 3) as response:
        raw=response.read()
        return json.loads(raw) if data else response.status

def run_contract(contract):
    image=contract["image"];model=Path(contract["model"]);port=contract["port"]
    raw=Path(contract["raw_root"])
    if raw.exists():raise RuntimeError("Immutable attempt root already exists")
    assert hashlib.sha256((model/"config.json").read_bytes()).hexdigest()==contract["model_config_sha256"]
    image_info=json.loads(command(["docker","image","inspect",image]))[0]
    inherited_pythonpath=next((x.split("=",1)[1] for x in image_info["Config"].get("Env",[]) if x.startswith("PYTHONPATH=")),"")
    diagnostic=contract.get("cache_diagnostic")
    if diagnostic:
        for name,expected in diagnostic["source_sha256"].items():
            path=HERE/name
            if path.resolve().is_relative_to(HERE.resolve()) is False:
                raise ValueError("diagnostic source outside workstream")
            if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
                raise ValueError("diagnostic source drift: "+name)
    first=snapshot()
    if first["foreign"]:raise RuntimeError("Physical0-3 occupied before admission")
    port_free(port)
    for p in range(contract["hccl_ports"][0],contract["hccl_ports"][1]+1):port_free(p)
    raw.mkdir(parents=True,exist_ok=False)
    (raw/"tmp").mkdir()
    if diagnostic:(raw/"diagnostics").mkdir()
    write(raw,"preflight.json",first)
    journal=DurableJournal(raw/"events.jsonl")
    journal.append({"event":"preflight","snapshot":first})
    cid=None;responses=[];samples=[];valid=False;error=None;worker_pids=set()
    physical_devices_seen=set();guard_stop=threading.Event();guard_error=[];guard_thread=None
    def retain_snapshot(snap):
        journal.append({"event":"isolation","snapshot":snap})
        samples.append(snap)
    def guard_loop():
        while not guard_stop.is_set():
            try:
                snap=snapshot(cid);retain_snapshot(snap)
                if snap["foreign"]:raise RuntimeError("Foreign physical process detected")
                worker_pids.update(pid for device,pid in snap["processes"])
                physical_devices_seen.update(device for device,pid in snap["processes"])
            except Exception as exc:
                guard_error.append({"type":type(exc).__name__,"message":str(exc),"raw":getattr(exc,"raw",None)})
                return
            guard_stop.wait(3)
    def require_guard():
        if guard_error:raise RuntimeError("Isolation guard failed: "+str(guard_error))
    try:
        args=["docker","run","-d","--name",contract["container_name"],"--network","host",
              "--shm-size","16g","--cpuset-cpus",contract["cpu_set"],
              "--label","model-tuning-lab.task="+TASK,"--label","model-tuning-lab.phase=native-smoke",
              "--entrypoint","vllm"]
        for d in ["/dev/davinci"+str(i) for i in range(4)]+["/dev/davinci_manager","/dev/hisi_hdc","/dev/devmm_svm"]:
            if Path(d).exists():args+=["--device",d]
        for src,dst in [(str(model),"/model"),(str(raw),"/scratch"),
                        ("/usr/local/Ascend/driver","/usr/local/Ascend/driver"),
                        ("/usr/local/Ascend/firmware","/usr/local/Ascend/firmware"),
                        ("/usr/local/dcmi","/usr/local/dcmi"),
                        ("/etc/ascend_install.info","/etc/ascend_install.info")]:
            if Path(src).exists():args+=["-v",src+":"+dst+(":rw" if dst=="/scratch" else ":ro")]
        env={"ASCEND_RT_VISIBLE_DEVICES":"0,1,2,3","HCCL_OP_EXPANSION_MODE":"AIV",
             "PYTORCH_NPU_ALLOC_CONF":"expandable_segments:True","TASK_QUEUE_ENABLE":"1",
             "VLLM_ASCEND_ENABLE_FLASHCOMM":"1","HCCL_NPU_SOCKET_PORT_RANGE":
             str(contract["hccl_ports"][0])+"-"+str(contract["hccl_ports"][1]),
             "TMPDIR":"/scratch/tmp","PYTHONDONTWRITEBYTECODE":"1"}
        for k,v in env.items():args+=["-e",k+"="+v]
        if diagnostic:
            args+=["-v",str(HERE)+":/probe:ro",
                   "-e","PYTHONPATH=/probe/diagnostic_bootstrap:/probe:"+inherited_pythonpath,
                   "-e","INDEPENDENT_CACHE_DIAGNOSTIC=1",
                   "-e","INDEPENDENT_DIAGNOSTIC_ROOT=/scratch/diagnostics",
                   "-e","INDEPENDENT_DIAGNOSTIC_BATCHES=2"]
        args += [image,"serve","/model","--served-model-name","qwen3.5","--host","0.0.0.0",
                 "--port",str(port),"--tensor-parallel-size","4","--data-parallel-size","1",
                 "--max-model-len","40960","--max-num-batched-tokens","40960",
                 "--max-num-seqs","32","--gpu-memory-utilization","0.85",
                 "--no-enable-prefix-caching","--additional-config",'{"enable_cpu_binding":false}',
                 "--compilation-config",'{"cudagraph_mode":"FULL_DECODE_ONLY","cudagraph_capture_sizes":[1,4,8,16,24,32]}',
                 "--trust-remote-code","--async-scheduling"]
        write(raw,"launch.json",{"argv":args,"controller_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                 "diagnostic_sources":diagnostic,
                                 "git_commit":command(["git","rev-parse","HEAD"]).strip()})
        cid=command(args,timeout=30).strip()
        guard_thread=threading.Thread(target=guard_loop,daemon=True)
        guard_thread.start()
        meta=inspect(cid)
        declared={d["PathOnHost"] for d in meta["HostConfig"]["Devices"] if re.fullmatch(r"/dev/davinci\d+",d["PathOnHost"])}
        assert declared=={"/dev/davinci"+str(i) for i in range(4)}
        assert meta["Image"]==image
        write(raw,"service-start.json",{"container_id":cid,"image":meta["Image"],"devices":sorted(declared),"labels":meta["Config"]["Labels"]})
        deadline=time.monotonic()+contract["startup_timeout_seconds"]
        while time.monotonic()<deadline:
            require_guard()
            snap=snapshot(cid);retain_snapshot(snap)
            if snap["foreign"]:raise RuntimeError("Foreign physical process detected")
            worker_pids.update(p for n,p in snap["processes"])
            if not inspect(cid)["State"]["Running"]:raise RuntimeError("Owned native service exited before health")
            try:
                if request(port)==200:break
            except (urllib.error.URLError,TimeoutError):pass
            time.sleep(5)
        else:raise TimeoutError("Native health deadline")
        payload={"model":"qwen3.5","messages":[{"role":"user","content":"Calculate 2 + 2. Reply with only the integer."}],
                 "temperature":0,"seed":0,"max_tokens":32,"chat_template_kwargs":{"enable_thinking":False}}
        for i in range(3):
            require_guard()
            before=snapshot(cid);retain_snapshot(before)
            if before["foreign"]:raise RuntimeError("Foreign process before request")
            response=request(port,payload)
            journal.append({"event":"response","index":i,"payload":payload,"response":response})
            require_guard()
            responses.append({"index":i,"payload":payload,"response":response})
            after=snapshot(cid);retain_snapshot(after)
            if after["foreign"]:raise RuntimeError("Foreign process after request")
        texts=[r["response"]["choices"][0]["message"]["content"].strip() for r in responses]
        assert all(t.rstrip(".")=="4" for t in texts),"Native smoke semantic result"
        assert len(set(texts))==1,"Native repeated response variability"
        assert len(worker_pids)>=4,"Missing physical worker evidence"
        assert physical_devices_seen==set(range(4)),"Missing physical card coverage"
        valid=True
    except Exception as e:
        error={"type":type(e).__name__,"message":str(e)}
    finally:
        guard_stop.set()
        if guard_thread:guard_thread.join(timeout=20)
        release={"owned_container":cid,"removed":cid is None,"port_free":False}
        if cid:
            try:
                meta=inspect(cid)
                assert meta["Config"]["Labels"].get("model-tuning-lab.task")==TASK
                logs=command(["docker","logs",cid],timeout=20)
                (raw/"service.log").write_text(logs)
                subprocess.run(["docker","stop","-t","10",cid],capture_output=True,timeout=30,check=False)
                command(["docker","rm",cid])
                release["removed"]=True
            except Exception as e:release["error"]=str(e)
        try:
            release["port_free"]=not command(["ss","-H","-ltn","sport = :"+str(port)]).strip()
        except OSError:pass
        final=snapshot()
        release["final_physical_processes"]=final["processes"]
        write(raw,"responses.json",responses)
        write(raw,"isolation.json",samples)
        write(raw,"release.json",release)
        result={"valid":valid and not guard_error and release["removed"] and release["port_free"],"error":error,
                "guard_errors":guard_error,"isolation_samples":len(samples),
                "responses":len(responses),"worker_pids":sorted(worker_pids),
                "physical_devices_seen":sorted(physical_devices_seen),"release":release}
        write(raw,"result.json",result)
        journal.append({"event":"terminal","result":result})
        journal.close()
        print(json.dumps(result),flush=True)
    if not result["valid"]:raise SystemExit(1)

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--run",action="store_true")
    parser.add_argument("--contract",type=Path,default=CONTRACT)
    args=parser.parse_args();contract=json.loads(args.contract.read_text())
    expected=contract["controller_sha256"]
    assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==expected
    assert contract["physical_npus"]==[0,1,2,3] and contract["tp"]==4
    if args.run:run_contract(contract)
    else:print(json.dumps({"configuration_valid":True,"device_run":False,"contract":contract}))
if __name__=="__main__":main()
