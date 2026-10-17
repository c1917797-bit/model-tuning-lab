import argparse,hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--source-audit',action='store_true');p.add_argument('--software',action='store_true');a=p.parse_args()
 if not(a.source_audit or a.software):print('{"enabled":false,"NPU":false,"qualified":false}');return 0
 m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes())
 for n,r in m['files'].items():
  b=(P/n).read_bytes()
  if(len(b),hashlib.sha256(b).hexdigest())!=(r['bytes'],r['sha256']):raise ValueError('exact own source '+n)
 if a.software:
  sys.path.insert(0,str(P));import unittest
  result=unittest.TextTestRunner().run(unittest.defaultTestLoader.discover(str(P),pattern='test*.py',top_level_dir=str(P)))
  return 0 if result.wasSuccessful()and result.testsRun==15 and not result.skipped else 3
 print('{"source_audited":true,"NPU":false,"resources_admitted":false}');return 0
if __name__=='__main__':raise SystemExit(main())
