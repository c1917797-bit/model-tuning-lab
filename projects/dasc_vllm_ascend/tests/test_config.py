from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from dasc_vllm_ascend.config import DascConfig, DascConfigurationError


class ConfigTest(unittest.TestCase):
    def test_disabled_defaults(self):
        with patch.dict(os.environ, {}, clear=True):
            config = DascConfig.from_env()
        self.assertFalse(config.enabled)
        self.assertEqual(config.mode, "nr-numerical")
        self.assertEqual(config.w_max, 64)

    def test_enabled_requires_absolute_evidence(self):
        env = {
            "MST_DASC_ENABLE": "1",
            "MST_DASC_EVIDENCE_PATH": "relative.jsonl",
        }
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaisesRegex(DascConfigurationError, "absolute"):
                DascConfig.from_env()

    def test_unimplemented_mode_fails_closed(self):
        with patch.dict(
            os.environ, {"MST_DASC_MODE": "physical"}, clear=True
        ):
            with self.assertRaisesRegex(DascConfigurationError, "must be"):
                DascConfig.from_env()

    def test_physical_cache_eager_mode_is_explicit(self):
        env = {
            "MST_DASC_ENABLE": "1",
            "MST_DASC_MODE": "physical-cache-eager",
            "MST_DASC_EVIDENCE_PATH": "/tmp/dasc-evidence.jsonl",
        }
        with patch.dict(os.environ, env, clear=True):
            config = DascConfig.from_env()
        self.assertTrue(config.enabled)
        self.assertEqual(config.mode, "physical-cache-eager")

    def test_numeric_bounds(self):
        invalid = (
            ("MST_DASC_W_MAX", "0"),
            ("MST_DASC_EPSILON", "1"),
            ("MST_DASC_EPSILON", "0"),
            ("MST_DASC_REPRESENTATIVE_A", "nan"),
        )
        for name, value in invalid:
            with self.subTest(name=name, value=value):
                with patch.dict(os.environ, {name: value}, clear=True):
                    with self.assertRaises(DascConfigurationError):
                        DascConfig.from_env()


if __name__ == "__main__":
    unittest.main()
