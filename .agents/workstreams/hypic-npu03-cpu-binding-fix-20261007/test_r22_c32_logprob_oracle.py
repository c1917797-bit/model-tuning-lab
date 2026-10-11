"""Host-only regression checks for the bounded r22 logprob request seam."""

from __future__ import annotations

import io
import json
from types import SimpleNamespace

import pytest

import r22_c32_logprob_oracle as r22
import r22_c32_logprob_oracle_audit as audit


ITEM = {
    "index": 82,
    "prompt": "Bounded synthetic prompt",
    "prompt_tokens": 12,
    "boundary": 8,
}
QUALITY = SimpleNamespace(
    MODEL_NAME="Qwen3.6-27B",
    BASE_URL="http://127.0.0.1:8223",
)


def _body(*, logprobs=True):
    choice = {
        "message": {"content": "A"},
        "finish_reason": "stop",
    }
    if logprobs:
        choice["logprobs"] = {
            "content": [{
                "token": "A",
                "logprob": -0.1,
                "top_logprobs": [
                    {"token": "A", "logprob": -0.1},
                    {"token": "B", "logprob": -2.0},
                ],
            }],
        }
    return {
        "id": "chatcmpl-test",
        "usage": {"prompt_tokens": 12, "completion_tokens": 1},
        "choices": [choice],
    }


def test_only_target_scored_request_is_traced(monkeypatch):
    seen = []
    def fake_open(request, timeout):
        seen.append((json.loads(request.data), timeout))
        return io.BytesIO(json.dumps(_body()).encode())
    monkeypatch.setattr(r22, "urlopen", fake_open)
    original = lambda item, max_tokens: {"delegated": (item["index"], max_tokens)}
    assert r22.traced_request(ITEM, 1, original, QUALITY, 900) == {
        "delegated": (82, 1)}
    assert r22.traced_request({**ITEM, "index": 81}, 2048,
                              original, QUALITY, 900) == {
        "delegated": (81, 2048)}
    row = r22.traced_request(ITEM, 2048, original, QUALITY, 900)
    assert row["response_text"] == "A"
    assert row["token_logprobs"][0]["top_logprobs"][0]["token"] == "A"
    assert len(seen) == 1
    payload, timeout = seen[0]
    assert timeout == 900
    assert payload["logprobs"] is True and payload["top_logprobs"] == 5
    assert payload["vllm_xargs"]["hypic_segment_ends"] == [8, 12]
    assert payload["max_tokens"] == 2048
    assert payload["temperature"] == 0 and payload["seed"] == 0
    assert payload["ignore_eos"] is False


def test_missing_logprobs_fail_closed(monkeypatch):
    monkeypatch.setattr(
        r22, "urlopen",
        lambda request, timeout: io.BytesIO(
            json.dumps(_body(logprobs=False)).encode()),
    )
    with pytest.raises(RuntimeError, match="logprob or token accounting"):
        r22.traced_request(ITEM, 2048, lambda *_: None, QUALITY, 900)


def test_first_divergence_and_margin_are_bounded():
    assert audit._first_difference(["A", "B"], ["A", "C"]) == 1
    assert audit._first_difference(["A"], ["A", "B"]) == 1
    assert audit._first_difference(["A"], ["A"]) is None
    assert audit._margin({"top_logprobs": [
        {"logprob": -0.1}, {"logprob": -1.6},
    ]}) == pytest.approx(1.5)
    assert audit._margin({"top_logprobs": [{"logprob": -0.1}]}) is None
    assert audit.seam()["enable"] == ["0", "1"]
