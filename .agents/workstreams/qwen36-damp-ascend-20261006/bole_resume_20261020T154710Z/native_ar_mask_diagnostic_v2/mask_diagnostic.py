"""Read-only saved nativeFA mask metadata; every mathematical gate stays false."""
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys


def primitive_tensor_bytes(t,value):
    if isinstance(value,t.Tensor):return value.numel()*value.element_size()
    if value is None or type(value)in(str,int,float,bool):return 0
    if type(value)in(list,tuple):return sum(primitive_tensor_bytes(t,v)for v in value)
    if type(value)is dict and all(type(k)in(str,int)for k in value):return sum(primitive_tensor_bytes(t,v)for v in value.values())
    raise ValueError('only actual original primitive capture values')


def scalar(value):
    value=value.item()
    if type(value)is float and not math.isfinite(value):return 'NaN'if math.isnan(value)else('+Inf'if value>0 else'-Inf')
    return value


def mask_metadata(t,mask):
    if mask is None:return dict(present=False,mask_semantics_qualified=False)
    if not isinstance(mask,t.Tensor):raise ValueError('actual captured atten_mask must be a tensor or None')
    if mask.device.type!='cpu' or mask.numel()*mask.element_size()>16*2**20:raise ValueError('original bounded CPU metadata tensor')
    flat=mask.contiguous();raw=flat.reshape(-1).view(t.uint8).numpy().tobytes()
    values,counts=t.unique(flat,sorted=True,return_counts=True)
    if values.numel()>256:raise ValueError('unknown >256 unique mask values; full raw preserved, no lossy histogram')
    histogram=[dict(value=scalar(value),count=int(count))for value,count in zip(values,counts)]
    integral=mask.dtype in(t.uint8,t.int8,t.int16,t.int32,t.int64)
    floating=mask.dtype in(t.float16,t.bfloat16,t.float32,t.float64)
    tests={};square=mask.ndim==2 and mask.shape[0]==mask.shape[1]and mask.shape[0]<=4096
    if square:
        upper=t.triu(t.ones(tuple(mask.shape),dtype=t.bool),diagonal=1)
        nonzero=mask!=0
        tests['full_nonzero_equals_strict_upper_triangle']=bool(t.equal(nonzero,upper))
        tests['full_nonzero_equals_strict_lower_triangle']=bool(t.equal(nonzero,upper.T))
        tests['full_exact_zero_one_upper_triangle']=bool(t.equal(mask,upper.to(mask.dtype)))
        tests['full_bool_upper_triangle']=mask.dtype==t.bool and bool(t.equal(mask,upper))
        tests['full_all_zero']=bool((mask==0).all());tests['full_all_one']=bool((mask==1).all())
        if floating:
            tests['full_additive_zero_then_negative_infinity']=bool((mask[~upper]==0).all()and(mask[upper]==-float('inf')).all())
            tests['full_additive_zero_then_dtype_min']=bool((mask[~upper]==0).all()and(mask[upper]==t.finfo(mask.dtype).min).all())
    return dict(present=True,dtype=str(mask.dtype),shape=list(mask.shape),stride=list(mask.stride()),
        storage_offset=mask.storage_offset(),numel=mask.numel(),element_size=mask.element_size(),
        contiguous=mask.is_contiguous(),contiguous_bytes=len(raw),contiguous_byte_sha256=hashlib.sha256(raw).hexdigest(),
        unique_values_counts=histogram,unique_values_complete=True,finite=bool(t.isfinite(mask).all()),
        negative_present=bool((mask<0).any())if integral or floating else False,
        exact_zero_or_one_only=bool(((mask==0)|(mask==1)).all()),bool_dtype=mask.dtype==t.bool,
        full_mask_formula_observations=tests,formula_comparison_implies_operator_semantics=False,
        mask_semantics_qualified=False)


def parameter_metadata(t,value):
    if isinstance(value,t.Tensor):
        raw=value.contiguous().reshape(-1).view(t.uint8).numpy().tobytes()
        result=dict(dtype=str(value.dtype),shape=list(value.shape),stride=list(value.stride()),
            numel=value.numel(),contiguous_byte_sha256=hashlib.sha256(raw).hexdigest())
        if value.numel()<=16384:result['complete_values']=value.tolist()
        else:result['complete_values_retained_in_original_raw']=True
        return result
    if value is None or type(value)in(str,int,float,bool):return value
    if type(value)in(list,tuple):return[parameter_metadata(t,v)for v in value]
    if type(value)is dict:return{k:parameter_metadata(t,v)for k,v in value.items()}
    raise ValueError('opaque lower operator parameter; original raw preserved')


