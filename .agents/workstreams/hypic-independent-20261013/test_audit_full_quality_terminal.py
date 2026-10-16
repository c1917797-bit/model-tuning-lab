import unittest
from audit_full_quality_terminal import audit_quality_terminal_records
class Tests(unittest.TestCase):
    def fixture(self):
        c=dict(image="image");start=dict(container_id="a"*64,image="image",devices=["/dev/davinci"+str(i)for i in range(4)])
        release=dict(owned_container="a"*64,removed=True,port_free=True,final_physical_processes=[])
        samples=[dict(foreign=[])];r=dict(valid=True,error=None,guard_errors=[],responses=381,isolation_samples=1,release=release)
        return c,r,[{}for _ in range(381)],[dict(event="isolation",snapshot=samples[0]),dict(event="terminal",result=r)],samples,start,release
    def test_complete(self):audit_quality_terminal_records(*self.fixture())
    def reject(self,fn):
        args=self.fixture();fn(*args)
        with self.assertRaises(ValueError):audit_quality_terminal_records(*args)
    def test_wrong_count(self):self.reject(lambda c,r,*a:r.update(responses=17))
    def test_missing_response(self):self.reject(lambda c,r,records,*a:records.pop())
    def test_failed(self):self.reject(lambda c,r,*a:r.update(valid=False))
    def test_foreign(self):self.reject(lambda c,r,recs,j,s,*a:s[0].update(foreign=[1]))
    def test_missing_terminal(self):self.reject(lambda c,r,recs,j,*a:j.pop())
    def test_wrong_cid(self):self.reject(lambda c,r,recs,j,s,start,rel:rel.update(owned_container="b"*64))
    def test_wrong_physical(self):self.reject(lambda c,r,recs,j,s,start,*a:start.update(devices=["/dev/davinci4"]))
    def test_not_released(self):self.reject(lambda c,r,recs,j,s,start,rel:rel.update(removed=False))
if __name__=="__main__":unittest.main()
