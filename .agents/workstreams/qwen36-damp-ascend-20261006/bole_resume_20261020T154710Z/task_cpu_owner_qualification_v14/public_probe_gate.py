"""Read-only prerequisite: actual frozen v8 public diagnostic, never qualification.
No library imports, process execution, device operations or source/output mutation.
"""
import argparse
import json
from pathlib import Path
import sys
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import owner_common as C


def successful(owner,x,report,terminal,binding,release):
    C.need(owner['schema']=='bole.actual-finite-task-CPU-owner/v2'and owner['primary']is None
           and owner['secondary']==[]and owner['diagnostic_only']is True and owner['tokenizer_probe']=='public-backend'
           and owner['tokenizer_import_diagnostic_completed']is True
           and owner['source_image_CPU_owner_software_controls_verified']is False
           and owner['private_namespace_restored_by_identity']is True
           and owner['source_input_before']and owner['source_input_before']==owner['source_input_after'],
           'actual source-stable completed public diagnostic; never a full qualification flag')
    C.need(x['schema']=='bole.task-finite-CPU-owner-inputs/v2'and x['default_enabled']is False
           and x['diagnostic_only']is True and x['tokenizer_probe']=='public-backend'
           and x['phase_order']==['cpu-preflight']and x['image_id']==C.IMAGE
           and x['CPU']==145 and x['host_CPU']==166 and x['guest_memory_bytes']==8*C.GIB
           and x['reserve_CPU_budget']==2 and x['summed_ancestor_CPU_budget']==7,
           'same immutable image and original bounded diagnostic CPU profile')
    p=report['payload']
    C.need(report['schema']=='bole.actual-task-CPU-child/v1'and report['mode']=='import-probe'
           and report['diagnostic_only']is True and report['readset_before']==report['readset_after']
           and report['source_image_CPU_owner_software_controls_verified']is False
           and report['NPU']is False and report['model_executed']is False and report['HTTP_executed']is False,
           'actual stable diagnostic child evidence without model requests')
    C.need(p['schema']=='bole.actual-tokenizer-public-factory-diagnostic/v1'and p['entry']=='public-backend'
           and p['outcome']=='public-factory-and-original-tiny-controls-completed'and p['error']is None
           and p['forbidden_attempts']==[]and p['tokenizer_constructed']is True
           and p['diagnostic_only']is True and p['software_qualification_accepted']is False
           and p['all15525_provenance_executed']is False and p['task_score_produced']is False,
           'real public factory completed without forbidden attempt; tiny controls are not full provenance')
    identity=p['identity'];controls=p['tiny_original_decoder_controls']
    C.need(identity['public_factory']=='TokenizersBackend.from_pretrained'
           and identity['versions']==dict(transformers='5.5.4',tokenizers='0.22.2')
           and identity['tokenizer_class']=='transformers.tokenization_utils_tokenizers.TokenizersBackend'
           and identity['eos_token_id']==248046 and identity['clean_up_tokenization_spaces']is False
           and identity['decoder_semantic_equivalence_not_yet_qualified']is True
           and controls['schema']=='bole.actual-decoder-software-controls/v1'
           and controls['empty_and_EOS_only_decode_verified']is True
           and controls['task_score_produced']is False and controls['task_ready']is False,
           'actual original class/assets/version/EOS/tiny controls; full equivalence pending')
    before=report['process_before'];after=report['process_after']
    C.need(terminal['exit_code']==0 and release['stopped']is True and release['retained']is True and release['errors']==[]
           and binding['uid']==0 and binding['Devices']==[]
           and binding['cpu']['effective_cpus']==[145]and binding['cpu']['effective_capacity']==1
           and binding['memory']['effective_bytes']==8*C.GIB
           and binding['guest_pid']==before['pid']==after['pid']
           and binding['start_ticks']==before['start_ticks']==after['start_ticks']
           and before['affinity']==after['affinity']==[145]and before['uid']==before['euid']==after['uid']==after['euid']==0,
           'actual finite exit0/live CPU145 identity and stopped retained cleanup')
    return True


def audit(reference,source_ref):
    path=C.checked(reference);C.need(path.stat().st_size<=4*2**20,'bounded actual prerequisite audit')
    rows=[]
    with path.open('rb')as f:
        for line in f:
            C.need(len(line)<=65536 and len(rows)<256,'bounded original audit line/count')
            v=json.loads(line)
            C.need(v['schema']=='bole.actual-tokenizer-import-audit-event/v1'and v['ordinal']==len(rows),
                   'complete actual audit ordinal/schema')
            C.need(v['event']in{'entry','import-attempt','closed'},'no denied forbidden import in prerequisite')
            if v['event']=='import-attempt':C.need(v['payload']['module'].split('.')[0]not in{'torch_npu','vllm','vllm_ascend','triton'},'zero actual forbidden import attempts')
            rows.append(v)
    C.need(len(rows)>=2 and rows[0]['event']=='entry'and rows[0]['payload']['source_ref']==source_ref
           and rows[-1]['event']=='closed'and rows[-1]['payload']['forbidden_attempts']==[]
           and rows[-1]['payload']['software_qualification_accepted']is False,
           'closed real audit joined to exact diagnostic source; no audit-to-qualification promotion')


