"""Reuse actual003 native server/client; new R156/receiver, no legacy gate."""
import argparse,ast,hashlib,importlib.util,json,os,sys,types
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
LOW=Path('/cache/cch/qwen36-paper-preparation-20261007/lowbit')
OLD=LOW/'mxr-r118-capture-launch-20261013-003'
WORKER=LOW/'mxr-r118-proc-snapshot-repair-20261013-008'
START,CUT=1792134133,1792220533
AUTH_SHA='e8c373b6664a4bdd80012428b686227a6f15c0535b3c57a7654fb7996c02cf28'
PINS={'capture_overlay.py':(6707,'848e180ac7612a69996a901ae68e3858825bf0878bbb0653708d55c37e4a234f'),'guest_capture_entry.py':(8309,'37c951e1ae2f4b650d93d414b930f9dd83a05913a68b213edfdd8143c2d70cd0'),'capture_client.py':(4648,'a1d942331600392ab19cf0c04108def0e0607215dc9c86a406a8fff052dc3c05')}
def need(v,m):
 if not v:raise ValueError(m)
def raw(leaf):
 b=(OLD/leaf).read_bytes();need((len(b),hashlib.sha256(b).hexdigest())==PINS[leaf],'complete original003 source');return b
def current(sr):
 p=Path(sr['path']);b=p.read_bytes();need(set(sr)=={'path','bytes','sha256'}and p==P/'SOURCE_MANIFEST.json'and (len(b),hashlib.sha256(b).hexdigest())==(sr['bytes'],sr['sha256']),'current exact own manifest')
 m=json.loads(b);need(m['schema']=='mxr.diag16.full-gdn-frame-bridge-source/v1'and m['root']==str(P)and m['default_enabled']is False and m['window']==dict(start=START,cutoff=CUT),'new source-qualified R156, not old clock')
 for r in m['files'].values():
  p=Path(r['path']);b=p.read_bytes();need(P in p.parents and not p.is_symlink()and (len(b),hashlib.sha256(b).hexdigest())==(r['bytes'],r['sha256']),'complete current leaves')
 return m
def overlay():
 name='_mxr042_native003_overlay';o=types.ModuleType(name);o.__file__=str(OLD/'capture_overlay.py');exec(compile(raw('capture_overlay.py'),o.__file__,'exec'),o.__dict__)
 need((o.START,o.CUTOFF)==(1791879730,1791922930),'exact historical donor clock')
 o.START,o.CUTOFF,o.AUTHORITY_SHA=START,CUT,AUTH_SHA
 native=o.native_argv;source=o.load_source
 def argv(upstream,port):
  v=native(upstream,port);expected={'--max-model-len':('33792','41984'),'--max-num-batched-tokens':('32768','40960'),'--max-num-seqs':('1','2')}
  for key,(old,new)in expected.items():need(v.count(key)==1 and v[v.index(key)+1]==old,'exact old scalar CLI');v[v.index(key)+1]=new
  spec=importlib.util.spec_from_file_location('_long012_cap48',P/'cap48_provider.py');cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
  return cap.explicit_lazy_argv(v)
 def sources(upstream,name):
  actual=source(upstream,name)
  if name!='config_cpu.py':return actual
  path=P/'DERIVED_config_cpu.py';s=importlib.util.spec_from_file_location('_long008_scalar_proof',path);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
 o.native_argv=argv;o.load_source=sources
 return o
def derive_client(b):
 pairs=[('launch["mode"] in ("capture", "shadow")','launch["mode"] in ("diag16-shadow",)'),('(launch["mode"] == "shadow")','(launch["mode"] == "diag16-shadow")')]
 text=b.decode();out=text
 for old,new in pairs:need(out.count(old)==1,'exact old client mode predicate');out=out.replace(old,new)
 inverse=out
 for old,new in reversed(pairs):inverse=inverse.replace(new,old)
 need(inverse==text,'whole original client inverse: requests/counts/wire/guard unchanged');return out.encode()
