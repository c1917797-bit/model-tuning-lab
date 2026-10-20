"""Source-only isolated candidate assembly. No host/device/container operations."""
import argparse
import json
from pathlib import Path
import shutil
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0,str(_Path(__file__).resolve().parent))
import pair_contract as C

P=Path(__file__).resolve().parent
HELPERS=('model_entry.py','worker_entry.py','identity_capture.py','identity_journal.py',
         'identity_oracle.py','sourceio.py')


def prepare(*,on_source_ref,on_command_ref,image_id,model_manifest_ref,authority_ref,
            new_root,receipt_root,consumer_output_root):
    on=C.obj(on_source_ref);command=C.obj(on_command_ref)
    C.need(on['prepared_only']is False and on['service_experiment']==dict(
        schema='bole.c1-two-request-service/v1',prefix=131,request_count=2,
        max_steps_per_request=1,max_output_tokens=2),'exact frozen bounded G1 ON source')
    C.need(command['source']==on_source_ref,'actual ON server command belongs to that source')
    argv=C.native_argv(command['argv'])
    C.need(type(image_id)is str and image_id.startswith('sha256:')and len(image_id)==71,
           'explicit actual immutable image ID')
    C.obj(model_manifest_ref);C.obj(authority_ref)
    C.need(new_root.is_absolute() and new_root.parent.is_dir() and not new_root.exists()
           and not any(p.is_symlink()for p in(new_root.parent,*new_root.parents)),
           'new unique owned candidate leaf; no existing source may be modified')
    C.need(receipt_root.is_absolute()and consumer_output_root.is_absolute(), 'prospective exact owned outputs')
    new_root.mkdir()
    for file in sorted(P.glob('*.py')):
        shutil.copyfile(file,new_root/file.name)
    meta='bole_native_ar_pair-0.0.0.dist-info'
    shutil.copytree(P/meta,new_root/meta)
    for name in HELPERS:
        C.need(not(new_root/name).exists(),'no local helper shadowing')
        shutil.copyfile(C.checked(on['files'][name]),new_root/name)
    files={str(p.relative_to(new_root)):C.ref(p)for p in sorted(new_root.rglob('*'))if p.is_file()}
    value=dict(schema='bole.native-ar-pair-observer-source/v1',root=str(new_root),prepared_only=False,
        default_enabled=False,scope=C.SCOPE,files=files,runtime_sources=on['runtime_sources'],
        BOLE_source_ref=on_source_ref,BOLE_server_command_ref=on_command_ref,
        native_server_argv=argv,expected_image_id=image_id,model_manifest_ref=model_manifest_ref,
        authority_ref=authority_ref,model_receipt_root=str(receipt_root),
        pair_consumer_output_root=str(consumer_output_root),actual_model_execution=False,
        whole_numerical_qualification=False,global_FA_precision_alignment_qualified=False,
        model_ready=False,task_ready=False,performance_ready=False,formal_success=False)
    return C.write(new_root/'SOURCE_BOUND.json',value)


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
    p.add_argument('--BOLE-source-ref');p.add_argument('--BOLE-server-command-ref')
    p.add_argument('--expected-image-id');p.add_argument('--model-manifest-ref');p.add_argument('--authority-ref')
    p.add_argument('--new-root',type=Path);p.add_argument('--receipt-root',type=Path)
    p.add_argument('--consumer-output-root',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    C.need(all(x is not None for x in (a.BOLE_source_ref,a.BOLE_server_command_ref,a.expected_image_id,
        a.model_manifest_ref,a.authority_ref,a.new_root,a.receipt_root,a.consumer_output_root)),
        'explicit frozen donor, actual image/model/authority and new owned paths')
    result=prepare(on_source_ref=json.loads(a.BOLE_source_ref),on_command_ref=json.loads(a.BOLE_server_command_ref),
        image_id=a.expected_image_id,model_manifest_ref=json.loads(a.model_manifest_ref),
        authority_ref=json.loads(a.authority_ref),new_root=a.new_root,receipt_root=a.receipt_root,
        consumer_output_root=a.consumer_output_root)
    print(json.dumps(result));return 0


if __name__=='__main__':raise SystemExit(main())
