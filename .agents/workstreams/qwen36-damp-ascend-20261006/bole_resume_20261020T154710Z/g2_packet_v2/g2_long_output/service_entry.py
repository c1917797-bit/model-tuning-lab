"""Cold G2 controls plus separately rerun exact qualified G1-v2 historical suite."""
import argparse,json,os,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))


def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--source-audit',action='store_true');p.add_argument('--software',action='store_true');a=p.parse_args()
 if not(a.source_audit or a.software):print('{"enabled":false,"NPU":false}');return 0
 import sourceio as C,g2_validate as V
 sr=C.ref(P/'SOURCE_BOUND.json');m=C.obj(sr);proof=V.validate(sr)
 if a.source_audit:print(json.dumps(proof));return 0
 scope=m['service_software_scope'];parent=C.obj(scope['parent_source'])
 C.need(scope['schema']=='bole.G2-explicit-historical-plus-current-controls/v1'and
    scope['parent_exact_cases']==parent['service_required_sameimage_software_cases']and
    scope['parent_suite_runs_in_separate_exact_source_process']is True and scope['current_pattern']=='test_g2*.py',
    'explicit current lifecycle controls and separate exact unchanged parent negative/math controls')
 env={k:v for k,v in os.environ.items()if not k.startswith('BOLE_')}
 q=subprocess.run([sys.executable,'-I','-B',str(Path(parent['root'])/'service_entry.py'),'--software'],
    env=env,capture_output=True,text=True,timeout=120)
 C.need(q.returncode==0,'full exact qualified G1-v2 historical suite failed '+q.stdout[-2000:]+q.stderr[-5000:])
 prior=json.loads(q.stdout.splitlines()[-1]);C.need(prior['all_tests_passed']is True and prior['tests']==scope['parent_exact_cases'],'actual214 parent suite count, never a cached PASS')
 import unittest
 suite=unittest.defaultTestLoader.discover(str(P),pattern=scope['current_pattern'],top_level_dir=str(P))
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 C.need(result.wasSuccessful()and result.testsRun==scope['new_current_cases']and
    result.testsRun+prior['tests']==m['service_required_sameimage_software_cases'],'all current source/stream protocol controls and original distinct historical count')
 from service_metadata import run
 installed=run(sr)
 print(json.dumps(dict(schema='bole.G2-explicit-combined-software-gate/v1',source=sr,
    tests=result.testsRun+prior['tests'],historical_cases=prior['tests'],current_cases=result.testsRun,
    all_tests_passed=True,historical_source=scope['parent_source'],parent_software_result=prior,
    actual_installed_metadata=installed,source_validated=proof,NPU=False,
    actual_scheduler_executed=False,model_ready=False,timing_is_formal=False)))
 return 0


if __name__=='__main__':raise SystemExit(main())
