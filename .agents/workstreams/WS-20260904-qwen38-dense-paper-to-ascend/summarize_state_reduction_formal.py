#!/usr/bin/env python3
"""Audit and render the formal Qwen3.6 DRRQR Ascend piercing report."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import socket
import statistics
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ARMS = {
    "baseline": {
        "served": "qwen36-state-reduction-baseline",
        "checkpoint": "/cache/efim/Qwen3.6-27B",
    },
    "drrqr-dk64": {
        "served": "qwen36-state-reduction-drrqr-dk64",
        "checkpoint": "/cache/cch/Qwen3.6-27B-gdn-drrqr-dk64",
    },
    "drrqr-dk96": {
        "served": "qwen36-state-reduction-drrqr-dk96",
        "checkpoint": "/cache/cch/Qwen3.6-27B-gdn-drrqr-dk96",
    },
}
QUALITY = {
    "longbenchv2": {
        "rows": 127,
        "sha256": "cdaa9e98deaefbba86f5eadeb287dd2ae90ed8f33313587dc547218b770fa39a",
    },
    "gsm8k": {
        "rows": 1319,
        "sha256": "3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14",
    },
}
EVALUATOR_SHA256 = "9c8cf4204964220acd31adc8a3f73332374f123e1b8681a522b33eff33504cc0"
MANIFEST_SHA256 = {
    "drrqr-dk64": "2eaa9a14fffe3dc0cd37906e08bee857be7c9ce2ed761f693a99a0ef02d90c0d",
    "drrqr-dk96": "a8f8f162f15fb6e4717ed509927d93c549a2ef01eca4c88e45e75cdf900b16fc",
}
CANDIDATE_ARM = "drrqr-dk96"
PERF_METRICS = (
    "ttft_mean_ms",
    "tpot_mean_ms",
    "output_tokens_per_second",
    "benchmark_duration_s",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def finite(value: Any, label: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label}: expected finite numeric value")
    return result


def aggregate(values: list[float]) -> dict[str, float]:
    return {
        "mean": statistics.fmean(values),
        "sample_stddev": statistics.stdev(values) if len(values) > 1 else 0.0,
        "min": min(values),
        "max": max(values),
        "range": max(values) - min(values),
    }


def audit_performance(path: Path, arm: str) -> dict[str, Any]:
    data = load_object(path)
    config = data.get("config", {})
    expected = {
        "model": ARMS[arm]["served"],
        "input_tokens": 32768,
        "prefix_tokens": 16384,
        "output_tokens": 1024,
        "requests": 40,
        "concurrency": 16,
        "warmup_requests": 2,
        "ignore_eos": True,
        "segment_ends": [16384, 32768],
    }
    drift = {
        key: {"observed": config.get(key), "expected": wanted}
        for key, wanted in expected.items()
        if config.get(key) != wanted
    }
    if drift:
        raise ValueError(f"{path}: performance contract drift: {drift}")
    summary = data.get("summary", {})
    if (
        summary.get("requests") != 40
        or summary.get("successful") != 40
        or summary.get("failed") != 0
        or summary.get("fixed_output_verified") is not True
        or summary.get("output_tokens") != 40960
    ):
        raise ValueError(f"{path}: incomplete fixed-output performance run")
    return {
        "path": str(path),
        "sha256": sha256(path),
        "metrics": {
            key: finite(summary.get(key), f"{path}:{key}")
            for key in PERF_METRICS
        },
        "successful": 40,
        "failed": 0,
    }


def audit_details(path: Path, rows: int) -> dict[str, Any]:
    accepted: dict[int, dict[str, Any]] = {}
    total_lines = 0
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        total_lines += 1
        row = json.loads(raw)
        if not isinstance(row, dict):
            raise ValueError(f"{path}: non-object JSONL row")
        index = row.get("index")
        if isinstance(index, int) and row.get("ok") is True:
            accepted[index] = row
    expected_indexes = set(range(rows))
    observed_indexes = set(accepted)
    if observed_indexes != expected_indexes:
        missing = sorted(expected_indexes - observed_indexes)
        extra = sorted(observed_indexes - expected_indexes)
        raise ValueError(
            f"{path}: index mismatch missing={missing[:20]} extra={extra[:20]}"
        )
    return {
        "path": str(path),
        "sha256": sha256(path),
        "total_lines": total_lines,
        "accepted_unique_indexes": len(accepted),
    }


def audit_quality(path: Path, arm: str, dataset: str) -> dict[str, Any]:
    data = load_object(path)
    spec = QUALITY[dataset]
    rows = spec["rows"]
    expected = {
        "dataset": dataset,
        "model": ARMS[arm]["served"],
        "requests": rows,
        "successful": rows,
        "failed": 0,
        "concurrency": 32,
        "max_out_len": 1024,
        "seed": 0,
        "temperature": 0,
        "enable_thinking": False,
        "ignore_eos": False,
        "data_sha256": spec["sha256"],
        "evaluator_script_sha256": EVALUATOR_SHA256,
        "unique_response_sha256": rows,
    }
    drift = {
        key: {"observed": data.get(key), "expected": wanted}
        for key, wanted in expected.items()
        if data.get(key) != wanted
    }
    if drift:
        raise ValueError(f"{path}: quality contract drift: {drift}")
    details = Path(data["details_path"])
    if not details.is_file():
        raise ValueError(f"{path}: details file missing: {details}")
    audited_details = audit_details(details, rows)
    if audited_details["sha256"] != data.get("details_sha256"):
        raise ValueError(f"{path}: details SHA256 mismatch")
    return {
        "path": str(path),
        "sha256": sha256(path),
        "details": audited_details,
        "accuracy_pct": finite(data.get("accuracy_pct"), f"{path}:accuracy_pct"),
        "correct": int(data["correct"]),
        "successful": rows,
        "failed": 0,
        "finish_reasons": data.get("finish_reasons"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()
    errors: list[str] = []
    failure_ledger_path = (
        Path(__file__).parent / "experiment-failures-state-reduction-qwen36.json"
    )
    failure_ledger = load_object(failure_ledger_path)
    failures = failure_ledger.get("failures")
    if not isinstance(failures, list):
        raise ValueError(f"{failure_ledger_path}: failures must be a list")
    performance = {arm: [] for arm in ARMS}
    quality = {
        arm: {dataset: [] for dataset in QUALITY}
        for arm in ARMS
    }

    for arm, expected_sha256 in MANIFEST_SHA256.items():
        manifest = Path(ARMS[arm]["checkpoint"]) / "drrqr_manifest.json"
        if not manifest.is_file():
            errors.append(f"missing {manifest}")
        elif sha256(manifest) != expected_sha256:
            errors.append(f"{manifest}: SHA256 drift")

    for arm in ARMS:
        for run_index in range(1, 4):
            path = args.root / arm / f"performance.run{run_index}.json"
            if not path.is_file():
                errors.append(f"missing {path}")
            else:
                try:
                    performance[arm].append(audit_performance(path, arm))
                except Exception as exc:
                    errors.append(str(exc))
        for dataset in QUALITY:
            for run_index in range(1, 4):
                path = (
                    args.root / arm / "quality"
                    / f"{dataset}.run{run_index}.summary.json"
                )
                if not path.is_file():
                    errors.append(f"missing {path}")
                else:
                    try:
                        quality[arm][dataset].append(
                            audit_quality(path, arm, dataset)
                        )
                    except Exception as exc:
                        errors.append(str(exc))

    perf_aggregate = {arm: {} for arm in ARMS}
    for arm in ARMS:
        if len(performance[arm]) == 3:
            for metric in PERF_METRICS:
                perf_aggregate[arm][metric] = aggregate(
                    [item["metrics"][metric] for item in performance[arm]]
                )

    relative_change: dict[str, float] = {}
    repeat_separated: dict[str, bool] = {}
    if all(len(performance[arm]) == 3 for arm in ARMS):
        for metric in PERF_METRICS:
            baseline = perf_aggregate["baseline"][metric]
            treatment = perf_aggregate[CANDIDATE_ARM][metric]
            relative_change[metric] = (
                treatment["mean"] / baseline["mean"] - 1.0
            ) * 100.0
            lower_is_better = metric != "output_tokens_per_second"
            repeat_separated[metric] = (
                treatment["max"] < baseline["min"]
                if lower_is_better
                else treatment["min"] > baseline["max"]
            )

    quality_aggregate = {arm: {} for arm in ARMS}
    for arm in ARMS:
        for dataset in QUALITY:
            if len(quality[arm][dataset]) == 3:
                quality_aggregate[arm][dataset] = aggregate(
                    [item["accuracy_pct"] for item in quality[arm][dataset]]
                )

    quality_gate: dict[str, dict[str, Any]] = {}
    for dataset in QUALITY:
        if all(dataset in quality_aggregate[arm] for arm in ARMS):
            baseline = quality_aggregate["baseline"][dataset]
            treatment = quality_aggregate[CANDIDATE_ARM][dataset]
            loss = baseline["mean"] - treatment["mean"]
            quality_gate[dataset] = {
                "baseline_mean_accuracy_pct": baseline["mean"],
                "baseline_repeat_range_pp": baseline["range"],
                "treatment_mean_accuracy_pct": treatment["mean"],
                "treatment_delta_pp": treatment["mean"] - baseline["mean"],
                "observed_loss_pp": loss,
                "pass": loss <= baseline["range"],
            }

    quality_complete = len(quality_gate) == len(QUALITY)
    quality_pass = (
        quality_complete
        and all(item["pass"] for item in quality_gate.values())
    )
    profile_required = quality_pass
    profile_path = args.root / "profile" / "profile-evidence.json"
    profile = None
    if profile_path.is_file():
        try:
            profile = load_object(profile_path)
            if profile.get("verified") is not True:
                errors.append(f"{profile_path}: verified is not true")
        except Exception as exc:
            errors.append(str(exc))
    elif profile_required:
        errors.append(f"missing {profile_path}")
    else:
        profile = {
            "verified": False,
            "status": (
                "not-run-by-preregistered-quality-gate"
                if quality_complete
                else "not-yet-run-quality-incomplete"
            ),
            "reason": (
                "Native profiling is intentionally skipped when any Dk96 "
                "quality dataset fails its baseline-variability gate."
                if quality_complete
                else "Native profiling cannot start before all Dk96 quality "
                "repetitions and gates are complete."
            ),
        }

    units_complete = (
        all(len(performance[arm]) == 3 for arm in ARMS)
        and all(
            len(quality[arm][dataset]) == 3
            for arm in ARMS
            for dataset in QUALITY
        )
        and (
            not profile_required
            or (
                profile is not None
                and profile.get("verified") is True
            )
        )
    )
    complete = units_complete and not errors
    serving_benefit = bool(relative_change) and (
        relative_change["output_tokens_per_second"] > 0
        and relative_change["benchmark_duration_s"] < 0
    )
    if not complete:
        decision = "in-progress-no-final-claim"
    elif not quality_pass:
        decision = "reject-dk64-and-dk96-under-frozen-quality-gate"
    elif serving_benefit:
        decision = "dk96-mean-serving-benefit-observed-within-frozen-ruler"
    else:
        decision = "dk96-quality-passes-but-no-serving-benefit"

    report = {
        "schema": "state-reduction-formal-summary/v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "complete" if complete else "in-progress",
        "paper": {
            "title": "The Key to State Reduction in Linear Attention: A Rank-based Perspective",
            "arxiv": "2602.04852v2",
            "official_commit": "919d8667d951c385e08510bc1267c2e7049a4f56",
        },
        "scope": {
            "model": "Qwen3.6-27B",
            "topology": "TP4 on host NPU4-7; container-visible NPU0-3",
            "baseline": "Dk128 unmodified checkpoint",
            "treatments": "official Strong-RRQR joint Q/K selection, Dk64 rejected then independent Dk96 fallback",
            "decision_candidate": CANDIDATE_ARM,
            "calibration": "adapted 16x2048-token LongBench-v2; not paper-exact FineWeb-Edu",
            "quality": "LongBench-v2 127 and GSM8K 1319; CEval excluded; NIAH+ absent",
        },
        "performance_runs": performance,
        "performance_aggregate": perf_aggregate,
        "relative_change_percent": relative_change,
        "repeat_ranges_separated": repeat_separated,
        "quality_runs": quality,
        "quality_aggregate": quality_aggregate,
        "quality_gate": quality_gate,
        "profile": profile,
        "profile_required_by_preregistered_gate": profile_required,
        "serving_benefit_gate_pass": serving_benefit,
        "quality_gate_pass": quality_pass,
        "decision": decision,
        "drrqr_dk64_disposition": "rejected: GSM8K loss exceeded the baseline three-run range",
        "failure_ledger": {
            "path": str(failure_ledger_path),
            "sha256": sha256(failure_ledger_path),
            "entries": failures,
        },
        "errors": errors,
    }
    output_json = args.root / "state-reduction-summary.json"
    output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# DRRQR 算法特性穿刺 · 完整实例（含命令）",
        "",
        "> 论文：The Key to State Reduction in Linear Attention: A Rank-based Perspective",
        "> 模型：Qwen3.6-27B｜设备：4× Ascend 910B4｜状态：" + report["status"],
        "",
        "---",
        "",
        "## Step 0. 环境准备",
        "",
        "- 主机资源：NPU4-7、CPU0-95、TP4；NPU0-3 为受保护外部任务。",
        "- 镜像：sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1。",
        "- 官方代码：camail-official/LinearAttentionPruning，commit 919d8667d951c385e08510bc1267c2e7049a4f56。",
        "- 校准适配：FineWeb-Edu 缺失，使用哈希冻结的 LongBench-v2 16×2048 token；不得称为论文原始校准。",
        "",
        "## Step 1-3. 捕获、DRRQR 转换、服务测试",
        "",
        "~~~bash",
        "bash .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/run_state_reduction_capture.sh",
        "",
        "# Dk64：50% Q/K state reduction",
        "docker run --rm --network none -v /cache:/cache sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1 python3 /cache/cch/.worktrees/WS-20260904-qwen38-dense-paper-to-ascend/.agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/build_qwen36_drrqr_checkpoint.py --src /cache/efim/Qwen3.6-27B --dst /cache/cch/Qwen3.6-27B-gdn-drrqr-dk64 --capture-dir /cache/cch/state-reduction-qwen36-formal-npu4-7-tp4-20260906/calibration/captures --calibration-jsonl /cache/cch/state-reduction-qwen36-formal-npu4-7-tp4-20260906/calibration/longbenchv2-16x2048-tokenids.jsonl --official-rrqr /cache/cch/LinearAttentionPruning/src/key_reduction/pruners/rrqr.py --new-head-k-dim 64 --expected-linear-layers 48 --tp-size 4 --captures-per-rank 16",
        "",
        "# Dk96：Dk64 质量失败后，独立执行 25% fallback",
        "docker run --rm --network none -v /cache:/cache sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1 python3 /cache/cch/.worktrees/WS-20260904-qwen38-dense-paper-to-ascend/.agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/build_qwen36_drrqr_checkpoint.py --src /cache/efim/Qwen3.6-27B --dst /cache/cch/Qwen3.6-27B-gdn-drrqr-dk96 --capture-dir /cache/cch/state-reduction-qwen36-formal-npu4-7-tp4-20260906/calibration/captures --calibration-jsonl /cache/cch/state-reduction-qwen36-formal-npu4-7-tp4-20260906/calibration/longbenchv2-16x2048-tokenids.jsonl --official-rrqr /cache/cch/LinearAttentionPruning/src/key_reduction/pruners/rrqr.py --new-head-k-dim 96 --expected-linear-layers 48 --tp-size 4 --captures-per-rank 16",
        "",
        "python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/state_reduction_formal_runner.py --arm baseline --phase performance",
        "python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/state_reduction_formal_runner.py --arm baseline --phase quality",
        "python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/state_reduction_formal_runner.py --arm drrqr-dk64 --phase performance",
        "python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/state_reduction_formal_runner.py --arm drrqr-dk64 --phase quality",
        "python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/state_reduction_formal_runner.py --arm drrqr-dk96 --phase performance",
        "python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/state_reduction_formal_runner.py --arm drrqr-dk96 --phase quality",
        "~~~",
        "",
        "主比较仅改变 checkpoint：Dk128 baseline 对 Dk64、Dk96 两个独立 official Strong RRQR treatment。捕获审计为 48 个真实 linear-attention layer ID × 4 TP ranks × 16 样本 = 3072 个文件；转换联合使用 post-conv Q/K 激活做 channel selection。Dk64 已因 GSM8K 门禁失败而淘汰；最终候选为 Dk96。",
        "",
    ]
    if relative_change:
        lines += [
            "## 实测性能结果",
            "",
            "| 指标 | Baseline均值 | DRRQR Dk96均值 | 变化 | 三次区间分离 |",
            "|---|---:|---:|---:|:---:|",
        ]
        for metric in PERF_METRICS:
            lines.append(
                f"| {metric} | {perf_aggregate['baseline'][metric]['mean']:.6f} | "
                f"{perf_aggregate[CANDIDATE_ARM][metric]['mean']:.6f} | "
                f"{relative_change[metric]:+.4f}% | {repeat_separated[metric]} |"
            )
        lines.append("")
        for arm in ARMS:
            lines += [
                f"### {arm} 三次原始性能",
                "",
                "| Run | TTFT ms | TPOT ms | output tok/s | duration s | artifact SHA256 |",
                "|---:|---:|---:|---:|---:|---|",
            ]
            for index, item in enumerate(performance[arm], start=1):
                metrics = item["metrics"]
                lines.append(
                    f"| {index} | {metrics['ttft_mean_ms']:.6f} | "
                    f"{metrics['tpot_mean_ms']:.6f} | "
                    f"{metrics['output_tokens_per_second']:.6f} | "
                    f"{metrics['benchmark_duration_s']:.6f} | "
                    f"`{item['sha256']}` |"
                )
            lines.append(
                f"| mean | {perf_aggregate[arm]['ttft_mean_ms']['mean']:.6f} | "
                f"{perf_aggregate[arm]['tpot_mean_ms']['mean']:.6f} | "
                f"{perf_aggregate[arm]['output_tokens_per_second']['mean']:.6f} | "
                f"{perf_aggregate[arm]['benchmark_duration_s']['mean']:.6f} | — |"
            )
            lines.append("")
    if quality_gate:
        lines += [
            "## 实测质量结果",
            "",
            "| 数据集 | Baseline均值 | Dk96均值 | Delta | Baseline三次范围 | 质量门 |",
            "|---|---:|---:|---:|---:|:---:|",
        ]
        for dataset, item in quality_gate.items():
            lines.append(
                f"| {dataset} | {item['baseline_mean_accuracy_pct']:.6f}% | "
                f"{item['treatment_mean_accuracy_pct']:.6f}% | "
                f"{item['treatment_delta_pp']:+.6f} pp | "
                f"{item['baseline_repeat_range_pp']:.6f} pp | {item['pass']} |"
            )
        lines.append("")
        lines += [
            "### Dk64 独立质量门结果",
            "",
            "| 数据集 | Dk64均值 | Delta vs baseline | Baseline三次范围 | 质量门 |",
            "|---|---:|---:|---:|:---:|",
        ]
        for dataset in QUALITY:
            baseline = quality_aggregate["baseline"][dataset]
            dk64 = quality_aggregate["drrqr-dk64"][dataset]
            loss = baseline["mean"] - dk64["mean"]
            lines.append(
                f"| {dataset} | {dk64['mean']:.6f}% | "
                f"{dk64['mean'] - baseline['mean']:+.6f} pp | "
                f"{baseline['range']:.6f} pp | {loss <= baseline['range']} |"
            )
        lines.append("")
        for dataset in QUALITY:
            if not all(
                dataset in quality_aggregate[arm]
                for arm in ("baseline", CANDIDATE_ARM)
            ):
                continue
            lines += [
                f"### {dataset} 三次原始质量",
                "",
                "| Arm | Run1 | Run2 | Run3 | mean | sample SD | range |",
                "|---|---:|---:|---:|---:|---:|---:|",
            ]
            for arm in ("baseline", "drrqr-dk64", CANDIDATE_ARM):
                runs = quality[arm][dataset]
                values = [item["accuracy_pct"] for item in runs]
                run_cells = [
                    f"{item['correct']}/{item['successful']} "
                    f"({item['accuracy_pct']:.6f}%)"
                    for item in runs
                ]
                agg = quality_aggregate[arm][dataset]
                lines.append(
                    f"| {arm} | {' | '.join(run_cells)} | "
                    f"{agg['mean']:.6f}% | {agg['sample_stddev']:.6f} pp | "
                    f"{agg['range']:.6f} pp |"
                )
            lines.append("")
    lines += [
        "## Native profiling",
        "",
    ]
    if profile_required:
        if profile is not None and profile.get("verified") is True:
            lines.append("- 质量门通过，baseline 与 Dk96 同工作负载 native profile 已验证。")
        else:
            lines.append("- 质量门通过，native profile 是必需项但尚未形成已验证证据。")
    elif quality_complete:
        lines.append(
            "- 因至少一个 Dk96 质量门失败，按预注册规则不启动 profiling；"
            "这不是证据缺失，也不得据此推断算子性能。"
        )
    else:
        lines.append("- Dk96 重复质量尚未完成；profiling 尚未获准启动。")
    lines.append("")
    lines += [
        "## 结论",
        "",
        f"- 决策状态：{decision}。",
        "- Dk64（50%）和 Dk96（25%）均因 GSM8K 三轮均值损失超过同分母 baseline 波动范围而拒绝；本冻结场景没有可采用的裁剪比例。",
        "- Dk96 性能均值方向略有利（约 0.33%-0.44%），但三轮区间全部重叠，不能声称稳定 serving 加速。",
        "- 已验证论文机制可在该 Qwen3.6/Ascend 栈完成捕获、结构裁剪、加载和真实服务；由于校准数据不是 FineWeb-Edu，且质量门失败，这不是 paper-exact reproduction，也不是收益复现。",
        "- 论文的 H100 训练 sequence-mixer 1.32× 不是本 Ascend vLLM 全模型 serving 实验的同分母对照。",
        "- Dk64 已因 GSM8K 超出基线三轮波动范围而拒绝；Dk96 是预声明的独立 25% 裁剪回退，不混合两者结果。",
        "",
        "## 失败与证据边界",
        "",
    ]
    lines += [
        "| 阶段 | 分类 | 是否开始测量 | 恢复方法 |",
        "|---|---|---|---|",
    ]
    for item in failures:
        stage = str(item.get("stage", "")).replace("|", "\\|")
        classification = str(item.get("classification", "")).replace("|", "\\|")
        measurement = str(item.get("measurement_started", "")).replace("|", "\\|")
        recovery = str(item.get("recovery", "")).replace("|", "\\|")
        lines.append(
            f"| {stage} | {classification} | {measurement} | {recovery} |"
        )
    lines.append("")
    if errors:
        lines.extend(f"- {item}" for item in errors)
    else:
        lines.append("- 无缺失或无效证据。")
    lines += [
        "",
        "详细失败及恢复见 experiment-failures-state-reduction-qwen36.json；编排失败不自动等价于算法失败。",
        "",
        "## Recovery / resume",
        "",
        "~~~bash",
        "cat /cache/cch/state-reduction-qwen36-formal-npu4-7-tp4-20260906/controller-status.json",
        "python3 /cache/cch/.worktrees/WS-20260904-qwen38-dense-paper-to-ascend/.agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/state_reduction_formal_runner.py --arm drrqr-dk96 --phase quality",
        "python3 /cache/cch/.worktrees/WS-20260904-qwen38-dense-paper-to-ascend/.agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/state_reduction_native_profile.py --arm baseline",
        "python3 /cache/cch/.worktrees/WS-20260904-qwen38-dense-paper-to-ascend/.agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/state_reduction_native_profile.py --arm drrqr-dk96",
        "~~~",
        "",
        "恢复前必须先确认权威 operation 已终止、无同名 controller、NPU4-7 为空且 8225 端口空闲；"
        "若质量门失败，不执行两条 profile 命令。",
        "",
    ]
    report_path = args.root / "STATE_REDUCTION_PIERCING_REPORT.md"
    report_path.write_text(
        "\n".join(lines), encoding="utf-8"
    )
    npu_release = {}
    for device in (4, 5, 6, 7):
        result = subprocess.run(
            ["npu-smi", "info", "-t", "proc-mem", "-i", str(device)],
            text=True,
            capture_output=True,
            check=False,
        )
        npu_release[str(device)] = {
            "exit_code": result.returncode,
            "no_process": "No process in device" in result.stdout,
        }
    container_result = subprocess.run(
        [
            "docker", "inspect", "-f",
            "{{json .State}}",
            "qwen36_state_reduction_drrqr_dk96_npu4_7_tp4",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    container_state = (
        json.loads(container_result.stdout)
        if container_result.returncode == 0
        else {"inspect_error": container_result.stderr}
    )
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        port_free = probe.connect_ex(("127.0.0.1", 8225)) != 0
    resource_released = (
        container_result.returncode == 0
        and container_state.get("Status") == "exited"
        and container_state.get("ExitCode") == 0
        and container_state.get("OOMKilled") is False
        and all(item["exit_code"] == 0 and item["no_process"] for item in npu_release.values())
        and port_free
    )
    final_audit = {
        "schema": "state-reduction-final-evidence-audit/v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "verified": complete and resource_released,
        "decision": decision,
        "summary": {
            "path": str(output_json),
            "sha256": sha256(output_json),
            "status": report["status"],
            "errors": len(errors),
        },
        "report": {
            "path": str(report_path),
            "sha256": sha256(report_path),
        },
        "artifact_counts": {
            "performance_runs": sum(len(items) for items in performance.values()),
            "quality_summaries": sum(
                len(items)
                for arm in quality.values()
                for items in arm.values()
            ),
            "quality_detail_files": sum(
                len(items)
                for arm in quality.values()
                for items in arm.values()
            ),
        },
        "profile": {
            "required": profile_required,
            "status": profile.get("status") if profile else None,
            "verified": profile.get("verified") if profile else None,
        },
        "resource_release": {
            "verified": resource_released,
            "container_state": container_state,
            "host_npu_4_7": npu_release,
            "port_8225_free": port_free,
            "npu_0_3_inspected": False,
        },
    }
    final_audit_path = args.root / "final-evidence-audit.json"
    final_audit_path.write_text(
        json.dumps(final_audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if not final_audit["verified"]:
        raise RuntimeError(f"{final_audit_path}: final evidence/resource audit failed")
    if complete or args.allow_incomplete:
        print(json.dumps({
            "status": report["status"],
            "decision": decision,
            "errors": len(errors),
        }))
        return 0
    for error in errors:
        print(error)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
