import copy,unittest
from audit_lifecycle_sequence import audit_sequence_records,audit_sequence
class Tests(unittest.TestCase):
    def fixture(self):
        common=dict(image="image",model="/model",model_config_sha256="hash",physical_npus=[0,1,2,3],tp=4,port=8233,hccl_ports=[26300,26400],cpu_set="112-191",formal_token_artifact={"path":"/tokens","sha256":"input"},max_output_tokens=64,lifecycle_private_output_tokens=64,enable_thinking=False,enable_prefix_caching=False,enforce_eager=True,completion=True,controller_sha256="controller",absolute_stop_utc="2026-10-17T06:48:09Z")
        package=dict(compact_manifest="manifest.json",source_sha256={"lifecycle_r16_tp4.py":"controller","patch.py":"patch"})
        rows=[]
        for i,name in enumerate(("disabled","enabled","uninstalled")):
            c=dict(copy.deepcopy(common),lifecycle_stage=name)
            if i<2:c["cache_diagnostic"]=copy.deepcopy(package)
            else:c.update(cache_diagnostic=None,baseline_host_source_sha256=copy.deepcopy(package["source_sha256"]))
            cid=str(i+1)*64
            a=dict(lifecycle_stage_audited=True,stage=name,startup={"startup_controls_verified":True},transport={"lifecycle_requests_verified":True},hot=None,physical=None)
            if i==1:a.update(hot={"accepted_hot_coverage":True,"denominator":2},physical={"four":True})
            rows.append(dict(contract=c,audit=a,start={"container_id":cid},release=dict(owned_container=cid,removed=True,final_physical_processes=[],utc="2026-10-16T12:0"+str(i*2+1)+":00Z"),preflight=dict(processes=[],foreign=[],utc="2026-10-16T12:0"+str(i*2)+":00Z"),raw_root="/raw/"+name))
        return rows
    def reject(self,fn):
        s=self.fixture();fn(s)
        with self.assertRaises(ValueError):audit_sequence_records(s)
    def test_complete_sequence(self):
        r=audit_sequence_records(self.fixture());self.assertTrue(r["lifecycle_sequence_audited"]);self.assertFalse(r["hot_inprocess_uninstall_claimed"]);self.assertFalse(r["prior_performance_quality_verified"])
    def test_order(self):self.reject(lambda s:s.reverse())
    def test_missing_stage(self):self.reject(lambda s:s.pop())
    def test_model_drift(self):self.reject(lambda s:s[2]["contract"].update(model="/other"))
    def test_input_drift(self):self.reject(lambda s:s[1]["contract"]["formal_token_artifact"].update(sha256="other"))
    def test_source_drift(self):self.reject(lambda s:s[2]["contract"]["baseline_host_source_sha256"].update(**{"patch.py":"other"}))
    def test_same_package_disabled_enabled(self):self.reject(lambda s:s[1]["contract"]["cache_diagnostic"].update(compact_manifest="other.json"))
    def test_restart_retains_package(self):self.reject(lambda s:s[2]["contract"].update(cache_diagnostic={"bad":True}))
    def test_missing_stage_audit(self):self.reject(lambda s:s[0]["audit"].update(lifecycle_stage_audited=False))
    def test_enabled_missing_hot(self):self.reject(lambda s:s[1]["audit"].update(hot={}))
    def test_disabled_has_hot(self):self.reject(lambda s:s[0]["audit"].update(hot={"present":True}))
    def test_failed_release(self):self.reject(lambda s:s[0]["release"].update(removed=False))
    def test_overlap(self):self.reject(lambda s:s[1]["preflight"].update(utc="2026-10-16T12:00:30Z"))
    def test_naive_time(self):self.reject(lambda s:s[0]["release"].update(utc="2026-10-16T12:01:00"))
    def test_missing_release_time(self):self.reject(lambda s:s[0]["release"].pop("utc"))
    def test_foreign_at_admission(self):self.reject(lambda s:s[1]["preflight"].update(processes=[[3,123]]))
    def test_reused_instance(self):
        def mutate(s):
            s[2]["start"]["container_id"]=s[0]["start"]["container_id"];s[2]["release"]["owned_container"]=s[0]["start"]["container_id"]
        self.reject(mutate)
    def test_reused_raw(self):self.reject(lambda s:s[2].update(raw_root=s[0]["raw_root"]))
    def test_paths_count_rejected_before_read(self):
        with self.assertRaises(ValueError):audit_sequence(["/one","/two"])
if __name__=="__main__":unittest.main()
