"""Actual short HTTP smoke; reuse complete existing native request_once."""
import argparse,ast,hashlib,importlib.util,json,types
from pathlib import Path
P=Path(__file__).resolve().parent
def http_module(b,o,need,filename):
 need((len(b),hashlib.sha256(b).hexdigest())==(4648,'a1d942331600392ab19cf0c04108def0e0607215dc9c86a406a8fff052dc3c05'),'exact native complete request helper')
 old='and usages[-1]["completion_tokens"] == 2';new='and usages[-1]["completion_tokens"] == 10';text=b.decode();need(text.count(old)==1 and new not in text,'one source-bound native2-to10 output assertion');adapted=text.replace(old,new);need(adapted.replace(new,old)==text,'whole native HTTP helper inverse')
 tree=ast.parse(adapted);imports=[n for n in tree.body if isinstance(n,ast.Import)and any(x.name=='capture_overlay'for x in n.names)];need(len(imports)==1,'one actual request overlay');tree.body.remove(imports[0]);C=types.ModuleType('_dl025_native_http');C.__file__=str(filename);C.own=o;exec(compile(tree,C.__file__,'exec'),C.__dict__);return C
def payload2048(config,need):
 need(config.get('model_type')=='qwen3_5'and type(config.get('text_config'))is dict,'actual checkpoint architecture')
 vocab=config['text_config'].get('vocab_size');need(type(vocab)is int and vocab>0,'actual model vocabulary')
 ids=[1000+j%257 for j in range(2048)];need(all(0<=x<vocab for x in ids),'raw token IDs outside checkpoint vocabulary')
 return dict(model='qwen36',prompt=ids,n=1,stream=True,temperature=0,seed=0,max_tokens=10,min_tokens=10,ignore_eos=True,echo=False,return_token_ids=True,stream_options={'include_usage':True})

def main():
 ap=argparse.ArgumentParser(allow_abbrev=False);ap.add_argument('--execute',action='store_true');ap.add_argument('--source-ref');ap.add_argument('--model-config',type=Path);ap.add_argument('--server-output',type=Path);ap.add_argument('--output',type=Path);ap.add_argument('--run-id');ap.add_argument('--port',type=int);a=ap.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return
 s=importlib.util.spec_from_file_location('_dl004_client_entry',P/'entry.py');E=importlib.util.module_from_spec(s);s.loader.exec_module(E);sr=json.loads(a.source_ref);E.current(sr);o=E.overlay()
 C=http_module((E.OLD/'capture_client.py').read_bytes(),o,E.need,E.OLD/'capture_client.py')
 launch=json.loads((a.server_output/'LAUNCH.json').read_bytes());E.need(launch['schema']=='deltalog.actual-model-smoke-launch/v004'and launch['source']==sr and launch['run_id']==a.run_id and launch['mode']=='DL-smoke','actual bound model launch')
 E.need(o.sha(a.model_config)==o.MODEL_CONFIG_SHA and not a.output.exists(),'actual config/new output');a.output.mkdir();cfg=json.loads(a.model_config.read_bytes());rows=[]
 for name,n in(('warmup',2048),('decode',2048)):
  body=payload2048(cfg,E.need);E.need(type(body['prompt'])is list and len(body['prompt'])==2048 and all(type(x)is int for x in body['prompt']),'exact model smoke token-ID arrays');body.update(echo=False,max_tokens=10,min_tokens=10,ignore_eos=True,return_token_ids=True);rid=a.run_id+'-'+name;response=C.request_once('http://127.0.0.1:%d/v1/completions'%a.port,body,a.output/name,rid)
  rows.append(dict(name=name,request_id=rid,prompt_tokens=n,response=response,request=E.leaf('prerequisite.py').ref((a.output/name).with_suffix('.request.json')),wire=E.leaf('prerequisite.py').ref((a.output/name).with_suffix('.response.bin'))))
 o.write_new(a.output/'RESULT.json',dict(schema='deltalog.actual-short-client/v004',source=sr,run_id=a.run_id,launch=E.leaf('prerequisite.py').ref(a.server_output/'LAUNCH.json'),rows=rows,diagnostic_only=True,performance_ready=False,task_accuracy=False))
if __name__=='__main__':main()
