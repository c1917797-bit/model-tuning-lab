"""OFF unless installed for the unchanged full64 CPU-only raw stage.
Known peer profile is source-pinned by this adapter MF, never a caller whitelist.
No numerical changes, NPU allocation, foreign stop, or peer-controller mutation.
"""
import ast,datetime,hashlib,inspect,json,os,re,shutil,time,types
from pathlib import Path
GIB=2**30
RAW_HOST=512*2**20
RAW_GUEST=8*GIB
RAW_RESERVE=8*GIB
WORKSPACE=32*GIB
SAFETY_SHA="2f6d876a3363840aabfa7ee09db1b2b01700ba8bce17fd3fab040464af2d6408"
SCHEMA="kivi.cpu-only-raw-joint-resources/v2"
def need(v,m):
 if not v:raise ValueError(m)
def positive(v):
 return type(v)is int and v>0
def stamp(value):
 return (value["pid"],value["start_ticks"],value["cgroup"])
def shared_limits(views,slots):
 rows={}
 for view,cpus in zip(views,slots):
  need(view["effective_capacity"]>=len(cpus) and set(cpus)<=set(view["effective_cpus"]),"QUEUE_RAW: actual eligible CPU/quota")
  for r in view["quota_ancestors"]:
   need(r["capacity"] is None or type(r["capacity"])in(int,float),"finite actual CPU quota")
   x=rows.setdefault(r["key"],dict(cpus=set(),caps=[]));x["cpus"].update(cpus)
   if r["capacity"]is not None:x["caps"].append(r["capacity"])
 for x in rows.values():
  need(not x["caps"]or min(x["caps"])>=len(x["cpus"]),"QUEUE_RAW: joint finite ancestor CPU budget")
 return min((v for x in rows.values()for v in x["caps"]),default=None)
def peer_slots(peer):
 state=peer["state"]
 need(state in("standalone","running","stopped-retained"),"exact resource peer state")
 if state=="standalone":return set(),set(),None
 a=peer["peer_allocation"]
 need(type(a)is dict and a["total"]==7 and a["host"]==1 and a["guest"]==4 and a["reserve"]==2,
  "reviewed peer declared7; no average-use discount")
 hc=a["host_cpu"];gc=a["guest_cpus"];rc=a["reserve_cpus"]
 need(type(hc)is int and len(gc)==4 and len(rc)==2 and len({hc,*gc,*rc})==7,"peer seven distinct slots")
 # On exact container stop, guest4 are released. Host1/reserve2 remain charged:
 # guest stop is NOT proof that the peer host controller/lease has terminated.
 return ({hc,*gc,*rc}if state=="running"else{hc,*rc}),set(rc),hc
def allocate(host,daemon,peer,*,fixed_guest=None):
 occupied,reserve,peer_host=peer_slots(peer)
 hs=sorted(set(host["effective_cpus"])-occupied)
 need(hs,"QUEUE_RAW: no disjoint raw host CPU")
 hc=hs[0]
 eligible=set(daemon["effective_cpus"])-occupied-{hc}
 need(eligible,"QUEUE_RAW: no disjoint raw guest CPU")
 gc=min(eligible)if fixed_guest is None else fixed_guest
 need(type(gc)is int and gc in eligible,"QUEUE_RAW: fixed actual raw guest CPU conflict")
 state=peer["state"]
 if state=="running":
  cap=shared_limits([host,daemon,peer["peer_host_cpu"],peer["peer_guest_cpu"]],
   [{hc},{gc,*reserve},{peer_host},set(peer["peer_allocation"]["guest_cpus"])])
 elif state=="stopped-retained":
  # Fresh daemon ancestor view accounts for all remaining historical host/reserve
  # slots conservatively. Never read a exited/reused peer PID or stale quota.
  cap=shared_limits([host,daemon],[{hc},{gc,*occupied}])
 else:cap=shared_limits([host,daemon],[{hc},{gc}])
 return dict(host_cpu=hc,guest_cpus=[gc],reserve_cpus=[],host_cpu_budget=1,guest_cpu_budget=1,
  reserve_cpu_budget=0,peer_reserved_cpus=sorted(occupied),peer_total_cpu_budget=len(occupied),
  total_cpu_budget=2+len(occupied),common_finite_capacity=cap,peer_state=state)
