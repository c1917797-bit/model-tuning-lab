"""Read-only false-attestation controls against the retained actual Git objects."""
import copy
import json
import os
from pathlib import Path
import unittest
from audit_local_git_lifecycle import audit

class LifecycleAttestationTests(unittest.TestCase):
    def setUp(self):
        self.root=Path(os.environ["MST_LIFECYCLE_FIXTURE"])
        self.actual=json.loads((self.root/"result.json").read_text())
    def rejects(self,key,value):
        altered=copy.deepcopy(self.actual)
        altered[key]=value
        with self.assertRaises(RuntimeError):
            audit(self.root,altered)
    def test_wrong_source(self):
        self.rejects("source",self.actual["base"])
    def test_wrong_parent(self):
        self.rejects("target_parent",self.actual["base"])
    def test_wrong_original_base(self):
        self.rejects("base",self.actual["implemented"])
    def test_wrong_frozen_contract(self):
        self.rejects("frozen_policy_sha256","0"*64)
    def test_wrong_skill_identity(self):
        self.rejects("skill_blob","0"*40)
    def test_wrong_merge(self):
        self.rejects("merged",self.actual["source"])

if __name__=="__main__":
    unittest.main()
