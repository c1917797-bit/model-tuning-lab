"""DEFAULT-OFF fixed declarations -> real post-assignment -> native ingress.
No controller, model/numerical/lease authority. No worker class monkeypatch.
"""
import hashlib
import inspect
import json
import os
from pathlib import Path

FLAG="QWEN36_KIVI_ACTUAL_INGRESS_BINDING"
ORACLE_SHA="f288191487869fe752fea8713742bff2e6245c30d9ed790243b8868520f0e333"
CAPTURE_SHA="1cfb4c995917c5d89868102e6bd8b4c6d68fe1f59881186be6e7831ff0ccaec5"
SCHED_SHA="44230b995721a011dbe2c1d012371b1d9ec844b1b09abfc24dd0c6d8a9e307fc"
NPU_SHA="94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968"
PROFILE={"endpoint":"/v1/completions","prompt_count":1,"n":1,"beam_search":False,"streaming_input":False}
PREFIX=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit")

def need(v,m):
    if not v:raise ValueError(m)
def bytes_read(ref,maximum=2*1024**2):
    need(type(ref) is dict and set(ref)=={"path","bytes","sha256"},"exact bounded original3Ref")
    p=Path(ref["path"])
    need(p.is_absolute() and p.is_file() and not p.is_symlink() and p.resolve()==p
         and type(ref["bytes"]) is int and 0<ref["bytes"]<=maximum
         and type(ref["sha256"]) is str and len(ref["sha256"])==64,"regular bounded actual Ref")
    before=p.stat();wire=p.read_bytes();after=p.stat()
    need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==
         (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)
         and len(wire)==ref["bytes"] and hashlib.sha256(wire).hexdigest()==ref["sha256"],
         "actual stable complete bytes/SHA")
    return wire
def ref_read(ref,maximum=2*1024**2):return json.loads(bytes_read(ref,maximum))
def source_pin(obj,digest):
    p=Path(inspect.getfile(inspect.unwrap(getattr(obj,"__func__",obj))))
    need(p.is_absolute() and p.resolve()==p and not p.is_symlink()
         and hashlib.sha256(p.read_bytes()).hexdigest()==digest,"real frozen source callable/type")
