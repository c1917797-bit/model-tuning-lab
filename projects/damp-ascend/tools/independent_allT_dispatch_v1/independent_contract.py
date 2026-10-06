"""Stdlib source admission for NEW restricted synthetic true-T packet."""
import hashlib
import importlib.util
import json
import re
from pathlib import Path
import sys
BASE_NEW = Path(__file__).resolve().parent
REPO = BASE_NEW.parents[3]
PROJECT = REPO/"projects/damp-ascend"
DEADLINE = "2026-10-07T08:48:03Z"
MODEL_CONFIG = Path("/cache/efim/Qwen3.6-27B/config.json")
MODEL_SHA = "69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c"
OWN = ("controller.py","runner.py","reference_seam.py","independent_contract.py",
       "test_contract.py","READY.md")
REUSED = {
  "projects/damp-ascend/operator/diagnostic/run_saved_step45_trace.py": "64cc9ee98a6354d16a49fa90f9c16170d9852c080cf576fad03e3183b4eb0b9a",
  "projects/damp-ascend/operator/production_integer_compaction_v1/graph_gate_v1/graph_contract.py": "b31984a9c0a074812bd859b75316188475c445848832478974c543aa733727f6",
  "projects/damp-ascend/operator/production_integer_compaction_v1/graph_gate_v1/graph_protocol.py": "35df04f1f8453a9c68f728cce65d4d4821906204fd74502a0cf900bab4e8b4ca",
  "projects/damp-ascend/operator/production_integer_compaction_v1/tests/candidate_adapter.py": "43d4639d1ac0d737392fab8526aba14af0b1e50161a1940855b71822b18e6a7c",
  "projects/damp-ascend/operator/production_integer_compaction_v1/tests/gate_contract.py": "b49b8113b77f2318d434fbca5beedbcc23b5a186b291e479c2cf1bd428b217a0",
  "projects/damp-ascend/operator/production_integer_compaction_v1/tests/protocols.py": "7a0747c8c1a1f246f32ec3ad32ab53cd7a5027339a5c8584d5552ae1508f7340",
  "projects/damp-ascend/operator/production_integer_compaction_v1/tests/run_npu_gate.py": "9d2ff5e8eed33c5ec3719dcee2748908924c8ce7151a2e3d2b4d582d285c1c1c",
  "projects/damp-ascend/tests/all_batch_gate_v1/README.md": "1637e687a31462ff2f1ecf09b0d9201f67e22be9f740dff2edc100f22d0385df",
  "projects/damp-ascend/tests/all_batch_gate_v1/arena_adapter.py": "4da0c821392541cd881b8fa6614f126d063a882add5bd280993cced65a9ea7b5",
  "projects/damp-ascend/tests/all_batch_gate_v1/contract.py": "f42a42ce36dc18cb65381f00ac3a4737cb8b50dbf50b22bf90a719dd800d87fd",
  "projects/damp-ascend/tests/all_batch_gate_v1/metadata_contract.py": "2803105bad54bbcd0cc67e2035ea31cfd5fb8116adad278a94e62ae72271bee4",
  "projects/damp-ascend/tests/all_batch_gate_v1/run_all_batch_gate.py": "fb0fde9ec2b257692cb6e8d9e473cbbaa42e5a2804416944edcc065d2a0a3b12",
  "projects/damp-ascend/tests/all_batch_gate_v1/test_software_contract.py": "9399cd82d0b7010e72522692a3cb3969dcc07b80ab4a33cb763ffff3142096e2",
  "projects/damp-ascend/tests/general_sr_contract.py": "6606bd18e1c29d50a063ba0742b8fb7b8b8d5a8f6e12a6f4a755004d74bfc2ad",
  "projects/damp-ascend/tests/general_sr_native_gate.py": "7eed726fd46e2e39c6bdd560fb769742d32d68861efb075fbca9647f976b4155",
  "projects/damp-ascend/tests/independent_oracle.py": "fc92395d65db63810ff70341dca255f7f4455d80f0fccbe80f48ff3bb679625a",
  "projects/damp-ascend/tests/native_call_contract.py": "162dba2a653b7c1fabd20eb24bc75d99225584ca48c4bd10c89eece5bc2fc1d5",
  "projects/damp-ascend/tests/native_compressed_golden.py": "95d11c42bea88daa14dbb2ce462e16a7d1864b3f2169faf360942fb0c16bea19",
  "projects/damp-ascend/tests/restricted_native_golden_gate.py": "f8b04cc7650cf2cc330a526cb261ffd85062454e56e1a9692b5913c18445a6b4",
  "projects/damp-ascend/tests/shared_arena_gate_v1/arena_adapter.py": "bef38eaa944a2c62bc765f56df6529e9a13fbbec5b4bf803916c624baa736dd7",
  "projects/damp-ascend/tools/allT_dispatch_controller_v1/controller.py": "c44412ffbfffa5b8e1630694343044d874c87ab72e3ad76875c2e69bc6c6e1ff",
  "projects/damp-ascend/tools/allT_dispatch_controller_v1/test_controller.py": "b066be3196df909d1fd48573c40adaa8bc0a9f7e129c26478739284e36bdeb72",
  "projects/damp-ascend/tools/allT_dispatch_controller_v1/READY.md": "799509c6a6982a98b9e560772e491874db9da2261e674c2f93333f5ef7be2af6",
  "projects/damp-ascend/tools/selected_prefill_dispatch_v1/READY.md": "bf01ebf5403d78becc049e213a59e60d2f0a261760c5f1f9da3ace4ca1e8b3a9",
  "projects/damp-ascend/tools/selected_prefill_dispatch_v1/child_shim.py": "fedb6cbbea961c4e4f76ae3cde167130407bf0bf09e6f059c351ac3b8c2434ab",
  "projects/damp-ascend/tools/selected_prefill_dispatch_v1/controller.py": "97fd9034a820102a6ad3d728ea3785776e03406f74d4e2299a5eba6223d84ac6",
  "projects/damp-ascend/tools/selected_prefill_dispatch_v1/test_dispatch.py": "f1ee37a11ee5005f08ab6e027f610b4d7e8efe2c2820cce0833097d087488a27",
  "projects/damp-ascend/tools/allT_dispatch_plan_v1/plan.py": "b2facaebbdef3fcc8636af4fc0b2b8a230947e9d31e734f4769f3b75b7410179",
  "projects/damp-ascend/tools/allT_dispatch_plan_v1/test_plan_contract.py": "92489e9331cc5d69a34344caccece1633f21c17893a0c516d1e9eb8bef651983",
  "projects/damp-ascend/tools/allT_dispatch_plan_v1/READY.md": "33de6895aca9c6c7cb429ff211d49a17ee7af1efd3a83ce5707e90a97d621403",
  "projects/damp-ascend/tools/run_full_capture.py": "9ad5e359766578a24f06e127a990ab93d1e86555baa15d1abb7bb2b3ffc51122",
  "projects/damp-ascend/tools/run_collector_smoke.py": "da541917ebd8764a81624a215a157b6d4e18fbaaa53d9310be54a104d2fbbf92",
  "projects/damp-ascend/tests/all_batch_gate_v1/runtime_manifest.json": "1755f39069b18b10aaabfb7ff341e6879ba741af3cbb72703b64ffe1070f38d5",
  "projects/damp-ascend/tools/selected_prefill_dispatch_v1/PACKET.json": "06457ede58af57875ca36db08462cc67a59a75c35616b474eda784a7e776991c"
}

