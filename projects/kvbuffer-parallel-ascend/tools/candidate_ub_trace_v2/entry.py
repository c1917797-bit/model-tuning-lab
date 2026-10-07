#!/usr/bin/env python3
"""MAIN-only saved-step UB trace entry. Default OFF; reproduction is not numerical PASS."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,os,re,sys,time
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab")
BASE=ROOT/"projects/kvbuffer-parallel-ascend/tools/candidate_ub_trace_v2"
PROJECT=BASE.parents[1]
B16=PROJECT/"tools/b16_saved_step_diagnostic_v1/replay.py"
B16_SHA="86cd69ee8c3de19ffeea91e753cc8056320e192c208741775d97bb0938530a00"
FULL=PROJECT/"tools/full_matrix_host_v2/host.py"
FULL_SHA="ab0296c698df00c9c3b2ce377601f6d6723adde6efb4a9e65407beca51ba5f86"
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
NAMESPACE="qwen36_kvbuffer_native_order_trace_v2"
SYMBOL="qwen36_gdn_kvbuffer_native_order_trace_v2_kernel"
SCHEMA=("qwen36_kvbuffer_native_order_trace_v2::decode_trace(Tensor query, Tensor key, Tensor value, "
 "Tensor g, Tensor beta, Tensor(a!) base_state, Tensor(b!) k_log, Tensor(c!) u_log, "
 "Tensor(d!) lambda_log, Tensor(e!) cumulative_decay, Tensor(f!) log_length, "
 "Tensor actual_seq_lengths, Tensor state_indices, Tensor(g!) trace_states, "
 "Tensor(h!) trace_output, Tensor(i!) trace_meta) -> Tensor")
EXPECTED_NEGATIVES=[
 (0,[1,4,128],"torch.bfloat16"),(0,[16,4,128],"torch.float32"),(1,[16,4,127],"torch.bfloat16"),
 (5,[4,12,128,128],"torch.float32"),(6,[19,4,15,128],"torch.bfloat16"),
 (8,[19,12,16],"torch.float32"),(10,[19,12,32],"torch.int64"),(11,[16],"torch.int32"),
 (12,[17],"torch.int32"),(13,[2,32,128],"torch.float32"),(14,[32],"torch.bfloat16"),(15,[17],"torch.int32")]

def require(v,why):
    if not v:raise ValueError(why)
def sha(path):
    p=Path(path);require(p.is_file() and not p.is_symlink(),"ordinary exact source/evidence")
    return hashlib.sha256(p.read_bytes()).hexdigest()
def strict_json(data):
    def pairs(items):
        d={}
        for k,v in items:
            require(k not in d,"duplicate JSON key");d[k]=v
        return d
    return json.loads(data,object_pairs_hook=pairs,
                      parse_constant=lambda x:(_ for _ in ()).throw(ValueError("nonfinite JSON")))
def checked_ref(ref):
    require(type(ref) is dict and set(ref)=={"path","sha256"} and type(ref["path"]) is str and
            Path(ref["path"]).is_absolute() and ".." not in Path(ref["path"]).parts and
            re.fullmatch("[0-9a-f]{64}",ref["sha256"]) is not None,"exact absolute Ref")
    require(sha(ref["path"])==ref["sha256"],"Ref bytes drift")
    return Path(ref["path"]).read_bytes()
def load(path,digest,name):
    require(sha(path)==digest,"source-bound module drift")
    if name in sys.modules:
        m=sys.modules[name]
        require(Path(m.__file__).resolve()==Path(path).resolve() and sha(m.__file__)==digest,
                "existing module does not match canonical source")
        return m
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def trace_artifacts(refs,operator_sources,sources77,config,*,reader=checked_ref,record_reader=None,now=None):
    """Byte-bound actual producer receipts; fixture tests cannot issue execution authority."""
    require(type(refs) is dict and set(refs)=={"library","build","meta"},"three trace artifact Refs")
    require(type(config) is dict and set(config)=={"build_root","source_manifest","namespace","schema"} and
            config["namespace"]==NAMESPACE and config["schema"]==SCHEMA,"actual source-derived v2 configuration")
    build=Path(config["build_root"])
    require(build.parent==Path("/cache/cch/qwen36-kvbuffer-parallel-20261006") and
            build.name.startswith("build-candidate-ub-trace-v2-") and ".." not in build.parts,
            "MAIN exact verified-builder OUT, not old failed v1")
    source_ref=config["source_manifest"]
    require(type(source_ref) is dict and set(source_ref)=={"path","sha256"} and
            source_ref["path"]==str(BASE/"SOURCE_MANIFEST.json") and
            re.fullmatch("[0-9a-f]{64}",source_ref["sha256"]) is not None,"actual v2 source Ref, never placeholder SHA")
    expected={"library":str(build/"build/libqwen36_gdn_kvbuffer_native_order_trace_v2_ops.so"),
              "build":str(build/"build-receipt.json"),"meta":str(build/"meta-receipt.json")}
    require({k:r["path"] for k,r in refs.items()}==expected,"exact existing trace build output")
    for r in refs.values():reader(r)
    b=strict_json(reader(refs["build"]));m=strict_json(reader(refs["meta"]))
    require(len(operator_sources)==7 and len(sources77)==77 and
            b.get("schema")=="kvbp.candidate-ub-trace-build/v2" and
            b.get("status")=="compiled_no_device" and b.get("npu_executed") is False and
            b.get("image_id")==IMAGE and b.get("namespace")==NAMESPACE and b.get("npu_arch")=="dav-2201" and
            b.get("sources")==operator_sources and b.get("sources_before")==sources77==b.get("sources_after") and
            b.get("library_sha256")==refs["library"]["sha256"],"actual seven-source/77-source compile receipt")
    start=datetime.fromisoformat(b["started_utc"]);end=datetime.fromisoformat(b["completed_utc"])
    require(start.tzinfo is not None and end.tzinfo is not None and start<=end<=(now or datetime.now(timezone.utc)),
            "actual completed compile times")
    expected_commands=[
      ["cmake","-S",str(PROJECT/"operator/candidate_ub_trace_v2"),"-B",str(build/"build"),
       "-DCMAKE_BUILD_TYPE=Release","-DPython3_EXECUTABLE=/usr/local/python3.12.13/bin/python3"],
      ["cmake","--build",str(build/"build"),"--parallel","1"]]
    cs=b.get("commands")
    require(type(cs) is list and len(cs)==2 and
            all(c.get("command")==a and type(c.get("exit_code")) is int and c["exit_code"]==0
                for c,a in zip(cs,expected_commands)),"actual two completed compile/link commands")
    k=b.get("exported_kernel",{})
    require(k=={"name":SYMBOL,"defined":True,"type":k.get("type")} and k["type"] in ("T","W"),
            "actual defined ASC launcher")
    require(m.get("schema")=="kvbp.candidate-ub-trace-meta/v2" and
            m.get("status")=="actual-load-schema-meta-only" and m.get("library")==refs["library"] and
            m.get("schema_loaded")==SCHEMA and type(m.get("positive_cases")) is int and m["positive_cases"]==2 and
            m.get("source_manifest_sha256")==source_ref["sha256"] and
            all(m.get(x) is False for x in ("npu_executed","numeric_verified","serving_ready")),
            "actual Meta proof is not current numerical success")
    ns=m.get("negative_cases")
    require(type(ns) is list and len(ns)==12 and
            [(v.get("argument"),v.get("shape"),v.get("dtype")) for v in ns]==EXPECTED_NEGATIVES and
            all(type(v.get("error")) is str and v["error"] for v in ns),"all twelve actual Meta rejections")
    maps=m.get("mapped_library_lines")
    require(type(maps) is list and maps and all(type(l) is str and "(deleted)" not in l and
            len(l.split())>=6 and l.split()[-1]==refs["library"]["path"] for l in maps),
            "actual mapped Meta library, not deleted bytes")
    evidence={}
    def auxiliary(name):
        path=build/name
        if record_reader is None:require(path.is_file() and not path.is_symlink(),"ordinary original producer record")
        raw=record_reader(path) if record_reader is not None else path.read_bytes()
        require(type(raw) is bytes,"original producer record bytes")
        evidence[name]={"path":str(path),"sha256":hashlib.sha256(raw).hexdigest()}
        return strict_json(raw)
    for i,c in enumerate(cs):
        require(auxiliary("command-%d.json"%i)==c,"actual original command record differs")
    export=auxiliary("exports.json")
    require(export.get("command")==["nm","-D","--defined-only",refs["library"]["path"]]
            and type(export.get("exit_code")) is int and export["exit_code"]==0,"actual exports command")
    matches=[line.split() for line in export.get("stdout","").splitlines()
             if line.split()[-1:]==[SYMBOL]]
    require(len(matches)==1 and matches[0][-2]==k["type"],"actual defined symbol raw output")
    child=auxiliary("original-meta-child.json")
    expected_child=["/usr/local/python3.12.13/bin/python3","-B",str(BASE/"meta_probe.py"),
      "--library",refs["library"]["path"],"--library-sha256",refs["library"]["sha256"],
      "--output",refs["meta"]["path"]]
    require(child.get("command")==expected_child and type(child.get("exit_code")) is int
            and child["exit_code"]==0,"actual completed Meta child command")
    summaries=[]
    for line in child.get("stdout","").splitlines():
        try:v=strict_json(line)
        except (ValueError,TypeError):continue
        if type(v) is dict and "meta_receipt" in v:summaries.append(v)
    require(summaries==[{"meta_receipt":refs["meta"]["path"],"meta_sha256":refs["meta"]["sha256"],
                        "negative_cases":12,"npu_executed":False}],"unique original Meta child Ref output")
    return {"trace_artifacts":refs,"trace_sources":sources77,"producer_evidence":evidence,
            "actual_build_meta_only":True,"npu_verified":False,"serving_ready":False}
def write(path,obj):
    with Path(path).open("x") as f:
        f.write(json.dumps(obj,indent=2,allow_nan=False)+"\n");f.flush();os.fsync(f.fileno())
    return {"path":str(path),"sha256":sha(path)}
def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
    p.add_argument("--script-sha256");p.add_argument("--identity",type=Path)
    for n in ("trace-library","trace-build","trace-meta"):
        p.add_argument("--"+n,type=Path);p.add_argument("--"+n+"-sha256")
    p.add_argument("--output-dir",type=Path);a=p.parse_args(argv)
    if not a.execute:
        print(json.dumps({"default_enabled":False,"npu_executed":False,"serving_ready":False,
                          "scope":"copy-only saved B16 graph0 step37 trace, never matrix PASS"}));return
    require(all(vars(a).values()),"complete MAIN explicit entry inputs")
    require(sha(__file__)==a.script_sha256,"MAIN actual entry bytes")
    require(os.environ.get("ASCEND_RT_VISIBLE_DEVICES")=="0" and
            os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD")=="0" and
            os.environ.get("PYTHONDONTWRITEBYTECODE")=="1","logical0/no-autoload/no-bytecode environment")
    b16=load(B16,B16_SHA,"_kvbp_trace_entry_b16")
    f=b16.module(FULL,FULL_SHA,"_kvbp_trace_entry_fullhost")
    c,source_ref,production_manifest,sources=f.legacy().source()
    require(source_ref=={"path":str(b16.GATE/"SOURCE_MANIFEST.json"),"sha256":b16.SOURCE_SHA}
            and len(sources)==64,"complete frozen64 identity")
    c.artifacts(f.REFS,production_manifest)
    ident=strict_json(a.identity.read_bytes())
    c.validate_identity(ident,16,6,source_ref,production_manifest,sources,f.REFS)
    require(ident.get("diagnostic_script")=={"path":str(Path(__file__).resolve()),"sha256":a.script_sha256},
            "MAIN actual explicitly admitted entry")
    trace_source_ref=c.ref(ident.get("trace_source_manifest"));checked_ref(trace_source_ref)
    require(trace_source_ref["path"]==str(BASE/"SOURCE_MANIFEST.json"),"actual new v2 manifest")
    runtime=ident.get("trace_runtime_sources")
    require(type(runtime) is dict and set(runtime)=={"protocol","builder","meta"},"three actual runtime source Refs")
    for key,name in (("protocol","protocol.py"),("builder","build_no_device.py"),("meta","meta_probe.py")):
        c.ref(runtime[key]);checked_ref(runtime[key])
        require(runtime[key]["path"]==str(BASE/name),"exact independently reviewed v2 runtime source")
    protocol=load(runtime["protocol"]["path"],runtime["protocol"]["sha256"],"protocol")
    builder=load(runtime["builder"]["path"],runtime["builder"]["sha256"],"_kvbp_trace_entry_builder_v2")
    require(protocol.NAMESPACE==NAMESPACE and protocol.SCHEMA==SCHEMA and protocol.HERE==BASE,
            "actual v2 code-object scope")
    trace_manifest,sources77=builder.manifest()
    require(sha(BASE/"SOURCE_MANIFEST.json")==trace_source_ref["sha256"],"actual builder v2 manifest identity")
    refs={k:{"path":str(path),"sha256":digest} for k,path,digest in
          (("library",a.trace_library,a.trace_library_sha256),("build",a.trace_build,a.trace_build_sha256),
           ("meta",a.trace_meta,a.trace_meta_sha256))}
    config={"build_root":str(builder.OUT),"source_manifest":trace_source_ref,
            "namespace":protocol.NAMESPACE,"schema":protocol.SCHEMA}
    admission=trace_artifacts(refs,trace_manifest["operator_sources"],sources77,config)
    require(ident.get("trace_artifact_refs")==refs,"actual MAIN identity must bind actual NEW artifacts")
    require(b16.sha(b16.RAW)==b16.RAW_SHA and b16.RAW.stat().st_size==b16.RAW_BYTES and
            sha(b16.NATIVE_HEADER)==b16.NATIVE_HEADER_SHA,"actual original raw/native-header bytes")
    require({n:sha(n) for n in c.legacy().NATIVE_PINS}==c.legacy().NATIVE_PINS,"original native source identity")
    cg=c.legacy().cgroup_limit()
    out=a.output_dir
    require(out.parent==Path("/kvbuffer-results") and not out.exists() and not out.is_symlink(),
            "fresh exclusive trace output under results RW mount")
    evidence=out.parent/(out.name+"-entry-evidence")
    require(not evidence.exists() and not evidence.is_symlink(),"exclusive entry evidence")
    evidence.mkdir()
    report={"schema":"kvbp.candidate-ub-trace-entry/v2","status":"admitted-not-device-executed",
      "created_ns":time.time_ns(),"identity_sha256":sha(a.identity),"script_sha256":a.script_sha256,
      "production_refs":f.REFS,"trace_admission":admission,"source_manifest":trace_source_ref,"trace_runtime_sources":runtime,"cgroup":cg,
      "original_raw":{"path":str(b16.RAW),"sha256":b16.RAW_SHA,"bytes":b16.RAW_BYTES},
      "npu_verified":False,"matrix_verified":False,"serving_ready":False,"native_precast_observed":False}
    serial=0;primary=None
    def save():
        nonlocal serial
        serial+=1;return write(evidence/("entry-%03d.json"%serial),report)
    save()
    try:
        import torch
        fixture=torch.load(b16.RAW,map_location="cpu",weights_only=True);b16.metadata(fixture)
        old=b16.module(b16.OLD,b16.OLD_SHA,"_kvbp_trace_entry_old_replay")
        require(all(old.bitwise(torch,fixture["inputs"][n],fixture["input_before"][n]) for n in fixture["inputs"]),
                "saved original inputs unchanged")
        report["cpu_fixture"]=b16.cpu_difference(torch,fixture);save()
        import torch_npu
        from vllm_ascend.utils import enable_custom_op
        from vllm_ascend.ops.triton.triton_utils import init_device_properties_triton
        torch_npu.npu.set_compile_mode(jit_compile=False);torch.npu.set_device(0)
        require(torch.npu.device_count()==1 and torch.npu.get_device_name(0)=="Ascend910B4","actual one910B4")
        require(enable_custom_op(),"original native bootstrap");init_device_properties_triton()
        helper=b16.module(b16.GATE/"oracle.py",production_manifest["files"]["oracle.py"],"_kvbp_trace_entry_oracle")
        helper.torch=torch;helper.torch_npu=torch_npu
        torch.ops.load_library(f.REFS["library"]["path"])
        production=getattr(torch.ops,c.NAMESPACE);helper.bind_candidate(production)
        torch.ops.load_library(refs["library"]["path"])
        trace=getattr(torch.ops,NAMESPACE)
        require(str(trace.decode_trace.default._schema)==SCHEMA==protocol.SCHEMA,"actual loaded16argument ABI")
        libraries={"production":f.REFS["library"],"trace":refs["library"],
                   "native":{"path":b16.NATIVE,"sha256":b16.NATIVE_SHA}}
        report["mapped_libraries"]=b16.mapped({r["path"]:r["sha256"] for r in libraries.values()});save()
        write(out.parent/"attribution-ready.json",{"pid":os.getpid(),"hold_seconds":12,
          "separate_canary_not_gate":True,"source_raw_sha256":b16.RAW_SHA,"candidate_matrix_verified":False})
        time.sleep(12) # bounded actual PID attribution; never performance.
        protocol.diagnostic(torch,helper,old,fixture,production,trace,out,enabled=True,
                            raw_path=b16.RAW,source_manifest_sha256=trace_source_ref["sha256"],libraries=libraries)
        report["status"]="trace-protocol-returned-diagnostic-only"
    except BaseException as e:
        primary=e;report.update(status="failed",original_error=repr(e));raise
    finally:
        report["completed_ns"]=time.time_ns()
        try:
            _,current=builder.manifest()
            require(current==sources77 and sha(__file__)==a.script_sha256 and
                    sha(B16)==B16_SHA and sha(FULL)==FULL_SHA and
                    sha(a.identity)==report["identity_sha256"] and sha(b16.RAW)==b16.RAW_SHA,"source/identity/raw drift")
            for r in (*refs.values(),*runtime.values(),trace_source_ref):checked_ref(r)
            c.artifacts(f.REFS,production_manifest)
            require(trace_artifacts(refs,trace_manifest["operator_sources"],current,config)==admission,
                    "actual trace receipts changed during diagnostic")
            print("MAIN_KVBUFFER_UB_TRACE_ENTRY "+json.dumps(save()),flush=True)
        except BaseException as secondary:
            if primary is None:raise
            try:print(json.dumps({"primary":repr(primary),"secondary_finalize":repr(secondary)}),flush=True)
            except BaseException:pass
if __name__=="__main__":main()
