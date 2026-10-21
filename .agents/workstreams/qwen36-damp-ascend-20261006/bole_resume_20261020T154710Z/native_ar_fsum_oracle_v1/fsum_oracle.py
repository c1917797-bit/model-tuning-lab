"""Independent all128 scalar CPU oracle control; never native/model qualification."""
import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import sys

FRAMES=128;HEADS=6;KEYS=132;DIM=256
QK_TERMS=FRAMES*HEADS*KEYS*DIM
PV_TERMS=QK_TERMS
EXP_TERMS=FRAMES*HEADS*KEYS
JOIN_ABS=1e-10;JOIN_REL=1e-12


def scalar_reference(q,k,v):
    """binary64 fsum of exact BF16 QK products; libm exp; fsum of rounded PV products.

    BF16 products fit binary64 exactly (<=16 significand bits, exponents
    contained in binary64). PV products generally round to binary64 because P
    is binary64; this function does not claim exact-real PV or exact exp.
    No tensor arithmetic, BLAS, dtype casts, mask changes or stage rounding.
    """
    if not(len(q)==HEADS and len(k)==len(v)==KEYS and all(len(a)==DIM for a in(*q,*k,*v))):
        raise ValueError('exact native Q6/KV132/D256 scalar operands; never sample')
    output=[];scores=[];probability=[]
    for head in range(HEADS):
        s=[math.fsum(a*b for a,b in zip(q[head],key))*(256**-.5)for key in k]
        maximum=max(s);exponentials=[math.exp(a-maximum)for a in s];denominator=math.fsum(exponentials)
        p=[a/denominator for a in exponentials]
        out=[math.fsum(p[token]*v[token][d]for token in range(KEYS))for d in range(DIM)]
        if not all(math.isfinite(a)for a in(*s,*p,*out))or not denominator>0:
            raise ValueError('finite independent scalar oracle')
        output.append(out);scores.append(s);probability.append(p)
    return output,scores,probability


