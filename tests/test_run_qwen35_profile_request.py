import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from qwen35_query_rewrite_bench import request_one
from run_qwen35_profile_request import cache_salt


class FakeStream:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def __iter__(self):
        event = {
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            "choices": [{"text": "x", "finish_reason": "stop"}],
        }
        return iter(
            [
                ("data: " + json.dumps(event) + "\n").encode(),
                b"data: [DONE]\n",
            ]
        )


def main():
    first = cache_salt("run-a", "profile", "a" * 64, 31)
    assert len(first) == 64
    assert first == cache_salt("run-a", "profile", "a" * 64, 31)
    assert first != cache_salt("run-b", "profile", "a" * 64, 31)
    assert first != cache_salt("run-a", "warmup", "a" * 64, 31)
    assert first != cache_salt("run-a", "profile", "a" * 64, 0)

    captured = {}

    def fake_urlopen(request, timeout):
        captured["payload"] = json.loads(request.data)
        captured["timeout"] = timeout
        return FakeStream()

    import qwen35_query_rewrite_bench as bench
    original_urlopen = bench.urllib.request.urlopen
    bench.urllib.request.urlopen = fake_urlopen
    try:
        result = request_one(
            "http://127.0.0.1:10010",
            "model",
            "private prompt",
            8,
            1024,
            60,
            first,
        )
    finally:
        bench.urllib.request.urlopen = original_urlopen
    assert captured["payload"]["cache_salt"] == first
    assert result["finish_reason"] == "stop"
    assert result["completion_tokens"] == 1
    print("PASS: run_qwen35_profile_request")


if __name__ == "__main__":
    main()
