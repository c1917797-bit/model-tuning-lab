"""Default-OFF Devices[] exact-source/runtime/metadata guard check; no model call."""
import argparse
import importlib
import importlib.metadata
import importlib.util
import ast
import json
import os
from pathlib import Path
import subprocess
import sys


def runner_source_declaration(C,reference):
    """Exact parsed declaration is not a runtime wrapper/closure qualification."""
    path=C.checked(reference);raw=path.read_bytes();tree=ast.parse(raw,filename=str(path))
    compile(tree,str(path),'exec')
    rows=[]
    expected=ast.dump(ast.parse('@torch.inference_mode()\ndef sample_tokens(self): pass\n').body[0].decorator_list[0],include_attributes=False)
    for cls in tree.body:
        if not isinstance(cls,ast.ClassDef):continue
        for method in cls.body:
            if isinstance(method,(ast.FunctionDef,ast.AsyncFunctionDef))and method.name=='sample_tokens':
                decorators=[ast.dump(value,include_attributes=False)for value in method.decorator_list]
                C.need(type(method)is ast.FunctionDef and decorators==[expected],
                       'one exact source-declared torch.inference_mode() decorator')
                rows.append(dict(class_name=cls.name,method_name=method.name,
                    decorators=[ast.unparse(value)for value in method.decorator_list],
                    source=reference,source_compiled_not_executed=True,
                    actual_runtime_wrapper_or_closure_examined=False))
    C.need(len(rows)==1,'one source-defined runner sample_tokens declaration')
    return rows[0]


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
    specification=importlib.util.find_spec('native_ar_bootstrap')
    C.need(specification is not None and specification.origin is not None and
           C.ref(specification.origin)==m['files']['native_ar_bootstrap.py'],
           'resolved exact plugin source without executing the module')
    refs=m['runtime_sources']
    for reference in refs.values():
        source=C.checked(reference)
        compile(source.read_bytes(),str(source),'exec')  # compile ONLY, no exec/import.
    declaration=runner_source_declaration(C,refs['runner'])
    forbidden=('torch','torch_npu','triton','vllm','vllm_ascend')
    C.need(not any(name==prefix or name.startswith(prefix+'.')for name in sys.modules for prefix in forbidden),
           'Devices[] source preflight imported no tensor/native worker/runner modules')
    report=dict(schema='bole.native-ar-owner-sameimage-source-preflight/v1',inputs=ir,source=x['AR_source'],
        Devices=[],readset_count=len(readset),actual_model_files=29,actual_model_shards=15,actual_model_bytes=55586107940,
        runtime_sources=m['runtime_sources'],actual_cold_cli=cold,plugin_entrypoint=entries[0].value,
        source_preflight_pass=True,inference_mode_source_guard_checked=False,
        inference_mode_source_decorator_declaration_checked=True,runner_source_declaration=declaration,
        actual_runtime_closure_guard_exercised=False,actual_instance_guards_exercised=False,
        tensor_runtime_imported=False,native_worker_or_runner_module_imported=False,
        plugin_module_executed=False,actual_runtime_closure_guard_required_at_real_load=True,
        original_observer_guards_still_required_at_real_load=True,NPU=False,model_ready=False,
        matched_common_plugin_effects_gate_pending=True,formal_success=False)
    print(json.dumps(C.write(a.output,report)));return 0


if __name__=='__main__':raise SystemExit(main())
