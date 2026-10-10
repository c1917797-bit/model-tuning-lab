"""One explicit retained CPU peer, not a scheduler/registry or NPU authority."""
import os
from pathlib import Path
GIB=1024**3
def need(v,m):
 if not v:raise ValueError(m)
def check_peer(ctl,ref):
 c=ctl.c if hasattr(ctl,"c") else __import__("model_contract")
 value=c.obj(ref)
 need(value["schema"]=="kivi.actual-independent-cpu-lease/v1"
  and value["portfolio_cutoff_epoch"]==1791788425 and value["Devices"]==[]
  and value["guest_limit_bytes"]==8*GIB and value["host_limit_bytes"]==512*1024**2,
  "exact single Devices[] peer budget")
 owned=c.obj(value["owned_ref"])
 need(owned["arm"]=="cpu-preflight" and owned["source"]==value["source_ref"],"actual CPU source owner")
 # Exact external peer inspector is part of the current immutable source closure.
 gate=c.role("peer_inspector");m=c.module(gate["path"],gate["sha256"],"_mixed_peer_inspector")
 raw,rr=ctl.call("peer-current-inspect",["/usr/bin/docker","inspect",owned["cid"]])
 import json
 rows=json.loads(raw["stdout"]);need(len(rows)==1,"one peer current inspect")
 x=rows[0];m.validate_peer_inspect(x,owned,value,c.obj)
 need(x["State"]["Running"] is True and x["State"]["Pid"]>0 and not x["State"].get("OOMKilled")
  and x["HostConfig"].get("Devices",[])==[],"current live CPU peer only")
 before=value["actual_host_process"];h=ctl.h.gate_process(before["pid"])
 need(h["pid"]==before["pid"] and h["start_ticks"]==before["start_ticks"] and h["argv"]==before["argv"],
  "current exact peer host PID/start/argv; never stale same PID")
 status=Path("/proc/%d/status"%before["pid"]).read_text()
 rss=[int(line.split()[1])*1024 for line in status.splitlines()if line.startswith("VmRSS:")]
 need(len(rss)==1 and 0<rss[0]<=512*1024**2,"actual peer host current RSS within declared512MiB")
 H=__import__("safety_host").H
 hv=H.cpu_view(before["pid"]);gv=H.cpu_view(x["State"]["Pid"])
 need(hv["effective_capacity"]>=1 and gv["effective_capacity"]==1
  and len(hv["effective_cpus"])==len(gv["effective_cpus"])==1
  and not set(hv["effective_cpus"])&set(gv["effective_cpus"]),"peer actual distinct host1+guest1")
 return dict(lease_ref=ref,current_inspect_ref=rr,host=hv,guest=gv,owned_cid=owned["cid"])
def choose_allocation(host,daemon,peer):
 used=set(peer["host"]["effective_cpus"])|set(peer["guest"]["effective_cpus"])
 hosts=sorted(set(host["effective_cpus"])-used)
 need(hosts and host["effective_capacity"]>=1 and daemon["effective_capacity"]>=8,"summed host2/guest5/reserve2")
 hc=hosts[0];spare=sorted(set(daemon["effective_cpus"])-used-{hc})
 need(len(spare)>=6,"distinct currenthost1/guest4/reserve2 outside peer2")
 views=[host,daemon,peer["host"],peer["guest"]]
 quotas={}
 for view in views:
  for row in view["quota_ancestors"]:
   if row["capacity"] is not None:quotas.setdefault(row["key"],[]).append(row["capacity"])
 shared=[min(v) for v in quotas.values() if len(v)>1]
 need(not shared or min(shared)>=9,"finite common quota covers joint9CPU")
 return dict(host_cpu=hc,guest_cpus=spare[:4],reserve_cpus=spare[4:6],
  host_cpu_budget=1,guest_cpu_budget=4,reserve_cpu_budget=2,
  common_finite_capacity=min(shared) if shared else None,
  explicit_peer_cpus=sorted(used),joint_CPU_budget=9,peer_owned_cid=peer["owned_cid"])
def publish(ctl,source,publish_fn):
 import safety_host as S
 x,ir=ctl.inspect()
 need(ctl.expected["arm"]=="cpu-preflight" and x["HostConfig"].get("Devices",[])==[]
  and x["State"]["Running"] is True,"only actual running independent CPU8 lease")
 host=S.H.frozen().gate_process(os.getpid())
 return publish_fn(ctl.out/"CPU-PEER-LEASE.json",dict(schema="kivi.actual-independent-cpu-lease/v1",
  source_ref=source,owned_ref=S.c.ref(ctl.out/"OWNED.json"),started_inspect_ref=ir,
  actual_host_process=host,cpu_allocation=ctl.cpu,Devices=[],guest_limit_bytes=8*GIB,
  host_limit_bytes=512*1024**2,portfolio_cutoff_epoch=1791788425,
  immutable_snapshot_requires_live_revalidation=True,npu_ownership_claim=False,run_authority=False))
