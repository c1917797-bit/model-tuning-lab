#!/usr/bin/env python3
from __future__ import annotations

import audit_quality_context
import unittest


class QualityContextAuditTest(unittest.TestCase):
    def test_summary_uses_nearest_rank_and_rounds_context(self) -> None:
        result = audit_quality_context.summarize([100, 200, 300, 400], 1000)
        self.assertEqual(result["p50_input_tokens"], 200)
        self.assertEqual(result["p95_input_tokens"], 400)
        self.assertEqual(result["required_context_tokens"], 1400)
        self.assertEqual(result["recommended_max_model_len"], 2048)

    def test_summary_rejects_empty_input(self) -> None:
        with self.assertRaises(ValueError):
            audit_quality_context.summarize([], 1000)

    def test_chat_tokens_accepts_dict_and_single_batch(self) -> None:
        class FakeTokenizer:
            def apply_chat_template(self, *args, **kwargs):
                return {"input_ids": [[1, 2, 3, 4]]}

        self.assertEqual(audit_quality_context.chat_tokens(FakeTokenizer(), "x"), 4)

    def test_chat_tokens_rejects_ambiguous_batch(self) -> None:
        class FakeTokenizer:
            def apply_chat_template(self, *args, **kwargs):
                return {"input_ids": [[1, 2], [3, 4]]}

        with self.assertRaises(ValueError):
            audit_quality_context.chat_tokens(FakeTokenizer(), "x")


if __name__ == "__main__":
    unittest.main()