def private(leaf,o):
 b=raw(leaf);b=derive_client(b)if leaf=='capture_client.py'else b
 tree=ast.parse(b);imports=[n for n in tree.body if isinstance(n,ast.Import)and len(n.names)==1 and n.names[0].name=='capture_overlay'];need(len(imports)==1,'one exact overlay import')
 tree.body.remove(imports[0]);v=types.ModuleType('_mxr042_'+leaf[:-3]);v.__file__=str(OLD/leaf);v.own=o
 exec(compile(tree,str(OLD/leaf),'exec'),v.__dict__);need(v.own is o and v.main.__globals__['own']is o,'private facade actual main global binding')
 if leaf=='guest_capture_entry.py':
  require=v.require_config
  def config(config,proof):
   policy=require(config,proof);L=config.load_config
   need(L.load_format=='safetensors'and L.safetensors_load_strategy=='lazy'and L.model_loader_extra_config.get('enable_multithread_load')is False and L.device is None and config.model_config.quantization is None,'actual same scoped cap48 lazy load recipe')
   need(config.scheduler_config.max_num_batched_tokens==40960 and config.scheduler_config.max_num_seqs==2 and config.scheduler_config.long_prefill_token_threshold==0 and config.cache_config.enable_prefix_caching is False,'actual numerical fullpacked scheduling prerequisites before weight load')
   atomic_path=P/'atomic'
   if str(atomic_path)not in sys.path:sys.path.insert(0,str(atomic_path))
   import barrier
   mf=json.loads((P/'SOURCE_MANIFEST.json').read_bytes());rid=mf['runtime_identity']['run_id']+'-packed40960'
   need(barrier.install(rid,Path(os.environ['MST_MXR_SOLVE_EVIDENCE_ROOT']).parent/'ATOMIC_ADMISSION.json'),'actual API frontend numerical-only atomic hook')
   return dict(policy,actual_load_format=L.load_format,actual_load_strategy=L.safetensors_load_strategy,actual_load_extra=L.model_loader_extra_config,actual_load_device=L.device,numerical_atomic_prefill=True)
  v.require_config=config
 return v
def environment(o,sr,pr,base,source,output,run):
 e=o.environment_original(base,source,output,run)
 e.update(MST_MXR_CAPTURE_ENABLE='0',MST_MXR_SOLVE_ENABLE='0',MXR_OBSERVERLESS_ENABLE='1',MXR_ONCE_CORRECTNESS_ENABLE='1',MXR_ONCE_CORRECTNESS_SOURCE_REF=json.dumps(sr,separators=(',',':')),MXR_OBSERVERLESS_SOURCE_REF=json.dumps(current(sr)['plugin_source'],separators=(',',':')),MXR_OBSERVERLESS_QUALIFICATION_REF=json.dumps(dict(path=str(P/'QUALIFICATION_CORRECTNESS.json'),bytes=(P/'QUALIFICATION_CORRECTNESS.json').stat().st_size,sha256=hashlib.sha256((P/'QUALIFICATION_CORRECTNESS.json').read_bytes()).hexdigest()),separators=(',',':')),MXR_Y16_EXPERIMENT_ENABLE='1',MXR_OBSERVERLESS_RECEIPT_ROOT=str(output),MXR_DIAG16_GDN_SHADOW_ENABLE='1',MXR_DIAG16_GDN_STAGE='short-full-gdn-diagnostic',MXR_DIAG16_GDN_SOURCE_REF=json.dumps(sr,separators=(',',':')),MXR_DIAG16_GDN_PREREQUISITE_REF=json.dumps(pr,separators=(',',':')),MST_MXR_SOLVE_EVIDENCE_ROOT=str(output),MST_MXR_MODEL_RUN_ID=run)
 # Original capture/solve entry points stay disabled; only our explicit receiver
 # and the actual008 native-worker receipt are registered. No hidden dense path.
 plugins=[x for x in e.get('VLLM_PLUGINS','').split(',')if x and x not in('mxr_source_bound_capture','mxr_source_bound_solve')]
 e['VLLM_PLUGINS']=','.join(dict.fromkeys(plugins+['ascend','mxr_native_worker_receipt','mxr_diag16_gdn_shadow']))
 e['PYTHONPATH']=str(P)+':'+str(WORKER)+':'+e.get('PYTHONPATH','')
 e['MXR_LONG_RAW_ROOT']=current(sr)['raw_storage']['root']
 # Exact044 common policy API; reenable only this untimed diagnostic collector.
 from plugin_discovery import component
 plugin_root,cp=component(current(sr)['plugin_source'])
 # Actual003 continues importing API/server IN THIS -I interpreter; spawn
 # inherits current sys.path, not a recomputed value from os.environ.
 if str(plugin_root)not in sys.path:sys.path.insert(0,str(plugin_root))
 e['PYTHONPATH']=str(plugin_root)+':'+e['PYTHONPATH']
 e=cp.environment(e,'candidate',output,current(sr)['plugin_source'])
 e.update(MXR_ONCE_CORRECTNESS_ENABLE='1',MXR_DIAG16_GDN_SHADOW_ENABLE='1')
 e['VLLM_PLUGINS']=','.join(dict.fromkeys([x for x in e['VLLM_PLUGINS'].split(',')if x!='mxr_block_refinement044']+['mxr_diag16_gdn_shadow']))
 need('mxr_common_precision044'in e['VLLM_PLUGINS'].split(',')and 'mxr_block_refinement044'not in e['VLLM_PLUGINS'].split(','),'one diagnostic installer plus common policy; no alias duplicate')
 e['NUMERICAL_ATOMIC_PREFILL_ENABLE']='1'
 return e
