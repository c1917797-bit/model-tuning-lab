"""Original full TRAIN producer with the same explicit source-bound CPU dependency."""
import argparse,json,runpy,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import current_contract as C
import input_dependency as D
def main():
    p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true");p.add_argument("--source-manifest-sha256")
    p.add_argument("--dependency-ref-json");p.add_argument("--output");a=p.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,NPU_access=False,model_ready=False)));return
    C.configure(a.source_manifest_sha256);dep,r,source=D.lock()
    rr=json.loads(Path(a.dependency_ref_json).read_bytes());C.checked(rr)
    D.consume(json.loads(Path(rr["path"]).read_bytes()),source,r,dep)
    D.install(dep);builder=D.original_builder()
    C.require(a.output,"unique original-builder destination required")
    # Preserve every original builder function, seed, sampler, input/domain
    # policy and original builder_ref. Only dependency initialization is added.
    sys.path.insert(0,str(D.BASE))
    sys.argv=[str(D.BASE/"build_inputs.py"),"--execute","--output",a.output]
    runpy.run_path(str(D.BASE/"build_inputs.py"),run_name="__main__")
if __name__=="__main__":main()
