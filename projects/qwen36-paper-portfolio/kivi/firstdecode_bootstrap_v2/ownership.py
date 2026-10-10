"""Concrete actual frontend/rank owner handoff for the existing Owned host.
No launch, polling controller, invented PID, SMI inference, or success authority.
"""
import hashlib
import inspect
import json
import os
from pathlib import Path
import time

INPUT_SHA="c5673988c0f7cfec268220e3f044e718702c015a4f236c020937cfd40a793f15"
ASYNC_SHA="2128cf018fe136b698c5e89dc7325bc6dced9d516cc9d772695f044716970b64"
CAPTURE_SHA="1cfb4c995917c5d89868102e6bd8b4c6d68fe1f59881186be6e7831ff0ccaec5"
BINDINGS_SHA="71b5c3650eab308b86a26da62abcd249c77fc7528c4c8022bf779af56ef38f99"
ASSIGNMENT_ORACLE_SHA="f288191487869fe752fea8713742bff2e6245c30d9ed790243b8868520f0e333"
CUTOFF=1791788425

def need(v,m):
    if not v:raise ValueError(m)

def pin(fn,digest):
    p=Path(inspect.getfile(inspect.unwrap(getattr(fn,"__func__",fn))))
    need(p.is_absolute() and p.resolve()==p and not p.is_symlink()
         and hashlib.sha256(p.read_bytes()).hexdigest()==digest,"exact original callable whole SHA")

def exact_ref(path):
    p=Path(path);b=p.read_bytes()
    need(p.is_absolute() and p.resolve()==p and not p.is_symlink() and p.is_file(),"actual ordinary Ref")
    return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())

def install_frontend(input_cls,async_cls,capture,bindings_module,assignment_oracle,recipe,read,publish):
    """Called by the source-bound server launch BEFORE real AsyncLLM creation.
    Actual2128 constructor builds InputProcessor BEFORE EngineCoreClient. The
    source-pinned constructor callback therefore publishes frontend before ranks
    need the real host-bound all4 owner. Actual assignment hook is installed once;
    Bindings is constructed lazily at the first actual assignment, not fake IDs.
    """
    pin(input_cls,INPUT_SHA);pin(input_cls.__init__,INPUT_SHA)
    pin(async_cls.__init__,ASYNC_SHA);pin(capture.install_assignment,CAPTURE_SHA)
    pin(bindings_module.Bindings,BINDINGS_SHA)
    pin(assignment_oracle.validate_assignment,ASSIGNMENT_ORACLE_SHA)
    need(os.environ.get(bindings_module.FLAG)=="1","actual ingress explicit opt-in")
    original=input_cls.__init__;state={"identity":None,"restore_assignment":None,"bindings":None}
    def bound():
        if state["bindings"] is None:
            ranks_ref=exact_ref(recipe["rank_bindings_path"])
            front_ref=exact_ref(recipe["frontend_binding_path"])
            plan_ref=recipe["declared_ingress_plan_ref"]
            state["bindings"]=bindings_module.Bindings(read(plan_ref),plan_ref,front_ref,ranks_ref,
                recipe["diagnostic_root"],assignment_oracle)
        return state["bindings"]
    def initialized(instance,*args,**kwargs):
        need(type(instance)is input_cls and state["identity"] is None,"one actual frontend input processor")
        answer=original(instance,*args,**kwargs)
        ident=capture.process_identity()
        need(recipe["container_id"]in ident["cgroup"],"actual frontend in exact owned CID")
        frontend_ref=publish(Path(recipe["frontend_binding_path"]),ident)
        need(frontend_ref==exact_ref(recipe["frontend_binding_path"]),"original frontend raw identity published")
        state["identity"]=ident
        def emit(kind,event):
            need(kind=="assignment" and capture.process_identity()==ident
                 and event["identity"]==ident,"actual post-original assignment source")
            bound().emit(publish,kind,event)
        original_assignment=capture.install_assignment(input_cls,emit)
        patched=input_cls.assign_request_id
        def restore_assignment():
            need(input_cls.assign_request_id is patched,"exact own assignment hook")
            input_cls.assign_request_id=staticmethod(original_assignment)
        state["restore_assignment"]=restore_assignment
        return answer
    input_cls.__init__=initialized
    def restore():
        need(input_cls.__init__ is initialized,"exact own input constructor hook")
        input_cls.__init__=original
        if state["restore_assignment"] is not None:state["restore_assignment"]()
    return restore