def memory_budget(host,daemon,peer,own_guest=None):
 views=[host,daemon]
 if own_guest is not None:views.append(own_guest)
 def usage(v,limit):
  leaf=v["ancestors"][0]
  need(leaf["limit"]==limit and 0<=leaf["used"]<=limit,"actual guest leaf exact memory limit/current")
  return leaf["used"]
 raw_used=usage(own_guest,RAW_GUEST)if own_guest else 0
 raw_remaining=RAW_GUEST-raw_used
 state=peer["state"];peer_slots(peer)
 charges=[(host,RAW_HOST),(daemon,raw_remaining+RAW_RESERVE)]
 peer_used=0;peer_guest=0;peer_host=0;peer_reserve=0
 if state=="running":
  ph=peer["peer_host_memory"];pg=peer["peer_guest_memory"];views.extend([ph,pg])
  peer_used=usage(pg,64*GIB);peer_guest=64*GIB;peer_host=RAW_HOST;peer_reserve=RAW_RESERVE
  charges.extend([(ph,peer_host),(pg,peer_guest-peer_used),(daemon,peer_reserve)])
 elif state=="stopped-retained":
  peer_host=RAW_HOST;peer_reserve=RAW_RESERVE
  charges.append((daemon,peer_host+peer_reserve))
 totals={};samples={}
 for v,n in charges:
  for r in v["ancestors"]:totals[r["key"]]=totals.get(r["key"],0)+n
 for v in views:
  for r in v["ancestors"]:
   need(type(r["used"])is int and r["used"]>=0 and (r["limit"]is None or positive(r["limit"])),"actual cgroup memory row")
   samples.setdefault(r["key"],[]).append(r)
 for key,total in totals.items():
  for r in samples[key]:
   need(r["limit"]is None or r["limit"]-r["used"]>=total,"QUEUE_RAW: joint cgroup ordinary memory headroom")
 ceiling=RAW_GUEST+RAW_HOST+RAW_RESERVE+peer_guest+peer_host+peer_reserve
 return dict(raw_guest_limit_bytes=RAW_GUEST,raw_host_limit_bytes=RAW_HOST,raw_reserve_bytes=RAW_RESERVE,
  peer_guest_limit_bytes=peer_guest,peer_host_limit_bytes=peer_host,peer_reserve_bytes=peer_reserve,
  raw_guest_current_bytes=raw_used,peer_guest_current_bytes=peer_used,
  ordinary_undrawn_floor_bytes=ceiling-peer_used-raw_used,full_declared_ceiling_bytes=ceiling,
  ancestor_charges_bytes=totals,HugeTLB_additive=False,residency_not_charged_twice=True,peer_state=state)
