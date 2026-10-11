"""CPU fixtures only; no host-test receipt counts as a real worker receipt."""
import copy
import hashlib
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

from numerical_state_observer import SWITCH, install_step_receipt
from numerical_state_writer import RawWriter, read_sealed
from numerical_state_audit import join_step_receipts
from test_numerical_state_audit import fixture, run

SOURCE = """def _validate_and_emit_hot_request_evidence(report, ctx, *, expected_full_layers, expected_gdn_layers):
    if report == "fail":
        raise RuntimeError("production validation failed")
    return 17
"""


class IOTests(unittest.TestCase):
    def metadata(self):
        return dict(request_id="selected", rank=0, pid=os.getpid())

    def test_exclusive_seal_and_roundtrip(self):
        with tempfile.TemporaryDirectory() as root:
            writer = RawWriter(root, metadata=self.metadata())
            event = dict(self.metadata(), schema="fixture", data=[1, 2])
            writer(event)
            sealed = writer.seal()
            manifest, events = read_sealed(writer.path)
            self.assertEqual(manifest, sealed)
            self.assertEqual(events, [event])
            with self.assertRaises(RuntimeError):
                writer(event)
            with self.assertRaises(FileExistsError):
                RawWriter(root, metadata=self.metadata())

    def test_corrupt_or_extra_raw_file_rejected(self):
        for kind in ("tamper", "extra", "symlink"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as root:
                writer = RawWriter(root, metadata=self.metadata())
                writer(dict(self.metadata(), data=1))
                writer.seal()
                path = writer.path/"0000.json"
                if kind == "tamper":
                    path.write_text("{}")
                elif kind == "extra":
                    (writer.path/"extra").touch()
                else:
                    outside = Path(root)/"outside"
                    outside.write_bytes(path.read_bytes())
                    path.unlink()
                    path.symlink_to(outside)
                with self.assertRaises(ValueError):
                    read_sealed(writer.path)

    def test_budget_identity_and_nan_fail_closed(self):
        for event, options in [
            (dict(self.metadata(), pid=1), {}),
            (dict(self.metadata(), value=float("nan")), {}),
            (dict(self.metadata(), value="large"), dict(max_bytes=1)),
        ]:
            with tempfile.TemporaryDirectory() as root:
                writer = RawWriter(root, metadata=self.metadata(), **options)
                with self.assertRaises(ValueError):
                    writer(event)
                with self.assertRaises(RuntimeError):
                    writer.seal()

    def test_no_seal_means_incomplete(self):
        with tempfile.TemporaryDirectory() as root:
            writer = RawWriter(root, metadata=self.metadata(), max_events=1)
            writer(self.metadata())
            with self.assertRaises(FileNotFoundError):
                read_sealed(writer.path)
            with self.assertRaises(ValueError):
                writer(self.metadata())
            with self.assertRaises(RuntimeError):
                writer.seal()

    def test_receipt_disabled_no_access(self):
        with patch.dict(os.environ, {SWITCH: "0"}):
            install_step_receipt(None, None, request_id=None, rank=None).uninstall()

    def test_receipt_only_after_validation_and_uninstall(self):
        with tempfile.TemporaryDirectory() as root, patch.dict(os.environ, {SWITCH: "1"}):
            path = Path(root)/"runner.py"
            path.write_text(SOURCE)
            module = types.ModuleType("fixture")
            module.__file__ = str(path)
            exec(compile(SOURCE, str(path), "exec"), module.__dict__)
            original = module._validate_and_emit_hot_request_evidence
            events = []
            handle = install_step_receipt(module, events.append, request_id="selected",
                    rank=0, source_hash=hashlib.sha256(SOURCE.encode()).hexdigest())
            ctx = types.SimpleNamespace(verified_hot_request_tokens={"selected": 12},
                                        batch_plan=types.SimpleNamespace(step_id=9))
            kwargs = dict(expected_full_layers={"attention"}, expected_gdn_layers={"gdn"})
            self.assertEqual(module._validate_and_emit_hot_request_evidence(None, ctx, **kwargs), 17)
            self.assertEqual(events[0]["step"], 9)
            self.assertEqual(events[0]["pid"], os.getpid())
            with self.assertRaises(RuntimeError):
                module._validate_and_emit_hot_request_evidence("fail", ctx, **kwargs)
            self.assertEqual(len(events), 1)
            ctx.verified_hot_request_tokens = {}
            module._validate_and_emit_hot_request_evidence(None, ctx, **kwargs)
            self.assertEqual(len(events), 1)
            handle.uninstall()
            self.assertIs(module._validate_and_emit_hot_request_evidence, original)
            module._validate_and_emit_hot_request_evidence(None, ctx, **kwargs)
            self.assertEqual(len(events), 1)
            with self.assertRaises(ValueError):
                install_step_receipt(module, events.append, request_id="selected", rank=0,
                                     source_hash="0"*64)

    def test_step_join_exact_and_negative_controls(self):
        events, _, bindings = fixture()
        report = run(events)
        digest = "1"*64
        receipts = [dict(schema="hypic-state-step-receipt/v1",
                         event="observer_validated_hot_step", request_id="selected",
                         rank=r, pid=100+r, step=7, skipped_prefix_tokens=12,
                         expected_full_layers=["attention"], expected_gdn_layers=["gdn"],
                         validation_completed=True, runtime_source_sha256=digest)
                    for r in range(4)]
        kwargs = dict(runtime_sha256=digest, kv_layer="attention", gdn_layer="gdn")
        joined = join_step_receipts(report, receipts, bindings, **kwargs)
        self.assertTrue(joined["captured_step_receipts_joined"])
        self.assertFalse(joined["physical_device_proven"])
        cases = [receipts[:-1], receipts+receipts[:1]]
        for key, value in (("step", 8), ("pid", 900), ("request_id", "other"),
                           ("runtime_source_sha256", "2"*64), ("validation_completed", False),
                           ("expected_full_layers", ["other"])):
            broken = copy.deepcopy(receipts)
            broken[0][key] = value
            cases.append(broken)
        for broken in cases:
            with self.assertRaises(ValueError):
                join_step_receipts(report, broken, bindings, **kwargs)


if __name__ == "__main__":
    unittest.main()
