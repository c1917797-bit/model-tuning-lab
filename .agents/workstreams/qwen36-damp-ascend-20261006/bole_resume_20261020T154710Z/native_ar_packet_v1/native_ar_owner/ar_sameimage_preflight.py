"""Default-OFF Devices[] exact-source/runtime/metadata guard check; no model call."""
import argparse
import importlib
import importlib.metadata
import importlib.util
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    p.add_argument('--execute',action='store_true');p.add_argument('--inputs-ref');p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false,"model_ready":false}');return 0
    if not a.inputs_ref or a.output is None:p.error('exact prepared inputs and new owned CPU output required')
    ir=json.loads(a.inputs_ref)
    # This reviewed source bootstrap opens only its declared sibling, no ambient package.
    root=Path(__file__).resolve().parent
    spec=importlib.util.spec_from_file_location('_ar_preflight_common',str(root/'ar_owner_common.py'))
    C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
    x=C.obj(ir);C.need(C.ref(__file__)==x['files']['ar_sameimage_preflight.py'] and
        C.ref(C.__file__)==x['files']['ar_owner_common.py'],'exact CPU entry/common sources')
    C.need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='' and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'
           and not list(Path('/dev').glob('davinci[0-9]*')),'actual Devices[] before tensor/runtime imports')
    m,on,readset=C.readset(x,installed=True)
    model=C.model_manifest(x['actual_model_manifest'],host=False,rehash=True)
    shared=C.obj(m['model_manifest_ref'])
    C.need(shared['schema']==model['schema'] and shared['model_root']==model['model_root'] and
           shared['files']==model['files'],'all29 actual guest model paths, never host Ref substitution')
    for r in m['files'].values():C.checked(r)
    cold=[]
    cli_refs=[(name,m['files'][name])for name in('native_ar_server.py','pair_entry.py','consume_pair.py','launch_profile.py','assemble_pair_inputs.py')]
    cli_refs += [(name,x['files'][name])for name in('native_ar_host.py','ar_sameimage_preflight.py','consume_pair_entry.py','prepare_native_owner.py')]
    for name,reference in cli_refs:
        for args in([],['--help']):
            result=subprocess.run([sys.executable,'-I','-B',reference['path'],*args],capture_output=True,text=True,timeout=10)
            C.need(result.returncode==0,'actual same-image cold CLI failed '+name)
            cold.append(dict(name=name,args=args,exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr))
    sys.path.insert(0,m['root'])
    pair=C.load(m['files']['pair_contract.py'],'pair_contract');pair.source(x['AR_source'])
    entries=[e for e in importlib.metadata.entry_points(group='vllm.general_plugins')if e.name=='bole_native_ar_pair']
    C.need(len(entries)==1 and entries[0].value=='native_ar_bootstrap:register','actual private plugin metadata resolution')
    bootstrap=importlib.import_module('native_ar_bootstrap')
    C.need(C.ref(bootstrap.__file__)==m['files']['native_ar_bootstrap.py'],'resolved actual private plugin module')
    import torch
    import torch_npu
    del torch_npu
    C.need(not torch.npu.is_initialized(),'no device context in Devices[] source preflight')
    refs=m['runtime_sources']
    def installed(key):
        path=refs[key]['path']
        if '/site-packages/'in path:part=path.split('/site-packages/',1)[1]
        elif '/vllm_ascend/'in path:part='vllm_ascend/'+path.split('/vllm_ascend/',1)[1]
        elif '/vllm/vllm/'in path:part='vllm/'+path.split('/vllm/vllm/',1)[1]
        else:raise ValueError('unmapped installed module path '+path)
        module=importlib.import_module(part[:-3].replace('/','.').removesuffix('.__init__'))
        C.need(C.ref(module.__file__)==refs[key],'actual imported installed module '+key)
        return module
    runner=installed('runner');classes=[v for v in vars(runner).values()if isinstance(v,type)and
        'sample_tokens'in vars(v)and C.ref(inspect.getsourcefile(v))==refs['runner']]
    C.need(len(classes)==1,'one actual source-bound runner sample_tokens owner')
    wrapped=vars(classes[0])['sample_tokens'];original=getattr(wrapped,'__wrapped__',None)
    C.need(original is not None and C.ref(inspect.getsourcefile(wrapped))==refs['torch_contextlib'] and
           C.ref(inspect.getsourcefile(original))==refs['runner'],'actual native inference-mode source wrapper')
    closure=inspect.getclosurevars(wrapped).nonlocals;factory=closure.get('ctx_factory');context=getattr(factory,'__self__',None)
    C.need(closure.get('func')is original and callable(factory)and C.ref(inspect.getsourcefile(factory))==refs['torch_grad_mode']
           and type(context)is torch.inference_mode and context.mode is True,'exact native inference-mode closure, no instance or model emulation')
    C.need(not torch.npu.is_initialized(),'source/metadata checks initialized no NPU')
    report=dict(schema='bole.native-ar-owner-sameimage-source-preflight/v1',inputs=ir,source=x['AR_source'],
        Devices=[],readset_count=len(readset),actual_model_files=29,actual_model_shards=15,actual_model_bytes=55586107940,
        runtime_sources=m['runtime_sources'],actual_cold_cli=cold,plugin_entrypoint=entries[0].value,
        source_preflight_pass=True,inference_mode_source_guard_checked=True,actual_instance_guards_exercised=False,
        original_observer_guards_still_required_at_real_load=True,NPU=False,model_ready=False,
        matched_common_plugin_effects_gate_pending=True,formal_success=False)
    print(json.dumps(C.write(a.output,report)));return 0


if __name__=='__main__':raise SystemExit(main())
