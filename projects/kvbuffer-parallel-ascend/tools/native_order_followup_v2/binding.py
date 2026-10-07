"""NEW v2 follow-up binding. Stdlib source audit is not execution authority."""
from __future__ import annotations
import hashlib,importlib.util,json,math,re,sys
from pathlib import Path
ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab")
PROJECT=ROOT/"projects/kvbuffer-parallel-ascend"
BASE=PROJECT/"tools/native_order_followup_v2"
GATE=PROJECT/"tools/split_gate_v2"
NS="qwen36_kvbuffer_native_order_v2"
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
PEER="lgw_a6109c51076a4a2c9d2674ca5a8704a0"
GROUPS={4:(2,14,15),5:(7,11,13),6:(3,4,9,12),7:(5,6,8,10)}
OWN=("binding.py","middle_run.py","middle_meta.py","consumer.py","test_followup.py","READY.md")
NATIVE_SO="/vllm-workspace/vllm-ascend/vllm_ascend/vllm_ascend_C.cpython-312-aarch64-linux-gnu.so"
NATIVE_SHA="eaa9457a21a45e2cb027c1345ee670b59d10fcd6f4a8be8b0b1bf2fde1d2232a"
FALSE_SCOPE=("serving_ready","model_lifecycle_verified","matched_e2e_verified",
             "task_accuracy_verified","formal_performance_authorized","graph_service_validated")
PREFIX="MAIN_KVBUFFER_NATIVE_ORDER_V2_CHILD "
GIB=1024**3
def require(ok,why):
    if not ok:raise ValueError(why)
def digest(data):return hashlib.sha256(data).hexdigest()
def canonical(x):return json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
def clean(data):
    def bad(x):raise ValueError("nonfinite JSON: "+x)
    x=json.loads(data,parse_constant=bad)
    def walk(v):
        if isinstance(v,float):require(math.isfinite(v),"nonfinite JSON metric")
        elif isinstance(v,dict):
            for y in v.values():walk(y)
        elif isinstance(v,list):
            for y in v:walk(y)
    walk(x);return x
def read_file(path):
    p=Path(path);require(p.is_absolute() and ".." not in p.parts and p.is_file()
                       and not p.is_symlink(),"ordinary absolute source/evidence")
    return p.read_bytes()
def ref(x):
    require(type(x) is dict and set(x)=={"path","sha256"} and type(x["path"]) is str
            and Path(x["path"]).is_absolute() and ".." not in Path(x["path"]).parts
            and type(x["sha256"]) is str and re.fullmatch("[0-9a-f]{64}",x["sha256"]),
            "exact absolute SHA-bound Ref")
    return x
def raw(r,read=read_file):
    ref(r);data=read(r["path"]);require(type(data) is bytes and digest(data)==r["sha256"],"Ref byte drift")
    return data
def obj(r,read=read_file):return clean(raw(r,read))
def actual_ref(path):return {"path":str(path),"sha256":digest(read_file(str(path)))}
def write_new(path,value):
    with Path(path).open("xb") as f:f.write(canonical(value)+b"\n")
def module(path,wanted,name,read=read_file):
    data=read(str(path));require(digest(data)==wanted,"imported frozen source drift")
    def runtime_modules():
        return {key:value for key,value in sys.modules.items()
                if key in ("torch","torch_npu") or key.startswith(("torch.","torch_npu."))}
    runtime_before=runtime_modules()
    m=type(sys)(name);m.__file__=str(path);sys.modules[name]=m
    exec(compile(data,str(path),"exec"),m.__dict__)
    require(runtime_modules()==runtime_before,
            "source module must not introduce, remove or replace runtime modules")
    return m