def admit(x):
 need(type(x)is dict and x["schema"]==SCHEMA,"actual raw joint resource record")
 a=allocate(x["host_cpu"],x["daemon_cpu"],x["peer"],fixed_guest=x.get("fixed_guest_cpu"))
 b=memory_budget(x["host_memory"],x["daemon_memory"],x["peer"],x.get("own_guest_memory"))
 need(x["memory"]["SwapTotal"]==x["memory"]["SwapFree"],"QUEUE_RAW: active swap unsupported")
 need(x["memory"]["MemAvailable"]>=b["ordinary_undrawn_floor_bytes"],"QUEUE_RAW: joint ordinary RAM")
 # Immutable existing raw input is not charged as new allocation. The running
 # peer's entire future320GiB is conservative, not double snapshot subtraction.
 future_peer=320*GIB if x["peer"]["state"]=="running"else 0
 need(x["disk_free_bytes"]>=WORKSPACE+future_peer+RAW_RESERVE,"QUEUE_RAW: joint new workspace + peer future + reserve")
 need(0<=x["output_bytes"]<=WORKSPACE and x["output_allowance_bytes"]==WORKSPACE,"original raw packet32GiB cap")
 need(x["cpu_allocation"]==a and x["joint_memory"]==b,"independent joint budget reconstruction")
 need(x["aggregate_rss_kib"]==x["host_peak_rss_kib"]+x["child_peak_rss_kib"]
  and 0<=x["aggregate_rss_kib"]<=RAW_HOST//1024,"own host+CLI512MiB")
 need(x["engine_NCPU"]>=a["total_cpu_budget"],"engine CPU inventory contradicts joint budget")
 return a
def own_allocation(a):
 # Original whole.consume compares pre/post raw allocations. Only the actual
 # raw-owned cpuset is invariant; independently replayed peer commitments may
 # decrease after exact stop. This does not discard the joint resource record.
 return {k:a[k]for k in("host_cpu","guest_cpus","host_cpu_budget","guest_cpu_budget","reserve_cpu_budget")}
def memory_view(H,pid):
 before=H.frozen().process_identity(pid);version,group,mount,chain=H.hierarchy(pid,"memory");rows=[]
 for p in chain:
  if version==1:
   lt=(p/"memory.limit_in_bytes").read_text().strip();ut=(p/"memory.usage_in_bytes").read_text().strip()
   limit=int(lt);limit=None if limit>=2**60 else limit
  else:
   lp=p/"memory.max";up=p/"memory.current"
   need((lp.is_file()and up.is_file())or p==Path(mount),"actual memory ancestor files")
   lt=lp.read_text().strip()if lp.is_file()else"max";ut=up.read_text().strip()if up.is_file()else"0"
   limit=None if lt=="max"else int(lt)
  need(int(ut)>=0 and (limit is None or positive(limit)),"actual memory values")
  rows.append(dict(key=str(p),limit=limit,used=int(ut),limit_text=lt,usage_text=ut))
 need(H.frozen().process_identity(pid)==before,"memory PID/start/cgroup drift")
 return dict(process=before,version=version,group=group,mount=mount,ancestors=rows)
def profile_source(c,plan,reviewed):
 need(type(plan)is dict,"exact resource plan")
 if plan=={"mode":"standalone"}:return None
 need(set(plan)=={"mode","profile","source","owned","resources"}and plan["mode"]=="reviewed-peer","exact reviewed peer plan")
 need(reviewed is not None,"QUEUE_RAW: MISSING_CURRENT_REVIEWED_PEER_PROFILE")
 need(plan["profile"]==reviewed,"reviewed peer profile must match this SHA-bound adapter MF")
 keys={"schema","source","resources_source","host_source","owner","phase","guest_memory_bytes","guest_CPU","total_CPU","guest_future_workspace_bytes"}
 need(type(reviewed)is dict and set(reviewed)==keys and reviewed["schema"]=="kivi.reviewed-skvq-peer-profile/v1"
  and reviewed["phase"]=="tp4-capture"and reviewed["guest_memory_bytes"]==64*GIB and reviewed["guest_CPU"]==4
  and reviewed["total_CPU"]==7 and reviewed["guest_future_workspace_bytes"]==320*GIB,"reviewed peer capability structure")
 need(type(reviewed["owner"])is str and re.fullmatch("skvq-current72h-preprojection-v1-[0-9]{3}",reviewed["owner"]),
  "reviewed exact SKVQ owner label")
 need(plan["source"]==reviewed["source"],"exact reviewed source Ref, not caller provider")
 source=c.obj(plan["source"])
 need(source["schema"]=="skvq.current72h.preprojection.sources/v1"and source["default_enabled"]is False,"actual reviewed SKVQ source schema")
 for r in source["files"]+source["dependencies"]:c.checked(r)
 rows=[r for r in source["files"]if Path(r["path"]).name=="resources.py"]
 need(len(rows)==1 and rows[0]==reviewed["resources_source"],"exact source-bound resources module SHA/bytes/path")
 rows=[r for r in source["files"]if Path(r["path"]).name=="MAIN_HOST.py"]
 need(len(rows)==1 and rows[0]==reviewed["host_source"],"exact source-bound peer host validator SHA/bytes/path")
 return source
def peer_inspect_value(c,owned,rs,profile,raw):
 need(raw["exit_code"]==0 and raw["requested_argv"]==["/usr/bin/docker","inspect",owned["cid"]],"fresh exact peer inspect")
 xs=json.loads(raw["stdout"]);need(len(xs)==1,"one exact peer CID");x=xs[0]
 cfg=x["Config"];hc=x["HostConfig"];st=x["State"]
 # Replay the actual reviewed peer's complete inspect validator, not a second
 # relaxed controller. It is a pure method: no imports, commands, or devices.
 hr=c.checked(profile["host_source"]);p=Path(hr["path"]);tree=ast.parse(p.read_bytes())
 cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=="Control")
 fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=="validate")
 ns=dict(require=need,IMAGE=c.IMAGE,OWNER=profile["owner"],GIB=GIB)
 exec(compile(ast.Module(body=[fn],type_ignores=[]),str(p),"exec"),ns)
 # Control.mounts creates tuples in memory; its JSON OWNED publication contains
 # arrays. Restore ONLY that source-supported container representation before
 # calling the same validator, retaining the original artifact unchanged.
 e=dict(owned);e["mounts"]={}
 for dst,value in owned["mounts"].items():
  need(type(dst)is str and type(value)in(list,tuple)and len(value)==2
   and type(value[0])is str and type(value[1])is bool,"exact original owned mount pair")
  e["mounts"][dst]=(value[0],value[1])
 ns["validate"](None,x,e)
 need(x["Id"]==owned["cid"]and x["Name"]=="/"+owned["name"]and x["Image"]==c.IMAGE
  and cfg["Labels"].get("model-tuning-lab.owner")==profile["owner"]
  and cfg["Labels"].get("model-tuning-lab.source")==profile["source"]["sha256"],"peer exact CID/source/name/image")
 need(owned["source"]==profile["source"]["sha256"]and owned["phase"]=="tp4-capture"and owned["npu"]is True
  and owned["mem"]==64*GIB,"source-bound actual peer capability")
 need(hc["Memory"]==hc["MemorySwap"]==64*GIB and hc["NanoCpus"]==4*10**9
  and hc["CpusetCpus"]==owned["cpuset"]and hc["NetworkMode"]=="none"and not hc["Privileged"]
  and hc["CgroupnsMode"]=="host","actual peer declared resource config")
 devices={"/dev/davinci"+str(p):"/dev/davinci"+str(p-4)for p in range(4,8)}
 devices.update({"/dev/"+p:"/dev/"+p for p in("davinci_manager","devmm_svm","hisi_hdc")})
 need(len(hc.get("Devices")or[])==7 and {d["PathOnHost"]:d["PathInContainer"]for d in hc["Devices"]}==devices
  and all(d["CgroupPermissions"]=="rwm"for d in hc["Devices"]),"peer only4-7, never protected0-3")
 want={dst:(src,bool(rw))for dst,(src,rw)in owned["mounts"].items()}
 need(len(x["Mounts"])==len(want)and {m["Destination"]:(m["Source"],m["RW"])for m in x["Mounts"]}==want
  and all(m["Type"]=="bind"for m in x["Mounts"]),"exact peer mounts")
 for k,v in owned["env"].items():
  need(cfg["Env"].count(k+"="+v)==1 and sum(s.startswith(k+"=")for s in cfg["Env"])==1,"peer env exact")
 need(st["OOMKilled"]is False and not st.get("Restarting",False),"peer noOOM/no restart")
 if st["Running"]is True:
  need(positive(st["Pid"]),"actual running peer PID");return x,"running"
 need(st["Running"]is False and st["Pid"]==0 and not x.get("ExecIDs")and not st.get("Dead",False)
  and type(st["FinishedAt"])is str and not st["FinishedAt"].startswith("0001-"),"exact stopped-retained peer proof")
 return x,"stopped-retained"