def actual_ref(p):
    b=p.read_bytes()
    return {"path":str(p),"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest()}
def identity_valid(x):
    need(type(x) is dict and set(x)=={"pid","start_ticks","cgroup"}
         and type(x["pid"]) is int and x["pid"]>0
         and type(x["start_ticks"]) is int and x["start_ticks"]>0
         and type(x["cgroup"]) is str and x["cgroup"],"actual namespace PID/start/cgroup")
def declaration(plan,oracle):
    need(plan["schema"]=="kivi.declared-model-ingress-plan/v1" and plan["profile"]==PROFILE
         and plan["declared_randomization_off"] is True and plan["model_ready"] is False
         and plan["run_authority"] is False,"declaration is NOT observed assignment/admission")
    need(type(plan["rows"]) is list and 0<len(plan["rows"])<=64,"bounded real input declarations")
    # These are immutable JSON provenance/qualification receipts, not invented data.
    for key in ("input_producer_ref","tokenizer_ref","model_binding_ref"):ref_read(plan[key])
    expected={}
    for row in plan["rows"]:
        need(type(row["header_request_id"]) is str and row["header_request_id"]
             and row["body_request_id"] is None,"explicit single header ID, no precedence ambiguity")
        server=oracle.expected_server_id(row["header_request_id"],None);passed=server+"-0"
        need(row["declared_server_id"]==server and row["declared_passed_id"]==passed and passed not in expected,
             "source-qualified declaration only, not SSE-derived or randomized ID")
        prompt=ref_read(row["prompt_token_ids_ref"])
        need(type(prompt) is list and 0<len(prompt)<=32768 and
             all(type(x) is int and 0<=x<2**31 for x in prompt),"actual complete token input, no fill")
        expected[passed]={"server":server,"prompt":prompt,"prompt_ref":row["prompt_token_ids_ref"]}
    return expected

def bound_owners(frontend_ref,ranks_ref):
    frontend=ref_read(frontend_ref);identity_valid(frontend)
    owner=ref_read(ranks_ref);cid=owner["container_id"]
    need(type(cid) is str and len(cid)==64 and all(c in "0123456789abcdef" for c in cid)
         and owner["frontend_binding_ref"]==frontend_ref and cid in frontend["cgroup"]
         and set(owner["rank_bindings"])=={"0","1","2","3"},"actual owner whole all4/frontend binding")
    ids=[]
    for ident in owner["rank_bindings"].values():
        identity_valid(ident);need(cid in ident["cgroup"],"every worker same exact owner CID")
        ids.append((ident["pid"],ident["start_ticks"]))
    need(len(set(ids))==4 and (frontend["pid"],frontend["start_ticks"]) not in ids,
         "four distinct actual workers, not frontend/startup substitutes")
    ref_read(owner["external_owner_authority_ref"])
    return frontend,owner

class Bindings:
    def __init__(self,plan,plan_ref,frontend_binding_ref,rank_bindings_ref,root,oracle):
        source_pin(oracle.validate_assignment,ORACLE_SHA)
        need(ref_read(plan_ref)==plan,"immutable whole real-input declaration")
        self.plan_ref=plan_ref;self.expected=declaration(plan,oracle);self.oracle=oracle
        self.frontend,self.owner=bound_owners(frontend_binding_ref,rank_bindings_ref)
        self.frontend_binding_ref=frontend_binding_ref;self.rank_bindings_ref=rank_bindings_ref
        self.root=Path(root)
        need(self.root.is_absolute() and self.root.resolve()==self.root and not self.root.is_symlink()
             and self.root.is_dir() and PREFIX in self.root.parents,"already-owned RW sink, never create/launch")
        self.seen=set()
    def path(self,passed):
        need(passed in self.expected,"only declared client")
        return self.root/("KIVI-ACTUAL-ASSIGN-"+hashlib.sha256(passed.encode()).hexdigest()+".json")
    def matches_install_owner(self,owner,rank,ident):
        need(type(rank) is int and rank in range(4) and ident==self.owner["rank_bindings"][str(rank)]
             and owner["rank_bindings"]==self.owner["rank_bindings"]
             and owner["container_id"]==self.owner["container_id"]
             and owner["declared_ingress_plan_ref"]==self.plan_ref
             and owner["actual_frontend_binding_ref"]==self.frontend_binding_ref
             and owner["actual_rank_bindings_ref"]==self.rank_bindings_ref
             and owner["declared_passed_request_ids"]==list(self.expected)
             and owner["prompt_lengths"]=={r:len(x["prompt"]) for r,x in self.expected.items()},
             "same immutable declarations + independently consumed actual owner, NOT future assigned IDs")
        return True
    def emit(self,publish,kind,event):
        need(kind=="assignment" and event["identity"]==self.frontend,"actual post-original assign callback")
        expected=self.expected.get(event["before_request_id"]);need(expected is not None,"unplanned real assign")
        passed,assigned=self.oracle.validate_assignment(expected["server"],PROFILE,event)
        need(event["disable_request_id_randomization"] is True and assigned==passed,
             "ACTUAL observed randomization OFF, not declaration")
        path=self.path(passed);ref=publish(path,event) # original exclusive atomic Path publisher
        need(ref==actual_ref(path) and ref_read(ref)==event,"whole original assignment Ref retained")
        return ref
    def check_new(self,scheduler,worker_identity,rank,publish):
        """Before real original _update_states. No scheduler/cache mutation or retry."""
        need(type(rank) is int and rank in range(4)
             and worker_identity==self.owner["rank_bindings"][str(rank)] and callable(publish),
             "actual owner-qualified rank/worker, not a supplied startup label")
        need(type(scheduler).__module__=="vllm.v1.core.sched.output"
             and type(scheduler).__name__=="SchedulerOutput","real deployed SchedulerOutput")
        source_pin(type(scheduler),SCHED_SHA)
        need(not scheduler.scheduled_spec_decode_tokens and not scheduler.preempted_req_ids
             and not scheduler.scheduled_cached_reqs.resumed_req_ids
             and set(scheduler.scheduled_cached_reqs.req_ids)<=self.seen,"no unseen cached owner/spec/resume")
        rows=[];incoming=[]
        for request in scheduler.scheduled_new_reqs:
            need(type(request).__module__=="vllm.v1.core.sched.output"
                 and type(request).__name__=="NewRequestData","real deployed NewRequestData")
            source_pin(type(request),SCHED_SHA)
            rid=request.req_id
            need(rid in self.expected and rid not in self.seen and rid not in incoming
                 and request.num_computed_tokens==0 and request.prompt_embeds is None
                 and request.lora_request is None and not request.mm_features
                 and request.pooling_params is None,"new actual token-input owner once, no ABA/recompute")
            incoming.append(rid);ref=actual_ref(self.path(rid));event=ref_read(ref)
            need(event["identity"]==self.frontend,"actual frontend owner unchanged")
            passed,assigned=self.oracle.validate_assignment(self.expected[rid]["server"],PROFILE,event)
            need(event["disable_request_id_randomization"] is True and assigned==passed==rid,
                 "actual assignment, NOT server/SSE ID guessing")
            tokens=request.prompt_token_ids
            need(type(tokens) is list and all(type(x) is int for x in tokens)
                 and tokens==self.expected[rid]["prompt"],"actual full native prompt equals original legitimate input")
            body={"schema":"kivi.actual-native-ingress/v1","rank":rank,"identity":dict(worker_identity),
                "req_id":rid,"prompt_token_ids":list(tokens),"scheduled_type":"SchedulerOutput/NewRequestData",
                "scheduled_source_sha256":SCHED_SHA,"runner_source_sha256":NPU_SHA,
                "actual_assignment_ref":ref,"frontend_binding_ref":self.frontend_binding_ref,
                "rank_bindings_ref":self.rank_bindings_ref,"plan_ref":self.plan_ref,
                "prompt_token_ids_ref":self.expected[rid]["prompt_ref"],
                "model_ready":False,"run_authority":False}
            row_ref=publish("KIVI-INGRESS-r%d-%s"%(rank,hashlib.sha256(rid.encode()).hexdigest()),body)
            need(ref_read(row_ref)==body,"complete original actual NewRequestData snapshot before native update")
            rows.append(row_ref)
        self.seen.update(incoming)
        return rows

class Verifier:
    """Independent raw consumer; does NOT call candidate check_new or use its seen state."""
    def __init__(self,oracle):
        source_pin(oracle.validate_assignment,ORACLE_SHA);self.oracle=oracle;self.plans={};self.contexts={}
    def __call__(self,row_refs,owner,rank,ident,already_seen):
        plan_ref=owner["declared_ingress_plan_ref"];key=json.dumps(plan_ref,sort_keys=True)
        if key not in self.plans:self.plans[key]=declaration(ref_read(plan_ref),self.oracle)
        expected=self.plans[key]
        owner_key=json.dumps([owner["actual_frontend_binding_ref"],owner["actual_rank_bindings_ref"]],sort_keys=True)
        if owner_key not in self.contexts:
            self.contexts[owner_key]=bound_owners(owner["actual_frontend_binding_ref"],owner["actual_rank_bindings_ref"])
        frontend,bound=self.contexts[owner_key]
        need(owner["rank_bindings"]==bound["rank_bindings"] and owner["container_id"]==bound["container_id"]
             and ident==bound["rank_bindings"][str(rank)]
             and owner["declared_passed_request_ids"]==list(expected)
             and owner["prompt_lengths"]=={r:len(x["prompt"]) for r,x in expected.items()},
             "independent actual owner/input declaration binding")
        need(type(row_refs) is list and len(row_refs)<=16,"bounded actual native new rows")
        current=set()
        for ref in row_refs:
            row=ref_read(ref);rid=row["req_id"]
            need(row["schema"]=="kivi.actual-native-ingress/v1" and row["rank"]==rank and row["identity"]==ident
                 and row["scheduled_type"]=="SchedulerOutput/NewRequestData"
                 and row["scheduled_source_sha256"]==SCHED_SHA and row["runner_source_sha256"]==NPU_SHA,
                 "actual whole source-bound native ingress origin")
            need(rid in expected and rid not in already_seen and rid not in current
                 and row["plan_ref"]==plan_ref and row["frontend_binding_ref"]==owner["actual_frontend_binding_ref"]
                 and row["rank_bindings_ref"]==owner["actual_rank_bindings_ref"]
                 and row["prompt_token_ids_ref"]==expected[rid]["prompt_ref"],"unique exact original ingress Refs")
            event=ref_read(row["actual_assignment_ref"])
            need(event["identity"]==frontend,"independent frontend actual owner")
            passed,assigned=self.oracle.validate_assignment(expected[rid]["server"],PROFILE,event)
            need(event["disable_request_id_randomization"] is True and passed==assigned==rid,
                 "independent actual assigned mapping, not declared/SSE prediction")
            need(type(row["prompt_token_ids"]) is list
                 and all(type(x) is int for x in row["prompt_token_ids"])
                 and row["prompt_token_ids"]==expected[rid]["prompt"],"independent full native/prompt bytes equality")
            current.add(rid)
        return current

def install_frontend(input_processor_cls,capture,bindings,publish):
    if os.environ.get(FLAG)!="1":return None
    source_pin(capture.install_assignment,CAPTURE_SHA)
    need(capture.process_identity()==bindings.frontend and callable(publish),"actual owner frontend before first request")
    original=capture.install_assignment(input_processor_cls,lambda kind,event:bindings.emit(publish,kind,event))
    current=input_processor_cls.assign_request_id
    def restore():
        need(input_processor_cls.assign_request_id is current,"only exact own frontend tap restore")
        input_processor_cls.assign_request_id=staticmethod(original)
    return restore
