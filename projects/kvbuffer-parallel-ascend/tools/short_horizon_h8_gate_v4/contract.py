"""H8 protocol observer only; reuses actual unchanged v3 operator build/Meta.
No old numerical PASS is fabricated. Exact eight-step flush replay with the
original output/full-state/per-head limits and complete 640-step coverage.
"""
from datetime import datetime, timezone
import importlib.util,json,sys
from pathlib import Path
ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab")
PROJECT=ROOT/"projects/kvbuffer-parallel-ascend"
BASE=PROJECT/"tools/short_horizon_h8_gate_v4"
V3=PROJECT/"tools/short_horizon_v3"
V3_REF={"path":str(V3/"SOURCE_MANIFEST.json"),"sha256":"7292ebd16430ac945fa8d9ebff842b11875643e5e09ec5cd1083e9163fca3c37"}
V3_CONTRACT_SHA="42cdee85622b9420df46133f3091df00b3b77f6f1e9a63b7847424bf28a295c0"
sys.path.insert(0,str(V3))
import hashlib
if hashlib.sha256((V3/"contract.py").read_bytes()).hexdigest()!=V3_CONTRACT_SHA:
 raise ValueError("frozen V3 contract source drift")
spec=importlib.util.spec_from_file_location("_h8_original_v3_contract",V3/"contract.py")
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
require,sha,ref,read_ref=old.require,old.sha,old.ref,old.read_ref
legacy,import_frozen=old.legacy,old.import_frozen
IMAGE,NAMESPACE,CGROUP_BYTES=old.IMAGE,old.NAMESPACE,old.CGROUP_BYTES
FINITE_SCOPE,FINITE_BUFFERS=old.FINITE_SCOPE,old.FINITE_BUFFERS
FLUSH_INTERVAL,LOG_CAPACITY=8,16
OWN=("contract.py","run.py","host_run.py","test_contract.py","READY.md")
def source_admission(manifest_ref):
 m=json.loads(read_ref(manifest_ref))
 require(m.get("schema")=="kvbp.short-horizon-h8-gate-sources/v4" and
         m.get("default_enabled") is False and m.get("npu_executed") is False and
         m.get("inherited_manifest")==V3_REF and set(m.get("files",{}))==set(OWN),
         "new complete protocol-observer/controller source identity")
 inherited,previous=old.source_admission(V3_REF)
 require(m.get("inherited_sources")==previous and
         m.get("operator_sources")==inherited["operator_sources"],
         "unchanged actual V3 operator/79-source lineage")
 own={str(BASE/n):sha(BASE/n) for n in OWN}
 require(own=={str(BASE/n):h for n,h in m["files"].items()},"new observer/controller source drift")
 return m,{**previous,**own}
def protocol(batch,physical):
 return old.protocol(batch,physical)
def artifacts(refs,manifest):
 inherited,previous=old.source_admission(V3_REF)
 require(manifest["operator_sources"]==inherited["operator_sources"],
         "build reuse limited to unchanged seven compiler inputs")
 # This is actual SO/schema/Meta evidence only, never old numerical evidence.
 return old.artifacts(refs,inherited)