def run(t,C,D,y,ir,verified):
    x,m,_,_,source_proof=verified
    owner,oldy,_,_,_,objects=D.prior(C,y)
    bundle=objects['NATIVE-AR-BUNDLE.json'];ranks=[]
    C.need(len(bundle['ranks'])==4,'all four actual original ranks, no selected-frame filtering')
    for rank,capture in enumerate(bundle['ranks']):
        receipt=C.obj(capture['receipt']);C.checked(capture['raw'])
        C.need(receipt['schema']=='bole.actual-native-ar-worker-receipt/v1'and receipt['rank']==rank and
            receipt['source']==x['AR_source']and receipt['primary']is None and receipt['raw']==capture['raw'],
            'exact actual original source/rank/raw receipt before CPU-only load')
        exported=t.load(C.checked(capture['raw']),map_location='cpu',weights_only=True);payload=exported['payload']
        logical=primitive_tensor_bytes(t,payload)
        C.need(exported['schema']=='bole.model-diagnostic-primitives/v1'and exported['cap_bytes']==2**30 and
            logical==exported['logical_tensor_bytes']==receipt['logical_tensor_bytes']and logical+64*2**20<=2**30 and
            payload['schema']=='bole.actual-native-ar-smoke-rank/v1'and payload['source']==x['AR_source']and
            payload['rank']==rank and payload['primary']is None and payload['native_AR']is True and
            payload['speculative_config']is None and payload['precision_intervention']is False and
            payload['source_after']==m['files']and payload['runtime_sources_after']==m['runtime_sources']and
            len(payload['requests'])==2,'all original unchanged-source primitive bytes and original aggregate bound')
        frames=[]
        for generation,request in enumerate(payload['requests'],1):
            C.need(request['generation']==generation and len(request['FA'])==16 and
                {f['layer']for f in request['FA']}==set(range(3,64,4)),'all sixteen actual native FA frames per request')
            for frame in request['FA']:
                C.need(frame['schema']=='bole.actual-production-native-FA-frame/v1'and frame['ordinal']==1 and
                    frame['prefix_length']==131 and frame['generation']==generation and
                    frame['request']==request['request']and len(frame['kernel'])==1,'actual q1/KV132 frame identity')
                kernel=frame['kernel'][0];kw=kernel['explicit_kwargs'];route=kernel['name']
                C.need(route in('_npu_paged_attention','npu_fused_infer_attention_score')and
                    kernel['original_called_exactly_once']is True and kernel['precision_intervention']is False,
                    'actual recorded original PA/FIA invocation; no operator execution here')
                parameters={name:parameter_metadata(t,value)for name,value in kw.items()if name!='atten_mask'}
                frames.append(dict(rank=rank,generation=generation,request=request['request'],layer=frame['layer'],
                    route=route,explicit_kwargs_keys=sorted(kw),parameters=parameters,
                    recorded_operator_schemas=kernel['actual_schema_family'],
                    mask=mask_metadata(t,kw.get('atten_mask')),mask_semantics_qualified=False,
                    native_FA_math_qualified=False))
        C.need(len(frames)==32,'retain every actual rank frame, no winning-mask filter')
        C.checked(capture['raw'])
        ranks.append(dict(rank=rank,receipt=capture['receipt'],raw=capture['raw'],logical_tensor_bytes=logical,
            frame_count=len(frames),frames=frames))
        del exported,payload,frames
    return dict(schema='bole.actual-native-ar-mask-metadata-diagnostic/v1',inputs=ir,source=x['AR_source'],
        actual_failed_owner=y['actual_v3_failure_refs']['RESULT.json'],
        actual_passed_original_G1_report=y['actual_v3_failure_refs']['cpu-consumer/BOLE-INDEPENDENT-GATE/ATTRIBUTION.json'],
        rank_count=4,frame_count=sum(r['frame_count']for r in ranks),ranks=ranks,source_proof=source_proof,
        all_saved_inputs_preserved=True,weights_only_load=True,CPU_only=True,Devices=[],NPU=False,
        original_G1_math_rerun=False,mathematics_recomputed=False,mask_semantics_qualified=False,
        native_FA_math_qualified=False,native_AR_numeric_pass=False,common_effects_pass=False,
        model_ready=False,task_ready=False,performance_ready=False,formal_success=False)


def main():
    p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False);p.add_argument('--execute',action='store_true')
    p.add_argument('--inputs-ref');p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false,"mask_semantics_qualified":false}');return 0
    if not(a.inputs_ref and a.output):p.error('exact diagnostic source and new owned output required')
    if not(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and
           not list(Path('/dev').glob('davinci[0-9]*'))):raise ValueError('actual Devices[] before tensor import')
    sys.dont_write_bytecode=True;s=importlib.util.spec_from_file_location('_mask_diag_common',Path(__file__).parent/'diag_common.py')
    D=importlib.util.module_from_spec(s);s.loader.exec_module(D);C=D.common();ir=json.loads(a.inputs_ref);y=D.source(C,ir)
    C.need(C.ref(__file__)==y['files']['mask_diagnostic.py']and a.output.parent==Path(y['consumer_output_root'])and
        a.output.parent.samefile('/adakv-results'),'sole actual source-bound RW diagnostic leaf')
    verified=D.readset(C,y,installed=True)  # All primary/saved hashes before torch.load/import.
    import torch
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    result=run(torch,C,D,y,ir,verified)
    C.need(not list(Path('/dev').glob('davinci[0-9]*')),'Devices[] preserved')
    C.write(a.output,result);return 0

if __name__=='__main__':raise SystemExit(main())
