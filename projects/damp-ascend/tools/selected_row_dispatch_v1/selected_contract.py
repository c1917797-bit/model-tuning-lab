"""NEW balanced selected-row execution contract, stdlib/default OFF."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import types

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
PROJECT=REPO/"projects/damp-ascend"
OLD_DIR=PROJECT/"tools/independent_allT_dispatch_v1"
OLD_PACKET_SHA="f182a72c5cea43bc5e12b48751d6d8c51c96050145d349c3e0b90ee0d0b6d89a"
SELECTED_DIR=PROJECT/"tools/selected_row_reference_v1"
SELECTED_SHA="85aba91c7941e9258eeea8c8f5d7f4f6550beca414e6fc78b2f90f4959754341"
BATCH_GROUPS={4:(1,8,9,16),5:(2,7,10,15),6:(3,6,11,14),7:(4,5,12,13)}
EXECUTION_PACKET="damp-selected-row-dispatch-v1"
OWN=("controller.py","runner.py","selected_contract.py","test_dispatch.py","READY.md")
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module
    spec.loader.exec_module(module);return module
sys.path.insert(0,str(OLD_DIR))
OLD=load("_selected_dispatch_old_contract",OLD_DIR/"independent_contract.py")
for name in ("sha","read","checked","require","DEADLINE","MODEL_CONFIG","model_geometry",
             "BASE","NAMESPACE","KERNEL","LIMITS","LAYOUTS","new_output","validate_device"):
    globals()[name]=getattr(OLD,name)
# BASE is the original numerical-fixture directory; compilation unchanged.
NUMERICAL_OLD=OLD.OLD
def packet(pin=None):
    path=HERE/"PACKET.json"
    if pin is not None:checked(path,pin)
    row=read(path)
    require(row.get("schema")=="damp-selected-row-dispatch-source/v1" and
        row.get("default_enabled") is False and row.get("npu_executed") is False and
        row.get("deadline_utc")==DEADLINE and set(row.get("sources",{}))==set(OWN) and
        row.get("balanced_groups")=={str(k):list(v) for k,v in BATCH_GROUPS.items()},
        "explicit NEW balanced packet, never original contiguous partition")
    for name,digest in row["sources"].items():checked(HERE/name,digest)
    selected=load("_selected_dispatch_seam_audit",SELECTED_DIR/"seam.py")
    bound=selected.source_bindings(REPO,SELECTED_SHA)
    expected={**bound["sources"],str((SELECTED_DIR/"SOURCE_MANIFEST.json").relative_to(REPO)):SELECTED_SHA}
    require(row.get("dependencies")==expected,"complete NEW seam+41 original source closure")
    for name,digest in expected.items():checked(REPO/name,digest)
    OLD.packet(OLD_PACKET_SHA)
    return row
def source_snapshot():
    p=packet()
    return {**{str(HERE/n):h for n,h in p["sources"].items()},
        **{str(REPO/n):h for n,h in p["dependencies"].items()},
        str(MODEL_CONFIG):OLD.MODEL_SHA,str(HERE/"PACKET.json"):sha(HERE/"PACKET.json")}
def source_bindings(args):
    p=packet(args.packet_sha256)
    require(tuple(args.batches)==BATCH_GROUPS[args.physical_card],"explicit true-T balanced group differs")
    legacy=copy.copy(args);legacy.packet_sha256=OLD_PACKET_SHA
    bound=OLD.source_bindings(legacy)
    bound["selected_row_packet"]={"path":str(HERE/"PACKET.json"),"sha256":args.packet_sha256}
    bound["selected_row_sources"]={str(HERE/n):h for n,h in p["sources"].items()}
    bound["selected_row_manifest"]={"path":str(SELECTED_DIR/"SOURCE_MANIFEST.json"),"sha256":SELECTED_SHA}
    bound["balanced_groups"]={str(k):list(v) for k,v in BATCH_GROUPS.items()}
    return bound
def validate_equivalence(report):
    e=report.get("selected_row_equivalence",{})
    expected={(t,v,i,s) for t in report["batches"] for v in(0,1) for i in(0,7,159) for s in(0,t+2)}
    require(e.get("schema")=="damp-selected-row-equivalence/v1" and
        e.get("status")=="restricted_fullS_localS1_bitwise_pass" and e.get("npu_executed") is True and
        e.get("pair_count")==48 and e.get("batches")==report["batches"] and
        e.get("general_sr_supported") is False and e.get("serving_ready") is False and
        e.get("performance_measurement_admitted") is False and len(e.get("cases",[]))==48,
        "actual fullS/localS1 equivalence remains incomplete")
    keys={"complete_FP32_state_bitwise","complete_packed_bitwise","selected_FP32_bitwise",
        "original_BF16_bitwise","all_native_calls_guards","full_native_untouched_bitwise",
        "original_CPU_merge_bitwise"}|{n+"_bitwise" for n in
        ("original_output_bf16","native_output_reordered_bf16","restored_fp32_after_native_bf16_cast",
         "native_updated_selected_fp32","transformed_value_bf16")}
    observed=set()
    for c in e["cases"]:
        observed.add((c["batch"],c["variant"],c["fixture_index"],c["original_slot"]))
        require(c["slots"]==c["batch"]+3 and c["local_index"]==0 and c["passed"] is True and
            set(c["guards"])==keys and all(v is True for v in c["guards"].values()),"strict pair guards")
        checked(c["raw_before"]["path"],c["raw_before"]["sha256"])
    require(observed==expected,"all first/last slots, identity/power2 and fixture indices required")
    identity=e.get("source_identity",{})
    require(identity.get("sha256")==SELECTED_SHA,"actual selected-row source identity")
def validate_shards(reports,pin):
    packet(pin); require(len(reports)==4,"four balanced shards")
    for r in reports:
        require(r.get("execution_packet")==EXECUTION_PACKET and r["batches"]==list(BATCH_GROUPS[r["physical_card"]])
            and r.get("bindings",{}).get("selected_row_packet")=={"path":str(HERE/"PACKET.json"),"sha256":pin},
            "actual NEW balanced execution identity")
        require(r.get("sources_before")==source_snapshot()==r.get("sources_after"),"complete source drift")
        OLD.validate_native_anchors(r);validate_equivalence(r)
        journal_module=load("_selected_dispatch_journal_validator",HERE/"runner.py")
        j=r["evidence_journal"];checked(j["path"],j["sha256"])
        require(journal_module.rebuild_journal(Path(j["path"]))==r,"lossless journal must reconstruct every original field")
        expected={"source_manifest_sha256":"a115f00eb371476ad96c440fca53db2c383e2f5f11c9b62e80214543754c1958",
            "runtime_manifest_sha256":"1755f39069b18b10aaabfb7ff341e6879ba741af3cbb72703b64ffe1070f38d5",
            "library_sha256":"a802d2584f6342acd198406a94c4a4cb3dd0e9cd6cc360569e58f3f117ac0ade",
            "build_receipt_sha256":"a9c8a6824f3f0948d4395eabcc731a0b4e0da6a7f94d6053d3159cf008e23d36"}
        require(all(r["bindings"].get(k)==v for k,v in expected.items()),"unchanged actual build identities")
    sys.path.insert(0,str(OLD.LEGACY.BASE))
    namespace=dict(vars(OLD.LEGACY));namespace["BATCH_GROUPS"]=BATCH_GROUPS
    original=OLD.LEGACY.validate_shards
    validate=types.FunctionType(original.__code__,namespace,original.__name__,
        original.__defaults__,original.__closure__)
    result=validate(reports)
    result.update(execution_packet=EXECUTION_PACKET,balanced_groups={str(k):list(v) for k,v in BATCH_GROUPS.items()},
        selected_row_pairs=192,native_split_anchor_cases=24,calibrated_plan_count=0,
        serving_ready=False,performance_measurement_admitted=False)
    return result
