#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math, statistics, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

def pct(xs,p):
    if not xs: return None
    xs=sorted(xs); pos=(len(xs)-1)*p; lo=math.floor(pos); hi=math.ceil(pos)
    return xs[lo] if lo==hi else xs[lo]*(hi-pos)+xs[hi]*(pos-lo)

def metric(xs):
    return {'mean':statistics.fmean(xs),'p50':pct(xs,.5),'p95':pct(xs,.95),'p99':pct(xs,.99)} if xs else {}

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def token_info(base,model,q,timeout):
    body={'model':model,'prompt':q}
    req=urllib.request.Request(base.rstrip('/')+'/tokenize',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=timeout) as r:
        o=json.load(r)
    return int(o['count']), int(o['max_model_len'])

def one(base,model,i,q,timeout,max_tokens):
    body={'model':model,'prompt':q,'temperature':0,'max_tokens':max_tokens,'stream':True,'stream_options':{'include_usage':True}}
    req=urllib.request.Request(base.rstrip('/')+'/v1/completions',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='POST')
    t0=time.perf_counter(); first=None; usage={}; err=None; finish_reason=None
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            for raw in r:
                line=raw.decode('utf-8','replace').strip()
                if not line.startswith('data:'): continue
                payload=line[5:].strip()
                if payload=='[DONE]': break
                o=json.loads(payload)
                if o.get('usage'): usage=o['usage']
                for c in o.get('choices') or []:
                    if c.get('text') and first is None: first=time.perf_counter()
                    if c.get('finish_reason') is not None: finish_reason=c.get('finish_reason')
    except Exception as e:
        err=f'{type(e).__name__}: {e}'
    t1=time.perf_counter()
    return {'id':i,'ttft_ms':(first-t0)*1000 if first else None,'e2e_ms':(t1-t0)*1000,'usage':usage,'finish_reason':finish_reason,'error':err}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data',required=True); ap.add_argument('--base-url',default='http://127.0.0.1:8210'); ap.add_argument('--model',default='qwen38'); ap.add_argument('--concurrency',type=int,required=True); ap.add_argument('--output',required=True); ap.add_argument('--timeout',type=float,default=3600)
    a=ap.parse_args(); rows=[json.loads(x) for x in Path(a.data).read_text().splitlines() if x.strip()]; qs=[str(r['question']) for r in rows]
    if len(qs)!=357 or any(not q.strip() for q in qs): raise RuntimeError(f'bad dataset rows={len(qs)}')
    # Resolve every prompt's real model-context allowance before the measured window.
    limits=[]
    for q in qs:
        count,max_model_len=token_info(a.base_url,a.model,q,min(a.timeout,120))
        limits.append((count,max_model_len-count))
    if any(limit <= 0 for _,limit in limits): raise RuntimeError('prompt exceeds model context')
    warm=one(a.base_url,a.model,-1,qs[0],a.timeout,limits[0][1])
    if warm['error']: raise RuntimeError('warmup failed: '+warm['error'])
    rec=[]; t0=time.perf_counter()
    with ThreadPoolExecutor(max_workers=a.concurrency) as ex:
        fs=[ex.submit(one,a.base_url,a.model,i,q,a.timeout,limits[i][1]) for i,q in enumerate(qs)]
        for n,f in enumerate(as_completed(fs),1):
            rec.append(f.result())
            if n%50==0: print(f'completed {n}/{len(qs)}',flush=True)
    wall=time.perf_counter()-t0; rec.sort(key=lambda x:x['id']); good=[r for r in rec if not r['error']]
    tt=[r['ttft_ms'] for r in good if r['ttft_ms'] is not None]; ee=[r['e2e_ms'] for r in good]
    pin=sum(r['usage'].get('prompt_tokens',0) for r in good); pout=sum(r['usage'].get('completion_tokens',0) for r in good)
    prompts=[r['usage'].get('prompt_tokens') for r in good if r['usage'].get('prompt_tokens') is not None]
    completions=[r['usage'].get('completion_tokens') for r in good if r['usage'].get('completion_tokens') is not None]
    finish_reasons={}
    for r in rec:
        k=str(r.get('finish_reason'))
        finish_reasons[k]=finish_reasons.get(k,0)+1
    s={'requests':len(rec),'completed':len(good),'errors':len(rec)-len(good),'wall_s':wall,'requests_per_s':len(good)/wall,'input_tokens':pin,'output_tokens':pout,'input_tokens_per_s':pin/wall,'output_tokens_per_s':pout/wall,'total_tokens_per_s':(pin+pout)/wall,'prompt_tokens':metric(prompts),'completion_tokens':metric(completions),'finish_reasons':finish_reasons,'ttft_ms':metric(tt),'e2e_ms':metric(ee)}
    out={'schema':'qwen38-query-rewrite-perf/v3','dataset':a.data,'dataset_sha256':sha256(a.data),'concurrency':a.concurrency,'generation':{'temperature':0,'natural_eos':True,'max_tokens':'per-request model context remainder'},'pretokenized_prompt_tokens':metric([x[0] for x in limits]),'summary':s,'records':rec}
    Path(a.output).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(s,indent=2,sort_keys=True)); return 1 if s['errors'] else 0
if __name__=='__main__': raise SystemExit(main())