def sources(packet_ref,read=read_file):
    require(ref(packet_ref)["path"]==str(BASE/"SOURCE_MANIFEST.json"),"canonical NEW source manifest")
    p=obj(packet_ref,read)
    require(p.get("schema")=="kvbp.native-order-followup-sources/v2" and
            p.get("default_enabled") is False and set(p.get("files",{}))==set(OWN),
            "NEW exact six sources/default OFF")
    own={str(BASE/n):h for n,h in p["files"].items()}
    for path,h in own.items():require(digest(read(path))==h,"NEW source drift")
    gr=ref(p["v2_gate_manifest"]);require(gr["path"]==str(GATE/"SOURCE_MANIFEST.json"),"actual v2 manifest path")
    gm=obj(gr,read)
    require(gm.get("schema")=="kvbp.split-native-sources/v2" and gm.get("namespace")==NS
            and gm.get("default_enabled") is False and gm.get("npu_executed") is False,
            "actual successor source-only manifest")
    original=obj(gm["original_packet"],read)
    old={str(Path(gm["original_packet"]["path"]).parent/n):h for n,h in original["sources"].items()}
    old.update(original["frozen_dependencies"])
    require(len(old)==49 and old==gm["frozen_dependencies"],"original49 never rewritten")
    pins={**old,**{str(GATE/n):h for n,h in gm["files"].items()},
          **{str(PROJECT/"operator/native_order_v2"/n):h for n,h in gm["operator_sources"].items()}}
    require(len(pins)==64 and len(gm["files"])==8 and len(gm["operator_sources"])==7,"actual v2 source64")
    for path,h in pins.items():require(digest(read(path))==h,"frozen source64 drift")
    old_bridge=PROJECT/"tools/middle_service_bridge_v1/PACKET.json"
    br=ref(p["old_consumer_packet"]);require(br["path"]==str(old_bridge),"reviewed old consumer closure")
    bm=obj(br,read)
    require(bm.get("schema")=="kvbp.middle-service-bridge-sources/v1" and len(bm["dependencies"])==60
            and bm["default_enabled"] is False,"old consumer60 source-only evidence")
    for n,h in bm["sources"].items():
        require(digest(read(str(old_bridge.parent/n)))==h,"old consumer source drift")
    for path,h in bm["dependencies"].items():
        require(digest(read(path))==h,"old consumer dependency drift")
    finite=module(GATE/"finite_contract.py",gm["files"]["finite_contract.py"],"_kv_v2_followup_finite",read)
    bridge=module(PROJECT/"tools/split_service_authority_v1/validator.py",
                  old[str(PROJECT/"tools/split_service_authority_v1/validator.py")],
                  "_kv_v2_followup_original_case_checks",read)
    legacy=module(PROJECT/"tools/split_gate_v1/contract.py",
                  old[str(PROJECT/"tools/split_gate_v1/contract.py")],
                  "_kv_v2_followup_native_pins",read)
    gm["_ref"]=gr
    return p,gm,pins,own,finite,bridge,legacy
def protocol(batches,physical):
    require(type(physical) is int and tuple(batches)==GROUPS.get(physical),"exact balanced true-T group")
    return dict(batches=list(batches),physical_device=physical,logical_device=0,
        slots={str(t):t+3 for t in batches},eager_trials=1,graph_trials=3,
        steps_per_case=160,feedback=True,output_limit=.00303,complete_and_per_head_l2_limit=2e-6,
        graph_active_schedule={str(t):[t] for t in batches},real_token_batches_only=True,
        reset_steps=[64,112],required_flushes=True,retry="none",
        scope="intermediate-kernel-only-not-model-E2E-or-task-accuracy",candidate_namespace=NS)
def split_protocol(batch,card,finite,legacy):
    return {**legacy.protocol(batch,card),"finite_scope":finite.FINITE_SCOPE,"candidate_namespace":NS}
def validate_batch(cases,batch,finite,bridge):
    # Only the original pure case checker is reused. No v1 status/schema/PASS is manufactured.
    steps=bridge.validate_cases({"cases":cases},batch)
    names={"state.base","state.k_log","state.u_log","state.lambda_log","state.decay","state.length",
           "actual_all","expected_active","logical_complete","native_state_all"}
    for case in cases:
        for row in case["steps"]:
            require(row.get("finite_scope")==finite.FINITE_SCOPE
                    and row.get("native_expected_defined_rows")==row["active"]
                    and row.get("native_expected_undefined_padding_rows")==batch-row["active"]
                    and row.get("native_padding_values_rewritten") is False,
                    "native defined output ABI, no padding rewrite")
            checks=row.get("finite_buffer_checks")
            require(type(checks) is dict and set(checks)==names and all(v is True for v in checks.values()),
                    "complete v2 candidate/full-state/native-state finite checks")
    return steps
