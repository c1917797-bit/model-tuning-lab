from pathlib import Path
import importlib.util


MODULE_PATH = Path(__file__).with_name("run_v12r14_all_heads_bridge_control.py")
SPEC = importlib.util.spec_from_file_location("run_v12r14_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
trial = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trial)


def test_v12r14_has_distinct_all_heads_identity():
    assert trial.controller.RESULT.name == "request-owned-all-heads-control-v12r14"
    assert trial.controller.CONTAINER == "dasc_qwen36_all_heads_bridge_v12r14_20260916"
    assert trial.controller.W_MAX == "1e-9"


def test_all_heads_threshold_is_forwarded_to_container(monkeypatch):
    captured = []
    monkeypatch.setattr(
        trial.controller,
        "run",
        lambda args, **_kwargs: captured.append(args) or "container-id",
    )
    assert trial.controller.launch() == "container-id"
    command = captured[-1]
    assert "MST_DASC_W_MAX=1e-9" in command


def test_all_heads_verdict_requires_every_rank_layer_and_dense_bytes():
    rows = []
    for pid in range(4):
        rows.append(
            {
                "event": "tp_geometry_aligned",
                "pid": pid,
                "extra_local_heads": 0,
                "local_counts": [12] * 48,
                "common_counts": [12] * 48,
            }
        )
        for layer in range(48):
            rows.append(
                {
                    "event": "physical_cache_bound",
                    "pid": pid,
                    "layer": layer,
                    "allocation_matches_spec": True,
                    "actual_page_bytes": 1588224,
                    "compact_page_bytes": 1588224,
                    "dense_page_bytes": 1588224,
                }
            )
    assert trial.all_heads_evidence_verdict(rows)["ok"] is True
    rows[-1]["compact_page_bytes"] = 605184
    assert trial.all_heads_evidence_verdict(rows)["ok"] is False


def test_main_validates_only_after_inner_success(monkeypatch):
    calls = []
    monkeypatch.setattr(trial.trial, "main", lambda: 0)
    monkeypatch.setattr(trial, "validate_all_heads_evidence", lambda: calls.append(True))
    assert trial.main() == 0
    assert calls == [True]

    calls.clear()
    monkeypatch.setattr(trial.trial, "main", lambda: 7)
    assert trial.main() == 7
    assert calls == []