def checked_peer(c,plan,inspect_fn,H,reviewed=None):
 source=profile_source(c,plan,reviewed)
 if source is None:return dict(state="standalone",plan=plan)
 owned=c.obj(plan["owned"]);rs=c.obj(plan["resources"])
 need(owned["resource_ref"]==plan["resources"],"exact actual peer resource Ref")
 row=reviewed["resources_source"]
 R=c.module(row["path"],row["sha256"],"_kivi_raw_peer_original_resources")
 need(R.allocate(rs["host_cpu"],rs["daemon_cpu"])==rs["allocation"],"actual peer frozen allocator")
 raw,ir=inspect_fn(owned["cid"]);x,state=peer_inspect_value(c,owned,rs,reviewed,raw)
 peer=dict(state=state,plan=plan,owned=owned,inspect=ir,peer_allocation=rs["allocation"])
 if state=="running":
  hp=rs["host_cpu"]["process"];ph=H.cpu_view(hp["pid"]);pg=H.cpu_view(x["State"]["Pid"])
  need(ph["process"]==hp and owned["cid"]in pg["process"]["cgroup"],"peer PID/start/namespace source ownership")
  need(pg["effective_capacity"]==4 and pg["effective_cpus"]==rs["allocation"]["guest_cpus"],"fresh peer actual CPU4")
  peer.update(peer_host_cpu=ph,peer_guest_cpu=pg,peer_host_memory=memory_view(H,hp["pid"]),peer_guest_memory=memory_view(H,x["State"]["Pid"]))
 # No access to peer Pid0 or its possibly exited/reused host PID in stopped state.
 return peer
