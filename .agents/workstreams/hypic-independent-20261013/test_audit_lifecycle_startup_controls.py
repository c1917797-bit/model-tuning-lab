import copy,unittest
from audit_lifecycle_startup_controls import audit_startup_controls
class Tests(unittest.TestCase):
    def fixture(self,stage="enabled"):
        cid="a"*64;c=dict(lifecycle_stage=stage)
        controls=dict(INDEPENDENT_COMPACT_HYPIC=None,INDEPENDENT_COMPACT_MANIFEST=None,PYTHONPATH="/official",VLLM_SERVER_DEV_MODE=None)
        argv=["docker","run"]
        if stage!="uninstalled":
            c["cache_diagnostic"]={"compact_manifest":"m.json"}
            controls.update(INDEPENDENT_COMPACT_HYPIC="1"if stage=="enabled"else"0",INDEPENDENT_COMPACT_MANIFEST="/probe/m.json",PYTHONPATH="/probe/compact_bootstrap:/probe:/official")
            argv+=["-v","/pkg:/probe:ro"]
            for k,v in controls.items():
                if v is not None:argv+=["-e",k+"="+v]
        argv+=["image","serve","--host","127.0.0.1"]
        owners=[dict(npu=i,pid=100+i,nspid=[100+i,50+i],owned=True,ownership_status="owned-cgroup",cgroup="/docker/"+cid)for i in range(4)]
        samples=[dict(utc="capture",foreign=[],owners=owners)]
        workers=[dict(physical_npu=i,host_pid=100+i,nspid=[100+i,50+i],controls=copy.deepcopy(controls))for i in range(4)]
        record=dict(event="lifecycle-worker-startup-controls",stage=stage,container_id=cid,snapshot_utc="capture",workers=workers)
        return record,c,samples,dict(container_id=cid),dict(argv=argv)
    def audit(self,args):return audit_startup_controls(*args,package_root="/pkg")
    def test_enabled(self):self.assertTrue(self.audit(self.fixture())["startup_controls_verified"])
    def test_disabled(self):self.assertEqual(self.audit(self.fixture("disabled"))["stage"],"disabled")
    def test_uninstalled(self):self.assertEqual(self.audit(self.fixture("uninstalled"))["stage"],"uninstalled")
    def reject(self,fn,stage="enabled"):
        args=self.fixture(stage);fn(*args)
        with self.assertRaises(ValueError):self.audit(args)
    def test_worker_switch_drift(self):self.reject(lambda r,c,s,start,l:r["workers"][0]["controls"].update(INDEPENDENT_COMPACT_HYPIC="0"))
    def test_worker_path_drift(self):self.reject(lambda r,c,s,start,l:r["workers"][0]["controls"].update(PYTHONPATH="/other"))
    def test_worker_namespace_drift(self):self.reject(lambda r,c,s,start,l:r["workers"][0].update(nspid=[100,999]))
    def test_nonowned(self):self.reject(lambda r,c,s,start,l:s[0]["owners"][0].update(owned=False))
    def test_foreign(self):self.reject(lambda r,c,s,start,l:s[0].update(foreign=[1]))
    def test_missing_worker(self):self.reject(lambda r,c,s,start,l:r["workers"].pop())
    def test_secret_field_rejected(self):self.reject(lambda r,c,s,start,l:r["workers"][0]["controls"].update(UNRELATED_SECRET="notpermitted"))
    def test_dev_interface_rejected(self):self.reject(lambda r,c,s,start,l:r["workers"][0]["controls"].update(VLLM_SERVER_DEV_MODE="1"))
    def test_public_host_rejected(self):self.reject(lambda r,c,s,start,l:l["argv"].__setitem__(-1,"0.0.0.0"))
    def test_uninstall_mount_rejected(self):self.reject(lambda r,c,s,start,l:l["argv"].extend(["-v","/pkg:/probe:ro"]),"uninstalled")
    def test_uninstall_worker_path_rejected(self):self.reject(lambda r,c,s,start,l:r["workers"][0]["controls"].update(PYTHONPATH="/probe/compact_bootstrap"),"uninstalled")
    def test_duplicate_env(self):self.reject(lambda r,c,s,start,l:l["argv"].extend(["-e","INDEPENDENT_COMPACT_HYPIC=0"]))
    def test_boolean_namespace_not_integer_identity(self):
        def mutate(r,c,s,start,l):
            r["workers"][0]["nspid"]=[100,False];s[0]["owners"][0]["nspid"]=[100,False]
        self.reject(mutate)
if __name__=="__main__":unittest.main()
