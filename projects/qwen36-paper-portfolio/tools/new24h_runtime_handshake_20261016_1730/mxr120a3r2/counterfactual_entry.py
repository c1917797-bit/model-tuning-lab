"""Actual Devices[] aggregate frontdoor and fixed independent CPU child."""
import argparse,importlib.util,json,os,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent


def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--software-only',action='store_true');p.add_argument('--source-ref');p.add_argument('--stage-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not(a.execute or a.software_only):print('{"enabled":false,"NPU":false}');return 0
 O=load(P/'owned_analysis.py','_CF120_owned_entry');sr=json.loads(a.source_ref);m=O.obj(sr)
 O.need(m['schema']=='mxr.counterfactual-owned-source/v120-analysis3'and m['root']==str(P)and m['default_enabled']is False,'exact counterfactual owned CPU source')
 [O.checked(r)for r in m['files'].values()];O.need(m['files']['counterfactual_entry.py']==O.ref(__file__)and m['files']['owned_analysis.py']==O.ref(O.__file__),'actual current entry/controller bytes')
 O.need(os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and not any(Path('/dev/davinci'+str(i)).exists()for i in range(8)),'actual Devices[]/autoloadOFF')
 cf=O.obj(m['counterfactual_source_ref']);O.need(cf['guest_source_ref']==m['guest_source']and cf['analysis_source_ref']==m['analysis_source_ref']and cf['actual_analysis_ref']==m['actual_analysis_report_ref']and cf['actual_stage_ref']==m['actual_stage_ref'],'exact historical inputs/new CPU source linkage')
 total=0
 for rr,n in((cf['files']['test_counterfactual.py'],6),(m['files']['test_owned.py'],6)):
  tests=O.load(rr,'_CF120_actual_suite_'+Path(rr['path']).stem);result=unittest.TextTestRunner(stream=sys.stderr).run(unittest.defaultTestLoader.loadTestsFromModule(tests));O.need(result.wasSuccessful()and result.testsRun==n and not result.skipped,'whole actual CPU counterfactual software aggregate');total+=result.testsRun
 O.need(total==O.SOFTWARE_CASES==m['software_cases'],'same unique control count12')
 O.need(a.output.is_absolute()and a.output.parent.is_dir()and not a.output.exists(),'fresh report/receipt output')
 software=dict(source=sr,tests=total,passed=True,NPU=False,actual_data_consumed=False);O.write(a.output.parent/'SOFTWARE_CONTROLS.json',software)
 if a.software_only:O.write(a.output,dict(schema='mxr.counterfactual-owned-software/v120-analysis3',**software));return 0
 O.need(json.loads(a.stage_ref)==m['actual_stage_ref'],'fixed completed child stage not a future PASS');O.historical_inputs(m)
 CF=O.load(cf['files']['counterfactual.py'],'_CF120_actual_independent_child');old=sys.argv
 try:sys.argv=[CF.__file__,'--execute','--source-ref',json.dumps(m['counterfactual_source_ref']),'--output',str(a.output)];code=CF.main()
 finally:sys.argv=old
 O.need(code==0,'independent full3case CPU counterfactual complete');d=json.loads(a.output.read_bytes())
 receipt=dict(schema='mxr.counterfactual-owned-child/v120-analysis3',source=sr,counterfactual_source=m['counterfactual_source_ref'],actual_stage_ref=m['actual_stage_ref'],report_ref=O.ref(a.output),software=software,NPU=False,qualified=False)
 O.write(a.output.parent/'COUNTERFACTUAL_RECEIPT.json',receipt);O.receive_report(d,m,sr,software);return 0


if __name__=='__main__':raise SystemExit(main())
