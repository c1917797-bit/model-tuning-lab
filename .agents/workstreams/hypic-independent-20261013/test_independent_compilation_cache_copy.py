import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import independent_compilation_cache_copy as c
class Tests(unittest.TestCase):
 def setup_case(self,base):
  seed=base/"seed";seed.mkdir();cache=seed/"compiled-cache";cache.mkdir();(cache/"binary").write_bytes(b"independent-fixture")
  (base/"old.py").write_text("source")
  old={"old.py":hashlib.sha256(b"source").hexdigest()}
  contract={"raw_root":str(seed),"cache_diagnostic":{"source_sha256":old}}
  data=json.dumps(contract).encode();(base/"seed.json").write_bytes(data)
  current={"compiled_cache":{"mode":"reuse","path":str(cache)},"compiled_cache_seed_contract":{"path":"seed.json","sha256":hashlib.sha256(data).hexdigest()},"cache_diagnostic":{"source_sha256":dict(old,**{x:"fixture" for x in c.EXTRAS})}}
  raw=base/"reuse";raw.mkdir();return current,raw,cache
 def test_copy_does_not_mutate_seed(self):
  with tempfile.TemporaryDirectory() as t:
   base=Path(t);x,raw,source=self.setup_case(base)
   with patch.object(c,"HERE",base),patch.object(c,"original_prepare_cache",return_value=source):
    staged=c.prepare_cache(x,raw);self.assertNotEqual(staged,source);self.assertEqual((staged/"binary").read_bytes(),b"independent-fixture")
    (staged/"binary").write_bytes(b"changed");self.assertEqual((source/"binary").read_bytes(),b"independent-fixture")
 def test_runtime_binding_drift(self):
  with tempfile.TemporaryDirectory() as t:
   base=Path(t);x,raw,source=self.setup_case(base);x["cache_diagnostic"]["source_sha256"]["old.py"]="wrong"
   with patch.object(c,"HERE",base):
    with self.assertRaises(ValueError):c.prepare_cache(x,raw)
 def test_seed_contract_drift(self):
  with tempfile.TemporaryDirectory() as t:
   base=Path(t);x,raw,source=self.setup_case(base);(base/"seed.json").write_text("{}")
   with patch.object(c,"HERE",base):
    with self.assertRaises(ValueError):c.prepare_cache(x,raw)
 def test_existing_destination_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   base=Path(t);x,raw,source=self.setup_case(base);(raw/"compiled-cache").mkdir()
   with patch.object(c,"HERE",base),patch.object(c,"original_prepare_cache",return_value=source):
    with self.assertRaises(ValueError):c.prepare_cache(x,raw)
 def test_failed_seed_cannot_bypass_original_gate(self):
  with tempfile.TemporaryDirectory() as t:
   base=Path(t);x,raw,source=self.setup_case(base)
   with patch.object(c,"HERE",base),patch.object(c,"original_prepare_cache",side_effect=ValueError("seed unreleased")):
    with self.assertRaises(ValueError):c.prepare_cache(x,raw)
if __name__=="__main__":unittest.main()
