"""Pending actual import preflight gate. Replays its exact pure source in isolation."""
import hashlib
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
POSTRUN_KEYS={'CPU145_prestart_update','binding_ref','create_argv_ref','inherited_lock_ref','inspect_ref',
    'logs_receipt','logs_ref','network_admission_ref','owned_ref','preflight_ref','release_ref','wait_receipt'}
OUTPUT_CAP=2**20


def postrun_refs(owner,read,add,expected):
    """Enumerate only the original E.consume direct post-run file reads.

    Its readset/predecessor helper inputs are already in source_input_before.
    Summary refs, owned.create_receipt and the five admission refs were also in
    the actual26 inventory. cleanup.after_inspect was the one omitted new Ref.
    This fixed schema walks no other path/Ref field and mounts no directory.
    """
    s=owner['summary'];C.need(set(s)==POSTRUN_KEYS,'exact frozen preflight summary/post-run read vocabulary')
    for key in sorted(POSTRUN_KEYS):add(s[key])
    owned=read(s['owned_ref']);add(owned['create_receipt'])
    proof=read(s['network_admission_ref'])
    for key in('binding_ref','namespace_ref','ready_ref','ack_ref','publication_ref'):add(proof[key])
    release=read(s['release_ref'])
    C.need(release['container']==owned['cid']and release['stopped']is True and release['retained']is True
        and release['errors']==[]and release['deleted']is False,'actual post-run cleanup belongs to exact retired probe')
    ref3=add(release['after_inspect'])
    C.need(ref3==expected['after_inspect_ref'],'whole Ref2 cleanup.after_inspect joins exact supplied actual Ref3')
    after=read(ref3);rows=json.loads(after['stdout'])
    C.need(after['exit_code']==0 and after['requested_argv']==['/usr/bin/docker','inspect',owned['cid']]
        and len(rows)==1 and rows[0]['Id']==owned['cid']and rows[0]['Name']=='/'+owned['name']
        and rows[0]['Image']==C.IMAGE and rows[0]['State']['Running']is False and rows[0]['State']['Pid']==0
        and rows[0]['State']['ExitCode']==0 and not rows[0].get('ExecIDs'),
        'actual exact same stopped probe inspect, not a caller-declared retirement')


def output_view(value,*,complete=True):
    raw=value if isinstance(value,bytes)else(value or'').encode()
    return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),
        complete=complete and len(raw)<=OUTPUT_CAP,retained_bytes=min(len(raw),OUTPUT_CAP),
        text=raw[:OUTPUT_CAP].decode('utf-8',errors='replace'))


def replay_reader(command):
    """Preserve actual nested diagnostics, including failure before child START.

    Frozen stdlib-only reader and exact Ref arguments are the entire command.
    Each retained stream is bounded1MiB. Oversize/timeout is an explicit failed
    incomplete capture, never silently labelled complete or a qualification.
    """
    try:r=subprocess.run(command,capture_output=True,text=True,timeout=30)
    except subprocess.TimeoutExpired as error:
        diagnostic=dict(schema='bole.actual-HE-dependency-reader-subprocess/v1',requested_argv=command,
            timeout_seconds=30,timed_out=True,returncode=None,
            stdout=output_view(error.stdout,complete=False),stderr=output_view(error.stderr,complete=False))
        raise ValueError('actual bounded dependency reader timeout '+C.canonical(diagnostic).decode())from error
    diagnostic=dict(schema='bole.actual-HE-dependency-reader-subprocess/v1',requested_argv=command,
        timeout_seconds=30,timed_out=False,returncode=r.returncode,
        stdout=output_view(r.stdout),stderr=output_view(r.stderr))
    detail=C.canonical(diagnostic).decode()
    C.need(r.returncode==0 and diagnostic['stdout']['complete']and diagnostic['stderr']['complete'],
        'actual exact-source independent dependency reader failed; captured nested stdout/stderr '+detail)
    try:return json.loads(r.stdout),diagnostic
    except (ValueError,TypeError)as error:
        raise ValueError('actual dependency reader returned invalid JSON; captured nested stdout/stderr '+detail)from error


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
    post=add(C.ref(P/'HE_DEPENDENCY_POSTRUN_EXPECTED.json'))
    C.need(post['sha256']==C.HE_DEPENDENCY_POSTRUN_SHA,'frozen explicit actual post-run source closure supplement')
    supplement=obj(post)
    C.need(supplement['actual_probe_owner_ref']==actual['RESULT.json'],'exact original successful dependency probe supplement')
    postrun_refs(owner,obj,add,supplement)
    # Fresh stdlib-only process avoids ambient module aliases in either CPU host
    # or Devices[] full decoder child. The source-bound reader has no execution
    # branch here: run_path receives a non-main name and only consume is called.
    code="""import json,runpy,sys
scope=runpy.run_path(sys.argv[1],run_name='_exact_HE_dependency_replay')
value=scope['consume'](json.loads(sys.argv[2]))
assert not {'numpy','tqdm','torch','torch_npu','vllm','vllm_ascend','transformers','triton'} & {n.split('.')[0] for n in sys.modules}
sys.stdout.write(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\\n')
"""
    replay,diagnostic=replay_reader([sys.executable,'-I','-B','-c',code,str(root/'preflight_evidence.py'),C.canonical(owner_ref).decode()])
    C.need(ind==replay and ind['schema']=='bole.independent-HE-dependency-preflight/v1'
        and add(ind['owner_ref'])==add(owner_ref)and ind['inputs_ref']==owner['inputs_ref']
        and all(ind[k]is True for k in('actual_dependency_and_official_module_imports_verified',
            'actual_before_import_network_ACK_verified','inherited_owner_lock_evidence_joined','actual_stopped_retained'))
        and ind['full_software_qualification_accepted']is False and ind['generated_code_executed']is False
        and ind['task_score_produced']is False,'actual saved independent readback must exactly match; captured nested stdout/stderr '+C.canonical(diagnostic).decode())
    for r in refs.values():C.checked(r)
    return list(refs.values())
