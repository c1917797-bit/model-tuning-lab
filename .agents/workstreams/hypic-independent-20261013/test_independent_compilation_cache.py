"""CPU protocol/storage controls; not live cache/NPU proof."""
import unittest,tempfile,json
from pathlib import Path
from unittest.mock import patch
import independent_compilation_cache as c
class Tests(unittest.TestCase):
 def test_bounds_and_mode(self):
  with self.assertRaises(ValueError):c.validate_cache_spec({})
  for p in ["/tmp/compiled-cache","/cache/cch/hypic-independent-20261013/../compiled-cache"]:
   with self.assertRaises(ValueError):c.validate_cache_spec({"compiled_cache":{"mode":"seed","path":p}})
 def test_symlink_and_storage_caps(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);(p/"x").write_bytes(b"123")
   with self.assertRaises(ValueError):c.inventory(p,max_bytes=2)
   with self.assertRaises(ValueError):c.inventory(p,max_files=0)
   (p/"link").symlink_to(p/"x")
   with self.assertRaises(ValueError):c.inventory(p)
 def test_seed_reuse_identity_and_tamper(self):
  with tempfile.TemporaryDirectory() as t,patch.object(c,"BASE",Path(t)):
   base=Path(t);seed=base/"seed";seed.mkdir();raw=base/"reuse";raw.mkdir()
   x={"compiled_cache":{"mode":"seed","path":str(seed/"compiled-cache")},"image":"same","model_config_sha256":"same","cache_diagnostic":{"source_sha256":{"a":"a"}},"tp":4,"physical_npus":[0,1,2,3]}
   p=c.prepare_cache(x,seed);(p/"kernel").write_bytes(b"binary")
   (seed/"compiled-cache-identity.json").write_text(json.dumps(c.identity(x)))
   (seed/"compiled-cache-inventory.json").write_text(json.dumps(c.inventory(p)))
   (seed/"result.json").write_text(json.dumps({"valid":True,"release":{"removed":True,"port_free":True}}))
   x["compiled_cache"]["mode"]="reuse";self.assertEqual(c.prepare_cache(x,raw),p)
   x["image"]="other"
   with self.assertRaises(ValueError):c.prepare_cache(x,raw)
   x["image"]="same";(p/"kernel").write_bytes(b"tamper")
   with self.assertRaises(ValueError):c.prepare_cache(x,raw)
 def test_no_formal_acceptance(self):
  for k in ["formal_performance","formal_quality"]:
   with self.assertRaises(ValueError):c.validate_cache_spec({"compiled_cache":{"mode":"seed","path":"/cache/cch/hypic-independent-20261013/a/compiled-cache"},k:True})
if __name__=="__main__":unittest.main()
