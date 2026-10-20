"""Explicit v012 input repair: reuse correct old GSM IDs, never re-render HE/MMLU."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import task_contract as C


def run(source_ref,output):
    m=C.source(source_ref,seconds=300,allow_unbound_inputs=True);C.cpu_runtime()
    C.need(C.ref(__file__)==m['files']['restore_GSM_inputs.py']and output.is_absolute()
           and not output.exists()and output.parent.is_dir(),'new owned explicit input-restoration leaf')
    base=C.verify_base_inputs(m);original=C.obj(m['original_inputs_ref'])
    a=C.obj(original['tasks']['GSM8K']['rows_ref']);b=C.obj(base['tasks']['GSM8K']['rows_ref'])
    C.need(len(a)==len(b)==1319,'complete original and011 GSM before new publication')
    rows=[];chain=hashlib.sha256()
    for original_row,old in zip(a,b):
        value=C.restored_gsm_row(original_row,old);rows.append(value)
        chain.update(bytes.fromhex(C.digest(value)))
    output.mkdir(mode=0o700)
    tasks=dict(base['tasks'])
    tasks['GSM8K']=dict(rows_ref=C.write(output/'GSM8K.rows.json',rows),count=len(rows),
        max_prompt_tokens=max(len(r['prompt_token_ids'])for r in rows),ordered_row_hash_chain=chain.hexdigest())
    result=dict(schema='bole.three-task-effective-inputs/v012',source=source_ref,
        authority_ref=m['authority_ref'],protocol=C.PROTOCOL,task_protocols=C.TASK_PROTOCOLS,
        base_rendered_inputs_ref=m['rendered_inputs_ref'],original_inputs_ref=m['original_inputs_ref'],
        tasks=tasks,smoke_ids=C.SMOKE,tokenizer_assets=base['tokenizer_assets'],
        GSM_format_instruction_token_ids=C.INSTRUCTION_IDS,GSM_original_token_ids_reused=True,
        GSM_tokenization_repeated=False,HE_MMLU_rerendered=False,thinking_enabled=False,
        minimum_model_context_tokens=max(x['max_prompt_tokens']for x in tasks.values())+2048,
        actual_decoder_text_verification_pending=True,model_output_consumed=False,
        model_ready=False,task_ready=False,NPU=False)
    C.current_authority(m['authority_ref'])
    return C.write(output/'EFFECTIVE_INPUTS.json',result)


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
    p.add_argument('--source-ref');p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false,"task_ready":false}');return 0
    C.need(a.source_ref and a.output,'explicit source and new output')
    print(json.dumps(run(json.loads(a.source_ref),a.output)));return 0


if __name__=='__main__':raise SystemExit(main())
