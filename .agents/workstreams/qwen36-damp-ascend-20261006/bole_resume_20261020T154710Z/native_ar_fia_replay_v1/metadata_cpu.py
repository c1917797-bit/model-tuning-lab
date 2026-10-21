"""DefaultOFF same-image Devices[] all128 ABI/catalog preflight; no native call."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys


def run(t,n,C,R,y,ir,context,output):
    x,m,on,_,mapping=context;original,num=R.math_sources(C,y)
    ar=C.obj(original['actual_saved_refs']['NATIVE-AR-BUNDLE.json'])
    sys.path.insert(0,m['root']);PC=C.load(m['files']['pair_contract.py'],'pair_contract')
    F=C.load(original['files']['derived_math_consumer.py'],'_fia_metadata_frozen_math')
    N=C.load(num['files']['numeric_diagnostic.py'],'_fia_metadata_frozen_diagnostic')
    A=C.load(y['files']['arena_layout.py'],'_fia_metadata_arena');L=C.load(y['files']['library_maps.py'],'_fia_metadata_maps')
    C.need(n.npu_fused_infer_attention_score is t.ops.npu.npu_fused_infer_attention_score,
        'actual installed export maps directly to same registered packet; no call performed')
    schemas={'npu.npu_fused_infer_attention_score':{k:str(v)for k,v in t.ops.npu.npu_fused_infer_attention_score._schemas.items()}}
    rows=[];raws=[]
    for rank,capture in enumerate(ar['ranks']):
        receipt=C.obj(capture['receipt']);export=t.load(C.checked(capture['raw']),map_location='cpu',weights_only=True);raw=export['payload']
        logical=N.primitive_bytes(t,raw)
        C.need(export['schema']=='bole.model-diagnostic-primitives/v1'and export['cap_bytes']==PC.CAP and
            logical==export['logical_tensor_bytes']==receipt['logical_tensor_bytes']and logical+64*2**20<=PC.CAP and
            raw['rank']==rank and raw['source']==x['AR_source']and raw['source_after']==m['files']and
            raw['runtime_sources_after']==m['runtime_sources']and raw['primary']is None and len(raw['requests'])==2,
            'exact original primitive/source/rank envelope')
        for generation,request in enumerate(raw['requests'],1):
            C.need(request['generation']==generation and len(request['FA'])==16 and {r['layer']for r in request['FA']}==set(range(3,64,4)),
                'both complete generations and all16FA layers')
            for frame in request['FA']:
                checks=F.actual_native_fa(t,frame);indices=A.check_identity(frame)
                C.need(frame['kernel'][0]['actual_schema_family']==schemas,'actual same-image registered schema equals every original frame')
                rows.append(dict(rank=rank,generation=generation,layer=frame['layer'],schema_equal=True,
                    all13_kwargs_checked=True,valid132_unique=len(set(indices))==132,original_checks=checks['checks'],
                    native_numerical_failure_preserved=not checks['checks']['FP64']['pointwise_pass']))
        C.checked(capture['raw']);raws.append(capture['raw']);del export,raw
    C.need(len(rows)==128 and sum(r['native_numerical_failure_preserved']for r in rows)==16,'all128 ABI controls; original16frame failure not hidden')
    fixed={};aliases=[]
    for path,row in mapping['installed_copies'].items():
        canonical=R.installed_alias(C,row['installed']);proof=L.fingerprint(canonical['path'])
        aliases.append(dict(installed_alias=row['installed'],canonical=canonical,host_copy=row['host'],ELF=proof['ELF']))
        if proof['ELF']['ELF']:
            key=canonical['path'];C.need(key not in fixed or fixed[key]['ref']==proof['ref'],'one fixed ELF identity');fixed[key]=proof
    for path,row in mapping['wheel_libraries'].items():
        canonical=R.installed_alias(C,row['installed']);proof=L.fingerprint(canonical['path'])
        C.need(proof['ELF']['ELF']is True,'explicit wheel executable library is an actual ELF')
        aliases.append(dict(installed_alias=row['installed'],canonical=canonical,wheel_RECORD=row['record'],ELF=proof['ELF']))
        key=canonical['path'];C.need(key not in fixed or fixed[key]['ref']==proof['ref'],'wheel/copied ELF identities agree');fixed[key]=proof
    # Save the complete map text before parsing. Unknown executable mappings
    # remain available if inventory itself rejects a source/ELF anomaly.
    maps=C.write(output/'CPU-PROCESS-MAPS.json',dict(pid=os.getpid(),maps=Path('/proc/self/maps').read_text()))
    actual=L.inventory();expected=dict(actual['libraries'])
    for path,value in fixed.items():
        C.need(path not in expected or expected[path]['ref']==value['ref']and expected[path]['ELF']==value['ELF'],
            'actual CPU mapped ELF joins exact stopped-image fixed evidence')
        expected[path]=value
    return dict(schema='bole.native-AR-FIA-Devices0-metadata/v1',inputs=ir,source=x['AR_source'],frame_count=128,rank_count=4,
        rows=rows,raws=raws,actual_registered_schema=schemas,actual_export_packet_identity=True,
        maps_receipt=maps,CPU_actual_map=actual,static_installed_aliases=aliases,allowed_executable_libraries=expected,
        catalog_semantics='actual CPU executable catalog plus exact fixed installed ELF identities; future NPU unknown maps fail',
        metadata_preflight_pass=True,native_operator_called=False,NPU=False,Devices=[],CPU_only=True,
        all128_original_geometry_checked=True,weights_only_load=True,unused_arena_reconstruction_not_original_capture=True,
        actual_NPU_loaded_libraries_proven=False,device_kernel_binary_proven=False,internal_precision_proven=False,
        original_native_numerical_pass=False,native_FA_math_qualified=False,common_effects_pass=False,formal_success=False)


def main():
    p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False);p.add_argument('--execute',action='store_true')
    p.add_argument('--inputs-ref');p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false,"formal_success":false}');return 0
    if not(a.inputs_ref and a.output):p.error('exact new inputs/output required')
    if os.environ.get('ASCEND_RT_VISIBLE_DEVICES')!=''or os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')!='0'or list(Path('/dev').glob('davinci[0-9]*')):
        raise ValueError('actual Devices[] before Torch/TorchNPU import')
    sys.dont_write_bytecode=True;s=importlib.util.spec_from_file_location('_fia_metadata_common',Path(__file__).parent/'replay_common.py')
    R=importlib.util.module_from_spec(s);s.loader.exec_module(R);C=R.common();ir=json.loads(a.inputs_ref);y=R.source(C,ir)
    C.need(C.ref(__file__)==y['files']['metadata_cpu.py']and a.output.parent==Path(y['output_root'])/'cpu-preflight'and
        a.output.parent.samefile('/adakv-results'),'sole exact owned CPU metadata RW leaf')
    context=R.readset(C,y,installed=True)
    import torch
    import torch_npu
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    value=run(torch,torch_npu,C,R,y,ir,context,a.output.parent)
    C.need(not list(Path('/dev').glob('davinci[0-9]*')),'Devices[] remained empty')
    C.write(a.output,value);return 0

if __name__=='__main__':raise SystemExit(main())
