import json
from pathlib import Path

import pytest

from build_formal_evidence import ARMS, DATASETS, RUN_IDS, build


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def make_root(root: Path) -> None:
    write_json(root / "candidate" / "activation.json", {"ok": True})
    for arm in ARMS:
        write_json(root / arm / "identity.json", {"arm": arm})
        for run_id in RUN_IDS:
            write_json(root / arm / f"performance.{run_id}.json", {"config": {}})
            write_json(
                root / arm / f"performance.{run_id}.metrics.before.json",
                {"prefix_cache_hits_total": 1},
            )
            write_json(
                root / arm / f"performance.{run_id}.metrics.after.json",
                {"prefix_cache_hits_total": 2},
            )
        for dataset in DATASETS:
            for run_id in RUN_IDS:
                quality = root / "quality" / arm
                write_json(
                    quality / f"{dataset}.{run_id}.summary.json",
                    {"dataset": dataset},
                )
                (quality / f"{dataset}.{run_id}.jsonl").write_text(
                    json.dumps({"index": 0, "ok": True}) + "\n",
                    encoding="utf-8",
                )


def test_build_uses_fixed_local_artifact_layout(tmp_path):
    make_root(tmp_path)
    result = build(tmp_path)
    assert result["schema"] == "dasc-formal-v13-normalized/v1"
    assert set(result["arms"]) == set(ARMS)
    assert result["candidate_activation"] == {"ok": True}
    assert [x["run_id"] for x in result["arms"]["dense"]["performance"]] == list(
        RUN_IDS
    )
    assert result["arms"]["candidate"]["quality"]["gsm8k"][2]["details"] == [
        {"index": 0, "ok": True}
    ]


def test_build_fails_closed_on_missing_raw_artifact(tmp_path):
    make_root(tmp_path)
    (tmp_path / "dense" / "performance.run2.metrics.after.json").unlink()
    with pytest.raises(FileNotFoundError):
        build(tmp_path)
