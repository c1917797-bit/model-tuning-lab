#!/usr/bin/env python3
"""Cache-hit adapter around the already validated HYPIC quality evaluator."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import urllib.request


BASE_EVALUATOR_RELATIVE = Path(
    ".agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/"
    "hypic_quality_eval.py"
)
BASE_EVALUATOR_SHA256 = (
    "9c8cf4204964220acd31adc8a3f73332374f123e1b8681a522b33eff33504cc0"
)
SCHEMA = "mst.dasc.cache-hit-quality/v1"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_shared_prefix(lines: int) -> str:
    if lines < 1:
        raise ValueError("shared-prefix-lines must be positive")
    return "\n".join(
        (
            f"DASC neutral cache record {index:04d}: this calibration header is "
            "unrelated to the task and must not affect the answer."
        )
        for index in range(lines)
    )


def load_base(repo: Path):
    path = repo / BASE_EVALUATOR_RELATIVE
    actual = sha256_file(path)
    if actual != BASE_EVALUATOR_SHA256:
        raise RuntimeError(
            f"base evaluator SHA256 mismatch: expected {BASE_EVALUATOR_SHA256}, "
            f"observed {actual}"
        )
    spec = importlib.util.spec_from_file_location("dasc_hypic_quality_base", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load base evaluator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def metric_snapshot(base_url: str) -> dict[str, float]:
    selected: dict[str, float] = {}
    needles = (
        "prefix_cache_queries_total",
        "prefix_cache_hits_total",
        "prompt_tokens_cached_total",
        "request_success_total",
    )
    with urllib.request.urlopen(base_url.rstrip("/") + "/metrics", timeout=30) as response:
        body = response.read().decode("utf-8")
    for line in body.splitlines():
        if line.startswith("#") or not any(needle in line for needle in needles):
            continue
        name, value = line.rsplit(" ", 1)
        selected[name] = float(value)
    return selected


def metric_sum(snapshot: dict[str, float], needle: str) -> float:
    return sum(value for name, value in snapshot.items() if needle in name)


def atomic_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def parse_adapter_args(argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--shared-prefix-lines", type=int, default=96)
    parser.add_argument("--require-cache-hit", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_known_args(argv)


def parse_base_identity(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8221")
    parser.add_argument("--model", default="qwen36-dasc-formal")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    value, _ = parser.parse_known_args(argv)
    return value


def self_test(repo: Path, lines: int) -> int:
    base, path = load_base(repo)
    prefix = build_shared_prefix(lines)
    assert prefix == build_shared_prefix(lines)
    assert sha256_bytes(prefix.encode("utf-8")) == sha256_bytes(
        build_shared_prefix(lines).encode("utf-8")
    )
    assert base.score_case("longbenchv2", "The correct answer is (B)", "B")[1]
    assert base.score_case("gsm8k", "work\nanswer:42", "42")[1]
    print(
        json.dumps(
            {
                "ok": True,
                "base_evaluator": str(path),
                "base_evaluator_sha256": sha256_file(path),
                "shared_prefix_lines": lines,
                "shared_prefix_sha256": sha256_bytes(prefix.encode("utf-8")),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    adapter, base_argv = parse_adapter_args(raw_argv)
    if adapter.self_test:
        return self_test(adapter.repo, adapter.shared_prefix_lines)

    identity = parse_base_identity(base_argv)
    base, base_path = load_base(adapter.repo)
    prefix = build_shared_prefix(adapter.shared_prefix_lines)
    original_build_case = base.build_case

    def build_cache_hit_case(dataset: str, sample: dict) -> tuple[str, str]:
        prompt, reference = original_build_case(dataset, sample)
        return prefix + "\n\n" + prompt, reference

    base.build_case = build_cache_hit_case
    before = metric_snapshot(identity.base_url)
    saved_argv = sys.argv
    try:
        sys.argv = [str(base_path), *base_argv]
        base_exit = int(base.main())
    finally:
        sys.argv = saved_argv
    after = metric_snapshot(identity.base_url)

    summary_path = (
        identity.output_dir
        / f"{identity.dataset}.{identity.run_id}.summary.json"
    )
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    hit_delta = metric_sum(after, "prefix_cache_hits_total") - metric_sum(
        before, "prefix_cache_hits_total"
    )
    query_delta = metric_sum(after, "prefix_cache_queries_total") - metric_sum(
        before, "prefix_cache_queries_total"
    )
    summary["schema"] = SCHEMA
    summary["base_evaluator_path"] = str(base_path)
    summary["base_evaluator_sha256"] = sha256_file(base_path)
    summary["adapter_sha256"] = sha256_file(Path(__file__))
    summary["shared_prefix_lines"] = adapter.shared_prefix_lines
    summary["shared_prefix_bytes"] = len(prefix.encode("utf-8"))
    summary["shared_prefix_sha256"] = sha256_bytes(prefix.encode("utf-8"))
    summary["effective_prompt_contract_sha256"] = sha256_bytes(
        (
            summary["prompt_template_sha256"]
            + ":"
            + summary["shared_prefix_sha256"]
        ).encode("ascii")
    )
    summary["metrics_before"] = before
    summary["metrics_after"] = after
    summary["prefix_cache_query_delta"] = query_delta
    summary["prefix_cache_hit_delta"] = hit_delta
    summary["cache_hit_verified"] = hit_delta > 0
    summary["adapter_require_cache_hit"] = adapter.require_cache_hit
    atomic_json(summary_path, summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True))

    if base_exit != 0:
        return base_exit
    if adapter.require_cache_hit and hit_delta <= 0:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
