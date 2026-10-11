"""Complete116 stdlib regressions; installed source audit or explicit local-only review."""
import argparse,hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import common as C
def audit_local(expected):
    row=C.reference(HERE/"SOURCE_MANIFEST.json")
    C.need(row["sha256"]==expected,"local declared manifest whole bytes")
    m=C.bound(row);C.need(m["root"]==C.ROOT.as_posix()and m["default_enabled"]is False,"local metadata; not installed authority")
    seen=set()
    for r in m["files"]:
        name=Path(r["path"]).name;C.need(name not in seen and Path(r["path"]).parent==C.ROOT,"unique declared own file")
        p=HERE/name;value=C.reference(p)
        C.need(value["bytes"]==r["bytes"]and value["sha256"]==r["sha256"],"actual all own file bytes")
        if name.endswith(".py"):compile(p.read_bytes(),str(p),"exec")
        seen.add(name)
    C.need(len(seen)==m["own_file_count"],"actual complete local own count")
    return row
def main():
    p=argparse.ArgumentParser();p.add_argument("--source-manifest-sha256",required=True)
    p.add_argument("--local-review",action="store_true");a=p.parse_args()
    source=audit_local(a.source_manifest_sha256)if a.local_review else C.source(a.source_manifest_sha256)
    bundle=json.loads((HERE/"author_sources.json").read_bytes())
    for r in bundle["files"]:
        raw=r["text"].encode();C.need(len(raw)==r["bytes"]and hashlib.sha256(raw).hexdigest()==r["sha256"],"all6 original author bytes")
        if r["name"].endswith(".py"):compile(raw,r["name"],"exec")
    import test_default,test_cpu_host,test_module_snapshots,test_rebind,test_control_ast,test_dependency_overlay,test_dependency_integration
    for module,count in ((test_default,23),(test_cpu_host,12),(test_module_snapshots,8),(test_rebind,10),(test_control_ast,18),(test_dependency_overlay,29),(test_dependency_integration,16)):
        C.need(module.main()==0,"complete actual "+str(count)+" "+module.__name__+" regressions")
    C.need("torch"not in sys.modules and"torch_npu"not in sys.modules,"software no framework")
    after=audit_local(a.source_manifest_sha256)if a.local_review else C.source(a.source_manifest_sha256)
    C.need(after==source,"immutable complete current source")
    print(json.dumps(dict(status="LOCAL_SOFTWARE_ONLY"if a.local_review else"SOFTWARE_ONLY",source_ref=source,
      tests=116,local_review_only=a.local_review,installed_full_dependency_closure_verified=not a.local_review,
      actual_derived_full_raw_whole_consumed=False,actual_fitting_executed=False,native_ready=False,model_ready=False)))
if __name__=="__main__":main()
