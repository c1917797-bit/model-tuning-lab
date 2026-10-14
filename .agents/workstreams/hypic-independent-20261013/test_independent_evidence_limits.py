import unittest
from types import SimpleNamespace
from independent_evidence_limits import evidence_limits
from independent_request_progress import RequestProgressLedger
class EvidenceLimitTests(unittest.TestCase):
    def test_defaults_and_full_quality_request_budget(self):
        self.assertEqual(evidence_limits()["max_requests"],128)
        limits=evidence_limits({"max_events":50000,"max_bytes":67108864,"max_requests":1024})
        ledger=RequestProgressLedger(limits["max_requests"])
        for i in range(762):
            ledger.observe([SimpleNamespace(request_id=str(i),rank=0,step=i,
                           computed_tokens=0,scheduled_tokens=10)])
        self.assertEqual(len(ledger.seen),762)
    def test_invalid_unbounded_or_unknown_limits(self):
        for spec in ({"max_requests":True},{"max_events":0},{"max_bytes":999999999},{"other":1}):
            with self.assertRaises(ValueError):evidence_limits(spec)
if __name__=="__main__":unittest.main()
