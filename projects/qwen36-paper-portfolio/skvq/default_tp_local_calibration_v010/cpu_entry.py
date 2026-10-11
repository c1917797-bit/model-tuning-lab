"""DEFAULT OFF: one Devices[] CPU workload, not an owned host/controller.
MAIN alone mounts one existing unique stage root RW; all sources/raw capture RO.
Author function/oracle implementations are executed in their original fresh children.
"""
import argparse,json,os,subprocess,sys,time,traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import common as C
def plans(source,whole_ref_json,stage,feature_mode):
    base=[sys.executable,"-I","-B"]
    shared=["--execute","--source-manifest-sha256",source["sha256"]]
    library=stage/"library";producer=stage/"producer";lr=stage/"LIBRARY_REF.json"
    return [
      ("LIBRARY",base+[str(HERE/"library_probe.py"),*shared,"--output",str(library)],library/"LIBRARY_PROBE.json"),
      ("PRODUCER",base+[str(HERE/"cluster_producer.py"),*shared,"--whole-ref-json",str(whole_ref_json),
        "--library-ref-json",str(lr),"--feature-mode",feature_mode,"--output",str(producer)],producer/"PRODUCER_RESULT.json"),
      ("INDEPENDENT",base+[str(HERE/"consume.py"),*shared,"--root",str(producer),
        "--whole-ref-json",str(whole_ref_json),"--output",str(producer/"INDEPENDENT.json")],producer/"INDEPENDENT.json")]
def child(label,argv,expected,stage,deadline,source):
    left=deadline-time.monotonic();C.need(left>0,"bounded CPU workload retains external90cleanup")
    timed_out=False;code=None
    try:
        r=subprocess.run(argv,capture_output=True,timeout=left);stdout=r.stdout;stderr=r.stderr;code=r.returncode
    except subprocess.TimeoutExpired as e:
        timed_out=True;stdout=e.stdout or b"";stderr=e.stderr or b""
    so=C.atomic().publish_bytes(stage/(label+".stdout"),stdout)
    se=C.atomic().publish_bytes(stage/(label+".stderr"),stderr)
    raw=C.publish(stage/(label+"_CLI.json"),dict(argv=argv,exit_code=code,timed_out=timed_out,
      stdout=so,stderr=se,source_ref=source,actual_child_completed=not timed_out))
    C.need(not timed_out and code==0,"actual fresh CPU child failed; original stdout/stderr and CLI retained")
    value=json.loads(stdout);ref=C.reference(expected)
    C.need(value==ref,"actual stdout equals sole expected actual file3Ref, no path guessing")
    return ref,raw
def run(expected,whole_ref_json,output,feature_mode):
    start=time.monotonic();source=C.source(expected);C.cpu_only()
    C.need(os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD")=="0"and
      all(os.environ.get(k)=="1"for k in("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS","NUMEXPR_NUM_THREADS")),
      "pre-import unchanged single-thread CPU environment")
    from calibration_inputs import inputs
    whole=json.loads(Path(whole_ref_json).read_bytes());inputs(whole) # fail before any fit if actual014 whole is absent/failed/partial
    stage=C.stage_root(output);C.need(not list(stage.iterdir()),"new empty actual mounted guest work leaf; no retry")
    stages=plans(source,whole_ref_json,stage,feature_mode);deadline=start+510
    primary=None;completed=[]
    try:
        for label,argv,result in stages:
            ref,raw=child(label,argv,result,stage,deadline,source);completed.append(dict(stage=label,result_ref=ref,original_cli_ref=raw))
            if label=="LIBRARY":C.publish(stage/"LIBRARY_REF.json",ref)
        final=C.bound(completed[-1]["result_ref"])
        C.need(final["status"]=="ALL4_TP_LOCAL_DEFAULT_CALIBRATION_CONSUMED"and
          final["source_ref"]==source and final["capture_whole_ref"]==whole and final["actual_rank_fits"]==128 and
          len(final["calibration_refs"])==len(final["writer_handoffs"])==64 and
          final["native_ready"]is False and final["model_ready"]is False and final["performance_ready"]is False,
          "actual all128/all64 independent calibration-only result")
    except BaseException as e:
        primary=dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc())
    result=dict(schema="skvq.default-tp-local.cpu-workload/v1",status="CALIBRATION_CPU_WORKLOAD_CONSUMED_HOST_AUTHORITY_PENDING"if primary is None else"FAILED",
      source_ref=source,capture_whole_ref=whole,completed=completed,primary=primary,total_seconds=600,
      cleanup_reserved_seconds=90,host_owned_terminal_consumer_required=True,
      author_global_grouping_equivalent=False,native_ready=False,model_ready=False,performance_ready=False,task_ready=False)
    ref=C.publish(stage/"CPU_WORKLOAD_RESULT.json",result)
    C.need(primary is None,"actual CPU workload failed; no fake host/algorithm permission")
    return ref
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--execute",action="store_true")
    ap.add_argument("--source-manifest-sha256");ap.add_argument("--whole-ref-json");ap.add_argument("--output")
    ap.add_argument("--feature-mode",choices=("original","bf16-exact-cpu32"));a=ap.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,native_ready=False,model_ready=False)));return
    C.need(a.whole_ref_json and a.output and a.feature_mode,"actual derived whole/unique mounted stage/explicit precision")
    print(json.dumps(run(a.source_manifest_sha256,a.whole_ref_json,a.output,a.feature_mode),sort_keys=True))
if __name__=="__main__":main()
