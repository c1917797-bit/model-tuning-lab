"""Two sequential two-output-token requests and one native retirement barrier."""
import argparse,json,sys,time,urllib.request,traceback
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import sourceio as C
import g1_contract as G1


def inputs(tokenizer):
 ids=tokenizer.encode('Explain how trees grow. '*256,add_special_tokens=False)
 C.need(len(ids)>=131 and all(type(x)is int and 0<=x<tokenizer.vocab_size for x in ids), 'actual tokenizer IDs, not string lengths')
 return ids[:131]


def run(sr,root,tokenizer,open_url=urllib.request.urlopen):
 m=C.obj(sr);C.need(m['prepared_only']is False and m['service_experiment']==G1.SCOPE,'actual bound G1 source')
 ids=inputs(tokenizer);C.write(root/'INPUTS.json',dict(source=sr,token_ids=ids,input_tokens=131,tokenizer='/models/Qwen3.6-27B',data_generated_by_actual_tokenizer=True))
 rows=[]
 for label,count in(('tree-1',2),('tree-2',2),('retirement-barrier',1)):
  header='bole-g1-131-'+label
  body=dict(model='qwen36-mxr-eager',prompt=ids,max_tokens=count,temperature=0,top_p=1,n=1,stream=False,ignore_eos=True,return_token_ids=True)
  request=urllib.request.Request('http://127.0.0.1:8230/v1/completions',data=json.dumps(body).encode(),headers={'Content-Type':'application/json','X-Request-Id':header})
  start=time.monotonic()
  try:
   with open_url(request,timeout=600)as response:wire=response.read(8*2**20+1);status=response.status
   C.need(len(wire)<=8*2**20,'bounded actual HTTP wire')
   path=root/('HTTP-'+label+'.json');path.write_bytes(wire)
   value=json.loads(wire);row=dict(label=label,header=header,request=body,response=C.ref(path),http_status=status,elapsed=time.monotonic()-start)
   rows.append(row);C.need(status==200 and 'error'not in value and value['id']=='cmpl-'+header,'actual completion response/header identity')
   C.need(type(value['choices'][0].get('token_ids'))is list and len(value['choices'][0]['token_ids'])==count and all(type(x)is int and x>=0 for x in value['choices'][0]['token_ids']), 'actual returned generated token IDs, no tokenization roundtrip')
   C.need(value['usage']['prompt_tokens']==131 and value['usage']['completion_tokens']==count and len(value['choices'])==1,'actual full diagnostic tokens; not performance/task')
  except BaseException as e:
   C.write(root/'HTTP-FAILURE.json',dict(source=sr,rows=rows,primary=repr(e),traceback=traceback.format_exc()));raise
 result=dict(schema=G1.HTTP_SCHEMA,source=sr,rows=rows,whole_model_qualified=False,scheduler_committed=False)
 C.write(root/'HTTP_RESULT.json',result);return result


def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 from transformers import AutoTokenizer
 run(json.loads(a.source_ref),a.output,AutoTokenizer.from_pretrained('/models/Qwen3.6-27B',trust_remote_code=True,local_files_only=True));return 0


if __name__=='__main__':raise SystemExit(main())
