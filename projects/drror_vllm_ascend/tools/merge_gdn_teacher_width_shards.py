#!/usr/bin/env python3
"""Merge three complete DRRQR candidate-width shards and apply frozen gates."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import time


RESULT_ROOT = Path("/drrqr-results")
ROOT = Path(__file__).resolve().parents[1]
WIDTH_SCRIPT = ROOT / "tools/replay_gdn_teacher_width_curve.py"
VARIANTS = ("energy48", "energy64", "energy80")


def require(value, message):
    if not value:
        raise ValueError(message)


def checksum(path):
    digest = __import__("hashlib").sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_width_module():
    spec = importlib.util.spec_from_file_location("width_curve_merge", WIDTH_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def combine_fidelity_rows(rows_by_variant):
    combined = {}
    for variant in VARIANTS:
        field = variant + "_relative_l2"
        rows = rows_by_variant.get(variant)
        require(isinstance(rows, list), variant + " fidelity rows missing")
        for row in rows:
            require(
                set(row)
                == {"sequence_id", "rank", "layer", "position", field},
                variant + " fidelity row schema differs",
            )
            key = (
                row["sequence_id"],
                row["rank"],
                row["layer"],
                row["position"],
            )
            require(
                field not in combined.setdefault(key, {}),
                "duplicate fidelity row",
            )
            combined[key][field] = row[field]
    return [
        {
            "sequence_id": key[0],
            "rank": key[1],
            "layer": key[2],
            "position": key[3],
            **values,
        }
        for key, values in sorted(combined.items())
    ]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for variant in VARIANTS:
        parser.add_argument("--" + variant + "-report", type=Path, required=True)
        parser.add_argument("--" + variant + "-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    output = args.output_dir
    require(
        output.is_absolute()
        and output == output.resolve()
        and RESULT_ROOT in output.parents
        and not output.exists(),
        "fresh canonical output below /drrqr-results required",
    )
    output.mkdir(parents=False, exist_ok=False)
    width = load_width_module()
    documents = {}
    provenance = {}
    rows_by_variant = {}
    common = None
    layers = None
    for variant in VARIANTS:
        path = getattr(args, variant + "_report")
        expected_sha = getattr(args, variant + "_sha256")
        require(checksum(path) == expected_sha, variant + " report hash mismatch")
        document = json.loads(path.read_text(encoding="utf-8"))
        require(
            document.get("schema") == "drrqr-captured-teacher-width-curve/v1"
            and document.get("status") == "width_shard_pass"
            and document.get("candidate_numerical_gate_passed") is True
            and document.get("protocol", {}).get("variants") == [variant],
            variant + " shard did not complete its numerical contract",
        )
        identity = {
            "script_sha256": document.get("script_sha256"),
            "captured_reference_helper_sha256": document.get(
                "captured_reference_helper_sha256"
            ),
            "bindings": document.get("bindings"),
            "prior_dense_evidence": document.get("prior_dense_evidence"),
        }
        if common is None:
            common = identity
            layers = document["protocol"]["layers"]
        require(identity == common, "shard source/binding/dense identity differs")
        rows_path = Path(document["token_fidelity"]["path"])
        require(
            checksum(rows_path) == document["token_fidelity"]["sha256"],
            variant + " token-fidelity hash mismatch",
        )
        rows = json.loads(rows_path.read_text(encoding="utf-8"))
        rows_by_variant[variant] = rows
        documents[variant] = document
        provenance[variant] = {
            "report": str(path),
            "sha256": expected_sha,
            "token_fidelity": document["token_fidelity"],
            "trajectory_count": len(document["trajectories"]),
        }

    rows = combine_fidelity_rows(rows_by_variant)
    fidelity = width.fidelity_screen(rows, layers)
    rows_path = output / "token-fidelity.json"
    rows_path.write_text(json.dumps(rows, allow_nan=False) + "\n", encoding="utf-8")
    report = {
        "schema": "drrqr-captured-teacher-width-curve-merge/v1",
        "status": "width_curve_pass" if fidelity["passed"] else "width_curve_failed",
        "claim": width.CLAIM,
        "created_unix_ns": time.time_ns(),
        "width_script_sha256": checksum(WIDTH_SCRIPT),
        "shards": provenance,
        "dense_capture_gate_passed": True,
        "candidate_numerical_gate_passed": True,
        "full_layer_capture_admitted": fidelity["passed"],
        "performance_admitted": False,
        "task_accuracy_admitted": False,
        "fidelity": fidelity,
        "token_fidelity": {
            "path": str(rows_path),
            "sha256": checksum(rows_path),
        },
    }
    report_path = output / "report.json"
    report_path.write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": report["status"], "report": str(report_path)}))
    return 0 if report["status"] == "width_curve_pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