def rank_request(capture,recipe,rank,source_ref,publish):
    ident=capture.identity()
    need(type(rank)is int and rank in range(4) and recipe["container_id"]in ident["cgroup"],
         "actual initialized namespace rank before native cache initialization")
    value=dict(schema="kivi.actual-rank-owner-request/v1",rank=rank,identity=ident,
               container_id=recipe["container_id"],source_ref=source_ref,run_id=recipe["run_id"],
               physical_card=rank+4,mapping_is_not_yet_verified=True,run_authority=False)
    return publish(Path(recipe["rank_request_paths"][str(rank)]),value)

def complete_host_bindings(ctl,request_refs,frontend_ref,external_authority_ref,read,publish):
    """Existing model-host startup observe calls this once all4 originals exist.
    Observe ORIGINAL known Owned ctl, and compare namespace/start/cgroup with
    actual /proc plus its SMI process proofs. Unknown/partial/live-unreadable fail.
    """
    need(len(request_refs)==4 and type(ctl.cid)is str and len(ctl.cid)==64,
         "actual owned controller and all4 originals")
    rows=[read(r)for r in request_refs];front=read(frontend_ref)
    need([r["rank"]for r in rows]==list(range(4)) and ctl.cid in front["cgroup"],
         "actual ordered all4 and frontend namespace")
    ctl.observe("kivi-real-all4-owner-bind")
    wanted=[front]+[r["identity"]for r in rows];host=[]
    for ident in wanted:
        need(type(ident)is dict and set(ident)=={"pid","start_ticks","cgroup"}
             and type(ident["pid"])is type(ident["start_ticks"])is int
             and ident["pid"]>0 and ident["start_ticks"]>0 and ctl.cid in ident["cgroup"],
             "actual exact namespace identity")
        matches=[]
        for p in Path("/proc").iterdir():
            if not p.name.isdigit():continue
            try:
                cg=(p/"cgroup").read_text()
                if ctl.cid not in cg:continue
                status=(p/"status").read_text()
                nspid=[int(x)for line in status.splitlines()if line.startswith("NSpid:")for x in line.split()[1:]]
                if not nspid or nspid[-1]!=ident["pid"]:continue
                before=(p/"stat").read_text();f=before[before.rfind(")")+2:].split()
                need(f[0]!="Z" and int(f[19])==ident["start_ticks"],"same live actual process/start")
                argv=(p/"cmdline").read_bytes()
                need(argv and argv.endswith(b"\0"),"live readable original argv")
                proof=ctl.h.gate_process(int(p.name))
                after=(p/"stat").read_text();g=after[after.rfind(")")+2:].split()
                need(g[0]!="Z" and int(g[19])==ident["start_ticks"]
                     and (p/"cgroup").read_text()==cg,"stable live source-qualified process")
                matches.append(dict(guest_identity=ident,host_pid=int(p.name),nspid=nspid,
                    stat_before=before,stat_after=after,cgroup=cg,process_proof=proof,
                    cmdline_sha256=hashlib.sha256(argv).hexdigest(),
                    physical_cards=sorted({x["physical"]for x in ctl.process_proofs if x["pid"]==int(p.name)})))
            except(FileNotFoundError,ProcessLookupError):continue
        need(len(matches)==1,"one actual namespace mapping; no unreadable/live identity exemption")
        host.append(matches[0])
    need(len({r["host_pid"]for r in host})==5,"frontend plus4 distinct actual workers")
    for rank,row in enumerate(rows):
        need(row["schema"]=="kivi.actual-rank-owner-request/v1" and row["container_id"]==ctl.cid
             and row["physical_card"]==rank+4 and host[rank+1]["physical_cards"]==[rank+4],
             "actual initialized physical4..7 mapping, no canary relabel")
    raw=publish(ctl.out/"KIVI_ALL4_NAMESPACE_RAW.json",
        dict(schema="kivi.actual-firstdecode-namespace-raw/v1",container_id=ctl.cid,
             request_refs=request_refs,frontend_ref=frontend_ref,host_processes=host,
             owned_inspect=ctl.inspect()[1],external_owner_authority_ref=external_authority_ref,
             original_consumer_required=True,run_authority=False))
    return dict(container_id=ctl.cid,frontend_binding_ref=frontend_ref,
                rank_bindings={str(row["rank"]):row["identity"]for row in rows},
                external_owner_authority_ref=external_authority_ref,actual_namespace_raw_ref=raw)

def await_ref(path,read,*,seconds=120):
    """One bounded immutable artifact wait inside old phase, not a scheduler."""
    p=Path(path);deadline=time.monotonic()+seconds
    while not p.exists():
        need(time.monotonic()<deadline and time.time()<CUTOFF,"actual owner handoff bounded/no deadline reset")
        time.sleep(.1)
    ref=exact_ref(p);return ref,read(ref)
