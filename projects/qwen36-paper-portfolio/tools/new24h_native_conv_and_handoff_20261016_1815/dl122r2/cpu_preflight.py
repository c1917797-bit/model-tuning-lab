"""Devices[] complete software frontdoor; cannot supply numerical evidence."""
import argparse,json,os,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import api122 as A
from software_contract import SOFTWARE_CASES
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--source-ref',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sr=json.loads(a.source_ref);A.source(sr)
 A.need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and not list(Path('/dev').glob('davinci[0-9]*')),'actual Devices[]/autoloadOFF')
 suite=unittest.defaultTestLoader.discover(str(P),pattern='test122.py');A.need(suite.countTestCases()==SOFTWARE_CASES,'one software count');v=unittest.TextTestRunner(stream=sys.stderr).run(suite)
 A.need(v.wasSuccessful()and v.testsRun==SOFTWARE_CASES and not v.skipped,'whole actual software aggregate')
 A.write(a.output,dict(schema='deltalog.production-pair-CPU/v122',source=sr,tests=SOFTWARE_CASES,pass_software=True,Devices=[],NPU=False,model=False));return 0
if __name__=='__main__':raise SystemExit(main())
