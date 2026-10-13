import copy,unittest
from operational_lifecycle_failure_20261013 import classify
class FailureAuditTests(unittest.TestCase):
    def setUp(self):
        self.t=dict(container_id="own",completed=False,error="lane guard detected foreign")
        self.s=dict(container_id="own",container_removed=True,owned_npus_released=True,port_released=True,service_reached_health=False,prehealth_top_error=None,service_log_error=None)
        self.g=dict(owned_container_id="own",samples=20,probe_errors=[],foreign=[dict(at_utc="t",processes=[dict(pid=1,physical_npu=3,container_id="foreign")])])
    def test_bounded_failure(self):self.assertFalse(classify(self.t,self.s,self.g,False,False)["lifecycle_pass"])
    def test_unreleased(self):
        self.s["owned_npus_released"]=False
        with self.assertRaises(ValueError):classify(self.t,self.s,self.g,False,False)
    def test_wrong_owner(self):
        self.g["foreign"][0]["processes"][0]["container_id"]="own"
        with self.assertRaises(ValueError):classify(self.t,self.s,self.g,False,False)
    def test_no_foreign(self):
        self.g["foreign"]=[]
        with self.assertRaises(ValueError):classify(self.t,self.s,self.g,False,False)
    def test_health_present(self):
        with self.assertRaises(ValueError):classify(self.t,self.s,self.g,True,False)
    def test_request_present(self):
        with self.assertRaises(ValueError):classify(self.t,self.s,self.g,False,True)
if __name__=="__main__":unittest.main()
