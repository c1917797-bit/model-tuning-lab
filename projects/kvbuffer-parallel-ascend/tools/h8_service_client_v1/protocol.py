"""H8 HTTP measurement contract. It cannot establish NPU or model acceptance."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
MODEL_CONFIG_SHA = "69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c"
PROTOCOL = {
    "requests": 40, "concurrency": 16, "input_tokens": 32768,
    "shared_prefix_tokens": 16384, "output_tokens": 1024,
    "temperature": 0, "seed": 0, "ignore_eos": True, "warmups": 2,
    "prompt_kind": "raw-token-ids-no-chat-template",
    "echo": True,
    "thinking_mode_enabled": False,
    "ttft_origin": "worker-http-submission-not-client-enqueue",
    "throughput_interval": "first-enqueue-to-last-response-DONE",
    "tpot_interval": "first-to-last-output-token-SSE-delta",
    "coalesced_delta_policy": "tokens-in-one-delta-share-receipt-time",
}
ANCESTOR = {
    "path": "/opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/service/bench.py",
    "reuse": "SSE-token-ID-and-usage-validation; not P1 launch, budget, or acceptance",
}


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


def sources():
    root = Path(__file__).resolve().parent
    return {name: sha(root / name) for name in ("protocol.py", "bench.py")}


def prompt_ids(index):
    require(type(index) is int and 0 <= index < PROTOCOL["requests"], "fixed request index")
    return [1000 + i % 257 for i in range(16384)] + [
        2000 + (index * 131 + i * 17) % 4093 for i in range(16384)
    ]


def arm_contract(arm, port):
    require(type(port) is int and 1024 < port < 65536, "explicit loopback service port")
    require(arm.get("schema") == "kvbp.h8-model-service-arm/v1", "not a legacy P1 arm")
    require(arm.get("arm") in ("dense", "candidate") and arm.get("prepare_only") is False,
            "actual launched H8 arm, not prepare-only")
    require(arm.get("image_id") == IMAGE and arm.get("model_config_sha256") == MODEL_CONFIG_SHA,
            "same pinned image/checkpoint")
    require(arm.get("port") == port and arm.get("served_model_name") == "qwen36-h8",
            "actual arm endpoint/model name")
    require(arm.get("protocol") == PROTOCOL and arm.get("client_sources") == sources(),
            "source-bound exact H8 measurement protocol")
    common = arm.get("common", {})
    require(common.get("tensor_parallel_size") == 4 and common.get("pipeline_parallel_size") == 1
            and common.get("data_parallel_size") == 1 and common.get("dtype") == "bfloat16"
            and common.get("max_num_seqs") == 16 and common.get("seed") == 0
            and common.get("max_model_len") == 40960 and common.get("max_num_batched_tokens") == 40960
            and type(common.get("enable_chunked_prefill")) is bool
            and common.get("enable_prefix_caching") is True
            and common.get("mamba_cache_mode") == "align"
            and common.get("speculative") is False and common.get("async_scheduling") is False
            and common.get("profiling") is False, "actual H8-supported common receiver contract")
    require(arm.get("measurement_scope") in ("same-eager-screen", "formal-graph-pair"),
            "explicit screen versus final protocol scope")
    require(common.get("enforce_eager") is (arm["measurement_scope"] == "same-eager-screen"),
            "eager screen cannot be relabelled formal graph performance")
    require(type(arm.get("MAIN_launch_authority")) is dict and arm["MAIN_launch_authority"],
            "MAIN launch authority required; independent terminal consumer must verify it")
    require(arm.get("candidate_numeric_prerequisite_checked") is True,
            "full and mixed numerical prerequisite checked before performance")
    require(type(arm.get("common_total_cache_budget_bytes")) is int
            and arm["common_total_cache_budget_bytes"] > 0, "same total native plus auxiliary cache budget")
    return arm


class StreamState:
    def __init__(self, prompt, outputs):
        self.prompt, self.outputs = prompt, outputs
        self.tokens = []
        self.first = self.last = None
        self.prompt_seen = self.done = False
        self.usage = self.finish = None

    def feed(self, data, now):
        require(math.isfinite(now), "nonfinite receipt time")
        if data == b"[DONE]":
            require(not self.done, "duplicate DONE")
            self.done = True
            return
        require(not self.done, "event after DONE")
        obj = json.loads(data)
        require("error" not in obj, "server stream error: " + str(obj))
        if obj.get("usage") is not None:
            require(self.usage is None, "duplicate usage")
            self.usage = obj["usage"]
        for choice in obj.get("choices", []):
            require(choice.get("index") == 0, "multiple or foreign choice")
            prompt = choice.get("prompt_token_ids")
            if prompt is not None:
                require(not self.prompt_seen and prompt == self.prompt, "prompt changed or repeated")
                self.prompt_seen = True
            ids = choice.get("token_ids")
            require(type(ids) is list and all(type(v) is int and v >= 0 for v in ids),
                    "actual token-ID deltas required; text chunks cannot substitute")
            if ids:
                require(self.finish is None and (self.last is None or now >= self.last),
                        "tokens after finish or nonmonotonic receipt")
                self.first = now if self.first is None else self.first
                self.last = now
                self.tokens.extend(ids)
                require(len(self.tokens) <= self.outputs, "overlong or cumulative token delta")
            if choice.get("finish_reason") is not None:
                require(self.finish is None, "duplicate terminal choice")
                self.finish = choice["finish_reason"]

    def finish_check(self):
        require(self.done and self.prompt_seen and self.finish == "length"
                and len(self.tokens) == self.outputs, "IDs/prompt/length/DONE incomplete")
        require(self.usage is not None and self.usage.get("completion_tokens") == self.outputs
                and self.usage.get("prompt_tokens") == len(self.prompt)
                and self.usage.get("total_tokens") == len(self.prompt) + self.outputs,
                "exact usage missing or wrong")
        require(self.first is not None and self.last is not None, "token arrival time absent")


def summarize(rows):
    require(len(rows) == 40 and {r["index"] for r in rows} == set(range(40)), "exact40 unique requests")
    require(all(r["ok"] and r["completion_tokens"] == 1024 and r["prompt_tokens"] == 32768
                and r["finish_reason"] == "length" and r["done"] for r in rows), "full1024 successful output")
    require(all(all(math.isfinite(r[k]) for k in ("enqueued", "submitted", "first", "last", "response_end"))
                and r["response_end"] >= r["last"] >= r["first"] >= r["submitted"] >= r["enqueued"]
                for r in rows), "finite monotonic actual client times")
    wall = max(r["response_end"] for r in rows) - min(r["enqueued"] for r in rows)
    require(wall > 0, "positive full response wall")
    return {
        "total_output_tokens": 40960, "wall_seconds": wall,
        "output_tokens_per_second": 40960 / wall,
        "mean_ttft_seconds": sum(r["first"] - r["submitted"] for r in rows) / 40,
        "mean_tpot_seconds": sum((r["last"] - r["first"]) / 1023 for r in rows) / 40,
        "mean_client_queue_seconds": sum(r["submitted"] - r["enqueued"] for r in rows) / 40,
        "mean_ttft_including_client_queue_seconds": sum(r["first"] - r["enqueued"] for r in rows) / 40,
        "timing_basis": "received-SSE-token-ID-deltas",
        "coalesced_delta_policy": PROTOCOL["coalesced_delta_policy"],
    }
