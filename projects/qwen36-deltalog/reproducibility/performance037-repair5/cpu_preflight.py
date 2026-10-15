"""Existing owner Devices[] stage: source/std software only, no fake NPU."""
import argparse,json,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--source-ref',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 from source_audit import audit
 from screen_binding import SOFTWARE_CASES
 sr=json.loads(a.source_ref);m=audit(sr)
 from mechanical import compare
 from qwen36_deltalog_screen import admission as A
 previous=A.obj(m['diagnostic_predecessor_ref'])
 compare(Path(previous['root'])/'qwen36_deltalog_service',P/'qwen36_deltalog_screen')
 suite=unittest.defaultTestLoader.discover(str(P),pattern='test_software.py')
 if suite.countTestCases()!=SOFTWARE_CASES:raise RuntimeError('same unique software contract count')
 result=unittest.TextTestRunner().run(suite)
 if not result.wasSuccessful() or result.testsRun!=SOFTWARE_CASES:raise RuntimeError('actual production software regression')
 if 'torch_npu'in sys.modules:raise RuntimeError('no hardware backend needed for software controls')
 value=dict(schema='deltalog.production-screen-CPU/v033',source=sr,tests=SOFTWARE_CASES,pass_software=True,Devices=[],NPU=False,model=False)
 with Path(a.output).open('x',encoding='utf8')as f:json.dump(value,f,sort_keys=True)
if __name__=='__main__':main()
