import copy
import unittest
from audit_physical_worker_namespaces import audit_physical_workers

class PhysicalJoin(unittest.TestCase):
    def setUp(self):
        self.cid = "a"*64
        self.workers = {0:62, 1:59, 2:61, 3:60}
        self.samples = [{"owners":[{"pid":100+i, "npu":i, "nspid":[100+i,self.workers[i]], "owned":True, "cgroup":"/docker/"+self.cid} for i in range(4)]}]
    def test_explicit_not_ordered(self):
        r=audit_physical_workers(self.samples,self.workers,owned_cid=self.cid)
        self.assertEqual(r["ranks"][0]["inner_pid"],62)
        self.assertEqual(r["ranks"][1]["physical_npu"],1)
    def test_fail_closed(self):
        for field,value in [("nspid",None),("owned",False),("cgroup","/"),("npu",7),("pid",999)]:
            s=copy.deepcopy(self.samples);s[0]["owners"][0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):
                audit_physical_workers(s,self.workers,owned_cid=self.cid)
    def test_ambiguous(self):
        s=copy.deepcopy(self.samples);x=copy.deepcopy(s[0]["owners"][0]);x["pid"]=999;x["nspid"][0]=999;s[0]["owners"].append(x)
        with self.assertRaises(ValueError):audit_physical_workers(s,self.workers,owned_cid=self.cid)
if __name__=="__main__":unittest.main()
