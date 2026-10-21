"""Metadata/source preparation only; never creates a container or admits a device."""
import argparse
import json
from pathlib import Path
import shutil
import sys
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import owner_common as C
import owner_namespace as N
import main_quiescence as Q

FILES=('owner_common.py','owner_namespace.py','prepare_owner.py','cpu_steps.py','cpu_host.py','he_owned.py','test_owner_pure.py','main_quiescence.py','test_quiescence_pure.py','cpu_import_guard.py','public_probe_gate.py','test_public_probe_pure.py','test_tokenizer_probe_pure.py','network_evidence.py','lock_evidence.py','he_admission.py','he_diagnostic_gate.py','test_HE_guard.py','dependency_gate.py')


def prepare(a):
    refs={name:json.loads(getattr(a,name))for name in('G1_source_ref','G1_owner_ref','G1_bundle_ref','G1_independent_ref','authority_ref','rendered_inputs_ref','main_quiescence_ref','public_probe_owner_ref','HE_diagnostic_owner_ref','HE_diagnostic_independent_ref','HE_dependency_owner_ref','HE_dependency_independent_ref')}
    refs['tokenizer_runtime_copy_refs']=[json.loads(r)for r in a.tokenizer_runtime_copy_ref]
    import public_probe_gate as G
    G.readset(refs['public_probe_owner_ref'],rendered_inputs_ref=refs['rendered_inputs_ref'])
    import he_diagnostic_gate as HEG
    HEG.readset(refs['HE_diagnostic_owner_ref'],refs['HE_diagnostic_independent_ref'])
    import dependency_gate as DEG
    DEG.readset(refs['HE_dependency_owner_ref'],refs['HE_dependency_independent_ref'])
    C.authority(refs['authority_ref'],C.PHASE)
    expected=C.obj(C.ref(P/'TOKENIZER_SOURCE_EXPECTED.json'));copied={}
    for reference in refs['tokenizer_runtime_copy_refs']:
        copy=C.obj(reference)
        C.need(copy['image']==C.IMAGE and copy['stopped_readonly_CID']=='0731d3f91b532c38d56aa30acde830ff0f6304d93db9baa66d25d59ea3d4c2dc'and set(copy['files'])<=set(expected),'actual same-image stopped qualified source copies')
        for n,r in copy['files'].items():
            actual=C.ref(C.checked(r['host']));C.need(n not in copied and r['installed']==expected[n]and(actual['bytes'],actual['sha256'])==(expected[n]['bytes'],expected[n]['sha256']),'unique complete actual tokenizer source copy '+n);copied[n]=r
    C.need(set(copied)==set(expected),'all seven pinned tokenizer source copies')
    Q.policy(refs['main_quiescence_ref'],authority_ref=refs['authority_ref'])
    on=C.basis(refs['G1_source_ref'],refs['G1_owner_ref'],refs['G1_bundle_ref'],refs['G1_independent_ref'])
    old=C.packet(a.packet_root)
    root=a.new_root;out=a.output_root
    C.need(root.is_absolute()and root.parent.is_dir()and not root.exists()and out.is_absolute()and not out.exists()
           and out.parent==Path('/opt/host/vnf/austinov')and out.name.startswith('run-bole-task-cpu-')
           and root!=out and not root.is_relative_to(out)and not out.is_relative_to(root),'new distinct source/output leaves')
    C.need(not any(p.is_symlink()for p in(*root.parents,*out.parents)),'ordinary source/output ancestors')
    helpers=N.helper_refs(C,on)
    root.mkdir(mode=0o700)
    for name in(*FILES,'TOKENIZER_SOURCE_EXPECTED.json','DIAGNOSTIC_SOURCE_EXPECTED.json','HE_DIAGNOSTIC_EXPECTED.json','HE_V3_FACTS_FIXTURE.json','HE_DEPENDENCY_SOURCE_EXPECTED.json','HE_DEPENDENCY_ACTUAL_REFS.json'):shutil.copyfile(P/name,root/name)
    native=root/'tokenizer_runtime';native.mkdir();tokenizer_runtime_sources={}
    for n,r in copied.items():
        shutil.copyfile(C.checked(r['host']),native/n);tokenizer_runtime_sources[n]=dict(installed=r['installed'],snapshot=C.ref(native/n))
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
    m=dict(schema='bole.task-finite-CPU-owner-inputs/v5',default_enabled=False,prepared_only=True,
        files={name:C.ref(root/name)for name in FILES},task_packet_root=str(packet_root),
        frozen_packet_manifest_ref=C.ref(packet_root/'PROPOSAL_MANIFEST.json'),
        task_source_unbound_ref=source,output_root=str(out),image_id=C.IMAGE,
        phase_seconds=C.PHASE,cleanup_seconds=C.CLEANUP,CPU=C.CPU,host_CPU=C.HOST_CPU,
        guest_memory_bytes=8*C.GIB,reserve_CPU_budget=2,summed_ancestor_CPU_budget=7,
        phase_order=['cpu-preflight','he-controls','cpu-consumer'],diagnostic_only=False,qualification_profile='full-v012-public-backend-network-isolation-python312/v4',tokenizer_runtime_sources=tokenizer_runtime_sources,helper_refs=helpers,
        task_readset=readset,tokenizer_mounts=tokenizer,HE_guard_fixture_ref=C.ref(root/'HE_V3_FACTS_FIXTURE.json'),**refs,
        model_requests_permitted=False,task_score_permitted=False,generated_code_scope='fixed official HE control snippets only',
        model_ready=False,performance_ready=False,formal_success=False)
    return C.write(root/'OWNER_INPUTS.json',m)


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--prepare',action='store_true')
    for name in('G1-source-ref','G1-owner-ref','G1-bundle-ref','G1-independent-ref','authority-ref','rendered-inputs-ref','main-quiescence-ref','public-probe-owner-ref','HE-diagnostic-owner-ref','HE-diagnostic-independent-ref','HE-dependency-owner-ref','HE-dependency-independent-ref'):p.add_argument('--'+name)
    for name in('packet-root','new-root','output-root'):p.add_argument('--'+name,type=Path)
    p.add_argument('--tokenizer-runtime-copy-ref',action='append')
    a=p.parse_args()
    if not a.prepare:print('{"enabled":false,"container_created":false,"NPU":false}');return 0
    C.need(all(v is not None for v in vars(a).values()),'all exact actual refs and new roots required')
    print(json.dumps(dict(inputs_ref=prepare(a),resources_admitted=False,model_ready=False,NPU=False)));return 0


if __name__=='__main__':raise SystemExit(main())
