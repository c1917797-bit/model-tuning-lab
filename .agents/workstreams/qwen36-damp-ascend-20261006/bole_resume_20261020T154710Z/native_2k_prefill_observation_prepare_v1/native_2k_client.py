"""One synthetic2048/one-token native observation request; not performance."""
import argparse,json,sys,traceback
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import contract090 as C
def inputs(tokenizer):
 ids=tokenizer.encode('Explain how trees grow. '*1024,add_special_tokens=False)
 C.need(len(ids)>=2048 and all(type(x)is int and 0<=x<tokenizer.vocab_size for x in ids),'actual tokenizer IDs for synthetic2k observation')
 return ids[:2048]
def run(sr,root,tokenizer,open_url=None):
 import urllib.request
 m=C.source(sr)
 C.need(m['performance_arm']=='native_ar'and m.get('native_2k_observation') is not None,'bound native-only observation source')
 C.need(root.is_dir()and not any((root/n).exists()for n in('INPUTS.json','HTTP-native2k.json','HTTP_RESULT.json','HTTP_FAILURE.json')),'fresh client output, no overwrite')
 ids=inputs(tokenizer);header='native-2k-prefill-'+m['native_2k_request_identity']
 C.need(type(m['native_2k_request_identity'])is str and m['native_2k_request_identity'] and len(header)<=160,'bound unique request identity')
 body=dict(model='qwen36-mxr-eager',prompt=ids,max_tokens=1,temperature=0,top_p=1,n=1,stream=False,ignore_eos=True,return_token_ids=True,seed=0)
 C.write(root/'INPUTS.json',dict(source=sr,token_ids=ids,input_tokens=2048,synthetic=True,screening_only=True))
 request=urllib.request.Request('http://127.0.0.1:8230/v1/completions',data=json.dumps(body).encode(),headers={'Content-Type':'application/json','X-Request-Id':header})
 try:
  with (urllib.request.urlopen if open_url is None else open_url)(request,timeout=2400)as response:
   wire=response.read(8*2**20+1);status=response.status
  C.need(len(wire)<=8*2**20 and status==200,'bounded actual native HTTP success')
  with(root/'HTTP-native2k.json').open('xb')as f:f.write(wire)
  value=json.loads(wire);choices=value.get('choices')
  C.need(value.get('id')=='cmpl-'+header and type(choices)is list and len(choices)==1 and choices[0].get('index')==0,'actual native HTTP identity')
  tokens=choices[0].get('token_ids')
  C.need(type(tokens)is list and len(tokens)==1 and type(tokens[0])is int and tokens[0]>=0 and value['usage']['prompt_tokens']==2048 and value['usage']['completion_tokens']==1,'one native output and exact2k usage')
  result=dict(schema='native.2k-prefill-http/v1',source=sr,header=header,request=body,response=C.ref(root/'HTTP-native2k.json'),status=status,
   numerical_qualified=False,formal_performance=False,task_accuracy=False)
  C.write(root/'HTTP_RESULT.json',result);return result
 except BaseException as exc:
  C.write(root/'HTTP_FAILURE.json',dict(source=sr,primary=repr(exc),traceback=traceback.format_exc()));raise
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 from transformers import AutoTokenizer
 run(json.loads(a.source_ref),a.output,AutoTokenizer.from_pretrained('/models/Qwen3.6-27B',trust_remote_code=True,local_files_only=True));return 0
if __name__=='__main__':raise SystemExit(main())
