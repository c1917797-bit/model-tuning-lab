import copy
import unittest
import verify_completed_campaign_routes as v

class RoutesTest(unittest.TestCase):
    def setUp(self):
        self.cp = {"campaign": v.CAMPAIGN, "state": "six-phases-audited-performance-complete",
                   "completed_phases": 6, "controller_operation": None,
                   "source_commit": "fixed", "quality_decision": "REJECT_OR_QUALIFY",
                   "deployment_allowed": False}
        self.agg = {"campaign": v.CAMPAIGN, "all_six_phases_valid": True,
                    "phases": list(range(6)), "source_commit": "fixed",
                    "quality_decision": "REJECT_OR_QUALIFY", "deployment_allowed": False}
        self.cases = {n: {"skill":n,"long_term_acceptance":a,"next_gate":"Review existing evidence offline.",
            "current_campaign_resume":{"campaign":v.CAMPAIGN,"aggregate_sha256":v.AGGREGATE_SHA,
                "next_action_kind":"offline-evidence-review","new_device_work_authorized":False,
                "historical_observations_unchanged":True,"regression":"verify_completed_campaign_routes.py"}}
            for n,a in v.EXPECTED.items()}
    def test_terminal_offline_routes(self):
        self.assertEqual(v.check(self.cp,self.cases,self.agg)["checked_case_routes"],5)
    def test_each_observed_stale_directive(self):
        for stale in v.STALE:
            c=copy.deepcopy(self.cases)
            c["ascend-canary-implementation"]["next_gate"]=stale
            with self.assertRaises(RuntimeError): v.check(self.cp,c,self.agg)
    def test_running_or_incomplete(self):
        for field,value in [("completed_phases",5),("controller_operation","live"),("state","running")]:
            cp=dict(self.cp);cp[field]=value
            with self.assertRaises(RuntimeError): v.check(cp,self.cases,self.agg)
    def test_no_quality_or_adoption_promotion(self):
        for field,value in [("quality_decision","PASS"),("deployment_allowed",True)]:
            a=dict(self.agg);a[field]=value
            with self.assertRaises(RuntimeError): v.check(self.cp,self.cases,a)
    def test_no_new_device_permission_or_skill_promotion(self):
        c=copy.deepcopy(self.cases)
        c["ascend-canary-implementation"]["current_campaign_resume"]["new_device_work_authorized"]=True
        with self.assertRaises(RuntimeError): v.check(self.cp,c,self.agg)
        c=copy.deepcopy(self.cases)
        c["ascend-canary-implementation"]["long_term_acceptance"]="verified"
        with self.assertRaises(RuntimeError): v.check(self.cp,c,self.agg)
    def test_source_and_case_drift(self):
        a=dict(self.agg);a["source_commit"]="other"
        with self.assertRaises(RuntimeError): v.check(self.cp,self.cases,a)
        c=dict(self.cases);del c["paper-ingestion"]
        with self.assertRaises(RuntimeError): v.check(self.cp,c,self.agg)
if __name__ == "__main__":
    unittest.main()
