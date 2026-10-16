"""Owned lifecycle-only controller, unchanged official image and generic guards."""
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
CONTRACT = HERE / "LIFECYCLE_R16_CONTRACT.json"
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

def classify_process_owner(cgroup,cid,*,same_pid_namespace=False):
    if cid and cid in cgroup:return 'owned-cgroup'
    if cid and same_pid_namespace:return 'owned-pid-namespace'
    paths=[line.split(':',2)[-1] for line in cgroup.splitlines()]
    if paths and any(path not in ('/','owner_unverified') for path in paths):
        return 'foreign-cgroup'
    return 'ownership-unresolved'

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
        same_namespace=False
        if cid and cid not in cgroup:
            try:
                meta=inspect(cid)
                if meta['Id']!=cid:raise ValueError('exact container identity changed')
                initpid=meta['State']['Pid']
                # Independent live membership proof; do not infer ownership
                # from a familiar PID or a historical process receipt.
                if meta['State']['Running'] and initpid>0:
                    same_namespace=(Path('/proc',str(pid),'ns','pid').readlink()==
                                    Path('/proc',str(initpid),'ns','pid').readlink())
            except (OSError,KeyError,ValueError,subprocess.SubprocessError):pass
        status=classify_process_owner(cgroup,cid,same_pid_namespace=same_namespace)
        owned=status.startswith('owned-')
        observation={"npu":n,"pid":pid,"cgroup":cgroup,"ownership_status":status}
        from independent_process_namespace import namespace_pids
        try:
            observation["nspid"]=list(namespace_pids(
                Path("/proc",str(pid),"status").read_text(),pid))
        except (OSError,ValueError) as exc:
            observation["nspid"]=None;observation["nspid_error"]=str(exc)
        if not owned:foreign.append(observation)
        owners.append(dict(observation,owned=owned))
    return {"utc":datetime.now(timezone.utc).isoformat(),"processes":target,"owners":owners,"foreign":foreign,"raw":text}

def port_free(port):
    with socket.socket() as s:
        s.bind(("0.0.0.0",port))

def prefix_cache_flag(contract):
    """Native PDC switch; absent means historical no-PDC protocol."""
    enabled=contract.get("enable_prefix_caching",False)
    if type(enabled) is not bool:
        raise ValueError("enable_prefix_caching must be an explicit boolean")
    return "--enable-prefix-caching" if enabled else "--no-enable-prefix-caching"

def write(root,name,data):
    path=root/name
    with path.open("x",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)
        f.flush()

def request(port,payload=None,*,completion=False,timeout=60):
    path="/health" if payload is None else ("/v1/completions" if completion else "/v1/chat/completions")
    data=None if payload is None else json.dumps(payload).encode()
    req=urllib.request.Request("http://127.0.0.1:"+str(port)+path,data=data,headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=timeout if data else 3) as response:
        raw=response.read()
        return json.loads(raw) if data else response.status

def stop_owned_on_foreign(cid,*,image,inspect_fn=None,command_fn=None):
    """Abort only the exact controller-created container; retain it for logs."""
    inspect_fn=inspect if inspect_fn is None else inspect_fn
    command_fn=command if command_fn is None else command_fn
    if not re.fullmatch(r"[0-9a-f]{64}",cid):raise ValueError("exact full owned CID required")
    meta=inspect_fn(cid)
    if meta["Id"]!=cid or meta["Image"]!=image or meta["Config"]["Labels"].get("model-tuning-lab.task")!=TASK:
        raise ValueError("owned controller container identity mismatch")
    devices={d["PathOnHost"] for d in meta["HostConfig"]["Devices"] if re.fullmatch(r"/dev/davinci\d+",d["PathOnHost"])}
    if devices!={"/dev/davinci"+str(i) for i in range(4)}:
        raise ValueError("owned container physical device mapping drift")
    if meta["State"]["Running"]:command_fn(["docker","stop","-t","3",cid],timeout=20)


