"""Read only whitelisted startup controls from exact owned physical workers."""
import re
from pathlib import Path
CONTROL_KEYS=("INDEPENDENT_COMPACT_HYPIC","INDEPENDENT_COMPACT_MANIFEST","PYTHONPATH","VLLM_SERVER_DEV_MODE")
def capture_worker_controls(snapshot,owned_cid,*,proc_root="/proc"):
    if not isinstance(owned_cid,str) or not re.fullmatch("[0-9a-f]{64}",owned_cid) or snapshot.get("foreign"):
        raise ValueError("exact owned container and foreign-free snapshot required")
    owners=[o for o in snapshot.get("owners",[]) if o.get("owned")is True and o.get("ownership_status")=="owned-cgroup"]
    if len(owners)!=4 or any(type(o.get("npu"))is not int for o in owners) or {o.get("npu")for o in owners}!=set(range(4)) or len({o.get("pid")for o in owners})!=4:
        raise ValueError("four independent owned physical workers required")
    rows=[]
    for owner in sorted(owners,key=lambda o:o["npu"]):
        pid=owner.get("pid");nspid=owner.get("nspid")
        exact_cgroup=re.search(r"(?:/docker/|/docker-)"+re.escape(owned_cid)+r"(?:\.scope)?(?:/|\n|$)",owner.get("cgroup",""))
        if type(pid)is not int or pid<=0 or not exact_cgroup or not isinstance(nspid,list) or len(nspid)<2 or nspid[0]!=pid or any(type(n)is not int or n<=0 for n in nspid):
            raise ValueError("exact worker cgroup and namespace identity required")
        with (Path(proc_root)/str(pid)/"environ").open("rb")as stream:data=stream.read(65537)
        if len(data)>65536:raise ValueError("bounded worker environment required")
        values={}
        for field in data.split(b"\0"):
            if b"="not in field:continue
            key,value=field.split(b"=",1)
            if key not in tuple(k.encode()for k in CONTROL_KEYS):continue
            name=key.decode("ascii")
            if name in values:raise ValueError("ambiguous duplicate startup control")
            values[name]=value.decode("utf-8")
        rows.append({"physical_npu":owner["npu"],"host_pid":pid,"nspid":nspid,
                     "controls":{k:values.get(k)for k in CONTROL_KEYS}})
    return rows
