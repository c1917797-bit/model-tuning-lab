"""Actual frozen TokenizersBackend decoder in an owned Devices[] runtime.

No weights, chat rendering, model requests, output repair or GPU backend calls.
"""
import argparse
import json
import os
from pathlib import Path
import sys
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import task_contract as C
import postprocess as S


def create(m,rendered):
    C.cpu_runtime()
    assets=rendered['tokenizer_assets'];G=S.gsm_module(m['files']['frozen/gsm_scorer.py'])
    expected=G.BINDING['assets']
    C.need(len(assets)==len(expected)==7 and {Path(r['path']).name for r in assets}==set(expected),
           'all seven original checkpoint decoder files')
    roots=set()
    for reference in assets:
        path=C.checked(reference);roots.add(path.parent)
        C.need(reference['sha256']==expected[path.name]['sha256'],'unchanged original decoder bytes')
    C.need(len(roots)==1 and str(next(iter(roots)))=='/models/Qwen3.6-27B','one frozen tokenizer root')
    # These are the original tokenizer-only environment controls, not module stubs.
    for key,value in dict(USE_TORCH='0',USE_TF='0',USE_FLAX='0',TOKENIZERS_PARALLELISM='false',
        HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1').items():os.environ[key]=value
    import transformers,tokenizers
    C.cpu_runtime()  # CPU Torch utility imports may occur; accelerator modules remain forbidden.
    C.need((transformers.__version__,tokenizers.__version__)==('5.5.4','0.22.2'),
           'same actual frozen decoder versions')
    original=C.obj(m['original_inputs_ref'])
    libraries=[]
    for module in(transformers,tokenizers):
        actual=C.ref(Path(module.__file__).resolve())
        C.need(actual in original['library_refs'],'same actual recorded library source file')
        libraries.append(actual)
    tok=transformers.AutoTokenizer.from_pretrained(str(next(iter(roots))),local_files_only=True,
                                                 trust_remote_code=False,use_fast=True)
    C.need(type(tok).__name__=='TokenizersBackend'and tok.eos_token_id==248046
           and tok.clean_up_tokenization_spaces is False,'same real checkpoint decoder identity')
    C.cpu_runtime()
    return tok,dict(versions=dict(transformers=transformers.__version__,tokenizers=tokenizers.__version__),
        tokenizer_class=type(tok).__module__+'.'+type(tok).__qualname__,eos_token_id=248046,
        clean_up_tokenization_spaces=False,assets=assets,libraries=libraries,
        python_executable=sys.executable,python_version=sys.version,
        weights_loaded=False,same_image_owner_verified=False,NPU=False)


def decode(tok,ids):
    C.need(type(ids)is list and len(ids)<=2048 and all(type(x)is int and 0<=x<248320 for x in ids),
           'exact actual returned completion IDs within normal-EOS cap')
    text=tok.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False)
    C.need(type(text)is str,'actual decoded string')
    return text


def controls(tok):
    values=[]
    for text in('#### 1,200','A','    return 7\n','line one\n  line two\n'):
        ids=tok.encode(text,add_special_tokens=False)
        C.need(type(ids)is list and ids and decode(tok,ids)==text
               and decode(tok,ids+[248046])==text,'actual decoder preserves exact text/indentation and strips EOS')
        values.append(dict(text=text,encoded_ids=ids,text_sha256=S.text_hash(text),
                           exact_roundtrip=True,EOS_strip_only=True,synthetic_control=True))
    C.need(decode(tok,[248046])==decode(tok,[])=='','actual empty/EOS-only decode semantics')
    def actual(text):
        result=decode(tok,tok.encode(text,add_special_tokens=False))
        C.need(result==text,'actual control text exact decoder roundtrip');return result
    gsm=[S.gsm_grade(actual(text),{'answer':gold})['correct']for text,gold in(
        ('#### 1,200','#### 1200'),('1200','#### 1200'),('#### 1.0','#### 1'),
        ('#### 2\n#### 1','#### 1'))]
    mmlu=[S.mmlu_grade(actual(text),gold)['correct']for text,gold in(
        ('A. explanation','A'),('B','A'),('The answer is A','A'),('Answer: D)','D'))]
    prompt='def synthetic_control():\n';body='    return 7\n'
    he=S.human_eval_completion(actual('```python\n'+prompt+body+'\n```'),prompt)
    C.need(gsm==[True,False,False,False]and mmlu==[True,False,False,True]
           and he['completion']==body and he['outer_single_fence_removed']is True
           and he['exact_original_prompt_prefix_removed']is True,'accepted scorer/conversion controls discriminate')
    return dict(schema='bole.actual-decoder-software-controls/v1',controls=values,
        postprocess_controls=dict(GSM_correct_flags=gsm,MMLU_correct_flags=mmlu,HumanEval=he),
        empty_and_EOS_only_decode_verified=True,task_model_output_consumed=False,
        task_score_produced=False,task_ready=False)


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--software-smoke',action='store_true')
    p.add_argument('--source-ref');p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.software_smoke:print('{"enabled":false,"NPU":false,"task_ready":false}');return 0
    C.need(a.source_ref and a.output,'explicit bound decoder source/output')
    sr=json.loads(a.source_ref);m=C.source(sr,seconds=300);C.cpu_runtime()
    C.need(C.ref(__file__)==m['files']['decoder.py'],'exact actual decoder source')
    rendered=C.verify_inputs(m)
    tok,identity=create(m,rendered);result=controls(tok)
    import provenance
    coverage=provenance.run(m,rendered,tok)
    C.current_authority(m['authority_ref'])
    reference=C.write(a.output,dict(source=sr,rendered_inputs_ref=m['rendered_inputs_ref'],
        effective_inputs_ref=m['effective_inputs_ref'],decoder=identity,result=result,coverage=coverage,
        actual_frozen_tokenizer_executed=True,same_image_owner_verified=False,
        model_ready=False,task_ready=False,performance_ready=False))
    print(json.dumps(reference));return 0


if __name__=='__main__':raise SystemExit(main())