def inventory(call):
 argv=["/usr/bin/docker","ps","--no-trunc","-q"]
 before,br=call("raw-joint-running-before",argv);need(before["exit_code"]==0,"actual running inventory")
 ids=before["stdout"].split()
 need(len(ids)<=32 and len(set(ids))==len(ids)and all(re.fullmatch("[0-9a-f]{64}",q)for q in ids),"bounded exact running CIDs")
 xs=[];ir=None
 if ids:
  raw,ir=call("raw-joint-running-inspect",["/usr/bin/docker","inspect",*ids])
  need(raw["exit_code"]==0,"actual bounded inventory inspect");xs=json.loads(raw["stdout"])
  need(len(xs)==len(ids)and {x["Id"]for x in xs}==set(ids),"exact inventory inspect IDs")
 after,ar=call("raw-joint-running-after",argv)
 need(after["exit_code"]==0 and set(after["stdout"].split())==set(ids),"QUEUE_RAW: running inventory changed during admission")
 return dict(before=br,after=ar,inspect=ir,values=xs)
def inventory_admit(inv,a,peer,own_cid,cpus):
 known={own_cid}if own_cid else set()
 if peer["state"]=="running":known.add(peer["owned"]["cid"])
 for x in inv["values"]:
  need(x["State"]["Running"]is True and positive(x["State"]["Pid"])and not x["State"]["OOMKilled"],"actual running inventory state")
  if x["Id"]in known:continue
  hc=x["HostConfig"];owner=(x["Config"].get("Labels")or{}).get("model-tuning-lab.owner","")
  need(not owner.startswith(("skvq-","kivi-")),
   "QUEUE_RAW: unaccounted MAIN resource lease requires reviewed current profile")
  # Docker Devices is an access declaration, NOT evidence of NPU use. An empty
  # CpusetCpus inherits eligible CPUs; even a nonempty cpuset is eligibility,
  # NOT a reservation. NanoCpus/CpuQuota/Memory are limits, not continuously
  # occupied resources. Do not turn an external shell/sleep declaration into a
  # full-host commitment or require foreign containers/device leases to vanish.
  # Foreign current residency is already in fresh MemAvailable/ancestor.used;
  # every own+reviewed MAIN declared commitment remains in admit(). This grants
  # no external-idle/exclusive-CPU claim and never stops a foreign process.
  cs=hc.get("CpusetCpus","")
  need(type(cs)is str,"actual external eligible cpuset type")
  if cs:cpus(cs) # validate the original field; do not charge its cardinality
  for key in("NanoCpus","Memory","CpuPeriod"):
   v=hc.get(key,0);need(type(v)is int and v>=0,"actual external resource limit type")
  q=hc.get("CpuQuota",0)
  need(type(q)is int and q>=-1,"actual external CPU quota type")
 return True
def consume_inventory(ctx,value,allocation,peer,own_cid):
 before=ctx.c.obj(value["before"]);after=ctx.c.obj(value["after"])
 argv=["/usr/bin/docker","ps","--no-trunc","-q"]
 need(before["exit_code"]==after["exit_code"]==0 and before["requested_argv"]==after["requested_argv"]==argv,
  "original actual running inventory receipts")
 ids=before["stdout"].split()
 need(len(ids)<=32 and len(set(ids))==len(ids)and all(re.fullmatch("[0-9a-f]{64}",q)for q in ids)
  and set(after["stdout"].split())==set(ids),"independent stable bounded inventory")
 if ids:
  raw=ctx.c.obj(value["inspect"]);xs=json.loads(raw["stdout"])
  need(raw["exit_code"]==0 and raw["requested_argv"]==["/usr/bin/docker","inspect",*ids]
   and len(xs)==len(ids)and {x["Id"]for x in xs}==set(ids)and value["values"]==xs,"independent exact inventory")
 else:need(value["inspect"]is None and value["values"]==[],"actual empty inventory, not invented inspect")
 h=ctx.c.module(ctx.c.H8,ctx.c.DEPS[str(ctx.c.H8)],"_kivi_raw_inventory_cpus")
 return inventory_admit(value,allocation,peer,own_cid,h.cpus)
