import unittest
from native_recovery import admit
class RecoveryAdmission(unittest.TestCase):
    def setUp(self):
        self.prior=dict(decision="FAILED_SEMANTIC_GUARD",canary_pass=False,
            exact_owned_release=True,source_identity_request_payload_physical_isolation_release_valid=True)
    def test_disabled_admitted(self):admit("disabled",self.prior)
    def test_uninstalled_admitted(self):admit("uninstalled",self.prior)
    def test_enabled_forbidden(self):
        with self.assertRaises(ValueError):admit("enabled",self.prior)
    def test_reclassification_forbidden(self):
        for key,value in [("decision","PASS"),("canary_pass",True)]:
            altered=dict(self.prior);altered[key]=value
            with self.assertRaises(ValueError):admit("disabled",altered)
    def test_incomplete_release_forbidden(self):
        self.prior["exact_owned_release"]=False
        with self.assertRaises(ValueError):admit("disabled",self.prior)
    def test_bad_identity_forbidden(self):
        self.prior["source_identity_request_payload_physical_isolation_release_valid"]=False
        with self.assertRaises(ValueError):admit("uninstalled",self.prior)
if __name__=="__main__":unittest.main()
