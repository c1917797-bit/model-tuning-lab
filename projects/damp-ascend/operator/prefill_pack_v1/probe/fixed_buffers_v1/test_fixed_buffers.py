"""Pure stdlib lifecycle/fixture/source contracts; NO Torch import or NPU execution."""
import ast
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

BASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("fixed_buffers_contract_subject", BASE / "run_fixed_buffers.py")
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)
cases = subject.load_module("fixed_buffers_contract_cases", BASE.parent / "cases.py")
gold = subject.load_module("fixed_buffers_contract_fraction", BASE.parent.parent / "independent_float_div.py")

class Storage:
    next_pointer = 0x100000
    def __init__(self, values):
        self.values = list(values)
        self.pointer = Storage.next_pointer
        Storage.next_pointer += ((4 * len(values) + 31) // 32 + 1) * 32
    def data_ptr(self): return self.pointer
    def nbytes(self): return len(self.values) * 4

class Tensor:
    def __init__(self, values=None, storage=None, offset=0, count=None, device="cpu"):
        self.storage = Storage(values) if storage is None else storage
        self.offset = offset
        self.count = len(self.storage.values) if count is None else count
        self.device = device
        self.dtype = "software-int32"
        self.shape = (self.count,)
    @property
    def values(self): return self.storage.values[self.offset:self.offset+self.count]
    def __getitem__(self, s):
        assert isinstance(s, slice) and s.step in (None, 1)
        start, stop, step = s.indices(self.count)
        return Tensor(storage=self.storage, offset=self.offset+start, count=stop-start, device=self.device)
    def to(self, device): return Tensor(self.values, device=device)
    def copy_(self, source, non_blocking=False):
        assert non_blocking is False and len(source.values) == self.count
        self.storage.values[self.offset:self.offset+self.count] = source.values
        return self
    def clone(self): return Tensor(self.values)
    def untyped_storage(self): return self.storage
    def element_size(self): return 4
    def numel(self): return self.count
    def data_ptr(self): return self.storage.pointer+self.offset*4
    def storage_offset(self): return self.offset
    def is_contiguous(self): return True

class FakeTorch:
    int32 = "software-int32"
    def __init__(self):
        self.npu = SimpleNamespace(synchronize=lambda: None)
        self.saved = {}
    def tensor(self, values, dtype):
        assert dtype == self.int32
        return Tensor(values)
    def equal(self, a, b): return a.values == b.values
    def save(self, data, path):
        self.saved[str(path)] = data.copy()
        Path(path).write_text("explicit-software-lifecycle-model-artifact\n")

class FakeOp:
    def __init__(self, poison=False):
        self.prepares = 0
        self.calls = 0
        self.input_views = None
        self.poison = poison
        self.prepare_contents = None
        self.first_contents = None
    def prepare(self, *args):
        self.prepares += 1
        self.input_views = args[:-1]
        self.prepare_contents = [t.values for t in args[:-1]]
    def divide_bits(self, *args):
        self.calls += 1
        if self.calls == 1: self.first_contents = [t.values for t in args[:-1]]
        assert all(a is b for a, b in zip(args[:-1], self.input_views))
        if self.poison: raise ValueError("primary-dispatch-sentinel")
        views, enabled = args[:-1], args[-1]
        columns = [t.values for t in views]
        results = [[], [], [], []]
        for sx, sc, sp in zip(*columns):
            x, c, p = sx & 0xffffffff, sc & 0xffffffff, sp & 0xffffffff
            valid, finite, bits = gold.oracle(x, c)
            output = (cases.signed(bits), int(valid), int(finite),
                      int(enabled and gold.oracle_certificate(x, c, p)))
            for j, value in enumerate(output): results[j].append(value)
        return tuple(Tensor([cases.GUARDS[j]]*8+results[j]+[cases.GUARDS[j]]*8,
                            device="npu:0") for j in range(4))

def nullable(tensors):
    return [t.clone() for t in tensors], []

class FixedBufferPreparation(unittest.TestCase):
    def test_frozen_scope_and_default(self):
        self.assertEqual(subject.COUNTS, (64, 896))
        self.assertEqual((subject.TURNS, subject.REPEATS), (20, 8))
        self.assertEqual(len(subject.FROZEN), 17)
        old = json.loads((BASE.parent / "runtime_manifest.json").read_text())
        self.assertTrue(all(subject.FROZEN[k] == v for k, v in old["sources"].items()))
        self.assertEqual(subject.FROZEN[str((BASE.parent / "runtime_manifest.json").relative_to(subject.REPO))],
                         subject.sha(BASE.parent / "runtime_manifest.json"))
        self.assertEqual(subject.FROZEN[str((BASE.parent / "source_manifest.json").relative_to(subject.REPO))],
                         subject.sha(BASE.parent / "source_manifest.json"))
    def test_same_buffer_twenty_distinct_turns_all_columns(self):
        for count in subject.COUNTS:
            prior = None
            # Pure fixture checking across all registered turns; not a device simulation.
            for turn in range(subject.TURNS):
                rows = subject.changing_fixture(count, turn, cases, gold)
                fp = subject.validate_rows(rows, count, gold)
                if prior is not None: self.assertTrue(all(a != b for a, b in zip(fp, prior)))
                prior = fp
    def test_fixture_errors_refused(self):
        rows = subject.changing_fixture(64, 0, cases, gold)
        for key in ("bits", "valid", "finite", "accepted"):
            bad = [dict(row) for row in rows]
            bad[0][key] ^= 1
            with self.assertRaisesRegex(RuntimeError, "incorrect independent fixture"):
                subject.validate_rows(bad, 64, gold)
        for value in (-1, 0x100000000, True, 1.25):
            bad = [dict(row) for row in rows]; bad[0]["x"] = value
            with self.assertRaises(RuntimeError): subject.validate_rows(bad, 64, gold)
        with self.assertRaises(RuntimeError): subject.validate_rows(rows, 128, gold)
    def test_overflow_not_clipped_and_signed_zero(self):
        rows = subject.changing_fixture(64, 0, cases, gold)
        by_xc = {(r["x"], r["c"]): r for r in rows[:16]}
        for x in (0x7f7fffff, 0xff7fffff):
            r = by_xc[x, 1]
            self.assertEqual((r["valid"], r["finite"], r["bits"] & 0x7fffffff), (1, 0, gold.INF))
        self.assertEqual(by_xc[0x80000000, 0x3f800000]["bits"], 0x80000000)
    def test_explicitly_software_lifecycle_only(self):
        # Temporarily smaller control-flow MODEL; frozen actual NPU constants remain20/8.
        for enabled in (False, True):
            torch, op = FakeTorch(), FakeOp()
            report = dict(cases=[], npu_dispatch_attempted=False, npu_executed=False)
            npu = SimpleNamespace(npu_format_cast=lambda t, fmt: t, get_npu_format=lambda t: 2)
            old = SimpleNamespace(nullable_copy=nullable)
            with tempfile.TemporaryDirectory(prefix="damp-fixed-buffer-software-") as tmp:
                with mock.patch.object(subject, "TURNS", 2), mock.patch.object(subject, "REPEATS", 2):
                    subject.execute_case(64, enabled, op, torch, npu, cases, gold, old,
                                         Path(tmp), report, lambda: None)
            self.assertEqual((op.prepares, op.calls), (1, 4))
            self.assertTrue(all(a != b for a, b in zip(op.prepare_contents, op.first_contents)))
            self.assertEqual(report["cases"][0]["changed_turns"], 2)
            self.assertEqual(report["cases"][0]["status"], "passed")
    def test_primary_failure_preserved_before_assert(self):
        torch, op = FakeTorch(), FakeOp(poison=True)
        report = dict(cases=[], npu_dispatch_attempted=False, npu_executed=False)
        npu = SimpleNamespace(npu_format_cast=lambda t, fmt: t, get_npu_format=lambda t: 2)
        old = SimpleNamespace(nullable_copy=nullable)
        with tempfile.TemporaryDirectory(prefix="damp-fixed-buffer-failure-") as tmp:
            with self.assertRaisesRegex(ValueError, "primary-dispatch-sentinel"):
                subject.execute_case(64, False, op, torch, npu, cases, gold, old,
                                     Path(tmp), report, lambda: None)
            before = str(Path(tmp) / "64-exact-turn-0.before.pt")
            after = str(Path(tmp) / "64-exact-turn-0.pt")
            self.assertIn(before, torch.saved)
            self.assertIn("primary-dispatch-sentinel", torch.saved[after]["dispatch_error"])
            self.assertEqual(torch.saved[after]["rows"], torch.saved[before]["rows"])
        self.assertEqual(op.prepares, 1)
        self.assertEqual(report["cases"][0]["status"], "failed")
    def test_nullable_failure_does_not_override_original(self):
        torch, op = FakeTorch(), FakeOp(poison=True)
        def after_poison(tensors):
            if op.calls: return [None for _ in tensors], [{"index": 0, "error": "poisoned-copy"}]
            return nullable(tensors)
        report = dict(cases=[], npu_dispatch_attempted=False, npu_executed=False)
        npu = SimpleNamespace(npu_format_cast=lambda t, fmt: t, get_npu_format=lambda t: 2)
        with tempfile.TemporaryDirectory(prefix="damp-fixed-buffer-nullable-") as tmp:
            with self.assertRaisesRegex(ValueError, "primary-dispatch-sentinel"):
                subject.execute_case(64, False, op, torch, npu, cases, gold,
                    SimpleNamespace(nullable_copy=after_poison), Path(tmp), report, lambda: None)
            saved = torch.saved[str(Path(tmp) / "64-exact-turn-0.pt")]
            self.assertIn("primary-dispatch-sentinel", saved["dispatch_error"])
            self.assertTrue(saved["copy_errors"])
            self.assertTrue(all(v is None for v in saved["after"]))
    def test_source_before_after_and_raw_save_contract(self):
        text = (BASE / "run_fixed_buffers.py").read_text()
        ast.parse(text)
        self.assertIn('safe_json(out / "SOURCE_BEFORE.json", before)', text)
        self.assertIn('safe_json(out / "SOURCE_AFTER.json", after)', text)
        self.assertLess(text.index('preserve_after(torch, path, artifact), "raw replay artifact save"'),
                        text.index('same_complete(raw, expected, torch)'))
        self.assertIn("allow_nan=False", text)
        self.assertIn('dst.copy_(src, non_blocking=False)', text)
        self.assertIn('op.prepare(*views, enabled)', text)
        self.assertNotIn("NPUGraph(", text)
    def test_default_cli_no_torch_or_artifact(self):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream): subject.main([])
        plan = json.loads(stream.getvalue())
        self.assertFalse(plan["npu_executed"])
        self.assertFalse(plan["launchable"])
        self.assertFalse(plan["graph_supported"])
        self.assertNotIn("torch", __import__("sys").modules)
    def test_actual_pointer_alias_checks(self):
        a = Tensor([0]*80, device="npu:0")
        b = a[8:72]
        self.assertEqual(subject.pointer_records([b])[0]["pointer"], a.data_ptr()+32)
        with self.assertRaisesRegex(RuntimeError, "backing alias"):
            subject.disjoint_backings(subject.pointer_records([a, b]))
    def test_failure_source_snapshot_is_nonthrowing(self):
        args = SimpleNamespace(fixed_manifest_sha256="0"*64)
        with mock.patch.object(subject, "sha", side_effect=OSError("source-read-sentinel")):
            snapshot = subject.source_snapshot(args)
        self.assertFalse(snapshot["all_match"])
        self.assertTrue(all(r["error"] is not None for r in snapshot["files"]))

if __name__ == "__main__":
    unittest.main()
