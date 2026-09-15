#!/usr/bin/env python3
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest


MODULE_PATH = Path(__file__).with_name("dasc_quality_eval.py")
SPEC = importlib.util.spec_from_file_location("dasc_quality_eval_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FakeVllmHandler(BaseHTTPRequestHandler):
    hits = 0
    report_hits = True

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:
        if self.path != "/metrics":
            self.send_error(404)
            return
        reported_hits = self.hits if self.report_hits else 0
        body = (
            f"vllm:prefix_cache_queries_total {self.hits}\n"
            f"vllm:prefix_cache_hits_total {reported_hits}\n"
            f"vllm:request_success_total {self.hits}\n"
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if self.path != "/v1/chat/completions":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length))
        content = payload["messages"][0]["content"]
        if not content.startswith("DASC neutral cache record 0000:"):
            self.send_error(400)
            return
        type(self).hits += 1
        body = json.dumps(
            {
                "choices": [
                    {
                        "message": {"content": "work\nanswer:42"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"completion_tokens": 2},
            }
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class DascQualityAdapterTest(unittest.TestCase):
    def test_end_to_end_cache_hit_summary(self) -> None:
        repo = MODULE_PATH.resolve().parents[3]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            data = root / "gsm8k.jsonl"
            data.write_text(
                json.dumps({"question": "Return forty two.", "answer": "x #### 42"})
                + "\n",
                encoding="utf-8",
            )
            output = root / "output"
            FakeVllmHandler.hits = 0
            FakeVllmHandler.report_hits = True
            server = ThreadingHTTPServer(("127.0.0.1", 0), FakeVllmHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                exit_code = MODULE.main(
                    [
                        "--repo",
                        str(repo),
                        "--shared-prefix-lines",
                        "2",
                        "--require-cache-hit",
                        "--dataset",
                        "gsm8k",
                        "--data",
                        str(data),
                        "--base-url",
                        f"http://127.0.0.1:{server.server_port}",
                        "--model",
                        "fake",
                        "--output-dir",
                        str(output),
                        "--run-id",
                        "run1",
                        "--concurrency",
                        "1",
                        "--max-out-len",
                        "8",
                        "--retries",
                        "0",
                    ]
                )
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
            self.assertEqual(exit_code, 0)
            summary = json.loads(
                (output / "gsm8k.run1.summary.json").read_text(encoding="utf-8")
            )
            self.assertEqual(summary["schema"], MODULE.SCHEMA)
            self.assertTrue(summary["cache_hit_verified"])
            self.assertGreater(summary["prefix_cache_hit_delta"], 0)
            self.assertEqual(summary["requests"], 1)
            self.assertEqual(summary["successful"], 1)
            self.assertEqual(summary["correct"], 1)
            self.assertEqual(
                summary["details_sha256"],
                MODULE.sha256_file(output / "gsm8k.run1.jsonl"),
            )

    def test_require_cache_hit_fails_closed(self) -> None:
        repo = MODULE_PATH.resolve().parents[3]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            data = root / "gsm8k.jsonl"
            data.write_text(
                json.dumps({"question": "Return forty two.", "answer": "x #### 42"})
                + "\n",
                encoding="utf-8",
            )
            output = root / "output"
            FakeVllmHandler.hits = 0
            FakeVllmHandler.report_hits = False
            server = ThreadingHTTPServer(("127.0.0.1", 0), FakeVllmHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                exit_code = MODULE.main(
                    [
                        "--repo",
                        str(repo),
                        "--shared-prefix-lines",
                        "2",
                        "--require-cache-hit",
                        "--dataset",
                        "gsm8k",
                        "--data",
                        str(data),
                        "--base-url",
                        f"http://127.0.0.1:{server.server_port}",
                        "--model",
                        "fake",
                        "--output-dir",
                        str(output),
                        "--run-id",
                        "nohit",
                        "--concurrency",
                        "1",
                        "--max-out-len",
                        "8",
                        "--retries",
                        "0",
                    ]
                )
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
                FakeVllmHandler.report_hits = True
            self.assertEqual(exit_code, 3)
            summary = json.loads(
                (output / "gsm8k.nohit.summary.json").read_text(encoding="utf-8")
            )
            self.assertFalse(summary["cache_hit_verified"])
            self.assertEqual(summary["prefix_cache_hit_delta"], 0)


if __name__ == "__main__":
    unittest.main()
