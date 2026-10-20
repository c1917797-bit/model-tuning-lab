"""Host-only repair controls; not counted as current same-image math tests."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
P=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('g2_control_v5_builder',P/'prepare_g2_control_v5.py');B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)

class PreparerTests(unittest.TestCase):
 def test_contract_changes_only_two_exact_output_assignments_and_reverses(self):
  text="OUTPUT_POSIX='/opt/old'\nCPU_OUTPUT_POSIX='/opt/old-CPU'\nCACHE=.8\n"
  changed=B.outputs(text,'/opt/new');self.assertIn('CACHE=.8',changed);self.assertEqual(B.outputs(changed,'/opt/old'),text)
  with self.assertRaises(ValueError):B.outputs(text+"OUTPUT_POSIX='/duplicate'\n",'/opt/new')
 def test_advisory_path_is_not_remote_identity_and_wronghash_or_symlink_fails(self):
  td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);root=Path(td.name);path=root/'one.py';path.write_text('reviewed\n')
  advisory=dict(B.ref(path),path='/workspace/advisory/one.py');self.assertEqual(B.inventory(root,'one.py',advisory),B.ref(path))
  with self.assertRaises(ValueError):B.inventory(root,'one.py',dict(advisory,sha256='0'*64))
  path.rename(root/'real.py');path.symlink_to(root/'real.py')
  with self.assertRaises(ValueError):B.inventory(root,'one.py',advisory)

if __name__=='__main__':unittest.main()