def main(argv=None):
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--role',choices=('guest','client'));p.add_argument('--source-ref');p.add_argument('--prerequisite-ref');a,rest=p.parse_known_args(argv)
 if not a.execute:print(json.dumps(dict(enabled=False,NPU=False,model_ready=False)));return 0
 need(a.role and a.source_ref and a.prerequisite_ref,'explicit new role/source/actual039 consumption')
 sr,pr=map(json.loads,(a.source_ref,a.prerequisite_ref));current(sr)
 spec=importlib.util.spec_from_file_location('_mxr042_prerequisite_entry',P/'prerequisite.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r);r.gate(pr)
 o=overlay()
 if a.role=='guest':
  need('--mode'not in rest and '--solve-gate'not in rest and '--solve-gate-sha256'not in rest,'no legacy shadow/gate path')
  o.environment_original=o.environment;o.environment=lambda *args:environment(o,sr,pr,*args)
  write=o.write_new
  def publish(path,value):
   if value.get('schema')=='mxr.actual-native-capture-launch/v1':value=dict(value,schema='mxr.diag16.actual-gdn-shadow-launch/v1',mode='diag16-shadow',candidate_enabled=True,observed_source_only=False,bridge_source=sr,diag16_prerequisite=pr,long_tokens=[32768,40960],layers_per_worker=48,complete_model_qualified=False)
   return write(path,value)
  o.write_new=publish
  for path in(P,WORKER):
   if str(path)not in sys.path:sys.path.insert(0,str(path))
  need(os.environ.get('MST_MXR_NATIVE_WORKER_RECEIPT')=='1','same actual008 loaded worker proof required')
  return private('guest_capture_entry.py',o).main(['--execute',*rest,'--mode','capture'])
 # Before invoking the complete original request client, require new launch
 # identity; its mode/count predicate alone is not a source authority.
 ap=argparse.ArgumentParser(add_help=False);ap.add_argument('--server-output',type=Path);z,_=ap.parse_known_args(rest)
 value=json.loads((z.server_output/'LAUNCH.json').read_text());need(value['schema']=='mxr.diag16.actual-gdn-shadow-launch/v1'and value['bridge_source']==sr and value['diag16_prerequisite']==pr and value['layers_per_worker']==48 and value['long_tokens']==[32768,40960],'actual current long launch')
 spec=importlib.util.spec_from_file_location('_long008_client',P/'long_client.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v.run(sys.modules[__name__],o,sr,pr,rest)
if __name__=='__main__':raise SystemExit(main())
