"""Immutable same-eager service contracts; no hardware success is inferred."""
from __future__ import annotations
import hashlib
from datetime import datetime, timezone
import json
from pathlib import Path

IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
LIBRARY_SHA = "0e7c64b53314f1e822a27b5f373376d82d3f73c01264a384cf58ee4bc6e3477b"
PROBE_SHA = "caa65dd94506edbd68a5600e9f813d93711ba162a8a2fc0565e7e00ede4414dd"
PLUGIN_SHA = "71be0c99af19d66bc5f44ebb983b748cd56e2e776d567b0b4df0789ca0d89e2d"
COMPLETION_SOURCES = {
 "/vllm-workspace/vllm/vllm/entrypoints/openai/completion/protocol.py":
 "93c720549f2a9ef217d7c2a60710225c862032517520dd9ba693d4820f55365c",
 "/vllm-workspace/vllm/vllm/entrypoints/openai/completion/serving.py":
 "c67bff55fa29c5f89000c3afdc9c7c66305612b13a8a1d85976e5872cee086d7",
}
TOTAL, NATIVE_CANDIDATE, AUX = 10658488320, 8053063680, 2605424640
PER_LAYER_SLOT, LAYERS = 119296, tuple(i for i in range(64) if i % 4 != 3)
COMMON = dict(tensor_parallel_size=4, data_parallel_size=1, dtype="bfloat16",
              max_model_len=40960, max_num_batched_tokens=40960, max_num_seqs=16,
              enforce_eager=True, enable_prefix_caching=False,
              mamba_cache_mode="none", enable_chunked_prefill=False, seed=0,
              speculative=False, profiling=False)
PROTOCOL = dict(requests=40, concurrency=16, input_tokens=32768,
                shared_prefix_tokens=16384, output_tokens=1024,
                temperature=0, seed=0, ignore_eos=True, warmups=2,
                prompt_kind="raw-token-ids-no-chat-template", thinking_mode_enabled=False)

def require(ok, reason):
    if not ok:
        raise ValueError(reason)

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()

def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write_new(path, value):
    with Path(path).open("xb") as stream:
        stream.write(canonical(value) + b"\n")

def prompt_ids(index):
    require(type(index) is int and 0 <= index < 40, "invalid fixed request index")
    prefix = [1000 + i % 257 for i in range(16384)]
    suffix = [2000 + (index * 131 + i * 17) % 4093 for i in range(16384)]
    return prefix + suffix

def validate_native_gate(gate):
    require(gate.get("schema") == "kvbp-parallel-fp32-native-gate/v1" and
            gate.get("status") == "kernel_native_eager_graph_pass" and
            gate.get("script_sha256") == PROBE_SHA and
            gate.get("library_sha256") == LIBRARY_SHA, "frozen real NPU matrix PASS required")
    expected = {(b, "eager", 0) for b in (1, 16)} | {
        (b, "graph", t) for b in (1, 16) for t in range(3)}
    cases = gate.get("cases", [])
    require(len(cases) == 8 and {(c.get("batch"), c.get("mode"), c.get("trial"))
                               for c in cases} == expected, "NPU matrix coverage incomplete")
    for c in cases:
        require(c.get("status") == "passed" and len(c.get("steps", [])) == 160 and
                all(r.get("passed") is True for r in c["steps"]) and
                c.get("merges", 0) > 0 and c.get("resets") == 2, "NPU multistep/merge/reset gate failed")

def validate_identity(ident, gate_sha, arm, port):
    require(arm in ("dense", "candidate") and type(port) is int and 1024 < port < 65536, "arm/port")
    require(ident.get("schema") == "kvbp.service-identity/v1" and
            ident.get("image_id") == IMAGE and ident.get("physical_devices") == [4,5,6,7] and
            ident.get("logical_to_physical") == {"0":4,"1":5,"2":6,"3":7} and
            ident.get("fresh_idle_verified") is True and ident.get("nonprivileged") is True and
            ident.get("source_canary_passed") is True and ident.get("native_gate_sha256") == gate_sha,
            "parent-created fresh mapping/source/NPU-gate receipt required")
    require(ident.get("arm") == arm and ident.get("port") == port and
            ident.get("common") == COMMON and ident.get("common_total_budget_bytes") == TOTAL,
            "identity arm/common protocol/budget differs")
    require(type(ident.get("preflight_utc")) is str and
            isinstance(ident.get("evidence"), dict) and bool(ident["evidence"]),
            "preflight timestamp and external evidence references required")
    checked=datetime.fromisoformat(ident["preflight_utc"].replace("Z","+00:00"))
    require(checked.tzinfo is not None and
            0 <= (datetime.now(timezone.utc)-checked).total_seconds() <= 600,
            "preflight receipt is stale/future/unzoned; MAIN must freshly inspect each arm")

def budget(arm, slots=None):
    native = TOTAL if arm == "dense" else NATIVE_CANDIDATE
    reserved = 0 if arm == "dense" else AUX
    if slots is not None and arm == "candidate":
        require(type(slots) is int and slots > 0 and slots * 48 * PER_LAYER_SLOT <= reserved,
                "actual full48 auxiliary state exceeds reservation; never silently increase budget")
    require(native + reserved == TOTAL, "both arms must have exactly equal total state budget")
    return dict(native_bytes=native, auxiliary_reserved_bytes=reserved, common_total_bytes=TOTAL)

def summarize(responses, timing_basis):
    require(len(responses) == 40 and {r["index"] for r in responses} == set(range(40)),
            "exact40 requests required")
    require(all(r["ok"] and r["completion_tokens"] == 1024 and r["prompt_tokens"] == 32768
                and r["finish_reason"] == "length" and r["done"] for r in responses),
            "usage/length/[DONE]/success coverage failed")
    total = sum(r["completion_tokens"] for r in responses)
    wall = max(r["response_end"] for r in responses) - min(r["submitted"] for r in responses)
    require(wall > 0 and all(r["last"] >= r["first"] >= r["submitted"] for r in responses), "stream times")
    return dict(total_output_tokens=total, wall_seconds=wall, output_tokens_per_second=total/wall,
                mean_ttft_seconds=sum(r["first"]-r["submitted"] for r in responses)/40,
                mean_tpot_seconds=sum((r["last"]-r["first"])/1023 for r in responses)/40,
                timing_basis=timing_basis, queue_included_in_ttft=True,
                throughput_wall_ends_at="last-response-[DONE]-not-kernel-time",
                tpot_interval="first-to-last-output-token-stream-event")
