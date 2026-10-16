"""Actual file writes/fences; no runtime/NPU activation."""
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from independent_evidence_step_sink import SourceBoundEventSink


class EvidenceStepSinkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
    def sink(self, name="events", **kw):
        args = dict(manifest_sha256="a"*64, max_events=10, max_bytes=8192)
        args.update(kw)
        s = SourceBoundEventSink(self.root/name, **args)
        self.addCleanup(s.close)
        return s
    def records(self, name="events"):
        return [json.loads(x) for x in (self.root/name).read_text().splitlines()]
    def test_default_per_event(self):
        s = self.sink()
        s({"event":"one"}); s({"event":"two"})
        self.assertEqual(s.sync_count, 2)
        self.assertEqual([x["event"] for x in self.records()], ["one","two"])
    def test_model_step_fence_and_outside_activation(self):
        s = self.sink(policy="model_step")
        s({"event":"install"})
        with s.model_step():
            s({"event":"a"}); s({"event":"b"})
            self.assertEqual(s.sync_count, 1)
            self.assertEqual(len(self.records()), 3)
        self.assertEqual(s.sync_count, 2)
    def test_exception_flushes_and_resets(self):
        s = self.sink(policy="model_step")
        with self.assertRaisesRegex(ValueError, "original"):
            with s.model_step():
                s({"event":"before"}); raise ValueError("original")
        self.assertEqual(s.sync_count, 1)
        with s.model_step(): s({"event":"next"})
        self.assertEqual(s.sync_count, 2)
    def test_nested_rejected_outer_still_fences(self):
        s = self.sink(policy="model_step")
        with self.assertRaises(RuntimeError):
            with s.model_step():
                s({"event":"outer"})
                with s.model_step(): pass
        self.assertEqual(s.sync_count, 1)
    def test_foreign_thread_rejected(self):
        s = self.sink(policy="model_step"); errors=[]
        def foreign():
            try: s({"event":"foreign"})
            except RuntimeError as exc: errors.append(str(exc))
        with s.model_step():
            s({"event":"owned"})
            t=threading.Thread(target=foreign); t.start(); t.join()
        self.assertEqual(len(errors), 1)
        self.assertEqual(len(self.records()), 1)
    def test_active_close_rejected(self):
        s = self.sink(policy="model_step")
        with s.model_step():
            s({"event":"one"})
            with self.assertRaises(RuntimeError): s.close()
        s.close(); s.close()
        with self.assertRaises(RuntimeError): s({"event":"late"})
    def test_per_event_not_model_step(self):
        s = self.sink()
        with self.assertRaises(RuntimeError):
            with s.model_step(): pass
    def test_count_limit_fails_closed(self):
        s = self.sink(policy="model_step", max_events=1)
        with self.assertRaises(ValueError):
            with s.model_step():
                s({"event":"one"}); s({"event":"two"})
        self.assertEqual(s.sync_count, 1)
        self.assertEqual(len(self.records()), 1)
        with self.assertRaises(RuntimeError): s({"event":"three"})
    def test_size_limit_no_write(self):
        s = self.sink(max_bytes=1)
        with self.assertRaises(ValueError): s({"event":"oversize"})
        self.assertEqual((self.root/"events").stat().st_size, 0)
        with self.assertRaises(RuntimeError): s({"event":"late"})
    def test_short_positive_writes_complete(self):
        s = self.sink(); actual=os.write
        with patch("independent_evidence_step_sink.os.write",
                   side_effect=lambda fd, data: actual(fd, data[:3])):
            s({"event":"complete"})
        self.assertEqual(self.records()[0]["event"], "complete")
    def test_write_failure_poisoned(self):
        s = self.sink()
        with patch("independent_evidence_step_sink.os.write",
                   side_effect=OSError("disk error")):
            with self.assertRaises(OSError): s({"event":"lost"})
        with self.assertRaises(RuntimeError): s({"event":"late"})
    def test_fsync_error_propagates_and_fails_closed(self):
        s = self.sink(policy="model_step")
        with patch("independent_evidence_step_sink.os.fsync",
                   side_effect=OSError("sync error")):
            with self.assertRaises(OSError):
                with s.model_step(): s({"event":"written"})
        with self.assertRaises(RuntimeError): s({"event":"late"})
        s.close()
        self.assertEqual(self.records()[0]["event"], "written")
    def test_same_records_both_policies(self):
        a=self.sink("a"); b=self.sink("b",policy="model_step")
        events=[{"event":"x","step":1},{"event":"y","step":1}]
        for e in events: a(e)
        with b.model_step():
            for e in events: b(e)
        self.assertEqual((self.root/"a").read_bytes(), (self.root/"b").read_bytes())
        self.assertEqual((a.sync_count,b.sync_count),(2,1))
    def test_existing_symlink_never_overwritten(self):
        target=self.root/"target"; target.write_text("keep")
        (self.root/"events").symlink_to(target)
        with self.assertRaises(FileExistsError): self.sink()
        self.assertEqual(target.read_text(), "keep")
    def test_nonfinite_event_rejected_before_write(self):
        s=self.sink(policy="model_step")
        with self.assertRaises(ValueError):
            with s.model_step():
                s({"event":"first"}); s({"value":float("nan")})
        self.assertEqual(s.sync_count,1)
        self.assertEqual(len(self.records()),1)
        with self.assertRaises(RuntimeError): s({"event":"after-invalid"})
    def test_nonserializable_fails_closed(self):
        s=self.sink()
        with self.assertRaises(TypeError): s({"value":object()})
        with self.assertRaises(RuntimeError): s({"event":"late"})
        self.assertEqual((self.root/"events").stat().st_size,0)
    def test_nondictionary_fails_closed(self):
        s=self.sink()
        with self.assertRaises(ValueError): s([])
        with self.assertRaises(RuntimeError): s({"event":"late"})
    def test_identity_cannot_be_spoofed(self):
        s=self.sink(); s({"pid":-1,"manifest_sha256":"wrong"})
        self.assertEqual(self.records()[0]["pid"],os.getpid())
        self.assertEqual(self.records()[0]["manifest_sha256"],"a"*64)
    def test_invalid_configuration_creates_no_file(self):
        for kw in ({"policy":"batch64"},{"manifest_sha256":"wrong"},{"manifest_sha256":None},
                   {"max_events":True},{"max_bytes":0}):
            with self.assertRaises(ValueError): self.sink(**kw)
        self.assertFalse((self.root/"events").exists())


if __name__=="__main__": unittest.main()
