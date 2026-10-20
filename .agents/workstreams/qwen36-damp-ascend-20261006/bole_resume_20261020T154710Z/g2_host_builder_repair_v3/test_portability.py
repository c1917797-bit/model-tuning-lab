"""Synthetic portable inventory checks; no host/container/model operations."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
P=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('portable_builder',P/'prepare_g2_host_v3.py');B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)


class Tests(unittest.TestCase):
 def fixture(self):
  td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);root=Path(td.name);f=root/'code.py';f.write_bytes(b'qualified bytes\n')
  actual=B.ref(f);advisory=dict(actual,path='/workspace/advisory/code.py');return root,f,actual,advisory
 def test_different_absolute_advisory_and_remote_paths_accept_exact_bytes_hash(self):
  root,f,actual,advisory=self.fixture();self.assertNotEqual(actual['path'],advisory['path'])
  self.assertEqual(B.portable_inventory(root,'code.py',advisory),actual)
 def test_wrong_hash_rejects_even_with_same_byte_count(self):
  root,f,actual,advisory=self.fixture();advisory['sha256']='0'*64
  with self.assertRaisesRegex(ValueError,'bytes/SHA'):B.portable_inventory(root,'code.py',advisory)
 def test_wrong_size_rejects_even_with_same_hash(self):
  root,f,actual,advisory=self.fixture();advisory['bytes']+=1
  with self.assertRaisesRegex(ValueError,'bytes/SHA'):B.portable_inventory(root,'code.py',advisory)
 def test_changed_actual_file_is_rejected(self):
  root,f,actual,advisory=self.fixture();f.write_bytes(b'unqualified data')
  with self.assertRaisesRegex(ValueError,'bytes/SHA'):B.portable_inventory(root,'code.py',advisory)
 def test_file_symlink_is_rejected(self):
  root,f,actual,advisory=self.fixture();target=root/'target';f.rename(target);f.symlink_to(target)
  with self.assertRaisesRegex(ValueError,'without symlink'):B.portable_inventory(root,'code.py',advisory)
 def test_parent_symlink_is_rejected(self):
  root,f,actual,advisory=self.fixture();link=root/'alias';link.symlink_to(root,target_is_directory=True)
  with self.assertRaisesRegex(ValueError,'without symlink'):B.portable_inventory(link,'code.py',advisory)
 def test_directory_or_path_escape_is_rejected(self):
  root,f,actual,advisory=self.fixture()
  for name in('../code.py','sub/code.py','..'):
   with self.subTest(name=name),self.assertRaises(ValueError):B.portable_inventory(root,name,advisory)
 def test_advisory_filename_mismatch_or_malformed_ref_is_rejected(self):
  root,f,actual,advisory=self.fixture()
  for v in(dict(advisory,path='/workspace/advisory/other.py'),dict(advisory,extra=True)):
   with self.assertRaises(ValueError):B.portable_inventory(root,'code.py',v)
 def test_cold_default_OFF_and_help(self):
  for mode in([],['--help']):
   q=subprocess.run([sys.executable,'-I','-B',str(P/'prepare_g2_host_v3.py'),*mode],capture_output=True,text=True,timeout=10)
   self.assertEqual(q.returncode,0,q.stderr)
   if not mode:self.assertEqual(json.loads(q.stdout),dict(enabled=False,NPU=False))


if __name__=='__main__':unittest.main()
