import importlib.util,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;s=importlib.util.spec_from_file_location('rawfs011',P/'raw_filesystem.py');F=importlib.util.module_from_spec(s);s.loader.exec_module(F)
class Tests(unittest.TestCase):
 def test_actual_inventory_and_budget_failure_retained(self):
  with tempfile.TemporaryDirectory()as td:
   p=Path(td);(p/'a').write_bytes(b'123');(p/'b').mkdir();(p/'b/c').write_bytes(b'4567');self.assertEqual(F.scan(p)['bytes'],7)
   old=F.BUDGET;F.BUDGET=6
   try:
    with self.assertRaises(ValueError):F.scan(p)
    self.assertEqual((p/'b/c').read_bytes(),b'4567')
   finally:F.BUDGET=old
 def test_source_wiring_cannot_alias_cache_space(self):
  h=(P/'host_ticket.py').read_text();w=(P/'worker.py').read_text();c=(P/'consume.py').read_text()
  self.assertIn('str(_RAW_ROOT):(str(_RAW_ROOT), not cpu)',h);self.assertIn('raw.prepare(h.OUT)',h);self.assertIn('raw_root.stat().st_dev==root.stat().st_dev',w);self.assertIn('codec.read(torch,raw[',c);self.assertIn('codec.read(torch,n[',c)
if __name__=='__main__':unittest.main()
