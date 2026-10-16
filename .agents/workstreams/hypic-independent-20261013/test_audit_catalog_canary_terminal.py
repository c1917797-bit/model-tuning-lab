import copy,unittest
from audit_catalog_canary_terminal import audit_terminal_records
class Tests(unittest.TestCase):
    def fixture(self):
        c=dict(image="image");start=dict(container_id="a"*64,image="image",devices=["/dev/davinci"+str(i)for i in range(4)])
        release=dict(owned_container="a"*64,removed=True,port_free=True,final_physical_processes=[])
        samples=[dict(foreign=[])];r=dict(valid=True,error=None,guard_errors=[],responses=17,isolation_samples=1,release=release)
        j=[dict(event="isolation",snapshot=samples[0]),dict(event="terminal",result=r)]
        return c,r,[{}for i in range(17)],j,samples,start,release
    def test_complete(self):audit_terminal_records(*self.fixture())
    def reject(self,fn):
        args=self.fixture();fn(*args)
        with self.assertRaises(ValueError):audit_terminal_records(*args)
    def test_failed_controller(self):self.reject(lambda c,r,*a:r.update(valid=False))
    def test_guard_error(self):self.reject(lambda c,r,*a:r.update(guard_errors=["foreign"]))
    def test_partial_responses(self):self.reject(lambda c,r,recs,*a:recs.pop())
    def test_terminal_missing(self):self.reject(lambda c,r,recs,j,*a:j.pop())
    def test_foreign(self):self.reject(lambda c,r,recs,j,s,*a:s[0].update(foreign=[1]))
    def test_wrong_device(self):self.reject(lambda c,r,recs,j,s,start,*a:start.update(devices=["/dev/davinci4"]))
    def test_release_cid_drift(self):self.reject(lambda c,r,recs,j,s,start,rel:rel.update(owned_container="b"*64))
    def test_port_not_released(self):self.reject(lambda c,r,recs,j,s,start,rel:rel.update(port_free=False))
    def test_remaining_process(self):self.reject(lambda c,r,recs,j,s,start,rel:rel.update(final_physical_processes=[1]))
if __name__=="__main__":unittest.main()
