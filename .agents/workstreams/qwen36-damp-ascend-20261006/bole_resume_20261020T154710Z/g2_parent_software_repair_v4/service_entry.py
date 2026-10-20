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
 import parent_software_output as OUTPUT
 C.need(C.ref(OUTPUT.__file__)==m['files']['parent_software_output.py'],'exact fresh-parent output retention/extraction helper')
 output_root,output_binding=OUTPUT.owned_output(C,m)
 prior,parent_evidence=OUTPUT.run(C,source_ref=sr,parent_source_ref=scope['parent_source'],
    expected_tests=scope['parent_exact_cases'],evidence_root=output_root,output_binding=output_binding,timeout=120)
 import unittest
 suite=unittest.defaultTestLoader.discover(str(P),pattern=scope['current_pattern'],top_level_dir=str(P))
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 C.need(result.wasSuccessful()and result.testsRun==scope['new_current_cases']and
    result.testsRun+prior['tests']==m['service_required_sameimage_software_cases'],'all current source/stream protocol controls and original distinct historical count')
 from service_metadata import run
 installed=run(sr)
 print(json.dumps(dict(schema='bole.G2-explicit-combined-software-gate/v1',source=sr,
    tests=result.testsRun+prior['tests'],historical_cases=prior['tests'],current_cases=result.testsRun,
    all_tests_passed=True,historical_source=scope['parent_source'],parent_software_result=prior,parent_software_evidence=parent_evidence,
    actual_installed_metadata=installed,source_validated=proof,NPU=False,
    actual_scheduler_executed=False,model_ready=False,timing_is_formal=False)))
 return 0


if __name__=='__main__':raise SystemExit(main())
