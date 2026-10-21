"""Run only explicit exact-source unittest files, with retained complete streams.

The historical v10 --software entry is deliberately never invoked. This process
imports sourceio and all old test helpers from the selected immutable root.
"""
import argparse,hashlib,json,sys,unittest
from pathlib import Path


def need(v,s):
 if not v:raise ValueError(s)


def ref(p):
 p=Path(p);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary exact control source')
 a=p.stat();data=p.read_bytes();b=p.stat();need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(b.st_dev,b.st_ino,b.st_size,b.st_mtime_ns),'stable complete control source')
 return dict(path=str(p),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())


def obj(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and ref(r['path'])==r,'full exact Ref3 before importing any test helper');return json.loads(Path(r['path']).read_bytes())


def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--role',choices=('source10','current11'));a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 sr=json.loads(a.source_ref);m=obj(sr);root=Path(m['root']);need(ref(__file__)==m['files']['g2_exact_controls.py'],'source-bound only-tests runner')
 scope=m['service_software_scope'];need(scope['schema']=='bole.G2-three-source-staged-software-scope/v11','explicit three-source gate')
 selected=scope['controls_source']if a.role=='source10'else sr;target=obj(selected);path=Path(target['root'])
 pattern='test_g2_cold*.py'if a.role=='source10'else'test_g2_stage*.py';count=scope['controls_source_cases']if a.role=='source10'else scope['new_current_cases']
 need(Path(selected['path'])==path/'SOURCE_BOUND.json'and type(count)is int and count>0,'one exact selected source and declared test count')
 for r in target['files'].values():need(ref(r['path'])==r,'all selected source whole bytes remain exact')
 need('sourceio'not in sys.modules,'no current helper may shadow exact historical namespace')
 sys.path.insert(0,str(path));import sourceio as C
 need(C.ref(C.__file__)==target['files']['sourceio.py'],'actual selected source-owned helper namespace')
 suite=unittest.defaultTestLoader.discover(str(path),pattern=pattern,top_level_dir=str(path));result=unittest.TextTestRunner(verbosity=2).run(suite)
 need(result.wasSuccessful()and not result.skipped and result.testsRun==count,'all exact selected controls really rerun; zero skipped/cached cases')
 print(json.dumps(dict(schema='bole.actual-exact-source-only-unittest/v11',source=sr,test_source=selected,role=a.role,pattern=pattern,tests=result.testsRun,all_tests_passed=True,skipped=0,cached_PASS_reused=False,original_software_entry_invoked=False,NPU=False)));return 0


if __name__=='__main__':raise SystemExit(main())
