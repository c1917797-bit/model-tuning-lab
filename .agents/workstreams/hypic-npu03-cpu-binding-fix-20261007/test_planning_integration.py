import copy
import unittest
from preflight_planning_integration import admit,TARGET,SOURCE,PATH,BEFORE,AFTER

class SelectiveIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.doc={"schema":"mst-selective-integration-candidate/v1",
                  "target_commit":TARGET,"source_commit":SOURCE,"paths":[PATH],
                  "before_blob":BEFORE,"after_blob":AFTER,"state":"offline-preflight-only",
                  "remote_authentication_verified":False,"primary_changed":False}
    def check(self,target=TARGET,before=BEFORE,after=AFTER,patch=b"exact patch"):
        return admit(self.doc,target,before,after,patch,b"exact patch")
    def test_exact_candidate(self):
        self.assertTrue(self.check())
    def test_target_drift(self):
        with self.assertRaisesRegex(ValueError,"target drift"):
            self.check(target="0"*40)
    def test_extra_path(self):
        self.doc["paths"].append("runtime.py")
        with self.assertRaisesRegex(ValueError,"allowlist"):
            self.check()
    def test_source_drift(self):
        self.doc["source_commit"]="0"*40
        with self.assertRaisesRegex(ValueError,"source drift"):
            self.check()
    def test_blob_mismatch(self):
        with self.assertRaisesRegex(ValueError,"blob"):
            self.check(after="0"*40)
    def test_patch_injection(self):
        with self.assertRaisesRegex(ValueError,"patch differs"):
            self.check(patch=b"additional unreviewed diff")
    def test_readiness_overclaim(self):
        self.doc["state"]="ready"
        with self.assertRaisesRegex(ValueError,"overclaims"):
            self.check()

if __name__=="__main__":
    unittest.main()
