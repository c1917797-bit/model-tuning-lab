"""MAIN-only exact fresh device proof; no proof generation or launching."""
import json,hashlib,re
from pathlib import Path
from .core import require
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
def bound(path,digest):
    p=Path(path);require(p.is_absolute() and ".." not in p.parts and p.is_file() and not p.is_symlink() and re.fullmatch("[a-f0-9]{64}",digest or ""),"actual exact absolute ordinary proof SHA Ref")
    raw=p.read_bytes();require(hashlib.sha256(raw).hexdigest()==digest,"source/proof bytes changed");return raw
def validate_proof(path,digest,source,files,argv,now_ns=None):
    import time
    raw=bound(path,digest);proof=json.loads(raw)
    require(raw==json.dumps(proof,sort_keys=True,separators=(",",":"),allow_nan=False).encode()+b"\n","actual canonical immutable proof bytes")
    template=proof.get("image_python_argv_template");sentinel="@ACTUAL_DEVICE_PROOF_SHA256@"
    require(type(template) is list and template.count(sentinel)==1 and template.index(sentinel)>0 and template[template.index(sentinel)-1]=="--device-proof-sha256","only exact proof SHA sentinel position")
    require([digest if s==sentinel else s for s in template]==argv and proof.get("source_manifest")==source and proof.get("sources")==files,"actual full source-bound proof/child CLI")
    require(proof.get("schema")=="sparq.token-device-proof/v4","new exact SparQ proof schema")
    inspect=proof["container_inspect"];host=inspect["HostConfig"]
    require(proof["privileged"] is False and host["Privileged"] is False,"nonprivileged owned runner")
    mapping=proof["logical_to_physical"]
    require(type(mapping) is dict and set(mapping)=={"0"} and mapping["0"]==6,
            "one authorized physical NPU -> logical0")
    physical=mapping["0"]
    require(proof["physical_npu_ids"]==[physical] and inspect["Image"]==IMAGE
            and proof["container_id"]==inspect["Id"],"actual original container/image/card")
    require(inspect["Config"]["Labels"].get("model-tuning-lab.owner")=="sparq-token-v4",
            "MAIN exact owned numeric container")
    devices=host["Devices"];commons={"/dev/davinci_manager","/dev/devmm_svm","/dev/hisi_hdc"}
    require(len(devices)==4 and {d["PathOnHost"] for d in devices}==commons|{"/dev/davinci%d"%physical},
            "exact one card plus3 common devices; protect0-3")
    for d in devices:
        require(d["CgroupPermissions"]=="rwm","device permissions")
        if d["PathOnHost"] in commons:require(d["PathInContainer"]==d["PathOnHost"],"common device mapping")
        else:require(d["PathInContainer"] =="/dev/davinci0","actual physical remap")
    require(0<=(time.time_ns() if now_ns is None else now_ns)-proof["observed_at_unix_ns"]<=30_000_000_000
            and proof["exclusive_resource_check_passed"] is True
            and isinstance(proof["fresh_resource_audit"],dict),"fresh fail-closed resource proof")
    require(host.get("Memory")==host.get("MemorySwap")==8*1024**3 and host.get("NanoCpus")==10**9 and re.fullmatch("[0-9]+",host.get("CpusetCpus","")) and host.get("NetworkMode")=="none" and host.get("IpcMode")=="private" and set(host.get("CapDrop") or [])=={"ALL"} and set(host.get("SecurityOpt") or [])=={"no-new-privileges"} and not host.get("DeviceRequests") and not host.get("DeviceCgroupRules"), "exact8GiB/1CPU/nonprivileged private owned numeric budget")
    cpu=proof["actual_guest_cpu"];require(cpu["effective_capacity"]==1 and cpu["effective_cpus"]==[int(host["CpusetCpus"])],"actual effective guest CPU, not declaration")
    labels=inspect["Config"]["Labels"];require(labels.get("model-tuning-lab.source-manifest-sha256")==source["sha256"] and labels.get("model-tuning-lab.numeric-script-sha256")==files["numeric_gate.py"],"actual new source/numeric producer labels")
    from receipt import load,docker_argv,validate_cpu_phase
    from preflight import validate_abi
    nd=validate_abi(load(proof["native_no_device_abi"]),source,files);child=load(proof["native_no_device_child"])
    _,stopped=validate_cpu_phase(proof,proof["cpu_container_id"],source,files)
    require(proof["cpu_container_id"]!=proof["container_id"] and __import__("datetime").datetime.fromisoformat(stopped["State"]["FinishedAt"].replace("Z","+00:00"))<=__import__("datetime").datetime.fromisoformat(inspect["State"]["StartedAt"].replace("Z","+00:00")),"actual CPU-only stop before distinct NPU start")
    expected=[__import__("receipt").PY,"-B",str(Path(source["path"]).parent/"preflight.py"),"--execute",
      "--source-manifest",source["path"],"--source-manifest-sha256",source["sha256"],"--output","/sparq-results/ABI.json"]
    require(nd["actual_argv"]==expected and child["requested_argv"]==docker_argv(proof["cpu_container_id"],expected) and
     child["argv"]==["/usr/bin/prlimit","--as=unlimited","--",*docker_argv(proof["cpu_container_id"],expected)] and child["exit_code"]==0,"actual no-device original Docker child before canary")
    canary=load(proof["canary"]);load(proof["probe_idle"])
    require(canary["native_no_device_abi"]==proof["native_no_device_abi"] and canary["preinit_actual_exports"]==nd["actual_exports"] and
     canary["source_manifest"]==source and canary["sources_before"]==canary["sources_after"]==files and canary["fresh_canary_passed"] is True,
     "actual new no-device/canary/source linkage")
    return proof

def cgroup_memory():
 choices=[Path("/sys/fs/cgroup/memory.max"),Path("/sys/fs/cgroup/memory/memory.limit_in_bytes")]
 p=next((x for x in choices if x.is_file()),None);require(p is not None,"actual guest memory control required")
 value=p.read_text().strip();require(value.isdigit() and int(value)==8*1024**3,"actual owned exact8GiB")
 return {"path":str(p),"value":int(value),"proc_cgroup":Path("/proc/self/cgroup").read_text()}
