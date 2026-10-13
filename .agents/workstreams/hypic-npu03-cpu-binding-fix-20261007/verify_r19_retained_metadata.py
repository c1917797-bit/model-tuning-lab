#!/usr/bin/env python3
"""Read retained r19 metadata and expose retry-evidence loss; no device/network calls."""
import argparse
import ast
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import re
from types import SimpleNamespace
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ROOT = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007")
EVAL = REPO / ".agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/hypic_quality_eval.py"
EVAL_SHA = "9c8cf4204964220acd31adc8a3f73332374f123e1b8681a522b33eff33504cc0"
ARMS = [
    ("full-baseline", "no-cache", "a37204901a95768121e116e72a3978ee64865ca085b09b4993265431133c200d", "6a4e6a1639665ff5c3413ef795b6642a6b4cd8cebc4916143612070e54fccee9", 638),
    ("full-hypic", "hypic-only", "c1b7283c8d46ffb330af3be35232703d9b935819813a68288eb02b0608abdb74", "f2f03e99cc06a751d229e750999221fdd569157628cee48ef95507ce224ed689", 638),
    ("gsm8k-baseline", "no-cache", "03a2093873b2dbf3a0f675c7d0d47d83cadd0389192e10fb491ca03525ece897", "157ee6c04cc4f17dd0b1addcd543a1df94d628f26e8c31b5cb5ef6d531705fba", 3957),
    ("gsm8k-hypic", "hypic-only", "3814b62c948bdc275cc3ef221678191c1160b97dbe2f7907c545f89f108dfa9b", "8f57043932005c9180316d6cab4b3abf187524fe3d5fdfb1f3534d958369b3eb", 3957),
]

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def retry_counterexample():
    require(sha(EVAL) == EVAL_SHA, "frozen evaluator drift")
    tree = ast.parse(EVAL.read_text())
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "request_one"]
    require(len(functions) == 1, "request_one definition count")
    code = compile(ast.Module(body=functions, type_ignores=[]), str(EVAL), "exec")
    outcomes = []
    for failures in (0, 1, 2):
        calls = []
        def fake_urlopen(request, timeout):
            calls.append(1)
            if len(calls) <= failures:
                raise TimeoutError("synthetic pre-server timeout")
            return io.BytesIO(json.dumps({"choices": [{"message": {"content": "4"}, "finish_reason": "stop"}],
                                         "usage": {"prompt_tokens": 8, "completion_tokens": 1}}).encode())
        namespace = dict(argparse=argparse, Any=Any, json=json, hashlib=hashlib,
                         Request=Request, HTTPError=HTTPError, urlopen=fake_urlopen,
                         time=SimpleNamespace(perf_counter=lambda: 0, sleep=lambda seconds: None),
                         build_case=lambda dataset, sample: ("2+2?", "4"),
                         score_case=lambda dataset, text, reference: (text, text == reference))
        exec(code, namespace)
        args = argparse.Namespace(dataset="gsm8k", model="synthetic", max_out_len=2048,
                                  seed=0, retries=2, timeout=2400, base_url="http://not-contacted")
        row = namespace["request_one"](args, 0, {})
        outcomes.append((len(calls), row))
    require([n for n, _ in outcomes] == [1, 2, 3], "counterexample did not exercise retries")
    require(outcomes[0][1] == outcomes[1][1] == outcomes[2][1], "final rows now preserve attempts")
    require(outcomes[0][1]["ok"] and outcomes[0][1]["error"] is None, "successful row schema changed")
    return {"synthetic_attempt_counts": [1, 2, 3], "identical_persisted_rows": True,
            "actual_r19_retries": None, "network_used": False,
            "meaning": "successful final row cannot recover earlier timeouts/retries"}

def audit():
    facts = []
    configurations = []
    for suffix, arm, result_hash, log_hash, expected_posts in ARMS:
        root = ROOT / ("quality-context-41984-hotpath-cache10r19-c32-" + suffix)
        require(sha(root / "arm-result.json") == result_hash, "arm result drift: " + suffix)
        start = json.loads((root / arm / "service-start.json").read_text())
        stop = json.loads((root / arm / "service-stop.json").read_text())
        require(start["container_id"] == stop["container_id"], "lifecycle identity mismatch")
        require(stop["container_removed"] and stop["owned_npus_released"] and stop["port_released"], "release gap")
        logs = list((root / arm).glob("service.full.*.log"))
        require(len(logs) == 1 and start["container_id"][:12] in logs[0].name, "log identity")
        require(sha(logs[0]) == log_hash == stop["service_log_sha256"], "retained log drift")
        npu = root / arm / "npu-smi-at-health.txt"
        require(sha(npu) == start["npu_smi_sha256"], "historical NPU snapshot drift")
        header = npu.read_text().splitlines()[1]
        require("npu-smi 25.2.0" in header and "Version: 25.2.0" in header, "NPU display version drift")
        text = logs[0].read_text()
        engines = [line.split("Initializing a V1 LLM engine ", 1)[1]
                   for line in text.splitlines() if "Initializing a V1 LLM engine " in line]
        require(len(engines) == 1 and engines[0].startswith("(v0.23.0)"), "runtime log identity")
        require("tokenizer_revision=None" in engines[0], "tokenizer log field drift")
        configurations.append(engines[0])
        posts = [line for line in text.splitlines() if "POST /v1/" in line]
        statuses = Counter()
        for line in posts:
            m = re.search(r'"POST (/v1/[^ ]+) HTTP/1\.1" (\d{3})', line)
            require(m is not None, "unparsed access log")
            statuses[m.group(1) + " " + m.group(2)] += 1
        require(dict(statuses) == {"/v1/chat/completions 200": expected_posts}, "HTTP record count drift")
        facts.append({"root": str(root), "container_id": start["container_id"],
                      "service_log_sha256": log_hash, "npu_snapshot_sha256": sha(npu),
                      "logged_framework_version": "0.23.0", "npu_smi_displayed_version": "25.2.0",
                      "tokenizer_revision": None, "historical_tokenizer_bytes_proven": False,
                      "http_200_records": expected_posts, "http_retry_count_proven": False})
    require(len(set(configurations)) == 1, "historical engine configuration differs")
    return {"arms": facts, "matching_logged_engine_configuration": True,
            "retry_counterexample": retry_counterexample(), "no_new_device_run": True,
            "no_quality_verdict_change": True, "full_skill_acceptance": False}

if __name__ == "__main__":
    print(json.dumps(audit(), sort_keys=True))
