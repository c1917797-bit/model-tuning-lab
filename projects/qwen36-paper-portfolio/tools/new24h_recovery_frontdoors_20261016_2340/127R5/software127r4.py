"""Whole inherited suite + new source seams, exact embedded historical fixtures."""
import base64,hashlib,json,os,sys,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
def main():
 fixture=json.loads((P/'FROZEN_TEST_INPUTS127R4.json').read_bytes())
 with tempfile.TemporaryDirectory()as td:
  root=Path(td)
  for n,v in fixture.items():
   data=base64.b64decode(v['base64']);r=v['ref']
   if len(data)!=r['bytes']or hashlib.sha256(data).hexdigest()!=r['sha256']:raise ValueError('exact historical software fixture')
   q=root/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
  os.environ['SOURCE127_ORIGINAL']=str(root/'original/run_consumer088.py');os.environ['SOURCE127_DONOR_HOST']=str(root/'donor/host.py')
  suite=unittest.defaultTestLoader.discover(str(P),pattern='test*.py');r=unittest.TextTestRunner(verbosity=1).run(suite);return 0 if r.wasSuccessful()else 1
if __name__=='__main__':raise SystemExit(main())
