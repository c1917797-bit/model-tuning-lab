"""Default-OFF local source assembly; real complete G1 pass required, no Docker."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import sys

FILES=('ar_owner_common.py','ar_host_namespace.py','ar_snapshot_bindings.py','ar_sameimage_preflight.py',
       'native_ar_host.py','consume_pair_entry.py','prepare_native_owner.py','fd_inventory_diagnostic.py')
HELPERS=('model_entry.py','worker_entry.py','identity_capture.py','identity_journal.py',
         'identity_oracle.py','sourceio.py')


def prepare_ar(C,*,on,sr,command,shared,native_packet_root,new_root,output_root):
    """Source-only derivative of frozen prepare_native_ar_pair.prepare.

    Every pair/observer/helper byte is copied unchanged. Only source metadata
    gains explicit common/observer partitions and their merged runtime map.
    No original/preexisting source file is changed after its initial creation.
    """
    P=C.load(C.ref(native_packet_root/'pair_contract.py'),'_ar_v4_source_pair_contract')
    new_root.mkdir()
    for file in sorted(native_packet_root.glob('*.py')):shutil.copyfile(C.checked(C.ref(file)),new_root/file.name)
    meta='bole_native_ar_pair-0.0.0.dist-info';shutil.copytree(native_packet_root/meta,new_root/meta)
    for name in HELPERS:
        C.need(not(new_root/name).exists(),'no local helper shadowing')
        shutil.copyfile(C.checked(on['files'][name]),new_root/name)
    files={str(p.relative_to(new_root)):C.ref(p)for p in sorted(new_root.rglob('*'))if p.is_file()}
    runtime=dict(on['runtime_sources'],**C.OBSERVER_RUNTIME)
    closure=C.runtime_key_audit(files,runtime)
    value=dict(schema='bole.native-ar-pair-observer-source/v1',root=str(new_root),prepared_only=False,
        default_enabled=False,scope=P.SCOPE,files=files,runtime_sources=runtime,
        common_runtime_sources=on['runtime_sources'],observer_runtime_sources=C.OBSERVER_RUNTIME,
        observer_runtime_purpose='source-bound native FA DeviceOperator class/method identity only; no execution replacement',
        runtime_key_closure=closure,frozen_pair_preparer=C.ref(native_packet_root/'prepare_native_ar_pair.py'),
        BOLE_source_ref=sr,BOLE_server_command_ref=command,native_server_argv=P.native_argv(C.obj(command)['argv']),
        expected_image_id=C.IMAGE,model_manifest_ref=shared,authority_ref=on['authority_ref'],
        model_receipt_root=str(output_root/'dense/receipts'),pair_consumer_output_root=str(output_root/'cpu-consumer'),
        actual_model_execution=False,whole_numerical_qualification=False,global_FA_precision_alignment_qualified=False,
        model_ready=False,task_ready=False,performance_ready=False,formal_success=False)
    return C.write(new_root/'SOURCE_BOUND.json',value)


def main():
    p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False);p.add_argument('--execute',action='store_true')
    for name in('G1-source-ref','G1-owner-ref','G1-bundle-ref','G1-independent-ref','G1-inspect-ref',
                'G1-initial-profile-ref','actual-model-manifest-ref','frozen-inputs-ref'):
        p.add_argument('--'+name)
    for name in('native-packet-root','new-AR-root','new-control-root','output-root'):p.add_argument('--'+name,type=Path)
    p.add_argument('--framework-host-evidence-json')
    p.add_argument('--observer-runtime-host-evidence-json')
    a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false,"prepared_only":true}');return 0
    if not all(vars(a).values()):p.error('all actual successful G1 evidence and unique absolute source/output paths required')
    root=Path(__file__).resolve().parent
    s=importlib.util.spec_from_file_location('_native_ar_builder_common',str(root/'ar_owner_common.py'))
    C=importlib.util.module_from_spec(s);s.loader.exec_module(C)
    sr,owner,bundle,independent,inspection,initial,actual_model,frozen=[json.loads(getattr(a,n))for n in
        ('G1_source_ref','G1_owner_ref','G1_bundle_ref','G1_independent_ref','G1_inspect_ref',
         'G1_initial_profile_ref','actual_model_manifest_ref','frozen_inputs_ref')]
    on,own,b,v=C.g1_pass(sr,owner,bundle,independent)
    framework_hosts=C.assemble_framework_copies(C.framework_sources(b),json.loads(a.framework_host_evidence_json),on)
    observer_hosts=C.observer_copies(json.loads(a.observer_runtime_host_evidence_json))
    C.need(not(set(on['runtime_sources'])&set(C.OBSERVER_RUNTIME)),'observer-only dependency cannot replace any ON common runtime key')
    runtime={}
    for key,r in on['runtime_sources'].items():
        copies=[q for q in on['files'].values()if q['path']!=r['path']and(q['bytes'],q['sha256'])==(r['bytes'],r['sha256'])]
        C.need(copies,'no source-bound host runtime copy for '+key)
        runtime[key]=sorted(copies,key=lambda q:q['path'])[0];C.checked(runtime[key])
    runtime.update(observer_hosts)
    audit_files={p.name:C.ref(p)for p in sorted(a.native_packet_root.glob('*.py'))}
    audit_files.update({name:on['files'][name]for name in HELPERS})
    audit_files.update({'owner/'+name:C.ref(root/name)for name in FILES})
    C.runtime_key_audit(audit_files,dict(on['runtime_sources'],**C.OBSERVER_RUNTIME))
    command=C.ref(Path(on['model_receipt_root'])/'SERVER_COMMAND.json')
    C.need(C.obj(command)['source']==sr,'actual ON command in dense/receipts')
    token=C.obj(frozen)
    C.need(token['source']==sr and token['input_tokens']==131 and len(token['token_ids'])==131 and
        token['tokenizer']=='/models/Qwen3.6-27B' and token['data_generated_by_actual_tokenizer']is True,
        'same exact actual G1 tokenizer IDs, no regenerated input')
    inspect=C.obj(inspection)
    C.need(type(inspect)is list and len(inspect)==1 and inspect[0]['Image']==C.IMAGE and
        inspect[0]['Id']==b['frontend_binding']['owned_cid'],'actual owned ON image and frontend CID')
    C.obj(initial) # Exact semantic/identity join is retained for the independent metadata reader.
    for path in(a.new_AR_root,a.new_control_root,a.output_root):
        C.need(path.is_absolute() and not path.exists() and path.parent.is_dir() and
            not any(z.is_symlink()for z in(path,*path.parents)),'three new distinct ordinary leaves')
    C.need(len({a.new_AR_root,a.new_control_root,a.output_root})==3,'source/control/output leaves distinct')
    model=C.model_manifest(actual_model,host=True,rehash=True)
    # Ref paths in shared guest manifest MUST be /models, not the host /cache paths just checked.
    model['files']=[dict(r,path=str(C.GUEST_MODEL/Path(r['path']).relative_to(C.MODEL_ROOT)))for r in model['files']]
    a.new_control_root.mkdir(mode=0o700)
    for name in FILES:shutil.copyfile(root/name,a.new_control_root/name)
    shared=C.write(a.new_control_root/'SHARED_MODEL_TOKENIZER.json',model)
    ar=prepare_ar(C,on=on,sr=sr,command=command,shared=shared,native_packet_root=a.native_packet_root,
        new_root=a.new_AR_root,output_root=a.output_root)
    x=dict(schema='bole.native-ar-owner-inputs/v1',authority=on['authority_ref'],AR_source=ar,
        files={name:C.ref(a.new_control_root/name)for name in FILES},output_root=str(a.output_root),
        G1_owner=owner,G1_bundle=bundle,G1_independent=independent,G1_docker_inspect=inspection,
        G1_server_command=command,G1_initial_profile=initial,frozen_inputs=frozen,actual_model_manifest=actual_model,
        shared_model_manifest=shared,runtime_host_evidence=runtime,framework_host_evidence=framework_hosts,
        observer_runtime_host_evidence=observer_hosts,
        prepared_only=True,default_enabled=False,
        worker_signal_permitted=False,matched_common_plugin_effects_gate_pending=True,model_ready=False,formal_success=False)
    C.readset(x,installed=False)
    result=C.write(a.new_control_root/'INPUTS.json',x)
    print(json.dumps(dict(inputs=result,AR_source=ar,prepared_only=True,NPU=False,resources_admitted=False,
        matched_common_plugin_effects_gate_pending=True,model_ready=False,formal_success=False)));return 0


if __name__=='__main__':raise SystemExit(main())
