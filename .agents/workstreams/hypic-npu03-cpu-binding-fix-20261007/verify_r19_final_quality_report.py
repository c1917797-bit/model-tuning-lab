#!/usr/bin/env python3
"""Read-only final-report replay; imports frozen auditors, never calls their writers."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import importlib
import json
import re
from pathlib import Path
import statistics
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCE = "4429e35177979c874bf053ab29789e4773f39b22"
AUDITS = {
    "longbench": ("hypic-r19-c32-2048-longbench-paired-audit.json",
                  "40ce887336be3446aa87a8e552fb50d366234fc10006ad5a3140f3dc0df16d9b"),
    "gsm8k": ("hypic-r19-c32-2048-gsm8k-paired-audit.json",
              "496f1dfacb3c3a8dd03f8ee07368fb142b432498c0ee5dbb5722e1d4f85fd187"),
}
REPORT = HERE / "HYPIC_R19_FINAL_QUALITY_REPORT_20261012.md"

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def replay(dataset):
    # A fresh process per dataset is mandatory: frozen configure() is single-use.
    module = "r19_repaired_c32_longbench_audit" if dataset == "longbench" else "r19_c32_gsm8k_audit"
    a = importlib.import_module(module)
    filename, expected = AUDITS[dataset]
    receipt_path = a.quality.ROOT / filename
    require(digest(receipt_path) == expected, "immutable paired audit drift")
    frozen = json.loads(receipt_path.read_text())
    require(a.quality.sha256(a.quality.EVALUATOR) == a.PREREG["evaluator_sha256"], "evaluator drift")
    if dataset == "longbench":
        cases, evaluator = a.frozen_cases()
        require(a.frozen_pair_seam() == frozen["frozen_pair_seam"], "one-switch seam drift")
        b = a.audit_arm(a.BASE, "no-cache", cases, evaluator, require_source_attestation=True)
        c = a.audit_arm(a.CAND, "hypic-only", cases, evaluator,
                        allow_hot_shortfall=True, require_source_attestation=True)
        decision = a.decide(b, c)
        for key, value in decision.items():
            require(frozen["quality"][key] == value, "quality decision drift: " + key)
        for root, arm in [(a.BASE, "no-cache"), (a.CAND, "hypic-only")]:
            require(a.audit_short_canary(root, arm) == frozen["short_canary"][arm], "canary drift")
            require(a.audit_integrated_wave(root, arm) == frozen["integrated_capacity_wave"][arm], "capacity wave drift")
        baseline_runs = decision["baseline_run_correct"]
        candidate_runs = decision["candidate_run_correct"]
        denominator = 127
        length = [b["length_limit"], c["length_limit"]]
        pairs = [decision["paired_improved"], decision["paired_regressed"]]
        result = frozen["quality"]["r19_quality_decision"]
        baseline_length_runs = [sum(r["finish_reason"] == "length" for r in b["rows"]
                                    if r["repetition"] == i) for i in range(1, 4)]
        expected_decision = ("PASS" if sum(candidate_runs) / 3 >= min(baseline_runs)
                             and length[1] / 3 <= max(baseline_length_runs)
                             and not decision["category_cliffs"] else "REJECT_OR_QUALIFY")
        require(result == expected_decision, "frozen LongBench variability gate drift")
        start = json.loads((a.CAND / "hypic-only/service-start.json").read_text())
        ns_path = a.CAND / "hypic-only/worker-namespace-map.json"
        ns = json.loads(ns_path.read_text())
        require(digest(ns_path) == start["worker_namespace_map_sha256"]
                and ns["container_id"] == start["container_id"]
                and ns["physical_npu_to_host_pid"] == start["worker_pid_by_physical_npu"]
                and ns["physical_npu_to_namespace_pid"] == start["worker_namespace_pid_by_physical_npu"],
                "physical-to-namespace proof drift")
        for physical, host_pid in ns["physical_npu_to_host_pid"].items():
            require(list(map(int, ns["nspid_lines"][physical].split()[1:])) ==
                    [host_pid, ns["physical_npu_to_namespace_pid"][physical]], "namespace PID row drift")
        worker_pids = set(start["worker_namespace_pid_by_physical_npu"].values())
        require(len(worker_pids) == 4, "namespace worker map missing")
        api_ids = {r["request_id"] for r in c["rows"]}
        joined = {}
        events = a.CAND / "hypic-only/hypic-evidence.jsonl"
        for line in events.read_text().splitlines():
            e = json.loads(line)
            if e.get("event") != "worker_hot_request_verified":
                continue
            rid = e.get("request_id", "")
            matches = [api for api in api_ids if re.fullmatch(re.escape(api) + r"-[0-9a-f]{8}", rid)]
            if not matches:
                continue
            require(len(matches) == 1 and e["pid"] in worker_pids
                    and e.get("complete_hybrid_repair_validated") is True
                    and e.get("expected_full_layers") == 16 and e.get("expected_gdn_layers") == 48,
                    "worker event identity drift")
            joined.setdefault(matches[0], []).append(e["pid"])
        require(len(joined) == 134 and all(len(v) == 4 and set(v) == worker_pids
                                          for v in joined.values()), "supplementary hot-ID coverage drift")
    else:
        require(a.pair_seam() == frozen["one_switch_seam"], "one-switch seam drift")
        samples, evaluator = a.frozen_samples(), a.frozen_evaluator()
        b = a.audit_arm(a.BASE, "no-cache", samples, evaluator)
        c = a.audit_arm(a.CAND, "hypic-only", samples, evaluator)
        for left, right in zip(b["rows"], c["rows"]):
            require((left["index"], left["repeat"], left["prompt_tokens"]) ==
                    (right["index"], right["repeat"], right["prompt_tokens"]), "paired identity drift")
        baseline_runs = [x["correct"] for x in b["units"]]
        candidate_runs = [x["correct"] for x in c["units"]]
        require(baseline_runs == frozen["baseline_correct_by_run"] and
                candidate_runs == frozen["candidate_correct_by_run"], "GSM8K score drift")
        denominator = 1319
        length = [sum(x["length_limit"] for x in arm["units"]) for arm in (b, c)]
        flips = Counter("improved" if not x["correct"] and y["correct"] else
                        "regressed" if x["correct"] and not y["correct"] else "unchanged"
                        for x, y in zip(b["rows"], c["rows"]))
        require(dict(flips) == frozen["pairwise"], "GSM8K pairwise drift")
        pairs = [flips["improved"], flips["regressed"]]
        result = frozen["quality_decision"]
        require(result == ("PASS" if sum(candidate_runs) / 3 >= min(baseline_runs)
                           and length[1] / 3 <= max(x["length_limit"] for x in b["units"])
                           else "REJECT_OR_QUALIFY"), "GSM8K quality gate drift")
    require(b["fingerprint"] == c["fingerprint"], "paired fingerprint drift")
    require(b["fingerprint"]["source_commit"] == SOURCE, "source drift")
    require(b["fingerprint"]["physical_npus"] == [0, 1, 2, 3], "physical lane drift")
    provenance = []
    for row, root, arm, name in [(b, a.BASE, "no-cache", "baseline"), (c, a.CAND, "hypic-only", "candidate")]:
        require({k: v for k, v in row.items() if k != "rows"} == frozen[name], "arm receipt replay drift")
        att_path = root / arm / "source-attestation.json"
        att = json.loads(att_path.read_text())
        old = a.quality.QROOT
        try:
            a.quality.QROOT = root
            _, binds, _, command = a.quality.spec(arm)
        finally:
            a.quality.QROOT = old
        require(att["actual_command"] == ["bash", "-lc", command] and
                sorted(att["actual_binds"]) == sorted(binds), "actual deployment command/bind drift")
        provenance.append({"root": str(root), "container_id": row["container_id"],
                           "guard_samples": row["guard_samples"],
                           "contract_sha256": row["contract_sha256"],
                           "arm_result_sha256": row["arm_result_sha256"],
                           "attestation_sha256": digest(att_path),
                           "exact_release_replayed": True})
    rates = [[100 * v / denominator for v in run] for run in (baseline_runs, candidate_runs)]
    return {"dataset": dataset, "source": SOURCE, "per_run_samples": denominator,
            "scored_rows_per_arm": denominator * 3, "correct": [sum(baseline_runs), sum(candidate_runs)],
            "runs": [baseline_runs, candidate_runs], "length": length, "paired_wins_losses": pairs,
            "means_pct": [statistics.mean(r) for r in rates],
            "sample_sd_pp": [statistics.stdev(r) for r in rates],
            "delta_pp": 100 * (sum(candidate_runs) - sum(baseline_runs)) / (denominator * 3),
            "decision": result, "audit_sha256": expected, "provenance": provenance,
            "raw_rows_rescored": True, "device_execution": False}

def report_rows(facts):
    rows = []
    for f in facts:
        b, c = f["correct"]
        br, cr = ("/".join(map(str, r)) for r in f["runs"])
        rows.append(f'| {f["dataset"]} | {b}/{f["scored_rows_per_arm"]} | {c}/{f["scored_rows_per_arm"]} | {br} | {cr} | {f["delta_pp"]:+.6f} | {f["decision"]} |')
    return rows

def audit_text(text, facts):
    for row in report_rows(facts):
        require(row in text, "report numeric row drift")
    for f in facts:
        require(f'{f["means_pct"][0]:.6f} ± {f["sample_sd_pp"][0]:.6f}' in text and
                f'{f["means_pct"][1]:.6f} ± {f["sample_sd_pp"][1]:.6f}' in text, "dispersion drift")
        require(f["audit_sha256"] in text, "audit digest absent")
        for p in f["provenance"]:
            require(p["root"] in text and p["arm_result_sha256"] in text, "arm provenance absent")
    for s in ["final negative quality report", "Step 0", "Step 1", "Step 2", "Step 3",
              "历史参考", "同源码性能未测", "off-path", "不得重跑", "源身份",
              "允许声称", "禁止声称", "仍未证明", "精确释放",
              "HYPIC_R19_ARM=no-cache", "HYPIC_R19_ARM=hypic-only",
              "HYPIC_R19_GSM8K_ARM=no-cache", "HYPIC_R19_GSM8K_ARM=hypic-only",
              "r19_repaired_c32_longbench_adapter.py --run", "r19_c32_gsm8k_adapter.py --run",
              "verify_r19_final_quality_report.py --check-report",
              "不是整个三阶段目标完成", "不重新上卡"]:
        require(s in text, "required report boundary missing: " + s)
    for s in ["TBD", "TODO", "待补充", "<hash>", "<measured>"]:
        require(s not in text, "placeholder")
    return True

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", choices=tuple(AUDITS))
    p.add_argument("--check-report", action="store_true")
    args = p.parse_args()
    if args.dataset:
        print(json.dumps(replay(args.dataset), sort_keys=True))
        return 0
    facts = []
    for dataset in AUDITS:
        out = subprocess.check_output([sys.executable, "-B", str(Path(__file__).resolve()),
                                       "--dataset", dataset], cwd=HERE, text=True)
        facts.append(json.loads(out))
    if args.check_report:
        audit_text(REPORT.read_text(), facts)
    print(json.dumps({"facts": facts, "report_checked": args.check_report,
                      "no_device_execution": True, "no_raw_artifacts_written": True}, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
