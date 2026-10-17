"""Declared-only separated deployment, no ambient neighbouring donor aliases."""
import hashlib,json,subprocess,sys,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parent


class Tests(unittest.TestCase):
 def test_actual_cold_entry_only_declared_tree_and_missing_helper_reject(self):
  manifest=json.loads((P/'SOURCE.json').read_bytes())
  with tempfile.TemporaryDirectory()as td:
   root=Path(td)/'separate'/'declared-lowbit'/'runtime131';root.mkdir(parents=True)
   for name,r in manifest['files'].items():
    body=(P/name).read_bytes();self.assertEqual((len(body),hashlib.sha256(body).hexdigest()),(r['bytes'],r['sha256']))
    dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(body)
   for name in('SOURCE.json','SOURCE_TEMPLATE.json'):(root/name).write_bytes((P/name).read_bytes())
   argv=[sys.executable,'-I','-B',str(root/'entry.py'),'--source-audit']
   positive=subprocess.run(argv,capture_output=True,text=True,timeout=20)
   self.assertEqual(positive.returncode,0,positive.stderr)
   # The missing real helper cannot be supplied by an ambient flat Temp root.
   (root/'prefill_tail.py').unlink()
   negative=subprocess.run(argv,capture_output=True,text=True,timeout=20)
   self.assertNotEqual(negative.returncode,0)


if __name__=='__main__':unittest.main()