def require(ok,message):
    if not ok: raise ValueError(message)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def read(path):
    p=Path(path)
    require(p.is_file() and not p.is_symlink() and p.stat().st_size<=64*1024*1024,"ordinary bounded JSON")
    def pairs(rows):
        d={}
        for k,v in rows:
            require(k not in d,"duplicate JSON key")
            d[k]=v
        return d
    def reject(v):raise ValueError("nonfinite JSON "+v)
    return json.loads(p.read_text(),object_pairs_hook=pairs,parse_constant=reject)

def checked(path,pin):
    p=Path(path)
    require(p.is_absolute() and p.is_file() and not p.is_symlink() and
            type(pin) is str and re.fullmatch("[a-f0-9]{64}",pin) and sha(p)==pin,"source drift "+str(p))
    return p

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def packet(pin=None):
    p=BASE_NEW/"PACKET.json"
    if pin is not None:checked(p,pin)
    row=read(p)
    require(row.get("schema")=="damp-independent-allT-source/v1" and
            set(row.get("sources",{}))==set(OWN) and row.get("reused_sources")==REUSED and
            row.get("default_enabled") is False and row.get("deadline_utc")==DEADLINE,
            "exact NEW source manifest")
    for n,h in row["sources"].items():checked(BASE_NEW/n,h)
    for n,h in REUSED.items():checked(REPO/n,h)
    model_geometry()
    return row

