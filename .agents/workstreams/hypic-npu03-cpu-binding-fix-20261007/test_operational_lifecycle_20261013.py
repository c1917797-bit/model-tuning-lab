import copy,unittest
from datetime import datetime,timezone
from operational_lifecycle_20261013 import root,admit_time
from operational_lifecycle_audit_20261013 import smoke,activation
class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.row=dict(request_id="chatcmpl-operational-lifecycle-20261013-disabled-smoke",
          max_tokens=1,request_sha256="frozen",response=dict(
          id="chatcmpl-operational-lifecycle-20261013-disabled-smoke",
          usage=dict(prompt_tokens=20414,completion_tokens=1),
          choices=[dict(finish_reason="length",message=dict(content="A"))]))
    def checkrow(self,r):smoke(r,"disabled",{"prompt_tokens":20414},"frozen")
    def test_operational_not_quality(self):self.checkrow(self.row)
    def test_no_enabled(self):
        with self.assertRaises(ValueError):root("enabled")
    def test_no_old_root(self):self.assertNotIn("20261012",str(root("disabled")))
    def test_deadline(self):
        with self.assertRaises(ValueError):
            admit_time(dict(deadline_utc="2026-10-13T18:00:00Z",phase_alarm_seconds=1200,
              cleanup_allowance_seconds=300),datetime(2026,10,13,17,50,tzinfo=timezone.utc))
    def test_wrong_request(self):
        r=copy.deepcopy(self.row);r["response"]["id"]="other"
        with self.assertRaises(ValueError):self.checkrow(r)
    def test_unbounded(self):
        r=copy.deepcopy(self.row);r["max_tokens"]=2048
        with self.assertRaises(ValueError):self.checkrow(r)
    def test_wrong_payload(self):
        r=copy.deepcopy(self.row);r["request_sha256"]="other"
        with self.assertRaises(ValueError):self.checkrow(r)
    def test_empty(self):
        r=copy.deepcopy(self.row);r["response"]["choices"][0]["message"]["content"]=""
        with self.assertRaises(ValueError):self.checkrow(r)
    def test_no_marker(self):activation([],"disabled",{1,2,3,4},{5},"x")
    def test_marker_fails(self):
        with self.assertRaises(ValueError):activation([{"event":"plugin_build_active"}],"uninstalled",{1,2,3,4},{5},"x")
if __name__=="__main__":unittest.main()
