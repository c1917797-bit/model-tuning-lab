"""Mandatory pure CPU22 controls, no HAL/native imports."""
import hashlib,json,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
def main():
 m=json.loads((P/'SOURCE_MANIFEST.json').read_bytes())
 for n,r in m['files'].items():
  b=(P/n).read_bytes()
  if len(b)!=r['bytes'] or hashlib.sha256(b).hexdigest()!=r['sha256']:raise ValueError('whole declared own source '+n)
 for n,r in m['software_fixture_origins'].items():
  b=(P/n).read_bytes()
  if len(b)!=r['bytes'] or hashlib.sha256(b).hexdigest()!=r['sha256']:raise ValueError('original unchanged software math fixture '+n)
 suite=unittest.TestSuite()
 for n in ('test_byteaudit','test_firstdecode','test_native_entries','test_namespace'):suite.addTests(unittest.defaultTestLoader.loadTestsFromName(n))
 if suite.countTestCases()!=22 or m['software_cases']!=22:raise ValueError('exact22 aggregate')
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 if not result.wasSuccessful() or result.testsRun!=22 or result.skipped:raise ValueError('all22/noSkip required')
 print(json.dumps(dict(schema='deltalog.firstdecode-software/v1',count=22,passed=True,NPU=False,qualification=False)))
 return 0
if __name__=='__main__':raise SystemExit(main())
