"""Freeze new code/authority, then explicitly bind actual restored v012 inputs. OFF."""
import argparse
import json
from pathlib import Path
import sys
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import task_contract as C


def prepare(authority_ref,rendered_ref,image_id,output):
    C.current_authority(authority_ref,300)
    C.need(type(image_id)is str and image_id.startswith('sha256:')and len(image_id)==71,'exact observed same-image ID')
    base=C.obj(rendered_ref);original=C.obj(base['original_inputs_ref'])
    refs=dict(rendered_inputs_ref=rendered_ref,original_inputs_ref=base['original_inputs_ref'],renderer_ref=base['producer_ref'],
        official_source_ref=original['source_ref'],human_eval_package_ref=original['human_eval_package_ref'])
    for key,(size,sha)in C.FROZEN.items():
        reference=refs[key];C.checked(reference)
        C.need((reference['bytes'],reference['sha256'])==(size,sha),'whole immutable old primary artifact '+key)
    files={str(p.relative_to(P)):C.ref(p)for p in sorted(P.rglob('*.py'))if '__pycache__'not in p.parts}
    files['PROTOCOL.json']=C.ref(P/'PROTOCOL.json')
    for path in sorted((P/'fixtures').glob('*.json')):files[str(path.relative_to(P))]=C.ref(path)
    C.need(set(files)>={'task_contract.py','prepare_packet.py','decoder.py','provenance.py','postprocess.py',
        'score_tokens.py','request_plan.py','compare_components.py','consume_results.py','he_policy.py','he_worker.py','stage_he.py','restore_GSM_inputs.py',
        'frozen/gsm_scorer.py','frozen/inputs004.py','frozen/content_contract.py'},'complete executable frozen source closure')
    value=dict(schema='bole.three-task-decoder-scorer/source/v1',root=str(P),prepared_only=True,default_enabled=False,
        authority_ref=authority_ref,image_id=image_id,files=files,**refs,
        tasks=C.COUNTS,smoke_ids=C.SMOKE,protocol=C.PROTOCOL,task_protocols=C.TASK_PROTOCOLS,
        generation=dict(max_tokens=2048,ignore_eos=False,thinking_enabled=False,temperature=0,seed=0),
        minimum_model_context_tokens=5199,effective_inputs_ref=None,input_preparation_source_ref=None,
        postprocess_protocol='bole.three-task-postprocess/prospective-v1',
        rules_frozen_before_task_model_outputs=True,model_ready=False,task_ready=False,formal_accuracy_accepted=False)
    reference=C.write(output,value);C.source(reference,allow_unbound_inputs=True);return reference


def bind(source_ref,effective_ref,output):
    m=C.source(source_ref,allow_unbound_inputs=True)
    C.need(m['effective_inputs_ref']is None and m['input_preparation_source_ref']is None,'one immutable unbound preparation source')
    result=dict(m,effective_inputs_ref=effective_ref,input_preparation_source_ref=source_ref)
    C.verify_inputs(result);return C.write(output,result)


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);g=p.add_mutually_exclusive_group()
    g.add_argument('--prepare',action='store_true');g.add_argument('--bind-inputs',action='store_true')
    for name in('authority-ref','rendered-inputs-ref','source-ref','effective-inputs-ref','image-id'):p.add_argument('--'+name)
    p.add_argument('--output',type=Path);a=p.parse_args()
    if not(a.prepare or a.bind_inputs):print('{"enabled":false,"task_ready":false}');return 0
    C.need(a.output,'explicit new output')
    if a.prepare:
        C.need(a.authority_ref and a.rendered_inputs_ref and a.image_id,'fresh authority, exact old rendered Ref, same-image ID')
        result=prepare(json.loads(a.authority_ref),json.loads(a.rendered_inputs_ref),a.image_id,a.output)
    else:
        C.need(a.source_ref and a.effective_inputs_ref,'explicit prepared source and actual restored input refs')
        result=bind(json.loads(a.source_ref),json.loads(a.effective_inputs_ref),a.output)
    print(json.dumps(result));return 0


if __name__=='__main__':raise SystemExit(main())
