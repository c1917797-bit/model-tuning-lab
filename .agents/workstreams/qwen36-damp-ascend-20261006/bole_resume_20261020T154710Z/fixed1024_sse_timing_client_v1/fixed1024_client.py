"""Fixed131/input1024-output SSE observer. Public execute is hard disabled.

No HTTP opener exists here. MAIN later supplies a separately qualified owner
and an already-open response; controlled local tests use an in-memory response.
"""
import argparse,hashlib,json,os,re,time
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from evidence import need,strict_json,ref,exclusive_json
MODEL='qwen36-mxr-eager';OUTPUT=1024;INPUT=131;WIRE_CAP=8*2**20;JOURNAL_CAP=8*2**20;READ_SIZE=65536
INPUT_RECIPE=dict(text='Explain how trees grow. '*256,add_special_tokens=False,take_first_tokens=131,tokenizer='/models/Qwen3.6-27B',actual_tokenizer_required=True)
LIVE_EXECUTION_ENABLED=False

def fixed_request(ids):
 need(type(ids)is list and len(ids)==131 and all(type(x)is int and x>=0 for x in ids),'actual131 tokenizer IDs required by future owner')
 return dict(model=MODEL,prompt=list(ids),max_tokens=1024,temperature=0,top_p=1,n=1,stream=True,ignore_eos=True,return_token_ids=True,echo=False,stream_options=dict(include_usage=True))

class Observer:
 def __init__(self):self.partial=b'';self.lines=[];self.offset=0;self.events=[];self.tokens=[];self.token_times=[];self.done=False
 def feed(self,data,received_ns):
  self.partial+=data
  while b'\n'in self.partial:
   line,self.partial=self.partial.split(b'\n',1);self.offset+=len(line)+1
   if line.endswith(b'\r'):line=line[:-1]
   if line:
    if not line.startswith(b':'):self.lines.append(line)
   else:
    if not self.lines:continue
    need(all(x.startswith(b'data:')for x in self.lines),'actual completion SSE data fields only')
    payload=b'\n'.join(x[5:].removeprefix(b' ')for x in self.lines);self.lines=[]
    need(not self.done,'no event after DONE')
    if payload==b'[DONE]':self.done=True;ids=[];kind='done'
    else:
     v=strict_json(payload);need(type(v)is dict and 'error'not in v,'valid actual completion chunk')
     ids=[]
     for choice in v.get('choices',[]):
      need(choice.get('index')==0,'one C1 choice');delta=choice.get('token_ids')
      if delta is not None:need(type(delta)is list and all(type(x)is int and x>=0 for x in delta),'actual generated delta token IDs');ids.extend(delta)
     kind='tokens'if ids else'non-token'
    self.events.append(dict(event=len(self.events),wire_end=self.offset,received_monotonic_ns=received_ns,kind=kind,token_ids=ids))
    self.tokens.extend(ids);self.token_times.extend([received_ns]*len(ids));need(len(self.tokens)<=1024,'never silently truncate output')
 def end(self):need(not self.partial and not self.lines and self.done,'complete SSE frames and DONE retained')

def observe_response(response,root,*,request_start_ns,request_id,input_ids,clock=time.monotonic_ns,identity=None):
 """Observe an owner-provided response; this function never opens HTTP.

 Every read1 return gets a monotonic timestamp BEFORE parsing/writes. All tokens
 in a delta share its event-completion receive time. No interpolation is made.
 """
 root=Path(root);need(root.is_absolute()and root.is_dir()and not any(x.is_symlink()for x in(root,*root.parents)),'existing new own leaf only')
 need(type(request_start_ns)is int and request_start_ns>0 and type(request_id)is str and re.fullmatch('cmpl-[A-Za-z0-9_-]{1,160}',request_id),'actual owner POST start and unique exact completion/header id')
 request=fixed_request(input_ids);raw=root/'SSE.raw';journal=root/'CHUNKS.jsonl';need(not any((root/n).exists()for n in('SSE.raw','CHUNKS.jsonl','CLIENT_TRACE.json')),'new own files only; never overwrite');observer=Observer();total=0;count=0;jbytes=0;last=request_start_ns;primary=None;err=None
 need(response.status==200 and response.headers.get_content_type()=='text/event-stream','actual200 SSE response required')
 try:
  with raw.open('xb',buffering=0)as wire,journal.open('xb',buffering=0)as rows:
   try:
    while True:
     before=clock();data=response.read1(READ_SIZE);received=clock()
     need(type(before)is int and type(received)is int and last<=before<=received,'actual monotonic read ordering');last=received
     need(type(data)is bytes and len(data)<=READ_SIZE,'actual bounded read1 bytes')
     row=dict(chunk=count,offset=total,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),read_start_monotonic_ns=before,received_monotonic_ns=received,eof=not data)
     enc=(json.dumps(row,sort_keys=True)+'\n').encode();need(total+len(data)<=WIRE_CAP and jbytes+len(enc)<=JOURNAL_CAP,'whole raw/journal caps; never trim/retry')
     need(wire.write(data)==len(data),'complete raw write');need(rows.write(enc)==len(enc),'complete timing row write');total+=len(data);count+=1;jbytes+=len(enc)
     if not data:break
     observer.feed(data,received)
    observer.end()
   except BaseException as e:primary=repr(e);err=e
   finally:os.fsync(wire.fileno());os.fsync(rows.fileno())
 except BaseException as e:primary=repr(e);err=e
 ts=observer.token_times;value=dict(schema='bole.fixed1024-SSE-client-observation/v1',request=request,request_id=request_id,expected_request_headers={'Content-Type':'application/json','X-Request-Id':request_id[5:]},request_start_monotonic_ns=request_start_ns,eof_monotonic_ns=last,http_status=response.status,content_type=response.headers.get_content_type(),raw=ref(raw),chunks=ref(journal),events=observer.events,ordered_token_ids=observer.tokens,token_receive_monotonic_ns=ts,TTFT_ns=None if not ts else ts[0]-request_start_ns,TPOT_numerator_ns=None if not ts else ts[-1]-ts[0],TPOT_denominator=1023,T_total_ns=None if not ts else ts[-1]-request_start_ns,actual_returned_tokens=len(ts),owner_identity=identity,primary=primary,formal_qualification=False,source_only_component=True)
 trace=exclusive_json(root/'CLIENT_TRACE.json',value)
 if err is not None:raise err
 return trace

def execute(*args,**kwargs):
 raise ValueError('SOURCE_ONLY: actual MODEL four Refs, captureOFF production qualification and paired owner remain null; live HTTP/timing execute is forbidden')

def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"HTTP":false,"NPU":false}');return 0
 execute()
if __name__=='__main__':raise SystemExit(main())
