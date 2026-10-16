"""Actual003 SSE/request helper, explicit long single and packed requests."""
import concurrent.futures,hashlib,importlib.util,json,time
from pathlib import Path
def run(E,o,sr,pr,rest):
 import argparse
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--model-config',type=Path,required=True);p.add_argument('--server-output',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--run-id',required=True);p.add_argument('--port',type=int,default=8252);a=p.parse_args(rest)
 o.need(E.START<=time.time()and time.time()+2100<E.CUT,'long requests plus owned cleanup fit fixed cutoff')
 launch=json.loads((a.server_output/'LAUNCH.json').read_bytes())
 o.need(launch['bridge_source']==sr and launch['diag16_prerequisite']==pr and launch['run_id']==a.run_id,'exact current long launch')
 o.need(o.sha(a.model_config)==o.MODEL_CONFIG_SHA and not a.output.exists(),'actual model/new client output')
 a.output.mkdir();config=json.loads(a.model_config.read_bytes());vocab=config['text_config']['vocab_size']
 def ids(c):
  o.need(c in(16,8192,32768),'frozen long token lengths');x=[1000+j%257 for j in range(c)];o.need(max(x)<vocab,'actual token range');return x
 # Reuse only actual request_once with exact declared count/timeout deltas.
 text=E.raw('capture_client.py').decode();text=text.replace('completion_tokens"] == 2','completion_tokens"] == 3').replace('timeout=120','timeout=900')
 import ast,types
 tree=ast.parse(text);tree.body=[n for n in tree.body if not(isinstance(n,ast.Import)and len(n.names)==1 and n.names[0].name=='capture_overlay')]
 c=types.ModuleType('_once008_actual003_client');c.__file__=str(E.OLD/'capture_client.py');c.own=o;exec(compile(tree,c.__file__,'exec'),c.__dict__)
 def request(count,label):
  body=dict(model='qwen36',prompt=ids(count),n=1,stream=True,temperature=0,seed=0,max_tokens=3,min_tokens=3,ignore_eos=True,echo=True,return_token_ids=True,stream_options={'include_usage':True})
  return c.request_once('http://127.0.0.1:%d/v1/completions'%a.port,body,a.output/label,a.run_id+'-'+label)
 warm=request(16,'warmup')
 o.write_new(a.server_output/'capture/ARM-LONG.json',dict(schema='mxr.long.arm/v1',run_id=a.run_id,lengths=[32768,40960]))
 one=request(32768,'long32768')
 # One pair, no retries. Actual40960 packed capture is mandatory in consumer;
 # a scheduler emitting32768+8192 separately is missing gate, not paper failure.
 path=Path(__file__).resolve().parent/'atomic'/'client.py'
 spec=importlib.util.spec_from_file_location('_long012_atomic_bulk',path);bulk=importlib.util.module_from_spec(spec)
 import sys
 atomic_dir=str(path.parent)
 if atomic_dir not in sys.path:sys.path.insert(0,atomic_dir)
 spec.loader.exec_module(bulk)
 target=a.output/'PACKED_BULK.json'
 o.need(bulk.main(['--execute','--url','http://127.0.0.1:%d/v1/completions'%a.port,'--model','qwen36','--request-id',a.run_id+'-packed40960','--output',str(target)])==0,'one true native bulk request')
 pair=dict(path=str(target),bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest())
 o.write_new(a.output/'RESULT.json',dict(schema='mxr.long.actual-request/v1',source=sr,run_id=a.run_id,warmup=warm,long32768=one,packed_pair=pair,expected_actual_aggregates=[32768,40960],numerical_pass=False,performance_ready=False))
 return 0
