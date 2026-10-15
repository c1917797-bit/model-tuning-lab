"""Native003 guest bootstrap with only DL003 plugin, common cap48/lazy."""
import argparse,ast,hashlib,importlib.util,json,os,sys,types
from pathlib import Path
P=Path(__file__).resolve().parent;LOW=Path('/cache/cch/qwen36-paper-preparation-20261007/lowbit');OLD=LOW/'mxr-r118-capture-launch-20261013-003';WORKER=LOW/'mxr-r118-proc-snapshot-repair-20261013-008'
PINS={'capture_overlay.py':(6707,'848e180ac7612a69996a901ae68e3858825bf0878bbb0653708d55c37e4a234f'),'guest_capture_entry.py':(8309,'37c951e1ae2f4b650d93d414b930f9dd83a05913a68b213edfdd8143c2d70cd0')}
def need(v,m):
 if not v:raise ValueError(m)
def leaf(name):
 path=P/name
 if not path.is_file():
  import owner_overlay as O
  path=O.obj_file(json.loads((P/'SOURCE_MANIFEST.json').read_bytes())['owner017_files'][name])
 s=importlib.util.spec_from_file_location('_dl004_'+name[:-3],path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def raw(name):
 b=(OLD/name).read_bytes();need((len(b),hashlib.sha256(b).hexdigest())==PINS[name],'complete normal native donor');return b
def current(sr):
 import owner_overlay as O
 m=O.current(sr);O.model_gate(m);return m
def overlay():
 o=types.ModuleType('_dl004_native_overlay');o.__file__=str(OLD/'capture_overlay.py');exec(compile(raw('capture_overlay.py'),o.__file__,'exec'),o.__dict__)
 o.START,o.CUTOFF,o.AUTHORITY_SHA=1791962297,1792135097,'71211e77fc870a8c94a7f80424925e38e1e092b9374d3a6a1066960ea74fbf99'
 native=o.native_argv;o.native_argv=lambda upstream,port:leaf('cap48_provider.py').explicit_lazy_argv(native(upstream,port));return o
def private(o):
 tree=ast.parse(raw('guest_capture_entry.py'));nodes=[x for x in tree.body if isinstance(x,ast.Import)and any(z.name=='capture_overlay'for z in x.names)];need(len(nodes)==1,'exact normal overlay import');tree.body.remove(nodes[0])
 v=types.ModuleType('_dl004_actual_guest');v.__file__=str(OLD/'guest_capture_entry.py');v.own=o;exec(compile(tree,v.__file__,'exec'),v.__dict__)
 require=v.require_config
 def config(cfg,proof):
  policy=require(cfg,proof);L=cfg.load_config;need(L.load_format=='safetensors'and L.safetensors_load_strategy=='lazy'and L.model_loader_extra_config.get('enable_multithread_load')is False and L.device is None,'same actual common lazy/no-prefetch/no-multithread loader');return policy
 v.require_config=config;return v
def environment(o,sr,base,source,output,run):
 import owner_overlay as O
 return O.environment(types.SimpleNamespace(WORKER=WORKER),o,sr,base,source,output,run)
def main(argv=None):
 ap=argparse.ArgumentParser(allow_abbrev=False);ap.add_argument('--execute',action='store_true');ap.add_argument('--role',choices=['guest']);ap.add_argument('--source-ref');a,rest=ap.parse_known_args(argv)
 if not a.execute:print('{"enabled":false,"NPU":false}');return
 sr=json.loads(a.source_ref);current(sr);o=overlay();o.environment_original=o.environment;o.environment=lambda *args:environment(o,sr,*args);write=o.write_new
 def publish(path,v):
  if v.get('schema')=='mxr.actual-native-capture-launch/v1':v=dict(v,schema='deltalog.actual-model-smoke-launch/v004',source=sr,mode='DL-smoke',candidate_enabled=True,observed_source_only=False,performance_ready=False)
  return write(path,v)
 o.write_new=publish
 for p in(P,WORKER):
  if str(p)not in sys.path:sys.path.insert(0,str(p))
 need(os.environ.get('MST_MXR_NATIVE_WORKER_RECEIPT')=='1','same native loaded-worker proof required')
 return private(o).main(['--execute',*rest,'--mode','capture'])
if __name__=='__main__':main()
