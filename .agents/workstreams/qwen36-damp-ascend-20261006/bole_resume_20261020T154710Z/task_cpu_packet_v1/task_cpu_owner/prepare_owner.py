"""Metadata/source preparation only; never creates a container or admits a device."""
import argparse
import json
from pathlib import Path
import shutil
import sys
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import owner_common as C
import owner_namespace as N

FILES=('owner_common.py','owner_namespace.py','prepare_owner.py','cpu_steps.py','cpu_host.py','he_owned.py','test_owner_pure.py')


def prepare(a):
    refs={name:json.loads(getattr(a,name))for name in('G1_source_ref','G1_owner_ref','G1_bundle_ref','G1_independent_ref','authority_ref','rendered_inputs_ref')}
    C.authority(refs['authority_ref'],C.PHASE)
    on=C.basis(refs['G1_source_ref'],refs['G1_owner_ref'],refs['G1_bundle_ref'],refs['G1_independent_ref'])
    old=C.packet(a.packet_root)
    root=a.new_root;out=a.output_root
    C.need(root.is_absolute()and root.parent.is_dir()and not root.exists()and out.is_absolute()and not out.exists()
           and out.parent==Path('/opt/host/vnf/austinov')and out.name.startswith('run-bole-task-cpu-')
           and root!=out and not root.is_relative_to(out)and not out.is_relative_to(root),'new distinct source/output leaves')
    C.need(not any(p.is_symlink()for p in(*root.parents,*out.parents)),'ordinary source/output ancestors')
    helpers=N.helper_refs(C,on)
    root.mkdir(mode=0o700)
    for name in FILES:shutil.copyfile(P/name,root/name)
    packet_root=root/'task_packet';packet_root.mkdir()
    for name in[*C.obj(old)['files'],'PROPOSAL_MANIFEST.json']:
        destination=packet_root/name;destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(a.packet_root/name,destination)
    C.packet(packet_root)
    C.need('task_contract'not in sys.modules,'private metadata preparation tokenizer namespace')
    task_prepare=C.load(C.ref(packet_root/'prepare_packet.py'),'_task_cpu_packet_prepare')
    source=task_prepare.prepare(refs['authority_ref'],refs['rendered_inputs_ref'],C.IMAGE,root/'TASK_SOURCE_UNBOUND.json')
    # Only stream exact data/tokenizer/source files, never load arrays or hash55GB weights on host.
    readset,tokenizer=C.task_readset(source,host=True)
    m=dict(schema='bole.task-finite-CPU-owner-inputs/v1',default_enabled=False,prepared_only=True,
        files={name:C.ref(root/name)for name in FILES},task_packet_root=str(packet_root),
        frozen_packet_manifest_ref=C.ref(packet_root/'PROPOSAL_MANIFEST.json'),
        task_source_unbound_ref=source,output_root=str(out),image_id=C.IMAGE,
        phase_seconds=C.PHASE,cleanup_seconds=C.CLEANUP,CPU=C.CPU,host_CPU=C.HOST_CPU,
        guest_memory_bytes=8*C.GIB,reserve_CPU_budget=2,summed_ancestor_CPU_budget=7,
        phase_order=['cpu-preflight','he-controls','cpu-consumer'],helper_refs=helpers,
        task_readset=readset,tokenizer_mounts=tokenizer,**refs,
        model_requests_permitted=False,task_score_permitted=False,generated_code_scope='fixed official HE control snippets only',
        model_ready=False,performance_ready=False,formal_success=False)
    return C.write(root/'OWNER_INPUTS.json',m)


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--prepare',action='store_true')
    for name in('G1-source-ref','G1-owner-ref','G1-bundle-ref','G1-independent-ref','authority-ref','rendered-inputs-ref'):p.add_argument('--'+name)
    for name in('packet-root','new-root','output-root'):p.add_argument('--'+name,type=Path)
    a=p.parse_args()
    if not a.prepare:print('{"enabled":false,"container_created":false,"NPU":false}');return 0
    C.need(all(v is not None for v in vars(a).values()),'all exact actual refs and new roots required')
    print(json.dumps(dict(inputs_ref=prepare(a),resources_admitted=False,model_ready=False,NPU=False)));return 0


if __name__=='__main__':raise SystemExit(main())
