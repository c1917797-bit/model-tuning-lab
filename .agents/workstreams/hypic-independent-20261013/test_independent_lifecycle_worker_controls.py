import copy,tempfile,unittest
from pathlib import Path
from independent_lifecycle_worker_controls import capture_worker_controls,CONTROL_KEYS
class Tests(unittest.TestCase):
    def fixture(self,root):
        cid="a"*64;owners=[]
        for rank in range(4):
            pid=100+rank;p=root/str(pid);p.mkdir();(p/"environ").write_bytes(
                b"INDEPENDENT_COMPACT_HYPIC=0\0INDEPENDENT_COMPACT_MANIFEST=/probe/m.json\0PYTHONPATH=/probe/compact_bootstrap:/probe\0UNRELATED_SECRET=never_output\0")
            owners.append(dict(npu=rank,pid=pid,nspid=[pid,50+rank],owned=True,ownership_status="owned-cgroup",cgroup="/docker/"+cid))
        return dict(foreign=[],owners=owners),cid
    def test_four_whitelisted_workers(self):
        with tempfile.TemporaryDirectory()as d:
            s,c=self.fixture(Path(d));out=capture_worker_controls(s,c,proc_root=d)
            self.assertEqual(len(out),4);self.assertEqual(set(out[0]["controls"]),set(CONTROL_KEYS))
            self.assertNotIn("never_output",str(out));self.assertEqual(out[0]["controls"]["INDEPENDENT_COMPACT_HYPIC"],"0")
    def test_uninstalled_absence_captured(self):
        with tempfile.TemporaryDirectory()as d:
            s,c=self.fixture(Path(d))
            for o in s["owners"]:(Path(d)/str(o["pid"])/"environ").write_bytes(b"OTHER=value\0")
            out=capture_worker_controls(s,c,proc_root=d);self.assertTrue(all(v is None for v in out[0]["controls"].values()))
    def reject(self,mutate):
        with tempfile.TemporaryDirectory()as d:
            s,c=self.fixture(Path(d));mutate(s,Path(d))
            with self.assertRaises(ValueError):capture_worker_controls(s,c,proc_root=d)
    def test_foreign_rejected_before_read(self):self.reject(lambda s,p:s.update(foreign=[1]))
    def test_wrong_cid(self):self.reject(lambda s,p:s["owners"][0].update(cgroup="/docker/"+"b"*64))
    def test_cid_prefix_not_owner(self):self.reject(lambda s,p:s["owners"][0].update(cgroup="/docker/"+"a"*64+"suffix"))
    def test_missing_worker(self):self.reject(lambda s,p:s["owners"].pop())
    def test_duplicate_pid(self):self.reject(lambda s,p:s["owners"][1].update(pid=100))
    def test_missing_namespace(self):self.reject(lambda s,p:s["owners"][0].update(nspid=[]))
    def test_duplicate_control(self):
        self.reject(lambda s,p:(p/"100"/"environ").write_bytes(b"INDEPENDENT_COMPACT_HYPIC=0\0INDEPENDENT_COMPACT_HYPIC=1\0"))
    def test_environment_bound(self):self.reject(lambda s,p:(p/"100"/"environ").write_bytes(b"x"*65537))
if __name__=="__main__":unittest.main()
