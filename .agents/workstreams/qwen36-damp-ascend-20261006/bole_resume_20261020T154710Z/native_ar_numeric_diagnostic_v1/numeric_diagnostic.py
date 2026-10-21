"""Full128-frame CPU numerical-failure diagnostic, never a qualification oracle."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys


def reference(t,q,k,v,dtype):
    # These expressions match frozen actual_native_fa literally. The original
    # function also runs for every frame and its metrics are independently joined.
    values=[];all_scores=[];all_probability=[]
    for h in range(6):
        scores=k[:,0].to(dtype).mv(q[0,h].to(dtype))*(256**-.5)
        probability=(scores-scores.max()).exp();probability/=probability.sum()
        values.append(v[:,0].to(dtype).T.mv(probability))
        all_scores.append(scores);all_probability.append(probability)
    return t.stack(values).unsqueeze(0),t.stack(all_scores),t.stack(all_probability)


def error_details(t,actual,truth):
    error=(actual.double()-truth.double()).abs();bound=.001+.01*truth.double().abs();bad=error>bound
    coords=bad.nonzero().tolist()
    return dict(violation_count=len(coords),peak_abs=float(error.max()),max_error_bound_ratio=float((error/bound).max()),
        violations=[dict(index=ix,actual=float(actual[tuple(ix)]),truth=float(truth[tuple(ix)]),
            error=float(error[tuple(ix)]),bound=float(bound[tuple(ix)]),ratio=float((error/bound)[tuple(ix)]))for ix in coords]),bad


def primitive_bytes(t,value):
    if isinstance(value,t.Tensor):
        if value.device.type!='cpu' or not value.is_contiguous():raise ValueError('original CPU contiguous primitives')
        return value.numel()*value.element_size()
    if value is None or type(value)in(str,int,float,bool):return 0
    if type(value)in(tuple,list):return sum(primitive_bytes(t,v)for v in value)
    if type(value)is dict and all(type(k)in(str,int)for k in value):return sum(primitive_bytes(t,v)for v in value.values())
    raise ValueError('opaque nonprimitive capture rejected')


def run(t,C,D,y,ir,context,output):
    x,m,on,_,_=context;refs,values,_,old,_=D.prior(C,y)
    ar=C.obj(old['actual_saved_refs']['NATIVE-AR-BUNDLE.json'])
    sys.path.insert(0,m['root']);PC=C.load(m['files']['pair_contract.py'],'pair_contract')
    F=C.load(old['files']['derived_math_consumer.py'],'_numeric_diag_exact_failed_math')
    ranks=[];all_rows=[];total=0
    for rank,capture in enumerate(ar['ranks']):
        receipt=C.obj(capture['receipt']);C.need(receipt['rank']==rank and receipt['source']==x['AR_source']and
            receipt['primary']is None and receipt['raw']==capture['raw'],'same original four captured primitives')
        exported=t.load(C.checked(capture['raw']),map_location='cpu',weights_only=True);raw=exported['payload']
        logical=primitive_bytes(t,raw)
        C.need(exported['schema']=='bole.model-diagnostic-primitives/v1'and exported['cap_bytes']==PC.CAP and
            logical==exported['logical_tensor_bytes']==receipt['logical_tensor_bytes']and logical+64*2**20<=PC.CAP and
            raw['rank']==rank and raw['source']==x['AR_source']and raw['source_after']==m['files']and
            raw['runtime_sources_after']==m['runtime_sources']and raw['primary']is None and len(raw['requests'])==2,
            'exact original source/budget primitive envelope before diagnosis')
        original=values['cpu-consumer/RANK-%d.json'%rank];rows=[];tensor_rows=[]
        for generation,request in enumerate(raw['requests'],1):
            oldrequest=original['requests'][generation-1]
            C.need(request['generation']==generation and request['request']==oldrequest['request']and
                len(request['FA'])==16 and {f['layer']for f in request['FA']}==set(range(3,64,4)),
                'all original generations/layers, no winning-frame filter')
            oldframes={f['layer']:f for f in oldrequest['FA']}
            for frame in request['FA']:
                frozen=F.actual_native_fa(t,frame)  # Original complete ABI/operand/bitwise guards and bounds.
                q,k,v,actual=(frame[name]for name in('query','key','value','output'))
                truths={};statistics={};binary={};failure=False
                for label,dtype in(('FP32',t.float32),('FP64',t.float64)):
                    truth,scores,probability=reference(t,q,k,v,dtype)
                    detail,bad=error_details(t,actual,truth);truths[label]=(truth,scores,probability)
                    C.need((detail['violation_count']==0)==frozen['checks'][label]['pointwise_pass']and
                        detail['peak_abs']==frozen['checks'][label]['peak_abs'],
                        'detailed calculation exactly reproduces unchanged frozen computation and threshold')
                    detail['prior_report_pointwise_pass']=oldframes[frame['layer']]['checks'][label]['pointwise_pass']
                    detail['prior_report_peak_abs']=oldframes[frame['layer']]['checks'][label]['peak_abs']
                    detail['prior_peak_difference']=detail['peak_abs']-detail['prior_report_peak_abs']
                    detail['scores_min_max']=[float(scores.min()),float(scores.max())]
                    detail['probability_min_max']=[float(probability.min()),float(probability.max())]
                    statistics[label]=detail;binary[label]=dict(truth=truth,violations=bad)
                    failure|=detail['violation_count']>0
                truth,scores,probability=truths['FP64'];vd=v[:,0].double();weighted_abs=vd.abs().T.matmul(probability.T).T.unsqueeze(0)
                nonzero=truth.abs()>0;cancel=weighted_abs[nonzero]/truth.abs()[nonzero]
                # Preregistered counterfactual stage models only. They never
                # replace the unrounded FP32/FP64 oracle or become pass gates.
                rounded_scores=scores.to(t.bfloat16).double()
                sp=(rounded_scores-rounded_scores.max(dim=1,keepdim=True).values).exp();sp/=sp.sum(dim=1,keepdim=True)
                models={'final_output_RNE_only':truth.to(t.bfloat16).double(),
                    'scores_BF16_only':sp.matmul(vd).unsqueeze(0),
                    'probabilities_BF16_only':probability.to(t.bfloat16).double().matmul(vd).unsqueeze(0),
                    'scores_and_probabilities_BF16':sp.to(t.bfloat16).double().matmul(vd).unsqueeze(0)}
                variants={}
                bound=.001+.01*truth.abs()
                for label,model in models.items():
                    residual=(actual.double()-model).abs()
                    variants[label]=dict(peak_residual_to_actual=float(residual.max()),
                        residual_count_above_original_truth_bound=int((residual>bound).sum()),
                        implementation_semantics_proven=False,qualification_oracle=False)
                row=dict(rank=rank,generation=generation,request=request['request'],layer=frame['layer'],
                    route=frozen['route'],checks=statistics,current_failure=failure,
                    actual_min_max=[float(actual.min()),float(actual.max())],V_abs_max=float(v.abs().max()),
                    cancellation_ratio_max=float(cancel.max())if cancel.numel()else None,
                    exactly_zero_truth_count=int((~nonzero).sum()),stage_hypotheses=variants,
                    observed_kernel_implementation_semantics_proven=False,native_FA_math_qualified=False)
                rows.append(row);all_rows.append(row)
                tensor_rows.append(dict(rank=rank,generation=generation,layer=frame['layer'],actual=actual,
                    checks=binary,FP64_scores=scores,FP64_probability=probability,stage_models=models))
        C.need(len(rows)==32,'retain every original rank frame')
        binary_path=output/('DIAG-RANK-%d.pt'%rank)
        with binary_path.open('xb')as stream:t.save(dict(schema='bole.native-FA-numeric-diagnostic-tensors/v1',
            inputs=ir,original_raw=capture['raw'],rank=rank,frames=tensor_rows),stream)
        br=C.ref(binary_path);jr=C.write(output/('DIAG-RANK-%d.json'%rank),dict(inputs=ir,rank=rank,
            original_raw=capture['raw'],original_rank_report=refs['cpu-consumer/RANK-%d.json'%rank],
            tensors=br,frames=rows,native_FA_math_qualified=False,formal_success=False))
        total+=br['bytes']+jr['bytes'];C.need(total<=128*2**20,'bounded full128 diagnostic export128MiB')
        ranks.append(dict(rank=rank,tensors=br,report=jr,raw=capture['raw']))
        C.checked(capture['raw']);del exported,raw,tensor_rows,rows,models,truths,binary
    return dict(schema='bole.actual-native-FA-numeric-failure-diagnostic/v1',inputs=ir,source=x['AR_source'],
        actual_failed_numeric=refs['RESULT.json'],actual_passed_G1=refs['cpu-consumer/BOLE-INDEPENDENT-GATE/ATTRIBUTION.json'],
        rank_count=4,frame_count=len(all_rows),current_failure_frame_count=sum(r['current_failure']for r in all_rows),
        ranks=ranks,total_export_bytes=total,weights_only_load=True,CPU_only=True,Devices=[],NPU=False,
        original_G1_math_rerun=False,mathematics_recomputed=True,diagnostic_only=True,
        original_pointwise_bound_preserved=True,stage_models_are_qualified_oracles=False,
        mask_semantics_qualified=False,native_FA_math_qualified=False,native_AR_numeric_pass=False,
        common_effects_pass=False,model_ready=False,performance_ready=False,formal_success=False)


def main():
    p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False);p.add_argument('--execute',action='store_true')
    p.add_argument('--inputs-ref');p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false,"formal_success":false}');return 0
    if not(a.inputs_ref and a.output):p.error('exact new source-bound input and fresh owned output required')
    if not(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and
        not list(Path('/dev').glob('davinci[0-9]*'))):raise ValueError('actual Devices[] before any tensor runtime import')
    sys.dont_write_bytecode=True;s=importlib.util.spec_from_file_location('_numeric_actual_common',Path(__file__).parent/'numeric_common.py')
    D=importlib.util.module_from_spec(s);s.loader.exec_module(D);C=D.common();ir=json.loads(a.inputs_ref);y=D.source(C,ir)
    C.need(C.ref(__file__)==y['files']['numeric_diagnostic.py']and a.output.parent==Path(y['consumer_output_root'])and
        a.output.parent.samefile('/adakv-results'),'sole exact new RW payload')
    context=D.readset(C,y,installed=True)
    import torch
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    result=run(torch,C,D,y,ir,context,a.output.parent)
    C.need(not list(Path('/dev').glob('davinci[0-9]*')),'Devices[] preserved')
    C.write(a.output,result);return 0

if __name__=='__main__':raise SystemExit(main())
