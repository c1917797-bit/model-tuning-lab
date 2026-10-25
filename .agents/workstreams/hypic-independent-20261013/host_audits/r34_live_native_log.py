"""Capture a bounded log from the exact owned running container before timing."""
import hashlib,json,os,re
from pathlib import Path
def take_owned_log(raw,contract,*,backend):
    raw=Path(raw);start=json.loads((raw/"service-start.json").read_bytes());cid=start["container_id"]
    if not re.fullmatch(r"[0-9a-f]{64}",cid):raise ValueError("exact owned CID required")
    meta=backend.inspect(cid)
    devices={x["PathOnHost"]for x in meta["HostConfig"]["Devices"]if re.fullmatch(r"/dev/davinci[0-9]+",x["PathOnHost"])}
    if(meta["Id"]!=cid or meta["Image"]!=contract["image"]
       or meta["Config"]["Labels"].get("model-tuning-lab.task")!=backend.TASK
       or meta["State"].get("Running")is not True
       or devices!={"/dev/davinci"+str(i)for i in range(4)}):
        raise ValueError("exact live owned image/task/physical mapping required")
    data=backend.command(["docker","logs",cid],timeout=30).encode()
    if not data or len(data)>16*1024**2:raise ValueError("bounded live native log required")
    name="r34-warm-native.log"
    with(raw/name).open("xb")as f:f.write(data);f.flush();os.fsync(f.fileno())
    return data,{"file":name,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()}
