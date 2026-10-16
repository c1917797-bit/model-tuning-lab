"""Source-derived two-filesystem and actual017 overlay ordering controls."""
import ast,hashlib,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
class ResourceBinding(unittest.TestCase):
 def test_actual_stage_output_floor_and_original_ram(self):
  import stage_resources as R
  b=(P/'actual_loader/safety_host.py').read_bytes();original,text,pairs=R.derive(b)
  self.assertIn('free>=int(8.5*c.GIB)+(WORKSPACE if initial else 0)',text)
  self.assertIn('RESERVE+HOST_MEM+(guest_budget if initial else 0)',text)
  inverse=text
  for old,new in reversed(pairs):inverse=inverse.replace(new,old)
  self.assertEqual(inverse,original)
 def test_host_installs_after_original_protection_before_run(self):
  text=(P/'host_ticket.py').read_text();ast.parse(text)
  self.assertLess(text.index('H.protect_cleanup(h)'),text.index('original_safety=h.safety'))
  self.assertLess(text.index('original_safety(source_ref'),text.index('h._EXTERNAL.install'))
  self.assertLess(text.index('h.safety=safety'),text.index('h.run=lambda'))
  self.assertIn('OUT = Path(',text);self.assertNotIn('relative_to(H.LOW.parent)',text)
if __name__=='__main__':unittest.main()
