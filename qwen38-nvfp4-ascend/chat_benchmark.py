#!/usr/bin/env python3
"""Switch-decision chat benchmark; raw responses stay in the private artifact root.

Derived from historical v3; v4 metrics must not be pooled with v3 timings.
Never treats role, usage, or finish-only events as a first token.
"""
from __future__ import annotations
import argparse, concurrent.futures, hashlib, json, math, statistics, time, urllib.request
from pathlib import Path

START='<|im_start|>'; END='<|im_end|>'

def percentile(v,q):
    s=sorted(v); p=(len(s)-1)*q; lo=math.floor(p); hi=math.ceil(p)
    return s[lo] if lo==hi else s[lo]*(hi-p)+s[hi]*(p-lo)

def summarize(v):
    if not v: return None
    return {'mean':statistics.fmean(v),'p50':percentile(v,.5),'p95':percentile(v,.95),'p99':percentile(v,.99),'min':min(v),'max':max(v)}

def parse_chatml(prompt:str):
    """Parse rendered ChatML into messages and require a final empty assistant prefix."""
    pos=0; messages=[]; saw_generation=False
    while pos < len(prompt):
        if not prompt.startswith(START,pos):
            raise ValueError(f'expected im_start at offset {pos}')
        role_start=pos+len(START)
        role=None
        for candidate in ('system','user','assistant','tool'):
            if prompt.startswith(candidate,role_start):
                role=candidate; break
        if role is None: raise ValueError('unrecognized ChatML role')
        content_start=role_start+len(role)
        # The frozen dataset omits the conventional newline after some role
        # labels, while model-native templates include it. Accept either form
        # and reconstruct semantic messages rather than copying render syntax.
        if content_start < len(prompt) and prompt[content_start]=='\n':
            content_start+=1
        end=prompt.find(END,content_start)
        if end<0:
            remainder=prompt[content_start:]
            if role!='assistant' or remainder.strip():
                raise ValueError('unterminated non-empty final message')
            saw_generation=True; pos=len(prompt); break
        content=prompt[content_start:end]
        messages.append({'role':role,'content':content})
        pos=end+len(END)
        if pos < len(prompt) and prompt[pos]=='\n': pos+=1
    if not saw_generation: raise ValueError('missing final assistant generation prefix')
    if not messages or messages[-1]['role']!='user':
        raise ValueError('last completed message is not user')
    return messages

def load_dataset(path:Path, limit:int):
    rows=[]
    for idx,line in enumerate(path.open(encoding='utf-8')):
        if not line.strip(): continue
        obj=json.loads(line); q=obj.get('question')
        if not isinstance(q,str) or not q: raise ValueError(f'row {idx} missing question')
        rows.append((len(rows),parse_chatml(q)))
        if limit and len(rows)>=limit: break
    if not rows: raise ValueError('empty dataset')
    return rows

def post_json(url,payload,timeout):
    req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
    return urllib.request.urlopen(req,timeout=timeout)

def token_info(base,model,messages,thinking,timeout):
    payload={'model':model,'messages':messages,'add_generation_prompt':True,'chat_template_kwargs':{'enable_thinking':thinking}}
    with post_json(base.rstrip('/')+'/tokenize',payload,min(timeout,120)) as r: x=json.load(r)
    count=int(x['count']); maxlen=int(x['max_model_len']); remain=maxlen-count
    if remain<=0: raise ValueError(f'prompt does not fit: {count}/{maxlen}')
    return count,maxlen,remain

