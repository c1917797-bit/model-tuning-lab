import ast,pathlib,unittest
P=pathlib.Path(__file__).resolve().parent
class Owner(unittest.TestCase):
    def test_ast(self):
        for f in P.glob('*.py'):ast.parse(f.read_text())
    def test_no_device_build(self):
        s=(P/'host.py').read_text()
        self.assertIn("x['HostConfig']['Devices']==[]",s)
        self.assertIn('C.PHASE=900;C.CLEANUP=90',s)
        self.assertIn('ctl.remaining(cap=810)',s)
    def test_guest_image_domain(self):
        h=(P/'host.py').read_text();g=(P/'guest.py').read_text()
        self.assertNotIn("m['image_refs']",h)
        self.assertIn("for r in m['image_refs']:checked(r)",g)
    def test_original_binder_cli_guard(self):
        s=(P/'bind_cohort.py').read_text()
        self.assertIn("'--as=unlimited','--','/usr/bin/docker'",s)
        self.assertIn('(536870912,resource.RLIM_INFINITY)',s)
        self.assertIn("'deltalog.owned-kdma-build-source/v1'",s)
    def test_no_model_claim(self):
        s=(P/'guest.py').read_text()
        self.assertIn("v['numeric_qualified'] is False",s)
        self.assertIn("v['model_ready'] is False",s)
if __name__=='__main__':unittest.main()