def model_geometry():
    checked(MODEL_CONFIG,MODEL_SHA)
    t=read(MODEL_CONFIG)["text_config"]
    require(t["num_hidden_layers"]==64 and t["layer_types"]==
            ["linear_attention" if i%4!=3 else "full_attention" for i in range(64)] and
            (t["linear_num_key_heads"],t["linear_num_value_heads"],
             t["linear_key_head_dim"],t["linear_value_head_dim"])==(16,48,128,128),
            "actual model geometry no longer matches TP4 synthetic gate")
    return {"path":str(MODEL_CONFIG),"sha256":MODEL_SHA,"tp":4,"local_key_heads":4,
            "local_value_heads":12,"linear_layers":48,"Dk":128,"Dv":128,
            "scope":"configuration geometry only; no calibrated plans or model execution"}

def source_snapshot():
    row=packet()
    return {**{str(BASE_NEW/n):h for n,h in row["sources"].items()},
            **{str(REPO/n):h for n,h in REUSED.items()},str(MODEL_CONFIG):MODEL_SHA}

LEGACY = load("_independent_allT_frozen_contract",
              PROJECT/"tests/all_batch_gate_v1/contract.py")
for _name in ("BASE","OLD","NAMESPACE","KERNEL","LIMITS","LAYOUTS","BATCH_GROUPS",
              "new_output","validate_device"):
    globals()[_name]=getattr(LEGACY,_name)

def source_bindings(args):
    require(getattr(args,"packet_sha256",None),"explicit NEW packet SHA")
    row=packet(args.packet_sha256)
    bound=LEGACY.source_bindings(args)
    bound["independent_packet"]={"path":str(BASE_NEW/"PACKET.json"),"sha256":args.packet_sha256}
    bound["new_runtime_sources"]={str(BASE_NEW/n):h for n,h in row["sources"].items()}
    bound["scheduling_source_pins"]=REUSED
    return bound

def validate_native_anchors(report):
    ref=report.get("native_row_reference",{})
    records=ref.get("anchors",[])
    require(ref.get("schema")=="damp-restricted-native-row-composition/v1" and
            ref.get("anchors_passed") is True and len(records)==6 and
            {(r.get("variant"),r.get("index")) for r in records}=={(v,i) for v in(0,1) for i in(0,7,159)},
            "six actual source-bound native B16 split anchors required")
    for r in records:
        require(r.get("batch")==16 and r.get("whole_native_calls")==1 and r.get("split_native_calls")==16 and
                r.get("passed") is True and set(r.get("guards",{}))==
                {"complete_FP32_state_bitwise","selected_FP32_state_bitwise","original_BF16_output_bitwise",
                 "complete_packed_bitwise","native_every_call_guards","native_untouched_bitwise"} and
                all(x is True for x in r["guards"].values()),"whole/split exact numerical anchor")
        checked(r["raw_before"]["path"],r["raw_before"]["sha256"])
    require(type(ref.get("actual_native_calls")) is int and ref["actual_native_calls"]>=102,
            "actual native calls, not a synthetic readiness flag")

def validate_shards(reports,packet_sha):
    packet(packet_sha)
    for report in reports:
        require(report.get("execution_packet")=="damp-independent-allT-v1" and
                report.get("bindings",{}).get("independent_packet")==
                {"path":str(BASE_NEW/"PACKET.json"),"sha256":packet_sha},
                "NEW run authority, not old receipt")
        validate_native_anchors(report)
        expected={"source_manifest_sha256":"a115f00eb371476ad96c440fca53db2c383e2f5f11c9b62e80214543754c1958",
                  "runtime_manifest_sha256":"1755f39069b18b10aaabfb7ff341e6879ba741af3cbb72703b64ffe1070f38d5",
                  "library_sha256":"a802d2584f6342acd198406a94c4a4cb3dd0e9cd6cc360569e58f3f117ac0ade",
                  "build_receipt_sha256":"a9c8a6824f3f0948d4395eabcc731a0b4e0da6a7f94d6053d3159cf008e23d36"}
        require(all(report.get("bindings",{}).get(k)==v for k,v in expected.items()),
                "each NEW actual report must match frozen build/SO/runtime/source")
        require(report.get("sources_before")==source_snapshot()==report.get("sources_after"),
                "complete NEW+frozen source identity before/after")
    sys.path.insert(0,str(LEGACY.BASE))
    result=LEGACY.validate_shards(reports)
    result.update(execution_packet="damp-independent-allT-v1",
                  native_split_anchor_cases=24,calibrated_plan_count=0,
                  full_model_cache_verified=False,serving_ready=False)
    return result
