import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import independent_full_protocol_cache as c
import full_protocol_cache_launcher as w
class Tests(unittest.TestCase):
 def fixture(self,root):
  seed=root/"seed";seed.mkdir();cache=seed/"compiled-cache";cache.mkdir();(cache/"kernel").write_bytes(b"fixture")
  (root/"old.py").write_text("source");old={"old.py":hashlib.sha256(b"source").hexdigest()}
  s={"raw_root":str(seed),"image":"same","model":"same","model_config_sha256":"same","physical_npus":[0,1,2,3],"tp":4,"cache_diagnostic":{"source_sha256":old}}
  b=json.dumps(s).encode();(root/"seed.json").write_bytes(b);(seed/"compiled-cache-identity.json").write_text(json.dumps(c.identity(s)))
  (seed/"compiled-cache-inventory.json").write_text(json.dumps(c.inventory(cache)));(seed/"result.json").write_text(json.dumps({"valid":True,"release":{"removed":True,"port_free":True}}))
  x={k:s[k] for k in ["image","model","model_config_sha256","physical_npus","tp"]};x.update(compiled_cache_seed_contract={"path":"seed.json","sha256":hashlib.sha256(b).hexdigest()},compiled_cache_source_sha256=dict(old,**{name:"fixture" for name in c.EXTRAS}))
  raw=root/"new";raw.mkdir();return x,raw,seed
 def test_injection_is_narrow(self):
  a=["docker","run","-d","--name","x","image","serve","/model"];b=c.inject_cache(a,Path("/own/cache"))
  self.assertEqual(a[:2],b[:2]);self.assertEqual(b[6:],a[2:]);self.assertEqual(a,["docker","run","-d","--name","x","image","serve","/model"])
  for a in [["docker","exec","x"],["docker","run","-e","TRITON_CACHE_DIR=/other"]]:
   with self.assertRaises(ValueError):c.inject_cache(a,Path("/own/cache"))
 def test_seed_copy_no_original_mutation(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);x,raw,seed=self.fixture(root)
   with patch.object(c,"HERE",root),patch.object(c,"BASE",root):
    target,before=c.stage_cache(x,raw);self.assertEqual(c.inventory(target),before);(target/"kernel").write_bytes(b"changed");self.assertEqual((seed/"compiled-cache"/"kernel").read_bytes(),b"fixture")
 def test_seed_identity_runtime_must_match(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);x,raw,seed=self.fixture(root);x["image"]="other"
   with patch.object(c,"HERE",root):
    with self.assertRaises(ValueError):c.seed_contract(x)
 def test_failed_seed_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);x,raw,seed=self.fixture(root);(seed/"result.json").write_text('{"valid":false}')
   with patch.object(c,"HERE",root),patch.object(c,"BASE",root):
    with self.assertRaises(ValueError):c.stage_cache(x,raw)
 def test_tamper_and_symlink_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);x,raw,seed=self.fixture(root);(seed/"compiled-cache"/"kernel").write_bytes(b"bad")
   with patch.object(c,"HERE",root),patch.object(c,"BASE",root):
    with self.assertRaises(ValueError):c.stage_cache(x,raw)
 def test_wrapper_restores_original_command_after_failure(self):
  with tempfile.TemporaryDirectory() as t:
   raw=Path(t);calls=[]
   def original(a,**kw):calls.append(a);return "ok"
   def fail(c):w.base.command(["docker","inspect","owned"]);raise RuntimeError("fixture")
   with patch.object(w,"validate"),patch.object(w.base,"command",original),patch.object(w.base,"run_contract",fail):
    with self.assertRaises(RuntimeError):w.run({"raw_root":str(raw)})
    self.assertIs(w.base.command,original);self.assertEqual(calls,[["docker","inspect","owned"]])
 def test_wrapper_stages_only_launch_and_seals_after_return(self):
  with tempfile.TemporaryDirectory() as t:
   raw=Path(t);cache=raw/"compiled-cache";cache.mkdir();calls=[];writes=[]
   def original(a,**kw):calls.append(a);return "owned"
   def run(c):
    w.base.command(["docker","inspect","before"]);w.base.command(["docker","run","-d","image"])
    (raw/"result.json").write_text('{"valid":true}')
   spec={"raw_root":str(raw),"launcher_sha256":"bound","compiled_cache_seed_contract":{"path":"seed","sha256":"bound"}}
   with patch.object(w,"validate"),patch.object(w,"stage_cache",return_value=(cache,{"file_count":1})),patch.object(w,"identity",return_value={}),patch.object(w.base,"command",original),patch.object(w.base,"run_contract",run),patch.object(w.base,"write",side_effect=lambda r,f,x:writes.append((f,x))):
    w.run(spec)
   self.assertEqual(calls[0],["docker","inspect","before"]);self.assertIn("TRITON_CACHE_DIR=/compilation-cache",calls[1]);self.assertIn(("cache-launcher-result.json",{"valid":True,"source":"audited copy; original seed never writable-mounted"}),writes)
if __name__=="__main__":unittest.main()
