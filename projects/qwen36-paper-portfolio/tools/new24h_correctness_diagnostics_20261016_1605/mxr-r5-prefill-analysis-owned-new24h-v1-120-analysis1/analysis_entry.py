"""Owned Devices[] software frontdoor then exact frozen analysis child."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest

P=Path(__file__).resolve().parent


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def main():
    p=argparse.ArgumentParser(allow_abbrev=False)
    p.add_argument('--execute',action='store_true');p.add_argument('--software-only',action='store_true')
    p.add_argument('--source-ref');p.add_argument('--stage-ref');p.add_argument('--output',type=Path)
    a=p.parse_args()
    if not(a.execute or a.software_only):print('{"enabled":false,"NPU":false}');return 0
    O=load(P/'owned_analysis.py','_analysis120_owned_frontdoor')
    sr=json.loads(a.source_ref);m=O.obj(sr)
    O.need(m['schema']=='mxr.prefill-analysis-owned-source/v120-analysis1'and m['root']==str(P)and m['default_enabled']is False,'exact new CPU owner source/root')
    [O.checked(r)for r in m['files'].values()]
    O.need(m['files']['analysis_entry.py']==O.ref(__file__)and m['files']['owned_analysis.py']==O.ref(O.__file__),'actual CPU entry and owner')
    O.need(os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and not any(Path('/dev/davinci'+str(i)).exists()for i in range(8)),'actual Devices[] frontdoor')
    original=O.obj(m['inherited_owner_source_ref']);analysis=O.obj(m['analysis_source_ref'])
    O.need(original['guest_source']==m['guest_source']and analysis['original_source_ref']==m['guest_source'],'exact unchanged120R2 analysis linkage')
    suites=[(analysis['files']['test_analysis.py'],7),(original['files']['test_owner120.py'],10),(m['files']['test_owned_analysis.py'],5)]
    total=0
    for rr,expected in suites:
        tests=O.load(rr,'_analysis120_full_'+Path(rr['path']).stem)
        result=unittest.TextTestRunner(stream=sys.stderr).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        O.need(result.wasSuccessful()and result.testsRun==expected and not result.skipped,'actual complete analysis software aggregate')
        total+=result.testsRun
    O.need(total==O.SOFTWARE_CASES==m['software_cases'],'single producer/consumer22 controls')
    proof=dict(source=sr,tests=total,passed=True,NPU=False,actual_data_consumed=False)
    O.need(a.output.is_absolute()and a.output.parent.is_dir()and not a.output.exists(),'fresh report output')
    O.write(a.output.parent/'SOFTWARE_CONTROLS.json',proof)
    if a.software_only:
        O.write(a.output,dict(schema='mxr.analysis120-owned-software/v1',**proof));return 0
    O.need(json.loads(a.stage_ref)==m['actual_stage_ref'],'one fixed actual completed120R2 child stage')
    O.historical_inputs(m)
    A=O.load(analysis['files']['analyze.py'],'_analysis120_frozen_child')
    old=sys.argv
    try:
        sys.argv=[A.__file__,'--execute','--source-ref',json.dumps(m['analysis_source_ref']),'--stage-ref',a.stage_ref,'--output',str(a.output)]
        code=A.main()
    finally:sys.argv=old
    O.need(code==0,'actual frozen CPU analysis complete')
    d=json.loads(a.output.read_bytes())
    # Add only transport metadata, never rewrite a numerical result or original raw.
    # Write a separate receipt; do not overwrite frozen analysis's exclusive output.
    receipt=dict(schema='mxr.prefill-analysis-owned-child/v120-analysis1',source=sr,analysis_source=m['analysis_source_ref'],stage_ref=m['actual_stage_ref'],analysis_ref=O.ref(a.output),software=proof,NPU=False,qualified=False)
    O.write(a.output.parent/'ANALYSIS_RECEIPT.json',receipt)
    O.receive_report(dict(d,owned_software=proof),m,sr)
    return 0


if __name__=='__main__':raise SystemExit(main())
