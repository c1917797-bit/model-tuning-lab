"""Current G3 only: all32 source-owned tests, never historical software entry."""
import argparse,hashlib,json,sys,unittest
from pathlib import Path
def need(v,s):
 if not v:raise ValueError(s)
def ref(p):
 p=Path(p);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary exact current G3 source')
 a=p.stat();data=p.read_bytes();b=p.stat();need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(b.st_dev,b.st_ino,b.st_size,b.st_mtime_ns),'whole stable current G3 source');return dict(path=str(p),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
def obj(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['bytes'])is int and ref(r['path'])==r,'full exact current source Ref3');return json.loads(Path(r['path']).read_bytes())
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 need(a.source_ref,'actual current G3 source required');sr=json.loads(a.source_ref);m=obj(sr);root=Path(m['root']);s=m['service_software_scope']
 need(ref(__file__)==m['files']['g3_exact_controls.py']and Path(sr['path'])==root/'SOURCE_BOUND.json'and s['schema']=='bole.G3-five-source-staged-software-scope/v1'and s['current_pattern']=='test_g3_*.py'and type(s['new_current_cases'])is int and s['new_current_cases']==32 and m['service_required_sameimage_software_cases']==381,'only source-bound current G3 all32 scope')
 for r in m['files'].values():need(ref(r['path'])==r,'all current G3 source files whole bytes')
 need('sourceio'not in sys.modules,'fresh current G3 helper namespace');sys.path.insert(0,str(root));import sourceio as C
 need(C.ref(C.__file__)==m['files']['sourceio.py'],'actual current G3 helper origin')
 suite=unittest.defaultTestLoader.discover(str(root),pattern='test_g3_*.py',top_level_dir=str(root));result=unittest.TextTestRunner(verbosity=2).run(suite)
 need(result.wasSuccessful()and not result.skipped and not result.expectedFailures and not result.unexpectedSuccesses and result.testsRun==32,'all32 including tensor4 actually execute; zero skip/cached PASS')
 print(json.dumps(dict(schema='bole.actual-G3-current-only-unittest/v1',source=sr,test_source=sr,role='currentG3',pattern='test_g3_*.py',tests=result.testsRun,all_tests_passed=True,skipped=0,cached_PASS_reused=False,original_software_entry_invoked=False,NPU=False)));return 0
if __name__=='__main__':raise SystemExit(main())
