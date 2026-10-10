"""Explicit spawn guard and real RPC hook receipt. No Torch/vLLM import here.
Not a controller or algorithm oracle; all original capture gates remain required.
"""
import importlib,inspect,json,multiprocessing as mp,os,sys
from pathlib import Path
import current_contract as C
ENV="VLLM_WORKER_MULTIPROC_METHOD"
THREADS=("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS")
def policy():
    C.require(os.environ.get(ENV)=="spawn","explicit spawn before native import; no fork fallback")
    C.require(all(os.environ.get(k)=="1"for k in THREADS),"unchanged single native thread budgets")
    return {k:os.environ[k]for k in (ENV,)+THREADS}
def identity():
    raw=Path("/proc/self/stat").read_text();tail=raw[raw.rfind(")")+2:].split()
    return {"pid":os.getpid(),"pid_start_ticks":int(tail[19])}
def native_context(source):
    manifest=json.loads(Path(source["path"]).read_bytes())
    rows=manifest["multiprocessing_runtime_sources"]
    row=next(x for x in rows if x["module"]=="vllm.utils.system_utils")
    C.checked(row["snapshot"])
    module=importlib.import_module(row["module"])
    spec=module.__spec__;origin=C.reference(module.__file__)
    C.require(spec is not None and spec.name==row["module"]and
      Path(spec.origin).resolve()==Path(module.__file__).resolve()and
      origin["path"]==row["runtime_path"]and
      origin["bytes"]==row["snapshot"]["bytes"]and origin["sha256"]==row["snapshot"]["sha256"],
      "original native multiprocessing module origin")
    fn=module.get_mp_context
    C.require(inspect.isfunction(fn)and fn.__module__==row["module"]and
      fn.__name__=="get_mp_context"and
      Path(inspect.getsourcefile(fn)).resolve()==Path(module.__file__).resolve()and
      Path(fn.__code__.co_filename).resolve()==Path(module.__file__).resolve(),
      "source-defined native get_mp_context, no wrapper or substitute")
    context=fn()
    C.require(context.get_start_method()=="spawn","actual native factory returns spawn")
    return {"module":row["module"],"origin":origin,"function":"get_mp_context","method":"spawn"}
def parent(source,root):
    env=policy();factory=native_context(source);pid=identity()
    record={"schema":"skvq.capture.spawn-parent/v1","source_ref":source,"identity":pid,
      "environment":env,"native_factory":factory,"before_actual_LLM_constructor":True,
      "capture_ready":False,"model_ready":False}
    return publish(Path(root)/"SPAWN_PARENT.json",record)
def publish(path,value):
    from io_contract import publish_json
    return publish_json(path,value)
def before_worker(source):
    env=policy()
    C.require(mp.get_start_method(allow_none=True)=="spawn",
      "actual worker process is spawn; no inherited fork state")
    return {"identity":identity(),"environment":env,"start_method":"spawn",
      "source_ref":source,"helper_ref":C.reference(__file__)}
def installed(w,session,source,before):
    C.require(before["source_ref"]==source and before["identity"]==identity()and
      mp.get_start_method(allow_none=True)=="spawn","same real spawn child during RPC installation")
    C.require(session.w is w and w._skvq_capture_session is session and
      session.rank()["pid"]==os.getpid(),"same actual worker owns the original session")
    patches=session.patches
    C.require(len(patches)==34 and all(obj.__dict__.get(name)is bound
      for obj,name,bound,original in patches),"all34 original instance hooks actually installed")
    C.require(sum(name=="reshape_and_cache"for _,name,_,_ in patches)==16 and
      sum(name=="forward"for _,name,_,_ in patches)==17 and
      sum(name=="capture"for _,name,_,_ in patches)==1 and len(session.linear)==48,
      "full16 cache+16 projection+model+sink hooks,48 GDN unchanged")
    C.require(session.active is None and session.next_id==0 and not session.closed and
      not session.poisoned,"actual installation before sample zero")
    record={"schema":"skvq.capture.spawn-worker-install/v1","source_ref":source,
      "rank":w.rank,"before":before,"after_identity":identity(),"start_method":"spawn",
      "instance_hooks":{"cache":16,"projection":16,"model":1,"sink":1,"total":34},
      "GDN_untouched_layers":48,"installed_before_sample_zero":True,
      "capture_ready":False,"model_ready":False}
    return publish(session.sink.path/"WORKER_SPAWN_INSTALL.json",record)
