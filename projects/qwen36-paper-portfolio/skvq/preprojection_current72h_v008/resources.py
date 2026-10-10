"""SKVQ-specific fresh CPU7/RAM resource adapter. Stdlib; no runtime launch at import.
Reuses exact H8 CPU/hierarchy proof, not its controller or numerical PASS.
"""
import hashlib,importlib.util,json,os,resource
from pathlib import Path
H8=Path("/opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/short_horizon_h8_gate_v4/host_run.py")
PINS={str(H8):"4ddd75d6ce7558f0131992da3a5514df43dfb4b33f45674722ba5769ecef5e20",
str(H8.parent.parent/"full_matrix_host_v2/host.py"):"ab0296c698df00c9c3b2ce377601f6d6723adde6efb4a9e65407beca51ba5f86",
str(H8.parent.parent/"saved_step_native_order_v2/host_run.py"):"86c1ca7f59c6ad5b2b4d5efb155394455a12376cf368e06f9e2e13d39b7192fc"}
GIB=2**30;HOST=512*2**20;RESERVE=8*GIB;HELPER=None
def require(x,m):
    if not x:raise ValueError(m)
def sha(p):
    p=Path(p);require(p.is_file() and not p.is_symlink(),"ordinary source "+str(p));h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()
def helper():
    global HELPER
    require(all(sha(p)==v for p,v in PINS.items()),"actual frozen H8 helper three-source closure")
    if HELPER is None:
        s=importlib.util.spec_from_file_location("_skvq_bound_cpu_h8",H8);HELPER=importlib.util.module_from_spec(s);s.loader.exec_module(HELPER)
        HELPER.frozen()
    return HELPER
def allocate(host,daemon):
    require(host["effective_capacity"]>=1 and daemon["effective_capacity"]>=6,"host1 + daemon guest4/reserve2")
    hc=min(host["effective_cpus"]);eligible=sorted(set(daemon["effective_cpus"])-{hc})
    require(len(eligible)>=6,"seven distinct eligible CPU slots")
    common={r["key"]:r["capacity"] for r in host["quota_ancestors"]}
    caps=[]
    for r in daemon["quota_ancestors"]:
        if r["key"] in common:
            caps.extend(v for v in (r["capacity"],common[r["key"]]) if v is not None)
    require(not caps or min(caps)>=7,"actual common ancestor summed7 CPU budget")
    return dict(host_cpu=hc,guest_cpus=eligible[:4],reserve_cpus=eligible[4:6],
       total=7,host=1,guest=4,reserve=2,common_finite_capacity=min(caps) if caps else None)
def memory_view(pid):
    h=helper();before=h.frozen().process_identity(pid);version,group,mount,chain=h.hierarchy(pid,"memory");rows=[]
    for p in chain:
        if version==1:
            limit=(p/"memory.limit_in_bytes").read_text().strip();used=(p/"memory.usage_in_bytes").read_text().strip()
            cap=int(limit);finite=None if cap>=2**60 else cap
        else:
            lp=p/"memory.max";up=p/"memory.current"
            require((lp.is_file() and up.is_file()) or p==Path(mount),"actual memory ancestor files")
            limit=lp.read_text().strip() if lp.is_file() else "max";used=up.read_text().strip() if up.is_file() else "0"
            finite=None if limit=="max" else int(limit)
        require(int(used)>=0 and (finite is None or finite>0),"positive actual memory ancestor")
        rows.append(dict(key=str(p),limit_text=limit,usage_text=used,limit=finite,used=int(used)))
    require(h.frozen().process_identity(pid)==before,"memory PID identity drift")
    return dict(process=before,version=version,group=group,mount=mount,ancestors=rows)
def memory_admit(host,daemon,guest_bytes):
    total=HOST+RESERVE+guest_bytes
    for r in host["ancestors"]:
        require(r["limit"] is None or r["limit"]-r["used"]>=HOST,"host .5GiB ancestor headroom")
    for r in daemon["ancestors"]:
        require(r["limit"] is None or r["limit"]-r["used"]>=guest_bytes+RESERVE,"daemon guest+8GiB ancestor headroom")
    common={r["key"]:r for r in host["ancestors"]}
    for r in daemon["ancestors"]:
        if r["key"] in common:
            a=common[r["key"]]
            for v in (a,r):require(v["limit"] is None or v["limit"]-v["used"]>=total,"common ancestor summed ordinary RAM")
    return total
def fresh(guest_bytes,out):
    h=helper();host=h.cpu_view(os.getpid());daemon=h.daemon_view();allocation=allocate(host,daemon)
    hm=memory_view(os.getpid());dm=memory_view(daemon["process"]["pid"]);total=memory_admit(hm,dm,guest_bytes)
    fields={l.split(":")[0]:int(l.split()[1])*1024 for l in Path("/proc/meminfo").read_text().splitlines()
      if l.startswith(("MemAvailable:","Hugetlb:","SwapTotal:","SwapFree:"))}
    require(fields["SwapTotal"]==fields["SwapFree"] and fields["MemAvailable"]>=total,"fresh ordinary RAM; HugeTLB never added or written")
    import shutil
    disk=shutil.disk_usage(out).free
    return dict(host_cpu=host,daemon_cpu=daemon,allocation=allocation,host_memory=hm,daemon_memory=dm,
      memory=fields,disk_available_bytes=disk,ordinary_floor_bytes=total)
def guest(pid,cpus,bytes_expected):
    h=helper();v=h.cpu_view(pid);m=memory_view(pid)
    require(v["effective_capacity"]==4 and v["effective_cpus"]==cpus,"actual guest CPU4 quota/cpuset readback")
    leaf=m["ancestors"][0];require(leaf["limit"]==bytes_expected,"actual guest leaf memory binding")
    return dict(cpu=v,memory=m)
def rss():
    # Observe only this host process and its own descendants. A reaped child
    # disappearance is terminal evidence, not an ESRCH error for a live parent.
    seen=set();pending=[os.getpid()];rows=[]
    while pending:
        pid=pending.pop()
        if pid in seen:continue
        seen.add(pid);require(len(seen)<=1024,"bounded owned host CLI tree")
        p=Path("/proc")/str(pid)
        try:
            before=(p/"stat").read_text();status=(p/"status").read_text();kids=(p/"task"/str(pid)/"children").read_text()
            after=(p/"stat").read_text()
        except (FileNotFoundError,ProcessLookupError):
            require(pid!=os.getpid(),"live MAIN controller missing");continue
        ticks=lambda t:int(t[t.rfind(")")+2:].split()[19])
        require(ticks(before)==ticks(after),"owned host CLI PID reuse")
        rr=[x for x in status.splitlines() if x.startswith("VmRSS:")]
        require(len(rr)<=1,"one actual RSS row");value=int(rr[0].split()[1])*1024 if rr else 0
        rows.append(dict(pid=pid,start_ticks=ticks(before),rss_bytes=value));pending.extend(int(x) for x in kids.split())
    peak=(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss+resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)*1024
    live=sum(r["rss_bytes"] for r in rows)
    return dict(rows=rows,live_sum_bytes=live,conservative_cumulative_peak_sum_bytes=peak,limit_bytes=HOST)