def request_one(base,model,messages,max_tokens,expected_prompt_tokens,thinking,seed,timeout,cache_salt):
    payload={'model':model,'messages':messages,'temperature':0,'seed':seed,'max_tokens':max_tokens,'stream':True,
             'stream_options':{'include_usage':True},'chat_template_kwargs':{'enable_thinking':thinking},'cache_salt':cache_salt}
    started=time.perf_counter(); first=None; content_parts=[]; reasoning_seen=False; reasoning_chunks=0
    completion_tokens=None; prompt_tokens=None; finish_reason=None; stream_events=[]
    with post_json(base.rstrip('/')+'/v1/chat/completions',payload,timeout) as r:
        for raw in r:
            line=raw.decode('utf-8').strip()
            if not line.startswith('data:'): continue
            data=line[5:].strip()
            if data=='[DONE]': break
            ev=json.loads(data); stream_events.append(ev); usage=ev.get('usage')
            if usage:
                if usage.get('prompt_tokens') is not None: prompt_tokens=int(usage['prompt_tokens'])
                if usage.get('completion_tokens') is not None: completion_tokens=int(usage['completion_tokens'])
            for choice in ev.get('choices',[]):
                delta=choice.get('delta') or {}
                content=delta.get('content')
                reasoning=delta.get('reasoning_content') or delta.get('reasoning')
                if reasoning:
                    reasoning_seen=True; reasoning_chunks+=1
                if first is None and (content or reasoning): first=time.perf_counter()
                if content: content_parts.append(content)
                if choice.get('finish_reason') is not None: finish_reason=str(choice['finish_reason'])
    ended=time.perf_counter()
    if completion_tokens is None or completion_tokens<1: raise RuntimeError('missing positive completion_tokens')
    if prompt_tokens is None: raise RuntimeError('missing prompt_tokens')
    gen_s=ended-first if first is not None else None
    tpot_s=gen_s/(completion_tokens-1) if gen_s is not None and completion_tokens>1 else None
    output=''.join(content_parts)
    return {'prompt_tokens':prompt_tokens,'tokenize_prompt_tokens':expected_prompt_tokens,'prompt_token_match':prompt_tokens==expected_prompt_tokens,
            'completion_tokens':completion_tokens,'finish_reason':finish_reason,'ttft_ms':(first-started)*1000 if first is not None else None,
            'tpot_ms':tpot_s*1000 if tpot_s is not None else None,'e2e_ms':(ended-started)*1000,'reasoning_seen':reasoning_seen,
            'reasoning_chunks':reasoning_chunks,'response_sha256':hashlib.sha256(output.encode()).hexdigest(),
            'response_text':output,'stream_events':stream_events,'messages_sha256':hashlib.sha256(json.dumps(messages,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),
            'output_chars':len(output),'output_nonempty':bool(output),'output_nonwhitespace':bool(output.strip())}

def report_valid(report):
    n = report['requests']
    return (n > 0 and report['errors'] == 0 and report['completed'] == n
            and report['prompt_token_mismatches'] == 0
            and report['reasoning_seen_requests'] == 0
            and report['finish_reasons'] == {'stop': n}
            and report['empty_content_responses'] == 0
            and report['whitespace_only_content_responses'] == 0)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--base-url',required=True); ap.add_argument('--model',required=True)
    ap.add_argument('--dataset',type=Path,required=True); ap.add_argument('--dataset-sha256',required=True); ap.add_argument('--concurrency',type=int,required=True)
    ap.add_argument('--repeat-index',type=int,default=1); ap.add_argument('--seed',type=int,default=1024); ap.add_argument('--limit',type=int,default=0)
    ap.add_argument('--timeout',type=float,default=2400); ap.add_argument('--cache-salt-prefix',required=True); ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--enable-thinking',action='store_true'); ap.add_argument('--max-output-tokens',type=int,default=4096); args=ap.parse_args()
    if args.enable_thinking: raise ValueError('This switch protocol requires thinking disabled')
    if args.max_output_tokens<2 or args.concurrency<1: raise ValueError('Invalid token cap or concurrency')
    actual=hashlib.sha256(args.dataset.read_bytes()).hexdigest()
    if actual!=args.dataset_sha256: raise ValueError(f'dataset SHA mismatch: {actual}')
    items=load_dataset(args.dataset,args.limit)
    token_limits=[]
    for idx,msgs in items:
        count,maxlen,remain=token_info(args.base_url,args.model,msgs,args.enable_thinking,args.timeout)
        token_limits.append((idx,msgs,count,maxlen,min(remain,args.max_output_tokens)))
    # Warmup uses the exact corrected chat path and must natural-stop in no-thinking preflight.
    wi,wmsgs,wcount,wmax,wremain=token_limits[0]
    warm=request_one(args.base_url,args.model,wmsgs,wremain,wcount,args.enable_thinking,args.seed,args.timeout,
                     f'{args.cache_salt_prefix}:warmup')
    if not warm['output_nonwhitespace']: raise RuntimeError('warmup has no usable content')
    if warm['finish_reason']!='stop': raise RuntimeError(f'warmup finish={warm["finish_reason"]}')
    if not warm['prompt_token_match']: raise RuntimeError('warmup /tokenize vs usage prompt token mismatch')
    if not args.enable_thinking and warm['reasoning_seen']: raise RuntimeError('reasoning chunk observed with enable_thinking=false')
    started=time.perf_counter(); results=[]; errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs=[]
        for idx,msgs,count,maxlen,remain in token_limits:
            salt=f'{args.cache_salt_prefix}:c{args.concurrency}:r{args.repeat_index}:request:{idx}'
            futs.append((idx,ex.submit(request_one,args.base_url,args.model,msgs,remain,count,args.enable_thinking,args.seed,args.timeout,salt)))
        for idx,f in futs:
            try:
                row=f.result(); row['request_index']=idx; results.append(row)
            except Exception as e:
                errors.append({'request_index':idx,'type':type(e).__name__,'reason_sha256':hashlib.sha256(str(e).encode()).hexdigest()})
    wall=time.perf_counter()-started; results.sort(key=lambda x:x['request_index'])
    fr={}
    for r in results: fr[r['finish_reason']]=fr.get(r['finish_reason'],0)+1
    comp=sum(r['completion_tokens'] for r in results); prompts=sum(r['prompt_tokens'] for r in results)
    report={'schema':'qwen-switch-chat-natural-eos/v4','max_output_tokens':args.max_output_tokens,
            'tpot_definition':'(stream_end-first_content_or_reasoning)/(usage_completion_tokens-1); undefined for <=1 token',
            'tpot_undefined_requests':sum(r['tpot_ms'] is None for r in results),'endpoint':'/v1/chat/completions','chat_template_kwargs':{'enable_thinking':args.enable_thinking},
            'model':args.model,'dataset_sha256':actual,'requests':len(items),'completed':len(results),'errors':len(errors),'error_types':sorted(set(e['type'] for e in errors)),
            'concurrency':args.concurrency,'repeat_index':args.repeat_index,'seed':args.seed,'natural_eos':True,'cache_salt_prefix':args.cache_salt_prefix,
            'wall_s':wall,'request_throughput':len(results)/wall,'output_token_throughput':comp/wall,'prompt_tokens':prompts,'completion_tokens':comp,
            'finish_reasons':fr,'prompt_token_mismatches':sum(not r['prompt_token_match'] for r in results),
            'reasoning_seen_requests':sum(bool(r['reasoning_seen']) for r in results),
            'empty_content_responses':sum(not r['output_nonempty'] for r in results),
            'whitespace_only_content_responses':sum(r['output_nonempty'] and not r['output_nonwhitespace'] for r in results),
            'output_chars':summarize([r['output_chars'] for r in results]),
            'ttft_ms':summarize([r['ttft_ms'] for r in results if r['ttft_ms'] is not None]),'tpot_ms':summarize([r['tpot_ms'] for r in results if r['tpot_ms'] is not None]),'e2e_ms':summarize([r['e2e_ms'] for r in results]),
            'errors_detail':errors}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    rows_path=args.output.with_suffix('.rows.jsonl')
    with rows_path.open('w',encoding='utf-8') as f:
        for r in results: f.write(json.dumps(r,sort_keys=True)+'\n')
    for path in (args.output,rows_path):
        path.with_suffix(path.suffix+'.sha256').write_text(hashlib.sha256(path.read_bytes()).hexdigest()+'  '+path.name+'\n')
    print(json.dumps(report,sort_keys=True))
    valid=report_valid(report)
    return 0 if valid else 2

if __name__=='__main__': raise SystemExit(main())
