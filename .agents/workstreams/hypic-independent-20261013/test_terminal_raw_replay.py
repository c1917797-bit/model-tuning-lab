"""Offline immutable G3 raw replay and fail-closed negative controls."""
import json
import unittest
import hashlib,subprocess
from pathlib import Path
from unittest.mock import patch
from audit_formal_terminal_unit import audit_unit

RAW="/cache/cch/hypic-independent-20261013/formal-performance-g3-r2"
CONTRACT="FORMAL_PERFORMANCE_G3_R2_CONTRACT.json"
REAL_READ=Path.read_text
REAL_BYTES=Path.read_bytes

class TerminalRawReplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Replay immutable historical bytes from their actual launch commit,
        # not the evolving candidate tree. Never rewrite original raw evidence.
        launch=json.loads(REAL_READ(Path(RAW)/'launch.json'))
        commit=launch['git_commit']
        contract=json.loads(REAL_READ(Path(CONTRACT)))
        expected=dict(contract['cache_diagnostic']['source_sha256'])
        expected['native_tp4_smoke.py']=contract['controller_sha256']
        prefix='.agents/workstreams/hypic-independent-20261013/'
        cls.archived={}
        for name,digest in expected.items():
            data=subprocess.check_output(['git','show',commit+':'+prefix+name])
            if hashlib.sha256(data).hexdigest()!=digest:
                raise ValueError('historical launch/source digest mismatch: '+name)
            cls.archived[name]=data

    def setUp(self):
        archived=self.archived
        def historical(path):
            return archived[str(path)] if str(path) in archived else REAL_BYTES(path)
        self.source_patch=patch.object(Path,'read_bytes',historical)
        self.source_patch.start();self.addCleanup(self.source_patch.stop)

    def test_positive_full40(self):
        result=audit_unit(RAW,CONTRACT)
        self.assertTrue(result["terminal_unit_valid"])
        self.assertEqual(result["source_bindings"],91)

    def reject_mutation(self, filename, mutate, *, journal=False):
        def read(path,*args,**kwargs):
            original=REAL_READ(path,*args,**kwargs)
            if path.name!=filename:return original
            obj=[json.loads(x) for x in original.splitlines()] if journal else json.loads(original)
            mutate(obj)
            return "\n".join(json.dumps(x) for x in obj)+"\n" if journal else json.dumps(obj)
        with patch.object(Path,"read_text",read):
            with self.assertRaises(ValueError):audit_unit(RAW,CONTRACT)

    def test_output_limit_mismatch(self):
        self.reject_mutation("events.jsonl",lambda xs:next(x for x in xs if x.get("event")=="measured-response")["metrics"].update(completion_tokens=1023),journal=True)

    def test_foreign_process(self):
        self.reject_mutation("events.jsonl",lambda xs:next(x for x in xs if x.get("event")=="isolation")["snapshot"].update(foreign=[{"pid":999}]),journal=True)

    def test_missing_scored_marker(self):
        self.reject_mutation("events.jsonl",lambda xs:next(x for x in xs if x.get("event")=="measured-response").pop("scored"),journal=True)

    def test_client_journal_drift(self):
        self.reject_mutation("performance-unit.json",lambda x:x["results"][0]["metrics"].update(text="altered"))

    def test_source_digest_drift(self):
        self.reject_mutation(Path(CONTRACT).name,lambda x:x["cache_diagnostic"]["source_sha256"].update({"independent_formal_client.py":"0"*64}))

    def test_source_map_missing(self):
        self.reject_mutation(Path(CONTRACT).name,lambda x:x["cache_diagnostic"].pop("source_sha256"))

    def test_release_receipt_drift(self):
        self.reject_mutation("release.json",lambda x:x.update(port_free=False))

if __name__=="__main__":unittest.main()