def cleanup_without_device_idle(S):
 # Reuse actual source method and remove ONLY the stage-inapplicable idle loop.
 p=Path(inspect.getfile(S.Controller));need(hashlib.sha256(p.read_bytes()).hexdigest()==SAFETY_SHA,"original safety source")
 tree=ast.parse(p.read_bytes());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=="Controller")
 fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=="cleanup")
 removed=[]
 class Narrow(ast.NodeTransformer):
  def visit_For(self,node):
   if isinstance(node.target,ast.Name)and node.target.id=="card"and isinstance(node.iter,ast.Name)and node.iter.id=="PHYSICAL":
    need(len(node.body)==1 and ast.unparse(node.body[0])=="self.h.idle_one(raw['stdout'], card)","unique original CPU-inapplicable idle loop")
    removed.append(node);return ast.copy_location(ast.Pass(),node)
   return self.generic_visit(node)
 fn=Narrow().visit(fn);need(len(removed)==1,"exact one idle-only cleanup difference")
 namespace=dict(S.__dict__);exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(p),"exec"),namespace)
 return namespace["cleanup"]
def install(S,plan,*,opt_in=False,reviewed_profile=None):
 need(opt_in is True,"CPU raw adapter default OFF")
 need(not getattr(S,"_raw_cpu_joint_installed",False),"one source-bound stage adapter")
 cleanup=cleanup_without_device_idle(S);original=S.Controller;c=S.c;H=S.H
 class CPUOnly(original):
  def create(self,refs,sources,model,arm):
   need(arm=="cpu-preflight","adapter cannot create device stage")
   v=super().create(refs,sources,model,arm)
   x,_=self.inspect();mv=memory_view(H,x["State"]["Pid"])
   need(mv["ancestors"][0]["limit"]==RAW_GUEST,"actual raw CPU8 leaf")
   return v
  def resources(self,initial=False):
   def peer_inspect(cid):return self.call("joint-peer-inspect",["/usr/bin/docker","inspect",cid])
   peer=checked_peer(c,plan,peer_inspect,H,reviewed_profile)
   host=H.cpu_view(os.getpid());daemon=H.daemon_view()
   fields={l.split(":")[0]:int(l.split()[1])*1024 for l in Path("/proc/meminfo").read_text().splitlines()
    if l.startswith(("MemAvailable:","SwapTotal:","SwapFree:","Hugetlb:"))}
   scan,used=c.output_scan(self.out.parent);scan_ref=c.write(self.out/("OUTPUT-SCAN-%d.json"%time.time_ns()),scan)
   x=dict(schema=SCHEMA,observed_epoch=time.time(),peer=peer,host_cpu=host,daemon_cpu=daemon,
    host_memory=memory_view(H,os.getpid()),daemon_memory=memory_view(H,daemon["process"]["pid"]),
    memory=fields,disk_free_bytes=shutil.disk_usage(self.out.parent).free,output_bytes=used,
    output_allowance_bytes=WORKSPACE,actual_output_scan_ref=scan_ref,**self.rss())
   if self.cpu is not None:x["fixed_guest_cpu"]=self.cpu["guest_cpus"][0]
   if self.cid:
    own,own_ref=self.inspect();need(own["State"]["Running"]and not own["State"]["OOMKilled"],"own CPU live/noOOM")
    pg=H.cpu_view(own["State"]["Pid"])
    need(pg["effective_capacity"]==1 and pg["effective_cpus"]==self.cpu["guest_cpus"]
     and self.cid in pg["process"]["cgroup"],"actual own CPU1/cpuset/CID")
    x["own_inspect"]=own_ref;x["own_guest_cpu"]=pg;x["own_guest_memory"]=memory_view(H,own["State"]["Pid"])
    need(stamp(pg["process"])==stamp(x["own_guest_memory"]["process"]),"own CPU/memory namespace identity")
   self.last_joint_resource_ref=c.write(self.out/("JOINT-CPU-RAW-INPUT-%d.json"%time.time_ns()),x)
   x["cpu_allocation"]=allocate(host,daemon,peer,fixed_guest=x.get("fixed_guest_cpu"))
   x["joint_memory"]=memory_budget(x["host_memory"],x["daemon_memory"],peer,x.get("own_guest_memory"))
   er,eref=self.call("engine",["/usr/bin/docker","info","--format","{{json .}}"])
   x["engine"]=eref;x["engine_NCPU"]=json.loads(er["stdout"])["NCPU"]
   x["running_inventory"]=inventory(self.call)
   detail=c.write(self.out/("JOINT-CPU-RAW-%d.json"%time.time_ns()),x);self.last_joint_resource_ref=detail
   allocation=admit(x);inventory_admit(x["running_inventory"],allocation,peer,self.cid,H.cpus)
   if peer["state"]=="running":
    need(peer["owned"]["cid"]in {v["Id"]for v in x["running_inventory"]["values"]},"QUEUE_RAW: peer finished during snapshot; fresh re-evaluation required")
   if self.cpu is None:self.cpu=allocation
   # Peer release changes total commitments, not this actual running raw cpuset.
   need(self.cpu["host_cpu"]==allocation["host_cpu"]and self.cpu["guest_cpus"]==allocation["guest_cpus"],
    "raw own CPU allocation changed")
   need(os.sched_getaffinity(0)=={allocation["host_cpu"]},"actual raw host affinity must equal admitted CPU")
   return x
  def observe(self,label,initial=False,cleanup=False):
   need(not cleanup,"cleanup uses exact inherited safety-only lane")
   raw,sr=self.call("smi",[S.SMI,"info"]);protect=self.h.protected(raw["stdout"])
   if self.protected is None:self.protected=protect
   record=dict(label=label,npu_smi=raw["stdout"],smi=sr,protected0_3=protect,observed_utc=raw["observed_utc"],
    protected_boundary=S.protected_boundary(self.protected,protect,[self.cid]if self.cid else[],[os.getpid()]),
    resources=self.resources(initial),CPU_only=True,Devices=[],device_lease_required=False)
   r=c.write(self.out/("observation-%d.json"%time.time_ns()),record);self.observations.append(r);return r
  def cleanup(self):
   if self.expected is not None:need(self.expected["arm"]=="cpu-preflight","no device stage cleanup override")
   return cleanup(self)
 S.Controller=CPUOnly;S._raw_cpu_joint_installed=True
 return CPUOnly