def obj(ref):
    C.checked(ref);return json.loads(Path(ref["path"]).read_bytes())
def consume_parent(ref,source):
    value=obj(ref);manifest=json.loads(Path(source["path"]).read_bytes())
    row=next(x for x in manifest["multiprocessing_runtime_sources"]
      if x["module"]=="vllm.utils.system_utils")
    C.checked(row["snapshot"])
    factory=value["native_factory"];origin=factory["origin"]
    C.require(value["schema"]=="skvq.capture.spawn-parent/v1"and value["source_ref"]==source and
      value["before_actual_LLM_constructor"]is True and value["capture_ready"]is False and
      value["model_ready"]is False,"actual source parent startup receipt")
    C.require(value["environment"]=={ENV:"spawn",**{k:"1"for k in THREADS}}and
      factory=={"module":row["module"],"origin":origin,"function":"get_mp_context","method":"spawn"}and
      origin=={"path":row["runtime_path"],"bytes":row["snapshot"]["bytes"],
        "sha256":row["snapshot"]["sha256"]},"native source-pinned spawn factory receipt")
    C.require(type(value["identity"]["pid"])is int and value["identity"]["pid"]>1 and
      type(value["identity"]["pid_start_ticks"])is int and value["identity"]["pid_start_ticks"]>0,
      "actual parent PID/start")
    return value
def consume_installs(installs,parent_ref,source):
    parent_value=consume_parent(parent_ref,source)
    C.require(type(installs)is list and len(installs)==4 and
      {r["rank"]for r in installs}==set(range(4)),"four original RPC install results")
    refs=[];seen=set()
    helper_ref=C.reference(__file__)
    for result in installs:
        ref=result["spawn_install_ref"];value=obj(ref);before=value["before"]
        rank=result["rank"];identity=result["identity"];pid=before["identity"]
        C.require(type(rank)is int and value["rank"]==rank and result["installed"]is True and
          value["schema"]=="skvq.capture.spawn-worker-install/v1"and value["source_ref"]==source and
          value["start_method"]==before["start_method"]=="spawn"and before["source_ref"]==source and
          before["helper_ref"]==helper_ref and before["environment"]==parent_value["environment"],
          "same source-qualified actual worker RPC startup and current helper")
        C.require(pid==value["after_identity"]and identity["pid"]==pid["pid"]and
          identity["pid_start_ticks"]==pid["pid_start_ticks"]and identity["public_TP_rank"]==rank and
          type(pid["pid"])is int and pid["pid"]>1 and pid["pid"]!=parent_value["identity"]["pid"]and
          type(pid["pid_start_ticks"])is int and pid["pid_start_ticks"]>0,
          "actual distinct worker PID/start/TP identity, not parent fixture")
        C.require(value["instance_hooks"]=={"cache":16,"projection":16,"model":1,"sink":1,"total":34}and
          value["GDN_untouched_layers"]==48 and value["installed_before_sample_zero"]is True and
          value["capture_ready"]is False and value["model_ready"]is False,
          "actual complete hook install evidence only; no numerical authority")
        key=(pid["pid"],pid["pid_start_ticks"]);C.require(key not in seen,"four distinct actual workers")
        seen.add(key);refs.append(ref)
    return refs
def consume_producer(value,source):
    refs=consume_installs(value["worker_install_results"],value["spawn_parent_ref"],source)
    C.require(value["worker_spawn_install_refs"]==refs,"exact complete original RPC receipt list")
    return refs
