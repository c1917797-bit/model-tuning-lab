#!/usr/bin/env python3
"""Run the pinned shared-prefix benchmark and retain each SSE request ID.

Only observation is added: one first-chunk ID parse per completion. Prompt,
barrier, streaming, token counting, metrics, and CLI stay in the pinned source.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import threading
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from binding_off_service import BENCHMARK, BENCHMARK_SHA, sha256


class RequestIdResponse:
    """Transparent response iterator that records the first completion ID."""

    def __init__(self, response: Any, local: threading.local) -> None:
        self.response = response
        self.local = local

    def __enter__(self) -> "RequestIdResponse":
        self.response.__enter__()
        return self

    def __exit__(self, *args: object) -> object:
        return self.response.__exit__(*args)

    def __iter__(self):
        for raw in self.response:
            if self.local.request_id is None and raw.startswith(b"data:"):
                body = raw[5:].strip()
                if body != b"[DONE]":
                    value = json.loads(body).get("id")
                    if isinstance(value, str) and value:
                        self.local.request_id = value
            yield raw


def load_pinned_benchmark(path: Path = BENCHMARK):
    if sha256(path) != BENCHMARK_SHA:
        raise RuntimeError("pinned shared-prefix benchmark bytes drifted")
    name = "_hypic_pinned_shared_prefix_benchmark"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("pinned benchmark import specification unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def attach_request_ids(module: Any) -> None:
    local = threading.local()
    original_post = module._post_json
    original_stream = module._stream_completion

    @dataclass(frozen=True)
    class IdentifiedResult(module.RequestResult):
        request_id: str | None = None

    def post(url: str, payload: dict, timeout: float):
        response = original_post(url, payload, timeout)
        if url.endswith("/v1/completions"):
            return RequestIdResponse(response, local)
        return response

    def stream(*args: Any, **kwargs: Any):
        local.request_id = None
        result = original_stream(*args, **kwargs)
        return IdentifiedResult(**asdict(result), request_id=local.request_id)

    module._post_json = post
    module._stream_completion = stream


def main() -> int:
    module = load_pinned_benchmark()
    attach_request_ids(module)
    return module.main()


if __name__ == "__main__":
    raise SystemExit(main())