def run_contract(contract):
    from independent_lifecycle_policy import lifecycle_mode,validate_lifecycle_sources
    stage,treatment_on=lifecycle_mode(contract)
    validate_lifecycle_sources(contract,HERE)
    from independent_execution_deadline import deadline_epoch,deadline_reached
    stop_at=deadline_epoch(contract.get("absolute_stop_utc"))
    if deadline_reached(stop_at,time.time()):raise TimeoutError("Frozen execution deadline reached before admission")
    image=contract["image"];model=Path(contract["model"]);port=contract["port"]
    pdc_flag=prefix_cache_flag(contract)
    raw=Path(contract["raw_root"])
    if raw.exists():raise RuntimeError("Immutable attempt root already exists")
    assert hashlib.sha256((model/"config.json").read_bytes()).hexdigest()==contract["model_config_sha256"]
    image_info=json.loads(command(["docker","image","inspect",image]))[0]
    inherited_pythonpath=next((x.split("=",1)[1] for x in image_info["Config"].get("Env",[]) if x.startswith("PYTHONPATH=")),"")
    diagnostic=contract.get("cache_diagnostic")
    formal_artifact=contract.get("formal_token_artifact")
    quality_spec=contract.get("quality_workload")
    if contract.get("formal_quality"):
        if contract.get("formal_performance") or not quality_spec or formal_artifact:
            raise ValueError("exclusive frozen quality workload required")
        from independent_quality_workload import read_bound
        quality_inputs=read_bound(quality_spec["inputs"])
        read_bound(quality_spec["catalog"])
        if any(len(x["token_ids"])+1024>40960 for x in quality_inputs["requests"]):
            raise ValueError("quality input exceeds actual service capacity")
    formal_payloads=None
    if formal_artifact:
        from independent_lifecycle_policy import lifecycle_payloads
        formal_payloads=lifecycle_payloads(formal_artifact)
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
    (raw/"compiled-cache").mkdir()
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
                if deadline_reached(stop_at,time.time()):
                    guard_error.append({"type":"TimeoutError","message":"Frozen execution deadline reached","raw":None})
                    journal.append({"event":"deadline_interrupt_owned_stop","container_id":cid})
                    stop_owned_on_foreign(cid,image=image)
                    return
                snap=snapshot(cid);retain_snapshot(snap)
                if snap["foreign"]:
                    guard_error.append({"type":"RuntimeError","message":"Foreign physical process detected","raw":None})
                    if contract.get("stop_owned_on_foreign"):
                        journal.append({"event":"foreign_interrupt_owned_stop","container_id":cid})
                        stop_owned_on_foreign(cid,image=image)
                    return
                worker_pids.update(pid for device,pid in snap["processes"])
                physical_devices_seen.update(device for device,pid in snap["processes"])
            except Exception as exc:
                guard_error.append({"type":type(exc).__name__,"message":str(exc),"raw":getattr(exc,"raw",None)})
                return
            guard_stop.wait(3)
    def require_guard():
        if deadline_reached(stop_at,time.time()):raise TimeoutError("Frozen execution deadline reached")
        if guard_error:raise RuntimeError("Isolation guard failed: "+str(guard_error))
    try:
        require_guard()
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
        if formal_artifact:
            args+=["-v",formal_artifact["path"]+":/inputs/tokens.json:ro"]
        if quality_spec:
            args+=["-v",quality_spec["catalog"]["path"]+":/inputs/catalog.json:ro"]
        env={"ASCEND_RT_VISIBLE_DEVICES":"0,1,2,3","HCCL_OP_EXPANSION_MODE":"AIV",
             "PYTORCH_NPU_ALLOC_CONF":"expandable_segments:True","TASK_QUEUE_ENABLE":"1",
             "VLLM_ASCEND_ENABLE_FLASHCOMM":"1","HCCL_NPU_SOCKET_PORT_RANGE":
             str(contract["hccl_ports"][0])+"-"+str(contract["hccl_ports"][1]),
             "TMPDIR":"/scratch/tmp","PYTHONDONTWRITEBYTECODE":"1",
             "TRITON_CACHE_DIR":"/scratch/compiled-cache"}
        for k,v in env.items():args+=["-e",k+"="+v]
        if diagnostic:
            bootstrap="compact_bootstrap" if diagnostic.get("compact_manifest") else "diagnostic_bootstrap"
            args+=["-v",str(HERE)+":/probe:ro",
                   "-e","PYTHONPATH=/probe/"+bootstrap+":/probe:"+inherited_pythonpath,
                   "-e","INDEPENDENT_CACHE_DIAGNOSTIC=1",
                   "-e","INDEPENDENT_DIAGNOSTIC_ROOT=/scratch/diagnostics",
                   "-e","INDEPENDENT_DIAGNOSTIC_BATCHES=2"]
            if diagnostic.get("public_config"):
                args+=["-e","INDEPENDENT_PUBLIC_STAGE_CONFIG=/probe/"+diagnostic["public_config"]]
            if diagnostic.get("private_c1"):
                args+=["-e","INDEPENDENT_PRIVATE_C1=1"]
            if diagnostic.get("c2_kv"):
                args+=["-e","INDEPENDENT_C2_KV=1"]
            if diagnostic.get("compact_manifest"):
                args+=["-e","INDEPENDENT_COMPACT_HYPIC="+("1" if treatment_on else "0"),
                       "-e","INDEPENDENT_COMPACT_MANIFEST=/probe/"+diagnostic["compact_manifest"],
                       "-e","INDEPENDENT_COMPACT_RAW=/scratch/diagnostics"]
        args += [image,"serve","/model","--served-model-name","qwen3.5","--host","127.0.0.1",
                 "--port",str(port),"--tensor-parallel-size","4","--data-parallel-size","1",
                 "--max-model-len","40960","--max-num-batched-tokens","40960",
                 "--max-num-seqs","32","--gpu-memory-utilization","0.85",
                 pdc_flag,"--additional-config",'{"enable_cpu_binding":false}',
                 "--compilation-config",('{"cudagraph_mode":"NONE"}' if contract.get("enforce_eager") else '{"cudagraph_mode":"FULL_DECODE_ONLY","cudagraph_capture_sizes":[1,4,8,16,24,32]}'),
                 "--trust-remote-code","--async-scheduling"]
        if contract.get("enforce_eager"):args.append("--enforce-eager")
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
                if request(port,timeout=3)==200:break
            except (urllib.error.URLError,TimeoutError):pass
            time.sleep(5)
        else:raise TimeoutError("Native health deadline")
        if contract.get("formal_quality"):
            from independent_quality_workload import run_quality_workload
            from independent_quality_client import http_quality
            from independent_current_material_readiness import current_materials_ready
            def quality_ready(digest):
                if not diagnostic:return
                manifest_hash=hashlib.sha256((HERE/diagnostic["compact_manifest"]).read_bytes()).hexdigest()
                until=time.monotonic()+300
                while time.monotonic()<until:
                    require_guard();worker_events=[]
                    for path in (raw/"diagnostics").glob("compact-worker-*.jsonl"):
                        data=path.read_text();complete=data[:data.rfind("\n")+1]
                        worker_events.extend(json.loads(line) for line in complete.splitlines())
                    if current_materials_ready(worker_events,manifest_hash,digest):return
                    time.sleep(1)
                raise TimeoutError("four-rank selected quality material readiness")
            result_unit=run_quality_workload(quality_spec,
                send=lambda p:http_quality(port,p,guard=require_guard,timeout=2400),
                guard=require_guard,record=journal.append,
                require_material_ready=quality_ready)
            responses=result_unit["results"]
            write(raw,"quality-unit.json",result_unit)
            if result_unit["successful"]!=381:
                raise RuntimeError("full quality request failures retained")
        elif contract.get("formal_performance"):
            if not formal_artifact:raise ValueError("formal performance artifact required")
            from independent_formal_workload import run_formal_workload
            from independent_formal_client import http_measure
            from independent_material_readiness import materials_ready
            def ready():
                if not diagnostic:return
                manifest_hash=hashlib.sha256((HERE/diagnostic["compact_manifest"]).read_bytes()).hexdigest()
                until=time.monotonic()+300
                while time.monotonic()<until:
                    require_guard();worker_events=[]
                    for path in (raw/"diagnostics").glob("compact-worker-*.jsonl"):
                        data=path.read_text()
                        complete=data[:data.rfind("\n")+1]
                        worker_events.extend(json.loads(line) for line in complete.splitlines())
                    if materials_ready(worker_events,manifest_hash):return
                    time.sleep(1)
                raise TimeoutError("four-rank public material readiness")
            def warm_send(p):
                require_guard()
                return request(port,p,completion=True,timeout=900)
            result_unit=run_formal_workload(formal_artifact,
                send_warmup=warm_send,
                send_measured=lambda p:http_measure(port,p,guard=require_guard,timeout=1800),
                guard=require_guard,record=journal.append,require_material_ready=ready)
            responses=result_unit["results"]
            write(raw,"performance-unit.json",result_unit)
            if not result_unit["valid"]:raise RuntimeError("formal measured request failure")
        else:
            payload={"model":"qwen3.5","messages":[{"role":"user","content":"Calculate 2 + 2. Reply with only the integer."}],
                     "temperature":0,"seed":0,"max_tokens":32,"chat_template_kwargs":{"enable_thinking":False}}
            payload=contract.get("request_payload",payload)
            payloads=contract.get("request_payloads")
            if formal_payloads is not None:
                if payloads or contract.get("request_payload_specs"):
                    raise ValueError("ambiguous formal request payloads")
                payloads=formal_payloads
            if contract.get("request_payload_specs"):
                from synthetic_compact_workload import expand_payloads
                payloads=expand_payloads(contract["request_payload_specs"],contract["public_token_recipe"])
            from independent_request_waves import execute_waves
            payloads=payloads if payloads else [payload]*3
            if contract.get("native_prefix_warmup"):
                if contract["native_prefix_warmup"] is not True or not formal_artifact or not pdc_flag=="--enable-prefix-caching":
                    raise ValueError("explicit formal nativePDC warmup required")
                from independent_formal_canary import native_prefix_warmup
                require_guard()
                warm_payload=native_prefix_warmup(formal_artifact)
                warm_response=request(port,warm_payload,completion=True,timeout=900)
                require_guard()
                journal.append({"event":"native-prefix-warmup","scored":False,
                    "prompt_tokens":len(warm_payload["prompt"]),"response":warm_response})
            if len(payloads)!=3:raise ValueError('smoke requires exact3 payloads')
            waves=contract.get('request_waves',[[0],[1],[2]])
            delays={int(k):v for k,v in contract.get('request_start_delays',{}).items()}
            def send(payload):
                require_guard()
                before=snapshot(cid);retain_snapshot(before)
                if before["foreign"]:raise RuntimeError("Foreign process before request")
                return request(port,payload,completion=contract.get("completion",False),
                               timeout=contract.get("request_timeout_seconds",60))
            for record in execute_waves(payloads,waves,send,check_guard=require_guard,start_delays=delays):
                journal.append(dict(record,event='response'))
                require_guard()
                responses.append(record)
                after=snapshot(cid);retain_snapshot(after)
                if after["foreign"]:raise RuntimeError("Foreign process after request")
            if not contract.get("completion",False):
                texts=[r["response"]["choices"][0]["message"]["content"].strip() for r in responses]
                assert all(t.rstrip(".")=="4" for t in texts),"Native smoke semantic result"
                assert len(set(texts))==1,"Native repeated response variability"
            else:
                assert all(isinstance(r["response"]["choices"][0]["text"],str) for r in responses)
                assert all(r["response"]["usage"]["completion_tokens"]>0 for r in responses)
        assert len(worker_pids)>=4,"Missing physical worker evidence"
        assert physical_devices_seen==set(range(4)),"Missing physical card coverage"
        from independent_lifecycle_worker_controls import capture_worker_controls
        control_snapshot=snapshot(cid);retain_snapshot(control_snapshot)
        control_record={"event":"lifecycle-worker-startup-controls","stage":stage,"container_id":cid,
            "snapshot_utc":control_snapshot["utc"],"workers":capture_worker_controls(control_snapshot,cid)}
        write(raw,"lifecycle-worker-controls.json",control_record);journal.append(control_record)
        from independent_lifecycle_policy import semantic_payload,check_semantic
        semantic_body=semantic_payload();require_guard()
        semantic_response=request(port,semantic_body,completion=False,timeout=120)
        semantic_record={"event":"lifecycle-semantic","stage":stage,"payload":semantic_body,"response":semantic_response}
        write(raw,"lifecycle-semantic.json",semantic_record);journal.append(semantic_record)
        require_guard();check_semantic(semantic_response)
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
        release["utc"]=final["utc"]
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
