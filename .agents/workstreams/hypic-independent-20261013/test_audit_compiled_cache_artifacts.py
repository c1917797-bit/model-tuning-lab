import base64,json,tempfile,unittest
from pathlib import Path
from audit_compiled_cache_artifacts import audit_groups
class Tests(unittest.TestCase):
 def fixture(self,root):
  h="1"*64;key=base64.urlsafe_b64encode(bytes.fromhex(h)).decode().rstrip("=")
  p=root/key;p.mkdir();meta={"hash":h,"target":{"backend":"npu","arch":"Ascend910B4"},"name":"chunk_fixture"}
  (p/"chunk_fixture.json").write_text(json.dumps(meta));(p/"chunk_fixture.npubin").write_bytes(b"fixture-not-real-device-code")
  d={"child_paths":{f:"/compilation-cache/"+key+"/"+f for f in ["chunk_fixture.json","chunk_fixture.npubin"]}}
  g=p/"__grp__chunk_fixture.json";g.write_text(json.dumps(d));return p,g,meta,d
 def test_valid_is_artifact_only(self):
  with tempfile.TemporaryDirectory() as t:
   self.fixture(Path(t));r=audit_groups(t);self.assertTrue(r["compiled_artifacts_valid"]);self.assertIn("not runtime hit",r["scope"])
 def test_missing_binary(self):
  with tempfile.TemporaryDirectory() as t:
   p,*_=self.fixture(Path(t));(p/"chunk_fixture.npubin").unlink()
   with self.assertRaises(ValueError):audit_groups(t)
 def test_wrong_target(self):
  with tempfile.TemporaryDirectory() as t:
   p,g,m,d=self.fixture(Path(t));m["target"]["arch"]="other";(p/"chunk_fixture.json").write_text(json.dumps(m))
   with self.assertRaises(ValueError):audit_groups(t)
 def test_key_drift(self):
  with tempfile.TemporaryDirectory() as t:
   p,g,m,d=self.fixture(Path(t));m["hash"]="2"*64;(p/"chunk_fixture.json").write_text(json.dumps(m))
   with self.assertRaises(ValueError):audit_groups(t)
 def test_path_escape(self):
  with tempfile.TemporaryDirectory() as t:
   p,g,m,d=self.fixture(Path(t));d["child_paths"]["chunk_fixture.npubin"]="/compilation-cache/../outside";g.write_text(json.dumps(d))
   with self.assertRaises(ValueError):audit_groups(t)
 def test_symlink_and_inventory_drift(self):
  with tempfile.TemporaryDirectory() as t:
   p,g,m,d=self.fixture(Path(t));r=audit_groups(t);(p/"extra").write_bytes(b"x")
   with self.assertRaises(ValueError):audit_groups(t,recorded_inventory=r["inventory"])
   (p/"link").symlink_to(p/"chunk_fixture.json")
   with self.assertRaises(ValueError):audit_groups(t)
 def test_empty(self):
  with tempfile.TemporaryDirectory() as t:
   with self.assertRaises(ValueError):audit_groups(t)
if __name__=="__main__":unittest.main()