def run(t,C,D,y,ir,context,output):
    x,m,on,_,_=context;refs,values,_,num_inputs,_=D.successful_numeric(C)
    original_inputs=C.obj(num_inputs['original_numeric_inputs'])
    ar=C.obj(original_inputs['actual_saved_refs']['NATIVE-AR-BUNDLE.json'])
    diagnostic=values['NUMERIC-DIAGNOSTIC.json']
    sys.path.insert(0,m['root']);PC=C.load(m['files']['pair_contract.py'],'pair_contract')
    F=C.load(original_inputs['files']['derived_math_consumer.py'],'_fsum_exact_original_consumer')
    N=C.load(num_inputs['files']['numeric_diagnostic.py'],'_fsum_exact_original_diagnostic')
    ranks=[];all_rows=[];total=0;qk_terms=0;pv_terms=0;exp_terms=0
    for rank,capture in enumerate(ar['ranks']):
        receipt=C.obj(capture['receipt']);C.need(receipt['rank']==rank and receipt['source']==x['AR_source']and
            receipt['primary']is None and receipt['raw']==capture['raw'],'same original four saved captures')
        saved=diagnostic['ranks'][rank];prior=C.obj(saved['report'])
        C.need(saved['rank']==rank and prior['rank']==rank and saved['raw']==prior['original_raw']==capture['raw']and
            prior['inputs']==refs['INPUTS.json']and prior['tensors']==saved['tensors'],'same full NUMdiag report/tensor/raw join')
        exported=t.load(C.checked(capture['raw']),map_location='cpu',weights_only=True);raw=exported['payload']
        recorded=t.load(C.checked(saved['tensors']),map_location='cpu',weights_only=True)
        logical=N.primitive_bytes(t,raw)
        C.need(exported['schema']=='bole.model-diagnostic-primitives/v1'and exported['cap_bytes']==PC.CAP and
            logical==exported['logical_tensor_bytes']==receipt['logical_tensor_bytes']and logical+64*2**20<=PC.CAP and
            raw['rank']==rank and raw['source']==x['AR_source']and raw['source_after']==m['files']and
            raw['runtime_sources_after']==m['runtime_sources']and raw['primary']is None and len(raw['requests'])==2 and
            recorded['schema']=='bole.native-FA-numeric-diagnostic-tensors/v1'and recorded['inputs']==refs['INPUTS.json']and
            recorded['original_raw']==capture['raw']and recorded['rank']==rank and len(recorded['frames'])==32,
            'original source/primitive budget and complete current diagnostic tensors')
        pmap={(r['generation'],r['layer']):r for r in prior['frames']}
        smap={(r['generation'],r['layer']):r for r in recorded['frames']}
        C.need(len(pmap)==len(smap)==32,'all32 unique rank diagnostic frames')
        rows=[];tensor_rows=[]
        for generation,request in enumerate(raw['requests'],1):
            C.need(request['generation']==generation and len(request['FA'])==16 and
                {r['layer']for r in request['FA']}==set(range(3,64,4)),'both full generations/every actual FA layer')
            for frame in request['FA']:
                key=(generation,frame['layer']);prior_frame=pmap[key];old=smap[key]
                C.need(prior_frame['rank']==old['rank']==rank and prior_frame['request']==request['request'],
                    'one actual frame identity across raw/report/full tensor export')
                frozen=F.actual_native_fa(t,frame)  # Complete unchanged ABI/operand/mask/FP32/FP64 function.
                q,k,v,actual=(frame[name]for name in('query','key','value','output'))
                C.need(t.equal(actual,old['actual']),'exact original published output retained')
                for label in('FP32','FP64'):
                    C.need(frozen['checks'][label]['peak_abs']==prior_frame['checks'][label]['peak_abs']and
                        frozen['checks'][label]['pointwise_pass']==prior_frame['checks'][label]['prior_report_pointwise_pass'],
                        'unchanged full original FP32/FP64 computation still reproduces all current metrics')
                original,scores64,prob64=N.reference(t,q,k,v,t.float64)
                C.need(t.equal(original,old['checks']['FP64']['truth']),'fresh original FP64 truth bitwise equals actual diagnostic export')
                result,scores,probability=scalar_reference(q[0].tolist(),k[:,0].tolist(),v[:,0].tolist())
                independent=t.tensor([result],dtype=t.float64)
                score_tensor=t.tensor(scores,dtype=t.float64);prob_tensor=t.tensor(probability,dtype=t.float64)
                details,bad=N.error_details(t,actual,independent)
                original_details,original_bad=N.error_details(t,actual,original)
                C.need(t.equal(original_bad,old['checks']['FP64']['violations'])and
                    original_details['violations']==prior_frame['checks']['FP64']['violations'],
                    'all original violating coordinates preserved without threshold changes')
                difference=(independent-original).abs();join_bound=JOIN_ABS+JOIN_REL*original.abs();join=bool((difference<=join_bound).all())
                membership=t.equal(bad,original_bad)
                qk_terms+=HEADS*KEYS*DIM;pv_terms+=HEADS*KEYS*DIM;exp_terms+=HEADS*KEYS
                row=dict(rank=rank,generation=generation,request=request['request'],layer=frame['layer'],
                    original_FP32_FP64_checks=frozen['checks'],independent=details,original_FP64=original_details,
                    original64_join_pass=join,join_abs=JOIN_ABS,join_rel=JOIN_REL,
                    original64_peak_difference=float(difference.max()),original64_max_join_ratio=float((difference/join_bound).max()),
                    all_violating_coordinates_equal=membership,score64_peak_difference=float((score_tensor-scores64).abs().max()),
                    probability64_peak_difference=float((prob_tensor-prob64).abs().max()),
                    original_pointwise_bound_preserved=True,runtime_ABI_proven_by_scalar_oracle=False,native_FA_math_qualified=False)
                rows.append(row);all_rows.append(row)
                tensor_rows.append(dict(rank=rank,generation=generation,layer=frame['layer'],independent_truth=independent,
                    original_FP64_truth=original,actual=actual,independent_violations=bad,original_violations=original_bad,
                    independent_scores=score_tensor,independent_probability=prob_tensor,signed_reference_difference=independent-original))
        C.need(len(rows)==32,'all rank frames retained')
        binary_path=output/('FSUM-RANK-%d.pt'%rank)
        with binary_path.open('xb')as stream:t.save(dict(schema='bole.native-FA-fsum-oracle-tensors/v1',inputs=ir,
            original_raw=capture['raw'],actual_NUMdiag_tensors=saved['tensors'],rank=rank,frames=tensor_rows),stream)
        br=C.ref(binary_path);jr=C.write(output/('FSUM-RANK-%d.json'%rank),dict(inputs=ir,rank=rank,original_raw=capture['raw'],
            actual_NUMdiag_report=saved['report'],actual_NUMdiag_tensors=saved['tensors'],tensors=br,frames=rows,
            native_FA_math_qualified=False,formal_success=False))
        total+=br['bytes']+jr['bytes'];C.need(total<=128*2**20,'bounded full128 independent oracle export128MiB')
        ranks.append(dict(rank=rank,tensors=br,report=jr,raw=capture['raw']))
        C.checked(capture['raw']);C.checked(saved['tensors'])
        del exported,raw,recorded,tensor_rows,rows,old,smap,prior_frame,pmap
    C.need(len(all_rows)==FRAMES and qk_terms==QK_TERMS and pv_terms==PV_TERMS and exp_terms==EXP_TERMS,
        'all128 and exactly51904512 scalar multiplication terms; never sample on timeout')
    joins=all(r['original64_join_pass']and r['all_violating_coordinates_equal']for r in all_rows)
    return dict(schema='bole.actual-native-FA-independent-fsum-oracle-control/v1',inputs=ir,source=x['AR_source'],
        actual_successful_NUMdiag=refs['RESULT.json'],actual_passed_G1=diagnostic['actual_passed_G1'],
        rank_count=4,frame_count=len(all_rows),independent_failure_frame_count=sum(r['independent']['violation_count']>0 for r in all_rows),
        independent_violation_count=sum(r['independent']['violation_count']for r in all_rows),
        all128_independent_oracle_join_pass=joins,independent_oracle_control_completed=joins,
        QK_product_terms=qk_terms,PV_product_terms=pv_terms,exp_terms=exp_terms,scalar_product_terms=qk_terms+pv_terms,
        join_abs=JOIN_ABS,join_rel=JOIN_REL,join_is_new_native_tolerance=False,
        ranks=ranks,total_export_bytes=total,weights_only_load=True,CPU_only=True,Devices=[],NPU=False,
        original_G1_math_rerun=False,mathematics_recomputed=True,diagnostic_only=True,
        original_pointwise_bound_preserved=True,runtime_ABI_proven_by_scalar_oracle=False,
        mask_semantics_qualified=False,native_FA_math_qualified=False,native_AR_numeric_pass=False,
        common_effects_pass=False,model_ready=False,performance_ready=False,formal_success=False)


