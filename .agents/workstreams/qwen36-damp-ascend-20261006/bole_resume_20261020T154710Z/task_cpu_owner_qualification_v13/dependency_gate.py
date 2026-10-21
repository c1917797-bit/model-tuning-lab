"""Pending actual import preflight gate. Replays its exact pure source in isolation."""
import json
from pathlib import Path
import subprocess
import sys
import owner_common as C

P=Path(__file__).resolve().parent
SOURCE_SCHEMA='bole.HE-dependency-preflight-inputs/v1'
FILES={'owner_common.py','owner_namespace.py','he_owned.py','main_quiescence.py','lock_evidence.py','network_evidence.py',
    'he_admission.py','he_policy.py','binding.py','preflight_contract.py','prepare_preflight.py','preflight_host.py',
    'preflight_evidence.py','test_preflight_pure.py'}
DATA={'DEPENDENCY_EXPECTED.json','PREVIOUS_CPU_EXPECTED.json','CPU12_ACTUAL_REFS.json'}
PUBLIC={'he_worker.py','task_contract.py','he_network_guard.py','HE_NETWORK_PROTOCOL.json',
    'network_uapi/if.h','network_uapi/if_arp.h','network_uapi/route.h','network_uapi/ipv6_route.h'}


def readset(owner_ref,independent_ref):
    refs={}
    def add(r):
        a=C.ref(C.checked(r));C.need(a['bytes']<=256*2**20 and Path(a['path']).suffix not in{'.safetensors','.bin','.pth'},
            'bounded source/evidence only; never hash checkpoint weights')
        refs[a['path']]=a;return a
    def obj(r):add(r);return C.obj(r)
    er=add(C.ref(P/'HE_DEPENDENCY_SOURCE_EXPECTED.json'))
    C.need(er['sha256']==C.HE_DEPENDENCY_EXPECTED_SHA,'exact frozen import-preflight advisory source inventory')
    actual_ref=add(C.ref(P/'HE_DEPENDENCY_ACTUAL_REFS.json'))
    C.need(actual_ref['sha256']==C.HE_DEPENDENCY_ACTUAL_SHA,'frozen full actual26 import-preflight primary inventory')
    actual=obj(actual_ref)
    C.need(add(owner_ref)==actual['RESULT.json']and add(independent_ref)==actual['HE_DEPENDENCY_V1_READBACK.json'],
        'exact actual complete import-only preflight and original successful independent reader refs')
    for r in actual.values():add(r)
    e=obj(er);owner=obj(owner_ref);ind=obj(independent_ref);x=obj(owner['inputs_ref'])
    C.need(owner['schema']=='bole.actual-HE-dependency-preflight-owner/v1'and owner['primary']is None and owner['secondary']==[]
        and owner['dependency_preflight_complete']is True and owner['source_input_before']
        and owner['source_input_before']==owner['source_input_after']and owner['private_namespace_restored_by_identity']is True
        and owner['full_software_qualification_accepted']is False and owner['evaluator_called']is False
        and owner['generated_code_executed']is False and owner['task_score_produced']is False
        and x['schema']==SOURCE_SCHEMA and x['image_id']==C.IMAGE and set(x['files'])==FILES and set(x['data_files'])==DATA,
        'actual complete source-equal import-only preflight, never caller success or full qualification')
    root=Path(owner['inputs_ref']['path']).parent
    for name,r in {**x['files'],**x['data_files']}.items():
        a=add(r);want=e['files'][name]
        C.need(Path(a['path'])==root/name and(a['bytes'],a['sha256'])==(want['bytes'],want['sha256'])
            and owner['source_input_before'].get(a['path'])==a['sha256'],'actual byteexact import-preflight source '+name)
    for name in PUBLIC:
        a=add(C.ref(root/name));want=e['files'][name]
        C.need((a['bytes'],a['sha256'])==(want['bytes'],want['sha256'])
            and owner['source_input_before'].get(a['path'])==a['sha256'],'actual original public worker/guard source '+name)
    for path,sha in owner['source_input_before'].items():add(dict(path=path,sha256=sha))
    # Fresh stdlib-only process avoids ambient module aliases in either CPU host
    # or Devices[] full decoder child. The source-bound reader has no execution
    # branch here: run_path receives a non-main name and only consume is called.
    code="""import json,runpy,sys
scope=runpy.run_path(sys.argv[1],run_name='_exact_HE_dependency_replay')
value=scope['consume'](json.loads(sys.argv[2]))
assert not {'numpy','tqdm','torch','torch_npu','vllm','vllm_ascend','transformers','triton'} & {n.split('.')[0] for n in sys.modules}
sys.stdout.write(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\\n')
"""
    r=subprocess.run([sys.executable,'-I','-B','-c',code,str(root/'preflight_evidence.py'),C.canonical(owner_ref).decode()],
        capture_output=True,text=True,timeout=30)
    C.need(r.returncode==0 and len(r.stdout.encode())<=2**20 and len(r.stderr.encode())<=2**20,
        'actual exact-source independent import-preflight replay succeeds in bounded isolated stdlib process')
    replay=json.loads(r.stdout)
    C.need(ind==replay and ind['schema']=='bole.independent-HE-dependency-preflight/v1'
        and add(ind['owner_ref'])==add(owner_ref)and ind['inputs_ref']==owner['inputs_ref']
        and all(ind[k]is True for k in('actual_dependency_and_official_module_imports_verified',
            'actual_before_import_network_ACK_verified','inherited_owner_lock_evidence_joined','actual_stopped_retained'))
        and ind['full_software_qualification_accepted']is False and ind['generated_code_executed']is False
        and ind['task_score_produced']is False,'actual saved independent readback exactly recomputed, never self-asserted import success')
    for r in refs.values():C.checked(r)
    return list(refs.values())
