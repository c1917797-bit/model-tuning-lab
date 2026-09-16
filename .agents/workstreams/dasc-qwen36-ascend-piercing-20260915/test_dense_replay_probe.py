from pathlib import Path
import importlib.util


MODULE_PATH = Path(__file__).with_name("run_dense_replay_probe.py")
SPEC = importlib.util.spec_from_file_location("dense_replay_probe_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


def test_dense_probe_uses_exact_dasc_long_request(monkeypatch, tmp_path):
    payloads = []
    monkeypatch.setattr(probe, "metric_sum", lambda *_args: 1536.0 * len(payloads))

    def fake_post(_base_url, payload):
        payloads.append(payload)
        return {
            "choices": [
                {
                    "message": {"content": "VERIFIED"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 1938},
        }, 1.0

    monkeypatch.setattr(probe, "post", fake_post)
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_dense_replay_probe.py",
            "--output-dir",
            str(tmp_path),
            "--activation",
            str(tmp_path / "unused.jsonl"),
        ],
    )

    assert probe.main() == 0
    assert len(payloads) == 3
    assert payloads[0] == payloads[1] == payloads[2]
    payload = payloads[0]
    assert payload["messages"][0]["content"] == (
        "Follow the requested exact output. Do not show hidden reasoning."
    )
    assert payload["messages"][1]["content"].endswith(
        "Question: Return exactly the word VERIFIED."
    )
    assert payload["messages"][1]["content"].count("DASC recurrent-state reuse") == 100
    assert payload["temperature"] == 0
    assert payload["seed"] == 0
    assert payload["max_tokens"] == 16
    assert payload["chat_template_kwargs"] == {"enable_thinking": False}

