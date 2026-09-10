#!/usr/bin/env python3

import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("run_quality_requests.py")
SPEC = importlib.util.spec_from_file_location("run_quality_requests", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class FakeTokenizer:
    def apply_chat_template(self, messages, **kwargs):
        return f"{messages[0]['content']}|{kwargs['enable_thinking']}"


class RunQualityRequestsTest(unittest.TestCase):
    def test_render_and_payload_chat(self):
        record = {
            "prompt_mode": "chat",
            "prompt": "hello",
            "generation": {"temperature": 0, "max_tokens": 8},
        }
        self.assertEqual(MODULE.render_prompt(record, FakeTokenizer()), "hello|False")
        route, payload = MODULE.request_payload(record, "model")
        self.assertEqual(route, "/v1/chat/completions")
        self.assertFalse(payload["chat_template_kwargs"]["enable_thinking"])
        self.assertEqual(payload["seed"], 1024)

    def test_completion_is_not_chat_wrapped(self):
        record = {
            "prompt_mode": "completion",
            "prompt": "def f():",
            "generation": {"temperature": 0, "max_tokens": 32},
        }
        self.assertEqual(MODULE.render_prompt(record, FakeTokenizer()), "def f():")
        route, payload = MODULE.request_payload(record, "model")
        self.assertEqual(route, "/v1/completions")
        self.assertEqual(payload["prompt"], "def f():")


if __name__ == "__main__":
    unittest.main()
