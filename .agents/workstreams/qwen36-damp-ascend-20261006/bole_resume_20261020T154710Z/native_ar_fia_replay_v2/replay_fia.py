"""DefaultOFF same-operator all128×two-filler diagnostic; no model/promotion."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys


def save_maps(C,L,root,label,allowed,*,rehash=False):
    text=Path('/proc/self/maps').read_text()
    ref=C.write(root/(label+'.json'),dict(pid=os.getpid(),maps=text))
    # Persistence precedes strict checking: unknown new dlopen remains evidence.
    observed=L.check(text,allowed,rehash=rehash)
    return dict(raw=ref,observed=observed,whole_SHA_rechecked=rehash)


def raw_rank(t,C,R,y,context,rank,capture):
    x,m,_,_,_=context;original,num=R.math_sources(C,y)
    N=C.load(num['files']['numeric_diagnostic.py'],'_fia_raw_diagnostic')
    PC=C.load(m['files']['pair_contract.py'],'pair_contract')
    receipt=C.obj(capture['receipt']);export=t.load(C.checked(capture['raw']),map_location='cpu',weights_only=True);raw=export['payload']
    logical=N.primitive_bytes(t,raw)
    C.need(export['schema']=='bole.model-diagnostic-primitives/v1'and export['cap_bytes']==PC.CAP and
        logical==export['logical_tensor_bytes']==receipt['logical_tensor_bytes']and logical+64*2**20<=PC.CAP and
        receipt['rank']==raw['rank']==rank and receipt['raw']==capture['raw']and receipt['primary']is None and
        raw['source']==receipt['source']==x['AR_source']and raw['source_after']==m['files']and
        raw['runtime_sources_after']==m['runtime_sources']and raw['primary']is None and len(raw['requests'])==2,
        'exact original source/weights-only primitive envelope and immutable raw')
    return export,raw


def frames(C,raw):
    for generation,request in enumerate(raw['requests'],1):
        C.need(request['generation']==generation and len(request['FA'])==16 and
            {f['layer']for f in request['FA']}==set(range(3,64,4)),'both complete generations/every actual FA layer')
        for frame in request['FA']:yield generation,request,frame


def run(t,n,C,R,y,ir,context,admission,hr,root):
    _,metadata=R.metadata_gate(C,y,ir,hr);x,m,_,_,_=context;original,num=R.math_sources(C,y)
    sys.path.insert(0,m['root'])
    F=C.load(original['files']['derived_math_consumer.py'],'_fia_replay_original_math')
    A=C.load(y['files']['arena_layout.py'],'_fia_replay_layout');L=C.load(y['files']['library_maps.py'],'_fia_replay_libraries')
    C.need(n.npu_fused_infer_attention_score is t.ops.npu.npu_fused_infer_attention_score,'actual original registered export packet')
    schemas={'npu.npu_fused_infer_attention_score':{k:str(v)for k,v in t.ops.npu.npu_fused_infer_attention_score._schemas.items()}}
    C.need(schemas==metadata['actual_registered_schema'],'actual CPU/current NPU packet schema exactly joined')
    allowed=L.bind(metadata['allowed_executable_libraries'])
    process=dict(pid=os.getpid(),status=Path('/proc/self/status').read_text(),cgroup=Path('/proc/self/cgroup').read_text(),
        cmdline=[a.decode()for a in Path('/proc/self/cmdline').read_bytes().split(b'\0')if a])
    stat=Path('/proc/self/stat').read_text();fields=stat[stat.rfind(')')+2:].split()
    C.need(fields[0]not in('Z','X'),'actual replay process live')
    process.update(stat=stat,start_ticks=int(fields[19]),cgroup_contains_CID=admission['owned_CID']in process['cgroup'],
        authoritative_host_NSpid_start_cgroup_join_required=True)
    # Private cgroup namespaces may report '/'. Do not infer CID from that
    # spelling: original host ctl.observe joins its actual compute PID below.
    C.write(root/'PROCESS-IDENTITY.json',process)
    start_maps=save_maps(C,L,root,'MAPS-START',allowed,rehash=True)
    t.npu.set_device(0);t.npu.matmul.allow_hf32=False
    C.need(t.npu.matmul.allow_hf32 is False,'same actual HF32-off setting, no precision experiment')
    t.npu.synchronize()
    initialized_maps=save_maps(C,L,root,'MAPS-INITIALIZED',allowed,rehash=True)
    ar=C.obj(original['actual_saved_refs']['NATIVE-AR-BUNDLE.json']);ranks=[];calls=0;old_failed=0;export_bytes=0;observed=set()
    for rank,capture in enumerate(ar['ranks']):
        export,raw=raw_rank(t,C,R,y,context,rank,capture);rows=[];outputs=[]
        for generation,request,frame in frames(C,raw):
            frozen=F.actual_native_fa(t,frame);A.check_identity(frame)
            C.need(frame['kernel'][0]['actual_schema_family']==schemas,'original frame operator schema identical')
            old_failed+=not frozen['checks']['FP64']['pointwise_pass']
            for filler in A.FILLERS:
                storage,kw,selected=A.build(t,frame,filler,'npu:0')
                C.need(storage.numel()==A.STORAGE_ELEMENTS and storage.dtype==t.bfloat16 and
                    tuple(kw['key'].shape)==tuple(kw['value'].shape)==A.SHAPE and
                    tuple(kw['key'].stride())==tuple(kw['value'].stride())==A.STRIDE and
                    kw['key'].storage_offset()==A.K_OFFSET and kw['value'].storage_offset()==A.V_OFFSET and
                    kw['key'].untyped_storage().data_ptr()==kw['value'].untyped_storage().data_ptr()==storage.untyped_storage().data_ptr(),
                    'actual reconstructed full shared storage/offset/shape/stride remains exact')
                C.need(t.equal(kw['key'].view(-1,1,256).index_select(0,selected).cpu().view(t.int16),frame['key'].view(t.int16))and
                    t.equal(kw['value'].view(-1,1,256).index_select(0,selected).cpu().view(t.int16),frame['value'].view(t.int16))and
                    t.equal(kw['query'].cpu().view(t.int16),frame['query'].view(t.int16))and t.equal(kw['atten_mask'].cpu(),frame['kernel'][0]['explicit_kwargs']['atten_mask'])and
                    t.equal(kw['block_table'].cpu(),frame['kernel'][0]['explicit_kwargs']['block_table']),
                    'all valid132/query/full mask/full table bitwise original operands')
                snapshots={name:value.clone()for name,value in dict(arena=storage,query=kw['query'],mask=kw['atten_mask'],table=kw['block_table']).items()}
                t.npu.synchronize();tag='CALL-%03d'%calls
                before=save_maps(C,L,root,tag+'-BEFORE',allowed,rehash=True)
                # EXACT original target interface: all13 captured explicit kwargs,
                # no inner_precise/default addition, no recaptured model state.
                result=n.npu_fused_infer_attention_score(**kw)
                t.npu.synchronize();calls+=1
                after=save_maps(C,L,root,tag+'-AFTER',allowed,rehash=True)
                observed.update(before['observed']);observed.update(after['observed'])
                C.need(type(result)in(tuple,list)and len(result)==2,'actual registered FIA result tuple, no guessed adapter')
                actual=result[0].detach().cpu();aux=result[1].detach().cpu()
                native_shape=list(actual.shape)
                C.need(actual.dtype==t.bfloat16 and actual.numel()==1536 and
                    tuple(actual.shape)==tuple(frame['kernel'][0]['output'].shape)and bool(t.isfinite(actual).all()),
                    'same captured original finite native output dtype/shape, no guessed result ABI')
                actual=actual.reshape(1,6,256)
                unchanged={name:bool(t.equal(value.view(t.int16)if value.dtype==t.bfloat16 else value,
                    snapshots[name].view(t.int16)if snapshots[name].dtype==t.bfloat16 else snapshots[name]))
                    for name,value in dict(arena=storage,query=kw['query'],mask=kw['atten_mask'],table=kw['block_table']).items()}
                C.need(all(unchanged.values())and t.npu.matmul.allow_hf32 is False,'all private full input bytes unchanged/HF32off')
                rows.append(dict(rank=rank,generation=generation,layer=frame['layer'],request=request['request'],filler=filler,
                    call_ordinal=calls,all13_original_kwargs=True,storage_elements=A.STORAGE_ELEMENTS,shared_storage=True,
                    original_checks=frozen['checks'],maps_before=before,maps_after=after,all_input_bits_unchanged=unchanged,
                    captured_output_bitwise_equal=bool(t.equal(actual.view(t.int16),frame['output'].view(t.int16))),
                    native_output_shape=native_shape,auxiliary_shape=list(aux.shape),auxiliary_dtype=str(aux.dtype),original_native_numerical_pass=False))
                outputs.append(dict(rank=rank,generation=generation,layer=frame['layer'],filler=filler,output=actual,auxiliary=aux))
                del snapshots,storage,kw,selected,result,actual,aux
        C.need(len(rows)==64,'all32 rank frames both preregistered fillers, no selected winners')
        path=root/('REPLAY-RANK-%d.pt'%rank)
        with path.open('xb')as f:t.save(dict(schema='bole.native-AR-FIA-replay-tensors/v1',inputs=ir,rank=rank,original_raw=capture['raw'],rows=outputs),f)
        br=C.ref(path);jr=C.write(root/('REPLAY-RANK-%d.json'%rank),dict(inputs=ir,rank=rank,original_raw=capture['raw'],tensors=br,rows=rows))
        export_bytes+=br['bytes']+jr['bytes'];C.need(export_bytes<=128*2**20,'bounded all256 output/metadata export128MiB excluding bounded maps')
        ranks.append(dict(rank=rank,raw=capture['raw'],tensors=br,report=jr));C.checked(capture['raw']);del export,raw,rows,outputs
    C.need(calls==256 and old_failed==16,'all128×two calls and unchanged original16 numerical failures')
    end_maps=save_maps(C,L,root,'MAPS-END',allowed,rehash=True)
    required=[row['canonical']['path']for row in metadata['static_installed_aliases']if Path(row['installed_alias']['path']).name in
        ('libtorch_npu.so','_C.cpython-312-aarch64-linux-gnu.so','libopapi.so')]
    C.need(len(set(required))==3 and set(required)<=observed,'actual executable mappings include all3 exact binding/TorchNPU/opapi files')
    return dict(schema='bole.native-AR-FIA-all128-two-filler-replay/v1',inputs=ir,source=x['AR_source'],metadata_handoff=hr,
        admission=admission['reference'],ranks=ranks,frame_count=128,rank_count=4,actual_operator_calls=calls,
        fillers=list(A.FILLERS),unused_arena_reconstruction=True,valid132_from_original_capture=True,all13_kwargs_unchanged=True,
        original_failure_frame_count=old_failed,start_maps=start_maps,initialized_maps=initialized_maps,end_maps=end_maps,
        allowed_executable_libraries=metadata['allowed_executable_libraries'],process=process,all_input_bits_unchanged=True,
        maps_checked_before_after_each_call=True,whole_SHA_buildIDs_recomputed_each_call_before_after=True,whole_SHA_buildIDs_joined_start_end=True,required_actual_mapped_libraries=required,
        precision_changed=False,HF32=False,weights_only_load=True,export_bytes=export_bytes,NPU=True,physical=[4],logical=[0],
        same_operator_replay_completed=True,original_native_numerical_pass=False,native_FA_math_qualified=False,
        internal_precision_proven=False,device_kernel_binary_proven=False,common_effects_pass=False,formal_success=False)


def main():
    p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False);p.add_argument('--execute',action='store_true')
    p.add_argument('--inputs-ref');p.add_argument('--metadata-handoff-ref');p.add_argument('--admission-ref');p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false,"formal_success":false}');return 0
    if not all((a.inputs_ref,a.metadata_handoff_ref,a.admission_ref,a.output)):p.error('exact inputs/realCPUhandoff/actualadmission/output required')
    if os.environ.get('ASCEND_RT_VISIBLE_DEVICES')!='0'or os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')!='0'or sorted(p.name for p in Path('/dev').glob('davinci[0-9]*'))!=['davinci0']:
        raise ValueError('only MAIN-admitted logical0 numbered NPU before import')
    sys.dont_write_bytecode=True;s=importlib.util.spec_from_file_location('_fia_actual_replay_common',Path(__file__).parent/'replay_common.py')
    R=importlib.util.module_from_spec(s);s.loader.exec_module(R);C=R.common();ir=json.loads(a.inputs_ref);hr=json.loads(a.metadata_handoff_ref);ar=json.loads(a.admission_ref);y=R.source(C,ir)
    C.need(C.ref(__file__)==y['files']['replay_fia.py']and a.output.parent==Path(y['output_root'])/'dense'and
        a.output.parent.samefile('/adakv-results'),'sole source-bound replay RW leaf')
    admission=R.admission_gate(C,y,ir,hr,ar);R.metadata_readset(C,y,ir,hr);context=R.readset(C,y,installed=True)
    import torch
    import torch_npu
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    value=run(torch,torch_npu,C,R,y,ir,context,admission,hr,a.output.parent);C.write(a.output,value);return 0

if __name__=='__main__':raise SystemExit(main())
