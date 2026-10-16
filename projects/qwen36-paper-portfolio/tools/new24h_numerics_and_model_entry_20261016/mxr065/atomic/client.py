"""One immutable native bulk completion request, not a benchmark or scheduling proof."""
import argparse,hashlib,json,sys,time,urllib.request
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
from barrier import CUT,need
def payload(model,request_id):
 return dict(model=model,request_id=request_id,prompt=[[1000+j%257 for j in range(n)]for n in (32768,8192)],n=1,stream=False,temperature=0,seed=0,max_tokens=3,min_tokens=3,ignore_eos=True,echo=False,return_token_ids=True)
def main(argv=None):
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--url',default='http://127.0.0.1:8252/v1/completions');p.add_argument('--model',default='qwen36');p.add_argument('--request-id');p.add_argument('--output',type=Path);a=p.parse_args(argv)
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 need(a.url.startswith('http://127.0.0.1:')and a.url.endswith('/v1/completions')and a.request_id.endswith('-packed40960')and a.output.is_absolute()and not a.output.exists(),'owned loopback/single explicit numerical request/new output')
 need(time.time()+910<CUT,'whole original900 second request+cleanup margin')
 body=payload(a.model,a.request_id);wire=json.dumps(body,separators=(',',':')).encode();start=time.monotonic()
 with urllib.request.urlopen(urllib.request.Request(a.url,data=wire,headers={'Content-Type':'application/json'}),timeout=900)as r:raw=r.read(2*1024**2+1)
 need(len(raw)<=2*1024**2,'bounded actual response');value=json.loads(raw)
 choices=value['choices'];need(len(choices)==2 and sorted(c['index']for c in choices)==[0,1],'both true bulk outputs')
 for i,c in enumerate(sorted(choices,key=lambda c:c['index'])):
  need(c['prompt_token_ids']==body['prompt'][i]and len(c['token_ids'])==3 and all(type(t)is int for t in c['token_ids'])and c['finish_reason']=='length','full exact prompt/generated identities')
 need(value['usage']['prompt_tokens']==40960 and value['usage']['completion_tokens']==6,'actual independent output usage, not packed proof')
 with a.output.open('x')as f:json.dump(dict(schema='numeric.bulk-completion-client/v1',request=body,request_sha256=hashlib.sha256(wire).hexdigest(),response=value,elapsed=time.monotonic()-start,actual_packed_verified=False,performance=False),f,sort_keys=True);f.write('\n')
 return 0
if __name__=='__main__':raise SystemExit(main())
