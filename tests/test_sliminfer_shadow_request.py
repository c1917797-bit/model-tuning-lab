from __future__ import annotations

import pytest

from tools.compare_sliminfer_shadow_outputs import compare_records
from tools.run_sliminfer_shadow_request import build_payload, canonical_response


def _record(text=" answer", prompt_tokens=13000):
    return {
        "schema": "sliminfer-shadow-request/v1",
        "model": "qwen36",
        "prompt_tokens_requested": prompt_tokens,
        "token_id": 100,
        "max_tokens": 1,
        "request_sha256": "same-request",
        "canonical_response": {
            "text": text,
            "finish_reason": "length",
            "stop_reason": None,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": 1,
        },
    }


def test_payload_uses_exact_token_id_count_and_deterministic_sampling():
    payload = build_payload("qwen36", prompt_tokens=13000, token_id=100)
    assert len(payload["prompt"]) == 13000
    assert set(payload["prompt"]) == {100}
    assert payload["temperature"] == 0.0
    assert payload["seed"] == 0
    assert payload["max_tokens"] == 1


def test_response_is_reduced_to_parity_fields():
    response = {
        "id": "variable",
        "created": 123,
        "choices": [
            {
                "index": 0,
                "text": " answer",
                "finish_reason": "length",
                "stop_reason": None,
            }
        ],
        "usage": {"prompt_tokens": 13000, "completion_tokens": 1},
    }
    assert canonical_response(response) == _record()["canonical_response"]


def test_compare_accepts_same_request_and_output():
    summary = compare_records(_record(), _record())
    assert summary["status"] == "passed"
    assert summary["request_sha256_equal"] is True


def test_compare_rejects_request_or_output_drift():
    with pytest.raises(ValueError, match="request fields"):
        compare_records(_record(), _record(prompt_tokens=12999))
    with pytest.raises(ValueError, match="response fields"):
        compare_records(_record(), _record(text=" different"))