def consume_cleanup(ctx,r,owned,host_pid):
 need(owned["arm"]=="cpu-preflight","independent CPU-only cleanup scope")
 ctx.s["validate_inspect"] # original exact Devices[] config is mandatory
 # Execute original whole cleanup predicate with only its four-card idle loop
 # removed. All original exact source/create/stop/Pid0/noExec/OOM/error predicates
 # and protected-boundary replay are unchanged.
 p=ctx._joint_base_whole/"consume_whole.py";b=p.read_bytes()
 need(hashlib.sha256(b).hexdigest()=="f695b5caadb3bb2ed58acb97449254509a5a98273c679e1c7b79ffcb0dfd8ddc","frozen original whole cleanup source")
 tree=ast.parse(b);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=="Context")
 fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=="cleanup");removed=[]
 class Narrow(ast.NodeTransformer):
  def visit_For(self,node):
   if isinstance(node.target,ast.Name)and node.target.id=="p"and isinstance(node.iter,ast.Tuple):
    if [getattr(n,"value",None)for n in node.iter.elts]==[4,5,6,7]:
     need(len(node.body)==1 and ast.unparse(node.body[0])=="self.h.idle_one(release['stdout'], p)","unique whole idle loop")
     removed.append(node);return ast.copy_location(ast.Pass(),node)
   return self.generic_visit(node)
 fn=Narrow().visit(fn);need(len(removed)==1,"exact one whole CPU-only idle difference")
 namespace=dict(ctx.__class__.cleanup.__globals__)
 exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(p),"exec"),namespace)
 return namespace["cleanup"](ctx,r,owned,host_pid)