def main():
    p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False);p.add_argument('--execute',action='store_true')
    p.add_argument('--inputs-ref');p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false,"formal_success":false}');return 0
    if not(a.inputs_ref and a.output):p.error('exact new source-bound input and fresh owned output required')
    if not(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and
        not list(Path('/dev').glob('davinci[0-9]*'))):raise ValueError('actual Devices[] before any tensor runtime import')
    sys.dont_write_bytecode=True;s=importlib.util.spec_from_file_location('_fsum_actual_common',Path(__file__).parent/'fsum_common.py')
    D=importlib.util.module_from_spec(s);s.loader.exec_module(D);C=D.common();ir=json.loads(a.inputs_ref);y=D.source(C,ir)
    C.need(C.ref(__file__)==y['files']['fsum_oracle.py']and a.output.parent==Path(y['consumer_output_root'])and
        a.output.parent.samefile('/adakv-results'),'sole exact new RW payload')
    context=D.readset(C,y,installed=True)
    import torch
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    result=run(torch,C,D,y,ir,context,a.output.parent)
    C.need(not list(Path('/dev').glob('davinci[0-9]*')),'Devices[] preserved')
    C.write(a.output,result)
    C.need(result['all128_independent_oracle_join_pass'],'all128 independent scalar oracle control; mismatch retained, never reinterpret failure')
    return 0

if __name__=='__main__':raise SystemExit(main())
