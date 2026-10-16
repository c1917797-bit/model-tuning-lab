import argparse,json,os,sys,traceback
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import common116 as C


def consume(t,sr,outer):
    import consume115,tree_fa115 as F,reference116 as R
    C.need(outer['schema']=='bole.tree-stage/v116'and outer['source']==sr and outer['primary']is None and outer['NPU']is True,'complete actual116 source-bound outer stage')
    inner=C.obj(outer['result']);report=consume115.consume(t,sr,inner)
    for row,original in zip(report['rows'],inner['rows']):
        raw=t.load(C.checked(original['raw']),map_location='cpu',weights_only=True)
        if raw['primary']is None:
            expected32=R.path_fp32(t,raw['inputs']);expected64=F.path_reference(t,raw['inputs'])
            row['independent_FP32']=F.score(t,raw['output'],expected32.double())
            delta=expected32.double()-expected64
            row['FP32_vs_FP64_diagnostic']=dict(peak_abs=float(delta.abs().max()),relative_l2=float(t.linalg.vector_norm(delta)/t.linalg.vector_norm(expected64).clamp_min(1e-30)))
            row['passed']=row['passed']and row['independent_FP32']['preregistered_allclose']
    report['observed_mask_modes_supported_on_exact_test_matrix']=[mode for mode in(0,1)if all(row['passed']for row in report['rows']if row['mode']==mode)]
    report.update(schema='bole.FIA-independent/v116',actual_NPU_stage=outer['result'],actual_abi_ref=outer['actual_abi_ref'],abi_ticket_ref=outer['abi_ticket_ref'],pass_gate=bool(report['observed_mask_modes_supported_on_exact_test_matrix']),source=sr)
    return report


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--stage-ref');p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    sr=json.loads(a.source_ref);m=C.source(sr);C.window(m)
    C.need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and not list(Path('/dev').glob('davinci*')),'actual Devices[] consumer')
    C.need(not a.output.exists()and a.output.parent.is_dir(),'fresh consumer output')
    try:
        import torch as t
        t.set_num_threads(1);value=consume(t,sr,C.obj(json.loads(a.stage_ref)));C.write(a.output,value)
    except BaseException as e:C.write(a.output.with_name(a.output.name+'.failure.json'),dict(primary=repr(e),traceback=traceback.format_exc(),source=sr,NPU=False));raise
    return 0 if value['pass_gate']else 3

if __name__=='__main__':raise SystemExit(main())
