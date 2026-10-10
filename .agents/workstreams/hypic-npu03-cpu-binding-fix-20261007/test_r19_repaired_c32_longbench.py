"""Offline r19 checks; these tests never start a service or use an NPU."""

from __future__ import annotations

import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import r19_repaired_c32_longbench_adapter as adapter


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


class R19LongBenchOfflineTest(unittest.TestCase):
    def test_preregistered_arms_are_c32_original_source(self) -> None:
        prereg = adapter.check_preregistration()
        code = (
            "import json, os; from r19_repaired_c32_longbench_adapter import configure; "
            "c=configure(os.environ['HYPIC_R19_ARM']); "
            "print(json.dumps({'root':str(c.quality.QROOT), "
            "'source_commit':c.quality.preflight()['source_commit'], "
            "'concurrency':c.CONCURRENCY, 'cap':c.MAX_OUTPUT}))"
        )
        for arm in ("no-cache", "hypic-only"):
            result = subprocess.run([sys.executable, "-B", "-c", code],
                                    cwd=Path(__file__).parent,
                                    env={**__import__("os").environ, "HYPIC_R19_ARM": arm},
                                    capture_output=True, text=True, check=True)
            row = json.loads(result.stdout)
            self.assertEqual(row["root"], prereg["arm_roots"][arm]["longbench"])
            self.assertEqual(row["source_commit"], prereg["source_commit"])
            self.assertEqual((row["concurrency"], row["cap"]), (32, 2048))

    def test_short_canary_is_deterministic_and_paired(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = root / "quality-context-41984-hotpath-cache10r19-c32-full-baseline"
            cand = root / "quality-context-41984-hotpath-cache10r19-c32-full-hypic"
            quality = SimpleNamespace(ROOT=root, QROOT=base, MODEL_NAME="test-model",
                                      BASE_URL="http://unused", write_json=write_json)

            def response(text: str):
                return io.BytesIO(json.dumps({"usage": {"completion_tokens": 1},
                                              "choices": [{"message": {"content": text}}]}).encode())

            with patch.object(adapter, "urlopen", side_effect=lambda *_a, **_k: response("7")):
                adapter._canary(quality, "no-cache")
                quality.QROOT = cand
                adapter._canary(quality, "hypic-only")
            left = json.loads((base / "no-cache" / "r19-short-canary.json").read_text())
            right = json.loads((cand / "hypic-only" / "r19-short-canary.json").read_text())
            self.assertEqual(left["response_sha256"], right["response_sha256"])
            with patch.object(adapter, "urlopen", side_effect=lambda *_a, **_k: response("8")):
                with self.assertRaisesRegex(RuntimeError, "differs from baseline"):
                    adapter._canary(quality, "hypic-only")

    def test_integrated_c32_wave_requires_exact_scored_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "capacity-wave.json"
            record = {"schema": "hypic-r19-c32-integrated-wave/v1",
                      "concurrency": 32, "scored_sample_indexes": list(range(1, 33)),
                      "guard_samples_so_far": 10, "event_summary_so_far": {}}
            write_json(path, record)
            code = ("import sys; from pathlib import Path; "
                    "import r19_repaired_c32_longbench_audit as a; "
                    "print(a.audit_integrated_wave(Path(sys.argv[1]), 'no-cache')"
                    "['guard_samples_so_far'])")
            command = [sys.executable, "-B", "-c", code, str(root)]
            first = subprocess.run(command, cwd=Path(__file__).parent,
                                   capture_output=True, text=True, check=True)
            self.assertEqual(first.stdout.strip(), "10")
            record["scored_sample_indexes"] = list(range(2, 34))
            write_json(path, record)
            second = subprocess.run(command, cwd=Path(__file__).parent,
                                    capture_output=True, text=True)
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("wave drift", second.stderr)


if __name__ == "__main__":
    unittest.main()