def validate_identity(identity,batch,physical,manifest_ref,manifest,sources,artifact_refs,now=None):
    p=protocol(batch,physical)
    require(identity.get("schema")=="kvbp.short-horizon-launch-identity/v4" and
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

MODES=(("eager",0),("graph",0),("graph",1),("graph",2))
GUARDS=("untouched_slots_bitwise","nonflush_base_bitwise","guards","pointers",
        "input_immutable","zero_length_output_zero","finite","metric_finite")
LOGS=("k_log","u_log","lambda_log","decay","length")
import math,re
def horizon_cases(report, batch):
    cases = report["cases"]
    require(len(cases) == 4 and {(c.get("batch"), c.get("mode"), c.get("trial")) for c in cases} ==
            {(batch, mode, trial) for mode, trial in MODES}, "four unique actual mode/trial cases")
    for case in cases:
        require(case.get("status") == "passed" and "error" not in case and "pending_raw_step" not in case,
                "failed/pending raw evidence cannot be promoted")
        rows = case["steps"]
        require(len(rows) == 160 and [r["step"] for r in rows] == list(range(1,161)),
                "160 unique ordered changing feedback steps")
        lengths = [0] * (batch + 3)
        merges = 0
        for i, row in enumerate(rows):
            active = (0,1,3,7,12,15,16,16)[i % 8] if batch == 16 and case["mode"] == "graph" else batch
            reset = (i // 16) % (batch + 3) if i in (64,112) else None
            require(row.get("active") == active and row.get("reset_slot") == reset,
                    "true active schedule/reset-slot protocol")
            if reset is not None:
                lengths[reset] = 0
            for token in range(active):
                slot = (token + i) % (batch + 3)
                if lengths[slot] == FLUSH_INTERVAL-1:
                    merges += 1
                    lengths[slot] = 0
                else:
                    lengths[slot] += 1
            require(row.get("passed") is True and all(row.get(k) is True for k in GUARDS),
                    "raw per-step finite/guard/pointer/input/untouched/base gate")
            logs = row.get("all_logs_bitwise_outside_new_U")
            require(type(logs) is dict and set(logs) == set(LOGS) and
                    all(v is True for v in logs.values()), "complete log invariant gate")
            for key, limit in (("output_error", .00303), ("complete_state_l2", 2e-6),
                               ("max_per_head_l2", 2e-6)):
                value = row.get(key)
                require(type(value) in (int,float) and math.isfinite(value) and 0 <= value <= limit,
                        "frozen numerical bound: " + key)
            receipt = row["raw_step"]
            name = "raw-step-b%d-%s-t%d-step%d.pt" % (batch, case["mode"], case["trial"], i+1)
            require(receipt.get("file") == name and receipt.get("step") == i+1 and
                    receipt.get("retained") is False and type(receipt.get("bytes")) is int and
                    receipt["bytes"] > 0 and re.fullmatch("[0-9a-f]{64}", receipt.get("sha256", "")),
                    "each original raw checkpoint identity/passed cleanup")
        require(case.get("resets") == 2 and case.get("merges") == merges and merges > 0,
                "source-replayed reset/flush coverage")
        for maximum, key in (("max_output_error", "output_error"), ("max_state_l2", "complete_state_l2"),
                             ("max_head_l2", "max_per_head_l2")):
            require(case.get(maximum) == max(r[key] for r in rows), "original metric maximum mismatch")
    return 640

def validate_cases(report,batch):
 require(report.get("schema")=="kvbp.short-horizon-native-gate/v4" and
         report.get("status")=="single_batch_kernel_native_eager_graph_pass" and
         report.get("finite_scope")==FINITE_SCOPE and report.get("candidate_namespace")==NAMESPACE and
         report.get("materialization_interval")==FLUSH_INTERVAL and
         report.get("storage_log_capacity")==LOG_CAPACITY and "error" not in report,
         "new complete H8 report only")
 steps=horizon_cases(report,batch)
 for case in report["cases"]:
  for row in case["steps"]:
   active=row["active"]
   require(row.get("finite_scope")==FINITE_SCOPE and
           row.get("native_expected_defined_rows")==active and
           row.get("native_expected_undefined_padding_rows")==batch-active and
           row.get("native_padding_values_rewritten") is False,"same defined native output domain")
   checks=row.get("finite_buffer_checks")
   require(type(checks) is dict and set(checks)==FINITE_BUFFERS and
           all(v is True for v in checks.values()),"original all-buffer finite gate")
 return {"changing_feedback_steps":steps,"batch":batch,"numerical_report_checked":True,
         "operation_authority_verified":False,"serving_ready":False,
         "other_batches_verified":False,"matched_e2e_verified":False,"task_accuracy_verified":False}