def consume_observation(ctx,r,owned,host_pid,whole_root,initial=False):
 x=ctx.c.obj(r);smi=ctx.c.obj(x["smi"])
 need(x["CPU_only"]is True and x["Devices"]==[]and x["device_lease_required"]is False,"actual no-device raw observation")
 need(smi["exit_code"]==0 and smi["requested_argv"]==["/usr/local/sbin/npu-smi","info"]
  and x["npu_smi"]==smi["stdout"]and x["observed_utc"]==smi["observed_utc"],"original protected SMI receipt")
 pb=x["protected_boundary"]
 need(pb["observed"]==x["protected0_3"]and pb==ctx.boundary(pb["baseline"],pb["observed"],[owned["cid"]],[host_pid]),
  "original protected0-3 replay")
 v=x["resources"];peer=v["peer"];plan=peer["plan"]
 need(plan==ctx._joint_peer_plan,"same actual resource plan throughout raw phase")
 source=profile_source(ctx.c,plan,ctx._joint_reviewed_profile)
 if source is None:
  need(peer==dict(state="standalone",plan=plan),"standalone cannot claim an unverified peer release")
 else:
  profile=ctx._joint_reviewed_profile;po=ctx.c.obj(plan["owned"]);rs=ctx.c.obj(plan["resources"])
  need(po["resource_ref"]==plan["resources"]and peer["owned"]==po,"exact actual peer OWNED/resources")
  raw=ctx.c.obj(peer["inspect"]);px,state=peer_inspect_value(ctx.c,po,rs,profile,raw)
  need(peer["state"]==state,"independent exact running/stopped state")
  row=profile["resources_source"]
  R=ctx.c.module(row["path"],row["sha256"],"_raw_whole_peer_resources")
  need(R.allocate(rs["host_cpu"],rs["daemon_cpu"])==peer["peer_allocation"],"independent peer7 allocation")
  old=getattr(ctx,"_raw_previous_peer_state",None)
  need(not(old=="stopped-retained"and state=="running"),"released peer cannot restart/reuse same lease")
  ctx._raw_previous_peer_state=state
  if state=="running":
   need(peer["peer_host_cpu"]["process"]==rs["host_cpu"]["process"]
    and peer["peer_guest_cpu"]["process"]["pid"]==px["State"]["Pid"]
    and po["cid"]in peer["peer_guest_cpu"]["process"]["cgroup"],"peer actual PID/start/CID")
   for cpu,mem in((peer["peer_host_cpu"],peer["peer_host_memory"]),(peer["peer_guest_cpu"],peer["peer_guest_memory"])):
    need(stamp(cpu["process"])==stamp(mem["process"]),"same peer actual CPU/memory identity")
  else:
   need(set(peer)=={"state","plan","owned","inspect","peer_allocation"},"no stale/dead peer PID views on released branch")
 for cpu,mem in((v["host_cpu"],v["host_memory"]),(v["daemon_cpu"],v["daemon_memory"])):
  need(stamp(cpu["process"])==stamp(mem["process"]),"same raw actual CPU/memory identity")
 need(v["host_cpu"]["process"]["pid"]==host_pid,"raw original host PID")
 if not initial:
  ox=ctx.inspect(v["own_inspect"],owned);pc=v["own_guest_cpu"]
  need(ox["State"]["Running"]and not ox["State"]["OOMKilled"]
   and pc["process"]["pid"]==v["own_guest_memory"]["process"]["pid"]==ox["State"]["Pid"]
   and owned["cid"]in pc["process"]["cgroup"]and stamp(pc["process"])==stamp(v["own_guest_memory"]["process"])
   and pc["effective_capacity"]==1 and pc["effective_cpus"]==owned["guest_cpus"],"actual raw Devices[] live CPU1 namespace")
 engine=ctx.c.obj(v["engine"])
 need(engine["exit_code"]==0 and engine["requested_argv"]==["/usr/bin/docker","info","--format","{{json .}}"]
  and json.loads(engine["stdout"])["NCPU"]==v["engine_NCPU"],"original CPU engine inventory")
 used=ctx.scanner.consume(ctx.c.obj(v["actual_output_scan_ref"]),Path(whole_root))
 need(v["output_bytes"]==used,"original strict whole32GiB scan")
 allocation=admit(v)
 consume_inventory(ctx,v["running_inventory"],allocation,peer,owned["cid"]if not initial else None)
 if peer["state"]=="running":
  need(peer["owned"]["cid"]in {q["Id"]for q in v["running_inventory"]["values"]},"original peer stayed running within snapshot")
 return own_allocation(allocation)
