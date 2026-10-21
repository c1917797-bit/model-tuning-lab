"""Cold G2-v9 controls plus separately rerun exact qualified G2 historical suite."""
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
 C.need(scope['schema']=='bole.G2-cold-clock-historical-plus-current-controls/v9'and
    scope['parent_exact_cases']==parent['service_required_sameimage_software_cases']and
    scope['parent_suite_runs_in_separate_exact_source_process']is True and scope['current_pattern']=='test_g2_cold*.py',
    'explicit current lifecycle controls and separate exact unchanged parent negative/math controls')
 from g2_cold_parent_output import run as actual_parent
 prior,parent_evidence=actual_parent(sr)
 import unittest
 suite=unittest.defaultTestLoader.discover(str(P),pattern=scope['current_pattern'],top_level_dir=str(P))
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 C.need(result.wasSuccessful()and not result.skipped and result.testsRun==scope['new_current_cases']and
    result.testsRun+prior['tests']==m['service_required_sameimage_software_cases'],'all current source/stream protocol controls and original distinct historical count')
 from service_metadata import run
 installed=run(sr)
 print(json.dumps(dict(schema='bole.G2-cold-clock-combined-software-gate/v9',source=sr,
    tests=result.testsRun+prior['tests'],historical_cases=prior['tests'],current_cases=result.testsRun,
    all_tests_passed=True,historical_source=scope['parent_source'],parent_software_result=prior,parent_software_evidence=parent_evidence,
    actual_installed_metadata=installed,source_validated=proof,NPU=False,
    actual_scheduler_executed=False,model_ready=False,timing_is_formal=False)))
 return 0


if __name__=='__main__':raise SystemExit(main())