def readset(reference,*,rendered_inputs_ref):
    er=C.ref(C.P/'DIAGNOSTIC_SOURCE_EXPECTED.json')
    C.need(er['sha256']==C.DIAGNOSTIC_EXPECTED_SHA,'exact frozen prerequisite source inventory')
    expected=C.obj(er);refs={}
    def add(r):
        p=C.checked(r);actual=C.ref(p);refs[actual['path']]=actual;return actual
    def obj(r):add(r);return C.obj(r)
    owner=obj(reference);ir=owner['inputs_ref'];x=obj(ir)
    C.need(x['rendered_inputs_ref']==rendered_inputs_ref and owner['summary'].keys()=={'CPU','CPU_release'},
           'same frozen rendered input header and exact one-stage diagnostic')
    manifest=obj(x['frozen_packet_manifest_ref'])
    C.need(x['frozen_packet_manifest_ref']['sha256']==C.LEGACY_PACKET_SHA==expected['frozen_v1_packet_manifest_sha256'],
           'whole original v1 diagnostic packet')
    root=Path(x['task_packet_root']);C.need(root.is_absolute(),'exact original diagnostic packet root')
    for name,row in manifest['files'].items():add(dict(row,path=str(root/name)))
    files=x['files'];want={n for n in expected['files']if n.endswith('.py')}
    C.need(set(files)==want,'whole exact frozen v8 executable diagnostic closure')
    for n,r in files.items():
        a=add(r);w=expected['files'][n]
        C.need((a['bytes'],a['sha256'])==(w['bytes'],w['sha256'])
               and owner['source_input_before'].get(a['path'])==a['sha256'],
               'actual v8 exact code before/after '+n)
    inventory=add(dict(path=str(Path(ir['path']).parent/'TOKENIZER_SOURCE_EXPECTED.json'),**expected['files']['TOKENIZER_SOURCE_EXPECTED.json']))
    actual_native=obj(inventory)
    C.need(set(x['tokenizer_runtime_sources'])==set(actual_native),'all seven actual diagnostic sources')
    for n,entry in x['tokenizer_runtime_sources'].items():
        a=add(entry['snapshot']);w=actual_native[n]
        C.need(entry['installed']==w and(a['bytes'],a['sha256'])==(w['bytes'],w['sha256']),
               'exact original same-image native source snapshot '+n)
    for r in x['tokenizer_runtime_copy_refs']:add(r)
    for r in x['helper_refs']:add(r)
    source=obj(x['task_source_unbound_ref'])
    C.need(source['schema']=='bole.three-task-decoder-scorer/source/v1'and source['image_id']==C.IMAGE
           and source['root']==str(root)and source['rendered_inputs_ref']==rendered_inputs_ref,
           'actual unchanged v1 task source only for diagnostic identity')
    C.need(source['authority_ref']==x['authority_ref']and owner['source_input_before'].get(x['task_source_unbound_ref']['path'])==x['task_source_unbound_ref']['sha256'],
           'exact original diagnostic authority/source before and after')
    for name,r in source['files'].items():
        a=add(r);w=manifest['files'][name]
        C.need(a==dict(w,path=str(root/name))and owner['source_input_before'].get(a['path'])==a['sha256'],
               'whole original diagnostic task executable/header source '+name)
    for r in(source['original_inputs_ref'],source['authority_ref'],x['main_quiescence_ref']):add(r)
    cpu=owner['summary']['CPU'];report=obj(cpu['report']);terminal=obj(cpu['terminal']);binding=obj(cpu['binding']);release=obj(owner['summary']['CPU_release'])
    C.need(report['inputs_ref']==ir and terminal['process_binding']==cpu['binding'],
           'actual child/terminal/owner strong source and live-binding joins')
    successful(owner,x,report,terminal,binding,release)
    before=report['process_before'];entry=obj(report['start_ref'])
    C.need(entry['pid']==before['pid']and entry['start_ticks']==before['start_ticks'], 'real child initial lifetime')
    for r in(terminal['stdout'],terminal['stderr'],cpu['inspect_ref']):add(r)
    p=report['payload'];add(p['import_audit_ref']);audit(p['import_audit_ref'],x['task_source_unbound_ref'])
    original=obj(source['original_inputs_ref']);rendered=obj(rendered_inputs_ref)
    C.need(rendered['original_inputs_ref']==source['original_inputs_ref'],'same exact original input provenance header')
    libraries=[r for r in original['library_refs']if Path(r['path']).parent.name in{'transformers','tokenizers'}]
    C.need(len(libraries)==2 and p['identity']['assets']==rendered['tokenizer_assets']and p['identity']['libraries']==libraries,
           'actual public identity uses all original tokenizer assets/library refs')
    for r in libraries:C.need(report['readset_before'].get(r['path'])==r['sha256'],'actual child before/after installed library identity')
    # Tokenizer assets use original guest paths; new full owner maps/verifies the
    # same hashes on host and reopens actual guest bytes. No weight file is read.
    add(er)
    return list(refs.values())


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--verify',action='store_true')
    p.add_argument('--owner-ref');p.add_argument('--rendered-inputs-ref');a=p.parse_args()
    if not a.verify:print('{"enabled":false,"NPU":false,"software_qualification_accepted":false}');return 0
    C.need(a.owner_ref and a.rendered_inputs_ref,'explicit completed actual public probe and original rendered header')
    refs=readset(json.loads(a.owner_ref),rendered_inputs_ref=json.loads(a.rendered_inputs_ref))
    print(json.dumps(dict(public_factory_prerequisite_pass=True,readset_count=len(refs),full_qualification_accepted=False,NPU=False)));return 0


if __name__=='__main__':main()
