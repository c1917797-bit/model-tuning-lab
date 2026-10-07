"""Read only exact owned cgroup-v1 memory counters; never reset/reclaim."""
from __future__ import annotations
import re
from pathlib import Path
import time
from v2_contract import require

def memory_path(cgroup_text,mountinfo,ident):
    rows=[line.split(":",2)[2] for line in cgroup_text.splitlines()
          if len(line.split(":",2))==3 and "memory" in line.split(":",2)[1].split(",")]
    require(len(rows)==1,"one actual memory-v1 membership required")
    member=Path(rows[0])
    require(member.is_absolute() and ".." not in member.parts and
            any(x in (ident,"docker-"+ident+".scope") for x in member.parts),
            "memory membership is not exact owned immutableID")
    matches=[]
    for line in mountinfo.splitlines():
        left,right=line.split(" - ",1);a=left.split();b=right.split()
        if b[0]=="cgroup" and "memory" in b[2].split(","):
            require(len(a)>=5 and "\\" not in a[3]+a[4],"escaped/unknown memory mount")
            mount_root=Path(a[3]); mount=Path(a[4])
            require(member==mount_root or mount_root in member.parents,"membership outside memory mount root")
            candidate=mount/member.relative_to(mount_root)
            require(candidate!=mount and mount in candidate.parents,"broad memory hierarchy rejected")
            matches.append(candidate)
    require(len(matches)==1,"one actual source-bound memory mount required")
    return matches[0]

def numeric(text,name):
    value=int(text.strip())
    require(value>=0,"negative counter: "+name)
    return value

def counters(read,path,limit):
    names=("memory.usage_in_bytes","memory.max_usage_in_bytes",
           "memory.limit_in_bytes","memory.failcnt")
    values={n:numeric(read(path/n),n) for n in names}
    require(values["memory.limit_in_bytes"]==limit,"owned actual kernel hard cap differs")
    require(values["memory.max_usage_in_bytes"]>=values["memory.usage_in_bytes"],
            "inconsistent sticky peak/current read")
    stat={}
    for line in read(path/"memory.stat").splitlines():
        key,value=line.split(); require(key not in stat,"duplicate memory.stat key")
        stat[key]=numeric(value,key)
    require("rss" in stat and "cache" in stat,"own anon/pagecache breakdown missing")
    return {"current_bytes":values[names[0]],"kernel_peak_bytes":values[names[1]],
            "limit_bytes":limit,"failcnt":values[names[3]],"memory_stat":stat}

class Peak:
    def __init__(self,value,*,proc=Path("/proc"),read=None):
        self.read=read or (lambda p:Path(p).read_text())
        self.proc=proc; self.ident=value["Id"];self.pid=value["State"]["Pid"]
        require(value["State"]["Running"] and type(self.pid) is int and self.pid>0,
                "own init PID unavailable")
        self.limit=value["HostConfig"]["Memory"]
        self.membership=self.read(proc/str(self.pid)/"cgroup")
        self.mountinfo=self.read(proc/"self/mountinfo")
        self.path=memory_path(self.membership,self.mountinfo,self.ident)
        self.start=self._start(self.pid)
        self.max_seen=0;self.samples=0

    def _start(self,pid):
        text=self.read(self.proc/str(pid)/"stat")
        tail=text[text.rfind(")")+2:].split()
        require(len(tail)>19,"own process stat incomplete")
        return numeric(tail[19],"starttime")

    def sample(self,value,*,model_completed=False):
        require(value["Id"]==self.ident and value["State"]["Pid"]==self.pid and
                value["State"]["Running"] and self._start(self.pid)==self.start and
                self.read(self.proc/str(self.pid)/"cgroup")==self.membership,
                "own PID/cgroup identity changed before peak read")
        data=counters(self.read,self.path,self.limit)
        require(data["kernel_peak_bytes"]>=self.max_seen,"sticky kernel peak regressed")
        self.max_seen=data["kernel_peak_bytes"];self.samples+=1
        return dict(data,schema="damp-own-cgroup-peak/v1",container_id=self.ident,
                    init_pid=self.pid,init_starttime=self.start,cgroup_path=str(self.path),
                    observed_at_unix_ns=time.time_ns(),sample=self.samples,
                    model_process_completed=model_completed,
                    coverage="through_completed_model" if model_completed else "through_observation",
                    complete_container_lifetime_claimed=False,
                    source="kernel own memory.max_usage_in_bytes, not Docker display/host delta")
