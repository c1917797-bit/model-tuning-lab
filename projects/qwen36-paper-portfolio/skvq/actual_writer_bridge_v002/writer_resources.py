"""Single-card packet CPU4 adaptation of exact reviewed CPU/RAM proof, no device IO."""
import ast,hashlib,os,sys
from pathlib import Path
import writer_contract as C
GIB=2**30;HOST=512*2**20;RESERVE=8*GIB
def allocate(host,daemon):
    C.need(host["effective_capacity"]>=1 and daemon["effective_capacity"]>=3,"host1+guest1+reserve2")
    hc=min(host["effective_cpus"]);eligible=sorted(set(daemon["effective_cpus"])-{hc})
    C.need(len(eligible)>=3,"four distinct actual CPU slots")
    common={r["key"]:r["capacity"]for r in host["quota_ancestors"]};caps=[]
    for r in daemon["quota_ancestors"]:
        if r["key"]in common:caps.extend(v for v in(r["capacity"],common[r["key"]])if v is not None)
    C.need(not caps or min(caps)>=4,"actual common ancestor summed4CPU")
    return dict(host_cpu=hc,guest_cpus=eligible[:1],reserve_cpus=eligible[1:3],total=4,host=1,guest=1,reserve=2,
      common_finite_capacity=min(caps)if caps else None)
def adapted():
    row=C.HOST_BINDINGS["resources.py"];raw=C.checked(row);tree=ast.parse(raw)
    keep=[n for n in tree.body if not(isinstance(n,ast.FunctionDef)and n.name in("allocate","guest"))]
    # Exact original hierarchy, PID/start, MemAvailable, summed RAM/RSS and H8 bodies.
    scope=dict(__name__="_skvq_writer_exact_resource_primitives",allocate=allocate)
    exec(compile(ast.Module(body=keep,type_ignores=[]),row["path"],"exec"),scope)
    return scope
_SCOPE=None
def scope():
    global _SCOPE
    if _SCOPE is None:_SCOPE=adapted()
    return _SCOPE
def helper():return scope()["helper"]()
def memory_admit(host,daemon,guest):return scope()["memory_admit"](host,daemon,guest)
def fresh(guest,out):return scope()["fresh"](guest,out)
def rss():return scope()["rss"]()
def guest(pid,cpus,bytes_expected):
    v=helper().cpu_view(pid);m=scope()["memory_view"](pid)
    C.need(v["effective_capacity"]==1 and v["effective_cpus"]==cpus and
      m["ancestors"][0]["limit"]==bytes_expected,"actual guest CPU1 cpuset+8GiB readback")
    return dict(cpu=v,memory=m)
