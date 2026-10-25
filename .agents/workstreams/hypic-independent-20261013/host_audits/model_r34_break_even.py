"""Offline break-even model; no performance claim from operation counts."""
import hashlib,json,sys
from pathlib import Path
W=Path(__file__).resolve().parent.parent
P=Path("/cache/cch/hypic-independent-20261013/r31-g3-offline-analysis-r1-20261025")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def model():
    pair=json.loads((W/"R30_FIRST_PAIR_DECISION_20261025.json").read_bytes())
    hw=json.loads((P/"four-rank-hardware-cost-r6.json").read_bytes())
    cpu=json.loads((P/"cpu-rank0-complete-prefix-r7.json").read_bytes())
    info_path=P/"profile/rank0_58_20261025130941427_ascend_pt/profiler_info_0.json"
    info=json.loads(info_path.read_bytes())["config"]
    assert pair["full_goal_accepted"]is False and pair["G3"]["tpot_ms"]>pair["G1"]["tpot_ms"]
    base=pair["G1"]["tpot_ms"];hypic=pair["G3"]["tpot_ms"]
    config=info["common_config"];experimental=info["experimental_config"]
    assert config["record_shapes"]is False and config["with_stack"]is False
    assert experimental["record_op_args"]is False
    ranks=[]
    for rank,row in enumerate(hw["ranks"]):
        assert set(row["devices"])=={str(rank)}
        apis={r["API Name"]:r for r in row["top_api_sum"]}
        copies={r["name"]:r for r in row["task_types"]}
        ranks.append({"rank":rank,"envelope_seconds":row["hardware_envelope_us"]/1e6,
            "stream_sync_api_sum_seconds":float(apis["aclrtSynchronizeStream"]["Time(us)"])/1e6,
            "device_sync_api_sum_seconds":float(apis["aclrtSynchronizeDeviceWithTimeout"]["Time(us)"])/1e6,
            "device_async_copy_union_seconds":copies["MEMCPY_ASYNC"]["union_us"]/1e6})
    matmul=next(r for r in cpu["top_self_cpu"]if r["name"]=="aten::matmul")
    return {"schema":"hypic-r34-break-even-model/v1",
        "formal_same_protocol_requirement":{"G1_tpot_ms":base,"G3_tpot_ms":hypic,
            "save_ms_per_output_token_to_break_even":hypic-base,
            "fraction_of_current_G3_tpot_to_remove":1-base/hypic,
            "meaning":"Necessary recovery of measured TPOT only; not a prediction of diagnostic64 or a component."},
        "profile64_four_ranks":ranks,
        "rank0_partial_cpu_all_matmul":{"calls":matmul["calls"],
            "inclusive_seconds":matmul["inclusive_us"]/1e6,
            "self_seconds":matmul["self_us"]/1e6,
            "scope":"All observed aten::matmul CPU spans, not prefix-only, not full hardware cost or removable walltime. Event trace has an incomplete final closure."},
        "attribution_gap":{"record_shapes":config["record_shapes"],"with_stack":config["with_stack"],
            "record_op_args":experimental["record_op_args"],"prefix_specific_walltime_budget":None,
            "reason":"No exact source/shape/critical-path association or baseline profile control. CPU API wait and device work overlap."},
        "equation":"T = useful_compute + boundary_state + discarded_outputs + transfer_wait + evidence + coordination_queue; only discarded_outputs changes in the current treatment.",
        "predictions":{"prefix_source_matmul_sites":"2L to L, not 50percent whole service",
            "retained":"All state arithmetic/order, query normalization/input observer, gate casts, suffix, material/evidence IO and completion guards.",
            "end_to_end_gain":None,"causal_status":"Unconfirmed; enabled service arm and three valid controls absent."},
        "next_decision":{"primary":"When renewed, one same-source prefix-output A/B/A with real warm proof and independent audits; evaluate measured gain against paired drift.",
            "do_not_claim":"No whole-regression explanation, estimated millisecond saving or formal1024 success from dispatch counts/profile64.",
            "if_not_material":"Stop expanding this route. Quantify source-owned evidence fsync critical-path budget before any durability-cadence treatment; preserve guards.",
            "low_direct_budget_routes":["Raw async copy bandwidth alone","Global completion guard removal"]},
        "source_sha256":{str(Path(__file__).relative_to(W)):sha(__file__)},
        "input_sha256":{"R30_FIRST_PAIR_DECISION_20261025.json":sha(W/"R30_FIRST_PAIR_DECISION_20261025.json"),
            str(P/"four-rank-hardware-cost-r6.json"):sha(P/"four-rank-hardware-cost-r6.json"),
            str(P/"cpu-rank0-complete-prefix-r7.json"):sha(P/"cpu-rank0-complete-prefix-r7.json"),
            str(info_path):sha(info_path)},
        "new_device_work":False,"full_goal_complete":False}
if __name__=="__main__":print(json.dumps(model(),sort_keys=True))
