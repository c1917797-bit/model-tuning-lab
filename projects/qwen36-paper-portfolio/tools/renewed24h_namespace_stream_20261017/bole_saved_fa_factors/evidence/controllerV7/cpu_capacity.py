"""Read-only effective CPU budget, not os.cpu_count() or Docker NCPU alone."""
import hashlib,json,math,os
from pathlib import Path
def require(value,why):
    if not value:raise ValueError(why)
def cpu_set(text):
    found=set()
    for token in text.strip().split(","):
        if not token:continue
        pair=token.split("-");require(len(pair)<=2,"cpuset syntax")
        lo=int(pair[0]);hi=int(pair[-1]);require(0<=lo<=hi,"cpuset range")
        found.update(range(lo,hi+1))
    return found
def unescape(text):
    for old,new in (("\\040"," "),("\\011","\t"),("\\012","\n"),("\\134","\\")):
        text=text.replace(old,new)
    return text
def capacity(pid,inherited_affinity=None,proc=Path("/proc")):
    """Read every ancestor quota/cpuset in the actual host cgroup mount."""
    base=proc/str(pid);cg=(base/"cgroup").read_text()
    mounts=(proc/"self/mountinfo").read_text();membership=[]
    for line in cg.splitlines():
        _,controllers,path=line.split(":",2);membership.append((set(controllers.split(","))-{""},path))
    rows=[];quotas=[];sets=[]
    affinity=set(os.sched_getaffinity(pid)) if inherited_affinity is None else set(inherited_affinity)
    require(affinity,"actual/inherited process affinity")
    for line in mounts.splitlines():
        left,right=line.split(" - ",1);fields=left.split();fs,source,options=right.split()[:3]
        if fs not in ("cgroup","cgroup2"):continue
        root=Path(unescape(fields[3]));mount=Path(unescape(fields[4]))
        names=set(options.split(","))
        for controllers,path in membership:
            if fs=="cgroup2" and controllers:continue
            if fs=="cgroup" and not (controllers & names & {"cpu","cpuset"}):continue
            target=Path(path)
            require(target.is_relative_to(root),"actual cgroup must map into observed mount root")
            directory=mount/target.relative_to(root);ancestors=[]
            while True:
                ancestors.append(directory)
                if directory==mount:break
                require(directory.is_relative_to(mount),"cgroup ancestry escape")
                directory=directory.parent
            for directory in ancestors:
                if fs=="cgroup2":
                    setfile=directory/"cpuset.cpus.effective";qfile=directory/"cpu.max"
                    if setfile.exists():
                        raw=setfile.read_text();rows.append({"path":str(setfile),"raw":raw})
                        if raw.strip():sets.append(cpu_set(raw))
                    if qfile.exists():
                        raw=qfile.read_text();rows.append({"path":str(qfile),"raw":raw})
                        quota,period=raw.split();period=int(period);require(period>0,"cpu.max period")
                        if quota!="max":
                            value=int(quota);require(value>0,"cpu.max quota");quotas.append(value/period)
                else:
                    if "cpuset" in controllers:
                        setfile=directory/"cpuset.effective_cpus"
                        if not setfile.exists():setfile=directory/"cpuset.cpus"
                        raw=setfile.read_text();rows.append({"path":str(setfile),"raw":raw})
                        if raw.strip():sets.append(cpu_set(raw))
                    if "cpu" in controllers:
                        qfile=directory/"cpu.cfs_quota_us";pfile=directory/"cpu.cfs_period_us"
                        raw=qfile.read_text();periodraw=pfile.read_text()
                        rows.extend([{"path":str(qfile),"raw":raw},{"path":str(pfile),"raw":periodraw}])
                        quota=int(raw);period=int(periodraw);require(period>0 and (quota==-1 or quota>0),"actual CFS quota")
                        if quota!=-1:quotas.append(quota/period)
    require(rows and any("cpu.max" in x["path"] or "cpu.cfs_quota_us" in x["path"] for x in rows),
        "actual host/engine cgroup quota observation required")
    allowed=affinity.copy()
    for allowedset in sets:allowed &= allowedset
    require(allowed,"effective cpuset intersection")
    effective=min([float(len(allowed))]+quotas)
    return dict(pid=pid,cgroup_raw=cg,mountinfo_sha256=hashlib.sha256(mounts.encode()).hexdigest(),
        affinity=sorted(affinity),effective_cpuset=sorted(allowed),ancestor_constraints=rows,
        effective_cpu_capacity=effective,quota_capacity=(min(quotas) if quotas else None))
def consume(host,engine,engine_info):
    require(type(engine_info.get("NCPU")) is int and engine_info["NCPU"]>0,"actual Docker engine NCPU")
    joint=set(host["effective_cpuset"]) & set(engine["effective_cpuset"])
    effective=min(host["effective_cpu_capacity"],engine["effective_cpu_capacity"],
        float(engine_info["NCPU"]),float(len(joint)))
    require(math.isfinite(effective) and effective>=4.0,"effective host+engine guest1+host1+reserve2 capacity")
    return dict(schema="qwen36-deltalog-effective-cpu/v6",required_capacity=4,
        host=host,engine=engine,engine_info=engine_info,joint_cpuset=sorted(joint),effective_capacity=effective)
