"""Thin Devices[] child; MAIN must wrap in an existing bounded CPU owner."""
import argparse,importlib.util,json,os,sys
from pathlib import Path
def main():
 if '--execute'not in sys.argv:print('disabled');return 0
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref',required=True);p.add_argument('--output',required=True);p.add_argument('--authority-ref',required=True);p.add_argument('--stage',choices=('cpu-preflight',),required=True);a=p.parse_args()
 here=Path(__file__).resolve().parent;s=importlib.util.spec_from_file_location('_composite022',here/'composite.py');C=importlib.util.module_from_spec(s);s.loader.exec_module(C)
 sr=json.loads(a.source_ref);m=json.loads(C.checked(sr));C.need(m['files']['entry.py']['path']==str(Path(__file__).resolve())and m['files']['composite.py']['path']==str(here/'composite.py'),'exact executing source entry')
 C.need(not list(Path('/dev').glob('davinci*'))and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0','actual Devices[] no backend autoload')
 ar=json.loads(a.authority_ref);authority=json.loads(C.checked(ar));C.need(ar==m['authority_ref']and ar['sha256']==C.AUTHORITY and authority['cutoff_epoch']==1792135097,'same fixed actual authority')
 out=Path(a.output);C.need(out.is_absolute()and out.parent.is_dir()and not out.exists(),'exclusive new composite output');out.mkdir()
 import unittest
 ts=importlib.util.spec_from_file_location('_composite022_software_controls',here/'test_composite.py');T=importlib.util.module_from_spec(ts);ts.loader.exec_module(T);suite=unittest.defaultTestLoader.loadTestsFromModule(T);expected=suite.countTestCases()
 with(out/'SOFTWARE_CONTROLS.txt').open('x',encoding='utf8')as stream:controls=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
 C.need(expected>0 and controls.testsRun==expected and controls.wasSuccessful(),'actual same-image complete software controls before raw admission')
 result=C.consume(sr)
 target=out/'CERTIFICATE.json'
 with target.open('x',encoding='utf8')as f:json.dump(result,f,sort_keys=True,allow_nan=False);f.write('\n')
 cr=dict(path=str(target),bytes=target.stat().st_size,sha256=C.hashlib.sha256(target.read_bytes()).hexdigest())
 with(out/'STAGE_RESULT.json').open('x',encoding='utf8')as f:json.dump(dict(schema='deltalog.composite-CPU/v022',source=sr,authority=ar,certificate=cr,software_controls=dict(discovered=expected,executed=controls.testsRun,passed=True,source=m['files']['test_composite.py']),pass_gate=True,NPU=False,model_ready=False),f,sort_keys=True,allow_nan=False);f.write('\n')
 return 0
if __name__=='__main__':raise SystemExit(main())
