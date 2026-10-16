"""Actual short HTTP smoke; reuse complete existing native request_once."""
import argparse,ast,hashlib,importlib.util,json,types
from pathlib import Path
P=Path(__file__).resolve().parent
def main():
 ap=argparse.ArgumentParser(allow_abbrev=False);ap.add_argument('--execute',action='store_true');ap.add_argument('--source-ref');ap.add_argument('--model-config',type=Path);ap.add_argument('--server-output',type=Path);ap.add_argument('--output',type=Path);ap.add_argument('--run-id');ap.add_argument('--port',type=int);a=ap.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return
 s=importlib.util.spec_from_file_location('_dl004_client_entry',P/'entry.py');E=importlib.util.module_from_spec(s);s.loader.exec_module(E);sr=json.loads(a.source_ref);E.current(sr);o=E.overlay()
 b=(E.OLD/'capture_client.py').read_bytes();E.need((len(b),hashlib.sha256(b).hexdigest())==(4648,'a1d942331600392ab19cf0c04108def0e0607215dc9c86a406a8fff052dc3c05'),'exact native complete request helper')
 tree=ast.parse(b);imports=[n for n in tree.body if isinstance(n,ast.Import)and any(x.name=='capture_overlay'for x in n.names)];E.need(len(imports)==1,'one actual request overlay');tree.body.remove(imports[0]);C=types.ModuleType('_dl004_native_http');C.__file__=str(E.OLD/'capture_client.py');C.own=o;exec(compile(tree,C.__file__,'exec'),C.__dict__)
 launch=json.loads((a.server_output/'LAUNCH.json').read_bytes());E.need(launch['schema']=='deltalog.actual-model-smoke-launch/v004'and launch['source']==sr and launch['run_id']==a.run_id and launch['mode']=='DL-smoke','actual bound model launch')
 E.need(o.sha(a.model_config)==o.MODEL_CONFIG_SHA and not a.output.exists(),'actual config/new output');a.output.mkdir();cfg=json.loads(a.model_config.read_bytes());rows=[]
 for name,n in(('warmup',16),('decode',129)):
  body=C.payload(cfg,n);body['echo']=False;rid=a.run_id+'-'+name;response=C.request_once('http://127.0.0.1:%d/v1/completions'%a.port,body,a.output/name,rid)
  rows.append(dict(name=name,request_id=rid,prompt_tokens=n,response=response,request=E.leaf('prerequisite.py').ref((a.output/name).with_suffix('.request.json')),wire=E.leaf('prerequisite.py').ref((a.output/name).with_suffix('.response.bin'))))
 o.write_new(a.output/'RESULT.json',dict(schema='deltalog.actual-short-client/v004',source=sr,run_id=a.run_id,launch=E.leaf('prerequisite.py').ref(a.server_output/'LAUNCH.json'),rows=rows,diagnostic_only=True,performance_ready=False,task_accuracy=False))
if __name__=='__main__':main()
