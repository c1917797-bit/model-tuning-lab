"""Exact current HYPIC-protocol32k input generator; no HYPIC routing or execution."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

GENERATOR=dict(path="/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bole2k_runtime_complete_prepare_v3/prepared-source-short8-qualifier/benchmark_shared_prefix.py",bytes=49810,
 sha256='cba2b1b463a1e436c818722d92147d93f8396b8d64f8da6582d7e67d2cb45822')
INPUT=32768
SHARED=16384
POOL=42


def need(v,s):
    if not v:raise ValueError(s)


def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def checked(r):
    p=Path(r['path']);b=p.read_bytes()
    need(p.is_file()and not any(x.is_symlink()for x in(p,*p.parents))and
         dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())==r,'exact current prompt generator')
    return b


def generator():
    b=checked(GENERATOR);name='_bole_current_hypic32k_generator'
    spec=importlib.util.spec_from_file_location(name,GENERATOR['path'])
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m
    try:exec(compile(b,GENERATOR['path'],'exec'),m.__dict__)
    except BaseException:sys.modules.pop(name,None);raise
    return m


def dataset(tokenizer):
    # Reuse _build_prompts and _tokens_at_least EXACTLY. Only the tokenizer
    # endpoint is replaced by the same local checkpoint tokenizer API.
    donor=generator();original=donor._tokenize
    def local(base_url,model,text,timeout):
        ids=tokenizer.encode(text,add_special_tokens=False)
        need(type(ids)is list and ids and all(type(x)is int and 0<=x<tokenizer.vocab_size for x in ids),
             'actual checkpoint tokenizer IDs, no bool/padding/text-length substitution')
        return ids
    donor._tokenize=local
    try:
        prompts=donor._build_prompts(SimpleNamespace(base_url='local-checkpoint-tokenizer',model='Qwen3.6-27B',
            prefix_tokens=SHARED,input_tokens=INPUT,requests=40,warmup_requests=2,timeout=2400))
    finally:donor._tokenize=original;sys.modules.pop(donor.__name__,None)
    value=dict(schema='bole.current-hypic-protocol32k-input/v1',generator=GENERATOR,
        input_tokens=INPUT,shared_prefix_tokens=SHARED,segment_ends=[SHARED,INPUT],
        prompt_cases=prompts,historical_prompt_bytes_identical=False,
        historical_40_C16_reference_only=True,current_concurrency=1,
        HYPIC_enabled=False,formal_output_tokens=1024)
    validate(value)
    return value


def validate(v):
    need(type(v)is dict and v['schema']=='bole.current-hypic-protocol32k-input/v1'and
         v['generator']==GENERATOR and v['input_tokens']==INPUT and v['shared_prefix_tokens']==SHARED and
         v['segment_ends']==[SHARED,INPUT]and v['current_concurrency']==1 and
         v['HYPIC_enabled']is False and v['formal_output_tokens']==1024,'one explicit32k/16k/C1 input protocol')
    rows=v['prompt_cases']
    need(type(rows)is list and len(rows)==POOL,'same current42-case generator pool')
    need(all(type(r)is list and len(r)==INPUT and all(type(x)is int and x>=0 for x in r)for r in rows),
         'all actual32768-token cases')
    prefix=rows[0][:SHARED]
    need(all(r[:SHARED]==prefix for r in rows),'all first16384 tokens identical')
    need(len({hashlib.sha256(canonical(r[SHARED:])).hexdigest()for r in rows})==POOL,
         'all generated request suffixes remain distinct')
    need(len(canonical(v))<=64*2**20,'bounded whole input packet')
    return v


def select(v,role):
    validate(v);need(role in('warmup','measured','retirement-barrier'),'explicit C1 role')
    # Same source pool as historical protocol; actual bytes are frozen anew.
    return list(v['prompt_cases'][{'warmup':0,'measured':2,'retirement-barrier':1}[role]])


def output(mode):
    need(mode in('smoke8','intermediate160','formal1024'),'typed output stage')
    return {'smoke8':8,'intermediate160':160,'formal1024':1024}[mode]


def demand(output_tokens):
    need(type(output_tokens)is int and output_tokens in(8,160,1024),'explicit8/160/1024')
    last=INPUT+output_tokens-2
    return dict(prefix=INPUT,max_before=last,publication_pages=(last+2+127)//128,
        private_pages=(last+3+127)//128,native_allocation_observed=False,
        full_before_FA_minimum_bytes=16*2*((INPUT+127)//128)*128*256*2,
        frame_cap_bytes=384*2**20,whole_frame_capture_fits=False)
