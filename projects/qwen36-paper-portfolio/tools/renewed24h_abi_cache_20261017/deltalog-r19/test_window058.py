import importlib.util,unittest
from types import SimpleNamespace
from pathlib import Path
P=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('w058',P/'window_overlay.py');W=importlib.util.module_from_spec(s);s.loader.exec_module(W)
class Window(unittest.TestCase):
 def test_registered(self):
  h=SimpleNamespace();m=dict(window=dict(start=W.START,cutoff=W.CUT),authority=W.AUTHORITY,authority_sha256=W.AUTHORITY['sha256'],cutoff_epoch=W.CUT);W.install(h,m);self.assertEqual(h.CUT,1792313000)
  m['authority_sha256']='wrong'
  with self.assertRaises(ValueError):W.install(h,m)
 def test_actual_generated_assignments(self):
  old='START, CUTOFF = 1791962297, 1792135097\nfacade.CUT = "2026-10-16T07:18:17+00:00"\nAUTH = ROOT / ".agents/workstreams/qwen36-damp-ascend-20261006/NEW48H_AUTHORITY_20261014.json"\n'
  new=W.transform(old);self.assertIn('1792313000',new);compile(new,'generated','exec')
  with self.assertRaises(ValueError):W.transform(new)
if __name__=='__main__':unittest.main()
