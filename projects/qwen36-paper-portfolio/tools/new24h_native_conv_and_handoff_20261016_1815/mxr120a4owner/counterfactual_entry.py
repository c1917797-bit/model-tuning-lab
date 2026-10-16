"""Same A3R2 Devices[] alias/owner; eight focused controls then actual saved raw."""
import argparse,importlib.util,json,os,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--software-only',action='store_true');p.add_argument('--source-ref');p.add_argument('--stage-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not(a.execute or a.software_only):print('disabled');return 0
 s=importlib.util.spec_from_file_location('_A4_owned',P/'owned_analysis.py');O=importlib.util.module_from_spec(s);s.loader.exec_module(O);sr=json.loads(a.source_ref);m=O.obj(sr)
 O.need(m['schema']=='mxr.counterfactual-owned-source/v120-analysis4'and m['root']==str(P)and m['files']['counterfactual_entry.py']==O.ref(__file__)and m['files']['owned_analysis.py']==O.ref(O.__file__),'exact new own entry/identity');[O.checked(r)for r in m['files'].values()]
 O.need(os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and not any(Path('/dev/davinci'+str(i)).exists()for i in range(8)),'actual Devices[]')
 r=O.obj(m['analysis4_source_ref']);O.need(r['actual_stage_ref']==m['actual_stage_ref']and r['actual_A3_report_ref']==m['actual_A3_report_ref'],'actual A4 stage/predecessor links')
 tests=O.load(r['files']['test_analysis4.py'],'_A4_full_software');result=unittest.TextTestRunner(stream=sys.stderr).run(unittest.defaultTestLoader.loadTestsFromModule(tests));O.need(result.wasSuccessful()and result.testsRun==O.SOFTWARE_CASES==m['software_cases']==8 and not result.skipped,'whole actual8 controls')
 O.need(a.output.is_absolute()and a.output.parent.is_dir()and not a.output.exists(),'fresh report');software=dict(source=sr,tests=8,passed=True,NPU=False,actual_data_consumed=False);O.write(a.output.parent/'SOFTWARE_CONTROLS.json',software)
 if a.software_only:O.write(a.output,software);return 0
 O.need(json.loads(a.stage_ref)==m['actual_stage_ref'],'actual old completed stage');O.historical_inputs(m);R=O.load(r['files']['reader.py'],'_A4_actual_reader');old=sys.argv
 try:sys.argv=[R.__file__,'--execute','--source-ref',json.dumps(m['analysis4_source_ref']),'--output',str(a.output)];code=R.main()
 finally:sys.argv=old
 O.need(code==0,'complete A4 read');d=json.loads(a.output.read_bytes());O.receive_report(d,m,sr,software)
 O.write(a.output.parent/'COUNTERFACTUAL_RECEIPT.json',dict(schema='mxr.counterfactual-owned-child/v120-analysis4',source=sr,counterfactual_source=m['counterfactual_source_ref'],reader_source=m['analysis4_source_ref'],actual_stage_ref=m['actual_stage_ref'],report_ref=O.ref(a.output),software=software,NPU=False,qualified=False));return 0
if __name__=='__main__':raise SystemExit(main())