def artifacts(refs,gm,pins,read=read_file):
    require(type(refs) is dict and set(refs)=={"build","meta","library"},"actual three artifact Refs")
    for r in refs.values():raw(r,read)
    build=obj(refs["build"],read);meta=obj(refs["meta"],read)
    require(build.get("status")=="compiled_no_device" and build.get("npu_executed") is False
            and build.get("image_id")==IMAGE and build.get("namespace")==NS
            and build.get("sources")==gm["operator_sources"] and build.get("npu_arch")=="dav-2201"
            and build.get("library_sha256")==refs["library"]["sha256"]
            and type(build.get("commands")) is list and build["commands"]
            and all(x.get("exit_code")==0 for x in build["commands"]),"actual unchanged compiled7 receipt")
    k=build.get("exported_kernel",{})
    require(k.get("name")=="qwen36_gdn_kvbuffer_native_order_v2_kernel"
            and k.get("defined") is True and k.get("type") in ("T","W"),"real defined host launcher")
    require(meta.get("status")=="pass" and meta.get("npu_executed") is False and meta.get("namespace")==NS
            and meta.get("library_sha256")==refs["library"]["sha256"]
            and meta.get("build_receipt_sha256")==refs["build"]["sha256"]
            and meta.get("sources_before")==pins==meta.get("sources_after")
            and meta.get("source_manifest")==gm["_ref"]
            and meta.get("no_davinci_devices_observed") is True
            and meta.get("native_bootstrap_verified") is False
            and meta.get("loaded_candidate_sha256")==refs["library"]["sha256"]
            and meta.get("loaded_libraries",{}).get(refs["library"]["path"])==refs["library"]["sha256"],
            "actual refreshed no-device Meta/source64/library maps")
    require(type(meta.get("schema")) is str and meta["schema"].startswith(NS+"::decode(")
            and meta.get("prepare_schema")==NS+"::prepare(Tensor query, Tensor base_state) -> ()"
            and [x["T"] for x in meta["meta"]]==[1,16]
            and all(x.get("shape")==[x["T"],12,128] and x.get("dtype")=="torch.bfloat16"
                    and x.get("device")=="meta" and x.get("nonalias") is True
                    and x.get("prepare_return_none") is True for x in meta["meta"]),
            "actual v2 B1/B16 operator schema/nonalias Meta")
    return {"artifacts":refs,"meta_schema":meta["schema"],"meta_is_not_npu_proof":True},meta
def validate_meta14(r,artifacts_ref,gate_ref,pins,own,read=read_file):
    m=obj(r,read)
    require(m.get("status")=="actual_v2_14_positive_Meta_pass" and m.get("namespace")==NS
            and m.get("source_manifest")==gate_ref and m.get("sources_before")=={**pins,**own}==m.get("sources_after")
            and m.get("artifact_refs")==artifacts_ref and m.get("npu_executed") is False
            and m.get("no_davinci_devices_observed") is True and m.get("native_bootstrap_verified") is False
            and m.get("loaded_libraries",{}).get(artifacts_ref["library"]["path"])==artifacts_ref["library"]["sha256"]
            and m.get("library_sha256")==artifacts_ref["library"]["sha256"],"actual NEW Meta14/source70/maps")
    rows=m.get("meta")
    require(type(rows) is list and [x.get("T") for x in rows]==list(range(2,16))
            and all(x.get("shape")==[x["T"],12,128] and x.get("dtype")=="torch.bfloat16"
                    and x.get("device")=="meta" and x.get("nonalias") is True
                    and x.get("prepare_return_none") is True for x in rows),"fourteen genuine Meta/nonalias cases")
    require(all(m.get(k) is False for k in ("serving_ready","graph_proven","physical_nd_proven")),
            "Meta never numerical/graph/service")
    return m

def load_oracle(gm,read=read_file):
    path=GATE/"finite_contract.py"
    found=sys.modules.get("finite_contract")
    if found is not None:
        require(Path(found.__file__).resolve()==path
                and digest(read(str(path)))==gm["files"]["finite_contract.py"],"wrong finite helper alias")
    else:module(path,gm["files"]["finite_contract.py"],"finite_contract",read)
    return module(GATE/"oracle.py",gm["files"]["oracle.py"],"_kv_v2_followup_original_oracle",read)
def meta_inputs(torch,t):
    # Byte/AST-equivalent argument constructor from frozen v2 meta_probe.meta_inputs.
    s=t+3
    def empty(shape,dtype):return torch.empty(shape,dtype=dtype,device="meta")
    return (
      empty((t,4,128),torch.bfloat16),empty((t,4,128),torch.bfloat16),
      empty((t,12,128),torch.bfloat16),empty((t,12),torch.float32),
      empty((t,12),torch.bfloat16),empty((s,12,128,128),torch.float32),
      empty((s,4,16,128),torch.bfloat16),empty((s,12,16,128),torch.float32),
      empty((s,12,32),torch.float32),empty((s,12,32),torch.float32),
      empty((s,12,32),torch.int32),empty((t+1,),torch.int32),empty((t,),torch.int32))
