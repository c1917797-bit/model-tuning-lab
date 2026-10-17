"""Linux same-image controls pending; no mock of production Guard's body."""
import os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
class Controls(unittest.TestCase):
 @unittest.skipUnless(sys.platform=='linux','actual Linux symlink semantics required')
 def test_global_mock_breaks_real_symlink_resolution_narrow_mock_preserves(self):
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);actual=root/'python3.12';actual.write_bytes(b'software fixture');alias=root/'python3';alias.symlink_to('python3.12');proc=root/'proc-exe';original=os.readlink
   self.assertEqual(alias.resolve(strict=True),actual)
   with patch.object(os,'readlink',return_value=str(alias)):
    with self.assertRaises((RuntimeError,OSError)):alias.resolve(strict=True)
   def narrow(p,*a,**kw):return str(alias)if Path(p)==proc else original(p,*a,**kw)
   with patch.object(os,'readlink',side_effect=narrow):self.assertEqual(Path(os.readlink(proc)).resolve(strict=True),actual)
 def test_current_mm_HWM_parser_contract_not_arbitrary_threshold_change(self):
  def parse(text):
   rows=[x.split()for x in text.splitlines()if x.startswith('VmHWM:')]
   if len(rows)!=1 or len(rows[0])!=3 or rows[0][2]!='kB':raise ValueError('exact proc VmHWM')
   return int(rows[0][1])*1024
  self.assertEqual(parse('VmHWM:\t16384 kB\n'),16*2**20)
  for text in('VmRSS: 1 kB','VmHWM: 1 MB','VmHWM: 1 kB\nVmHWM: 2 kB'):
   with self.assertRaises(ValueError):parse(text)
if __name__=='__main__':unittest.main()
