#!/usr/bin/env python3
"""Extra all-T prerequisite, then exec unchanged original diagnostic launcher."""
from __future__ import annotations
import argparse,ast,json,os,sys
from types import SimpleNamespace
from pathlib import Path
import contract as c

def flags(argv):
    require=c.require
    allowed={"--manifest","--manifest-sha256","--inputs","--inputs-sha256","--checked","--checked-sha256",
             "--identity","--identity-sha256","--arm","--output-dir","--port","--model","--library"}
    modes={"--prepare-only","--execute-diagnostic"}
    result={};i=0
    while i<len(argv):
        key=argv[i];require(key not in result,"duplicate original launch flag")
        if key in modes:result[key]=True;i+=1;continue
        require(key in allowed and i+1<len(argv),"known original launcher flag/value")
        result[key]=argv[i+1];i+=2
    require(sum(k in result for k in modes)==1,"one original prepare OR diagnostic mode")
    return result

def binding(argv,inputs,checked_ref,identity,identity_ref,packet):
    x=flags(argv)
    expected={"--manifest":inputs["split_manifest"]["path"],
              "--manifest-sha256":inputs["split_manifest"]["sha256"],
              "--inputs":inputs["split_checked"]["input_ref"]["path"],
              "--inputs-sha256":inputs["split_checked"]["input_ref"]["sha256"],
              "--checked":inputs["split_checked"]["checked"]["path"],
              "--checked-sha256":inputs["split_checked"]["checked"]["sha256"],
              "--identity":identity_ref["path"],"--identity-sha256":identity_ref["sha256"]}
    c.require(all(x.get(k)==v for k,v in expected.items()),"unchanged exact original split/identity Refs")
    c.require(identity.get("evidence",{}).get("all_T_kernel_prerequisite")==checked_ref,
              "actual fresh TP4 identity binds NEW all-T checked Ref")
    c.require(identity.get("native_gate_kind")=="split-kernel-prerequisite" and
              identity.get("formal_performance_authorized") is False and
              identity.get("diagnostic_scope")=="same-eager-P1-lifecycle-screen",
              "original diagnostic identity/labels retained, no legacy PASS rewriting")
    c.require(x.get("--arm") in ("dense","candidate") and
              x.get("--output-dir") and x.get("--port") and
              x.get("--model","/models/Qwen3.6-27B")=="/models/Qwen3.6-27B" and
              x.get("--library",str(c.RESULT/"build-p1-v1/libqwen36_gdn_kvbuffer_parallel_ops.so"))==
              str(c.RESULT/"build-p1-v1/libqwen36_gdn_kvbuffer_parallel_ops.so"),
              "unchanged real model/candidate library/arm/output/port")
    return x

def mounts(packet,old):
    path=c.SPLIT/"launch.py"
    data=c.read_file(str(path))
    c.require(c.digest(data)==packet["dependencies"][str(path)],"original launch source")
    tree=ast.parse(data,str(path))
    selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ("mount_binding","evidence_paths")]
    c.require({n.name for n in selected}=={"mount_binding","evidence_paths"},"actual two original pure mount helpers")
    # Private function globals only; do not import/rebind old launcher or generic contract.
    env={"c":old,"Path":Path}
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(path),"exec"),env)
    return SimpleNamespace(**{n.name:env[n.name] for n in selected})

def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    if "--" in argv:
        c.require(argv.count("--")==1,"sole original-argv separator")
        i=argv.index("--");outer,inner=argv[:i],argv[i+1:]
    else:outer,inner=argv,[]
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--enable",action="store_true")
    for n in ("packet","inputs","checked"):
        p.add_argument("--"+n);p.add_argument("--"+n+"-sha256")
    a=p.parse_args(outer)
    if not a.enable:
        print(json.dumps(dict(status="OFF",launches_model=False,service_ready=False)));return 0
    c.require(os.environ.get("KVBUFFER_ALL_T_DIAGNOSTIC")=="1","explicit MAIN NEW bridge diagnostic opt-in")
    c.require(all(getattr(a,n) and getattr(a,n+"_sha256") for n in ("packet","inputs","checked")) and inner,
              "reviewed NEW packet/raw inputs/checked and original argv")
    refs={n:dict(path=getattr(a,n),sha256=getattr(a,n+"_sha256")) for n in ("packet","inputs","checked")}
    inputs=c.obj(refs["inputs"]);expected=c.validate_complete(inputs,refs["packet"],enabled=True)
    expected["input_ref"]=refs["inputs"]
    c.require(c.obj(refs["checked"])==expected,"inside-image all-T raw replay, not host status")
    packet,old=c.sources(refs["packet"])
    x=flags(inner);ir=dict(path=x["--identity"],sha256=x["--identity-sha256"]);ident=c.obj(ir)
    binding(inner,inputs,refs["checked"],ident,ir,packet)
    legacy=mounts(packet,old)
    inspected=c.obj(ident["evidence"]["container_inspect"])
    c.require(type(inspected) is list and len(inspected)==1,"actual fresh TP4 inspected container")
    for path in legacy.evidence_paths([refs,inputs,expected]):
        if path.startswith(str(c.ROOT)) or path.startswith("/cache/"):
            legacy.mount_binding(inspected[0],path)
    # A new interpreter preserves the original launcher module/contract search path.
    # No torch.ops reassignment, runpy, injected PASS, or persistent state is used.
    original=c.SPLIT/"launch.py"
    command=[sys.executable,"-B",str(original),*inner]
    try:os.execv(sys.executable,command)
    except BaseException as primary:
        print("KVBP_ALL_T_EXEC_PRIMARY "+repr(primary),file=sys.stderr)
        raise
if __name__=="__main__":raise SystemExit(main())
