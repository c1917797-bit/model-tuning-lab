"""NEW v2 numerical/source contracts. No MAIN execution authority is self-issued."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib, importlib.util, json, math, re, sys
from pathlib import Path
from finite_contract import FINITE_SCOPE

ROOT = Path("/opt/host/vnf/austinov/model-tuning-lab")
PROJECT = ROOT / "projects/kvbuffer-parallel-ascend"
BASE = PROJECT / "tools/split_gate_v2"
OPERATOR = PROJECT / "operator/native_order_v2"
NAMESPACE = "qwen36_kvbuffer_native_order_v2"
IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
OLD_PACKET = PROJECT / "tools/split_dispatch_v1/PACKET.json"
OLD_PACKET_SHA = "eb2fd0cae186db8b73749255bc8f1ceba5ef1d57f67e2a557126b8bbb37517a9"
OLD_CONTRACT = PROJECT / "tools/split_gate_v1/contract.py"
OLD_CONTRACT_SHA = "32dd50050a28de0038aa847f55068e58efba98be07d15229b2e1f36eef4ae880"
OLD_BRIDGE = PROJECT / "tools/split_service_authority_v1/validator.py"
OLD_BRIDGE_SHA = "25ff2746b0d1c537a1728c244009799c22431c7d5d1910698780ffad76b741fc"
CGROUP_BYTES = 8 * 1024**3
OWN = ("oracle.py","finite_contract.py","test_finite_contract.py",
       "contract.py","run.py","meta_probe.py","test_source_contract.py","READY.md")
FINITE_BUFFERS = frozenset(("state.base","state.k_log","state.u_log","state.lambda_log",
                           "state.decay","state.length","actual_all","expected_active",
                           "logical_complete","native_state_all"))

def require(ok, why):
    if not ok: raise ValueError(why)

def sha(path):
    p=Path(path)
    require(p.is_file() and not p.is_symlink(), "ordinary exact source/evidence file")
    return hashlib.sha256(p.read_bytes()).hexdigest()

def ref(value):
    require(type(value) is dict and set(value)=={"path","sha256"}, "exact Ref")
    require(type(value["path"]) is str and Path(value["path"]).is_absolute() and
            ".." not in Path(value["path"]).parts and
            re.fullmatch("[0-9a-f]{64}",value["sha256"]) is not None, "absolute SHA-bound Ref")
    return value

def read_ref(value):
    value=ref(value);require(sha(value["path"])==value["sha256"],"Ref bytes drift")
    return Path(value["path"]).read_bytes()

def import_frozen(path,wanted,name):
    require(sha(path)==wanted,"frozen helper drift")
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod)
    return mod

def legacy():
    return import_frozen(OLD_CONTRACT,OLD_CONTRACT_SHA,"_kvbp_v2_legacy_contract")

def source_admission(manifest_ref):
    m=json.loads(read_ref(manifest_ref))
    require(m.get("schema")=="kvbp.split-native-sources/v2" and m.get("default_enabled") is False
            and m.get("npu_executed") is False and set(m.get("files",{}))==set(OWN),
            "NEW exact source-only manifest")
    require(m.get("namespace")==NAMESPACE and m.get("original_packet")==
            {"path":str(OLD_PACKET),"sha256":OLD_PACKET_SHA}, "explicit successor identity")
    packet=json.loads(read_ref(m["original_packet"]))
    frozen={str(OLD_PACKET.parent/n):h for n,h in packet["sources"].items()}
    frozen.update(packet["frozen_dependencies"])
    require(len(frozen)==49 and m.get("frozen_dependencies")==frozen,"old49 closure unchanged")
    actual={str(BASE/n):sha(BASE/n) for n in OWN}
    require(actual=={str(BASE/n):h for n,h in m["files"].items()},"NEW driver source drift")
    for p,h in frozen.items():require(sha(p)==h,"old frozen source drift: "+p)
    expected=m.get("operator_sources")
    require(type(expected) is dict and len(expected)==7 and
            set(expected)=={"CMakeLists.txt","op_extension/ops.h","op_extension/register.cpp",
                            "op_extension/qwen36_gdn_kvbuffer_native_order_v2_torch.cpp",
                            "op_kernel/qwen36_gdn_kvbuffer_native_order_v2.h",
                            "op_kernel/qwen36_gdn_kvbuffer_native_order_v2_kernel.asc",
                            "op_kernel/qwen36_gdn_kvbuffer_native_order_v2_tiling.h"},
            "new seven-source queued ASC closure")
    for p,h in expected.items():
        require(sha(OPERATOR/p)==h,"new numerical operator source drift")
    return m, {**frozen,**actual,**{str(OPERATOR/p):h for p,h in expected.items()}}

def protocol(batch,physical):
    p=legacy().protocol(batch,physical)
    return {**p,"finite_scope":FINITE_SCOPE,"candidate_namespace":NAMESPACE}

def validate_identity(identity,batch,physical,manifest_ref,manifest,sources,artifact_refs,now=None):
    p=protocol(batch,physical)
    require(identity.get("schema")=="kvbp.split-launch-identity/v2" and
            identity.get("image_id")==IMAGE and identity.get("protocol")==p,"new MAIN identity/protocol")
    require(identity.get("physical_devices")==[physical] and
            identity.get("logical_to_physical")=={"0":physical} and
            all(identity.get(k) is True for k in ("fresh_idle_verified","nonprivileged","source_canary_passed")),
            "MAIN fresh actual canary/mapping, not logical0 inference")
    require(identity.get("memory_cgroup_bytes")==CGROUP_BYTES and
            identity.get("source_manifest")==manifest_ref and identity.get("sources")==sources and
            identity.get("artifact_refs")==artifact_refs,"actual immutable sources/artifact Refs")
    require(type(identity.get("evidence")) is dict and identity["evidence"],
            "MAIN original proof/inspect/resource Refs required")
    for r in identity["evidence"].values():read_ref(r)
    now=now or datetime.now(timezone.utc)
    t=datetime.fromisoformat(identity["preflight_utc"].replace("Z","+00:00"))
    require(t.tzinfo is not None and 0<=(now-t).total_seconds()<=600,"fresh <=600s MAIN preflight")
    return p

def build_artifact_identity(build_ref,library_ref,manifest):
    for r in (build_ref,library_ref):read_ref(r)
    b=json.loads(read_ref(build_ref))
    require(b.get("status")=="compiled_no_device" and b.get("npu_executed") is False and
            b.get("image_id")==IMAGE and b.get("namespace")==NAMESPACE and
            b.get("sources")==manifest["operator_sources"] and b.get("npu_arch")=="dav-2201" and
            b.get("library_sha256")==library_ref["sha256"] and
            type(b.get("commands")) is list and b["commands"] and
            all(c.get("exit_code")==0 for c in b["commands"]),"actual new compile/link receipt")
    k=b.get("exported_kernel",{})
    require(k.get("defined") is True and k.get("name")=="qwen36_gdn_kvbuffer_native_order_v2_kernel"
            and k.get("type") in ("T","W"),"real non-UND ASC host launcher")
    return b

def artifacts(refs,manifest):
    require(type(refs) is dict and set(refs)=={"build","meta","library"},"three actual NEW artifact Refs")
    build_artifact_identity(refs["build"],refs["library"],manifest)
    m=json.loads(read_ref(refs["meta"]))
    require(m.get("status")=="pass" and m.get("npu_executed") is False and
            m.get("namespace")==NAMESPACE and m.get("library_sha256")==refs["library"]["sha256"]
            and m.get("build_receipt_sha256")==refs["build"]["sha256"] and
            [v["T"] for v in m["meta"]]==[1,16] and
            all(v.get("nonalias") is True and v.get("prepare_return_none") is True and
                v.get("shape")==[v["T"],12,128] and v.get("dtype")=="torch.bfloat16"
                and v.get("device")=="meta" for v in m["meta"]),
            "actual new load/Meta, not NPU proof")
    require(type(m.get("schema")) is str and m["schema"].startswith(NAMESPACE+"::decode("),
            "actual operator schema, not a forged old schema")
    require(m.get("source_manifest")==refs_manifest(m) and
            m.get("sources_before")==m.get("sources_after") and
            m.get("no_davinci_devices_observed") is True and
            m.get("native_bootstrap_verified") is False and
            m.get("loaded_candidate_sha256")==refs["library"]["sha256"],
            "no-device actual mapped candidate/source closure")
    return {"artifacts":refs,"meta_schema":m["schema"],"meta_is_not_npu_proof":True}

def refs_manifest(meta):
    source_ref=ref(meta.get("source_manifest"))
    _,actual=source_admission(source_ref)
    require(actual==meta.get("sources_before"),"Meta sources bind real current manifest")
    return source_ref

def validate_cases(report,batch):
    require(report.get("schema")=="kvbp.split-native-gate/v2" and
            report.get("status")=="single_batch_kernel_native_eager_graph_pass" and
            report.get("finite_scope")==FINITE_SCOPE and report.get("candidate_namespace")==NAMESPACE
            and "error" not in report,"NEW complete report only; old v1 cannot be promoted")
    bridge=import_frozen(OLD_BRIDGE,OLD_BRIDGE_SHA,"_kvbp_v2_case_validator")
    steps=bridge.validate_cases(report,batch) # same original limits/raw160/slots/logs/flush/replay protocol
    for case in report["cases"]:
        for row in case["steps"]:
            active=row["active"]
            require(row.get("finite_scope")==FINITE_SCOPE and
                    row.get("native_expected_defined_rows")==active and
                    row.get("native_expected_undefined_padding_rows")==batch-active and
                    row.get("native_padding_values_rewritten") is False,"exact native output domain")
            checks=row.get("finite_buffer_checks")
            require(type(checks) is dict and set(checks)==FINITE_BUFFERS and
                    all(v is True for v in checks.values()),"all candidate/state/native-state finite gate")
    return {"changing_feedback_steps":steps,"batch":batch,"numerical_report_checked":True,
            "operation_authority_verified":False,"serving_ready":False,"other_batches_verified":False,
            "matched_e2e_verified":False,"task_accuracy_verified":False}
