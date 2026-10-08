#!/usr/bin/env python3
"""CPU-only request-ID observation adapter regression."""

import json
import threading
import unittest
from dataclasses import asdict, dataclass
from types import SimpleNamespace

from hotpath_request_id_benchmark import (
    RequestIdResponse, attach_request_ids, load_pinned_benchmark,
)


class FakeResponse:
    def __init__(self, lines):
        self.lines = lines
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.closed = True

    def __iter__(self):
        return iter(self.lines)


class RequestIdBenchmarkTests(unittest.TestCase):
    def test_first_sse_completion_id_retained_without_line_change(self):
        lines = [
            b"data: " + json.dumps({"id": "cmpl-one", "choices": []}).encode() + b"\n",
            b"data: " + json.dumps({"id": "cmpl-one", "choices": []}).encode() + b"\n",
            b"data: [DONE]\n",
        ]
        local = threading.local()
        local.request_id = None
        response = FakeResponse(lines)
        with RequestIdResponse(response, local) as wrapped:
            self.assertEqual(list(wrapped), lines)
        self.assertEqual(local.request_id, "cmpl-one")
        self.assertTrue(response.closed)

    def test_pinned_source_loads_without_running_live_requests(self):
        source = load_pinned_benchmark()
        self.assertTrue(callable(source.main))
        self.assertTrue(callable(source._stream_completion))

    def test_adapter_retains_id_in_serialized_result(self):
        @dataclass(frozen=True)
        class Result:
            index: int
            ok: bool
        lines = [b'data: {"id":"cmpl-observed","choices":[]}\n',
                 b'data: [DONE]\n']
        def original_stream():
            with source._post_json("/v1/completions", {}, 1) as response:
                list(response)
            return Result(index=0, ok=True)
        source = SimpleNamespace(
            RequestResult=Result,
            _post_json=lambda url, payload, timeout: FakeResponse(lines),
            _stream_completion=original_stream)
        attach_request_ids(source)
        self.assertEqual(asdict(source._stream_completion())["request_id"],
                         "cmpl-observed")


if __name__ == "__main__":
    unittest.main()
