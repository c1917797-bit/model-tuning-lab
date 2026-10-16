"""Cold source contracts; no framework emulation or numeric PASS."""
import ast,copy,hashlib,importlib.metadata,importlib.util,json,os,subprocess,sys,tempfile,types,unittest,unittest.mock
from pathlib import Path,PurePosixPath
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
def baseline_math(m,read):
 def checked(r):
  if type(r)is not dict or set(r)!={'path','bytes','sha256'}:raise ValueError('baseline Ref3')
  b=read(r)
  if(len(b),hashlib.sha256(b).hexdigest())!=(r['bytes'],r['sha256']):raise ValueError('baseline exact source bytes')
  return b
 sr=m['baseline067_source'];old=json.loads(checked(sr));deps={r['path']:r for r in m['dependencies']}
 if str(PurePosixPath(sr['path']).parent)!=old['root']:raise ValueError('baseline root from pinned actual template')
 result={}
 for n in('boundary_oracle.py','independent_block_reference.py','lossless_raw.py','deferred_registry.py'):
  r=old['files'][n]
  if deps.get(r['path'])!=r or str(PurePosixPath(r['path']).parent)!=old['root']:raise ValueError('exact baseline file in readonly dependency closure')
  result[n]=checked(r)
 return result
class Tests(unittest.TestCase):
 def test_01_cold_real_frontdoors(self):
  for name in('host_ticket.py','entry.py','parser_probe.py','registry_child_probe.py','bind_source.py','consume.py','software.py'):
   r=subprocess.run([sys.executable,'-I','-B',str(P/name)],cwd=P.parent,capture_output=True,text=True,timeout=15);self.assertEqual(r.returncode,0,(name,r.stderr));self.assertFalse(json.loads(r.stdout)['enabled'])
 def test_02_deferred_no_early_operator(self):
  import deferred_registry
  self.assertTrue(deferred_registry.software_controls()['first_core_missing_hardfail'])
  tree=ast.parse((P/'worker.py').read_bytes());reg=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='register');s=ast.get_source_segment((P/'worker.py').read_text(),reg);self.assertIn('deferred(install',s);self.assertNotIn('install()',s)
 def test_03_full_actual_parser_argv_and_symbol_table(self):
  import dis
  sp=importlib.util.spec_from_file_location('_actual068_parser',P/'parser_probe.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
  self.assertNotIn('importlib',m.main.__code__.co_varnames)
  s=(P/'parser_probe.py').read_text();self.assertIn('native_argv_contract(native,o,upstream)',s);self.assertNotIn("native[-2:]",s)
 def test_04_manifest_identity_actual_files(self):
  m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes());self.assertEqual(m['stage'],'short2048');self.assertEqual(m['tokens'],2048);self.assertEqual(m['runtime_identity']['owner'],m['runtime_identity']['run_id']);self.assertEqual(m['budgets']['phase_seconds'],5400)
  self.assertIn('073',m['root']);self.assertIn('073',m['output_root']);self.assertNotIn('raw_storage',m);self.assertEqual(m['raw_total_cap_GiB'],12)
  for n,r in m['files'].items():
   b=(P/n).read_bytes();self.assertEqual((len(b),hashlib.sha256(b).hexdigest()),(r['bytes'],r['sha256']),n)
 def test_05_no_long_controlpath(self):
  h=(P/'host_ticket.py').read_text();w=(P/'worker.py').read_text();c=(P/'consume.py').read_text();e=(P/'entry.py').read_text()
  self.assertNotIn('_RAW_ROOT',h);self.assertNotIn('raw_filesystem',h);self.assertNotIn('long_client.py',e);self.assertIn('tokens==2048',w);self.assertIn('len(notes)==48',c);self.assertIn('multistep_state=passed',c)
  self.assertIn('native_recurrent=torch.ops',w);self.assertNotIn('barrier.install',e)
 def test_06_complete_scanner_inverse(self):
  original=(P/'actual011/output_budget.py').read_bytes();d=(P/'DERIVED_output_budget.py').read_bytes();self.assertEqual(d.replace(b'LIMIT=12*1024**3',b'LIMIT=32*1024**3'),original)
  from small_disk_contract import preflight
  with self.assertRaises(ValueError):preflight(P/'foreign')
  self.assertIn('32*2**30',(P/'small_disk_contract.py').read_text())
 def test_07_default_off_real_entrypoint(self):
  eps={e.name:e.value for d in importlib.metadata.distributions(path=[str(P)])for e in d.entry_points if e.group=='vllm.general_plugins'};self.assertEqual(eps,{'mxr_diag16_gdn_shadow':'mxr_diag16_gdn_shadow:register'})
  sp=importlib.util.spec_from_file_location('_off068',P/'worker.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);self.assertIsNone(m.register());self.assertIsNone(m._installed_bridge)
 def test_08_math_reference_and_source_AST(self):
  manifest=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes())
  def reader(r):
   if sys.platform=='linux':return Path(r['path']).read_bytes()
   # Local software-only mapping: exact pinned manifest snapshot and already
   # identical own files, with every byte/SHA checked by baseline_math.
   if r==manifest['baseline067_source']:return(P/'evidence/SOURCE_TEMPLATE067.json').read_bytes()
   actual=json.loads((P/'evidence/SOURCE_TEMPLATE067.json').read_bytes())
   matches=[n for n,f in actual['files'].items()if f==r]
   if len(matches)!=1:raise ValueError('no exact local source mapping')
   return(P/matches[0]).read_bytes()
  for n,b in baseline_math(manifest,reader).items():self.assertEqual((P/n).read_bytes(),b,n)
  for p in P.rglob('*.py'):ast.parse(p.read_bytes())
  sp=importlib.util.spec_from_file_location('_actual068_host',P/'host_ticket.py');H=importlib.util.module_from_spec(sp);sp.loader.exec_module(H)
  donor=Path(H.HOST_REF['path'])if sys.platform=='linux'else P.parent/'mxr-r118-proc-snapshot-repair-20261013-008/host_ticket.py';b=donor.read_bytes();self.assertEqual((len(b),hashlib.sha256(b).hexdigest()),(H.HOST_REF['bytes'],H.HOST_REF['sha256']))
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);(root/'SOURCE_MANIFEST.json').write_bytes((P/'SOURCE_TEMPLATE.json').read_bytes());H.HERE=root
   changed,pairs=H.adapt(b.decode(),{},{});ast.parse(changed);self.assertIn('mxr-2k-memory32-model-new24h-v1-073-repair6',changed);self.assertNotIn('_RAW_ROOT',changed);self.assertGreater(len(pairs),20)
 def test_09_actual_client_complete_inverse(self):
  sp=importlib.util.spec_from_file_location('_actual072_entry',P/'entry.py');E=importlib.util.module_from_spec(sp);sp.loader.exec_module(E)
  old=(Path(E.OLD)if sys.platform=='linux'else P.parent/'mxr-r118-capture-launch-20261013-003')/'capture_client.py';b=old.read_bytes();self.assertEqual((len(b),hashlib.sha256(b).hexdigest()),E.PINS['capture_client.py'])
  d=E.derive_client(b).decode();self.assertIn('payload(config, 2048)',d);self.assertIn('max_tokens=10, min_tokens=10',d);self.assertIn('completion_tokens"] == 10',d);self.assertIn('payload(config, 16)',d);ast.parse(d)
  with self.assertRaises(ValueError):E.derive_client(b.replace(b'payload(config, 129)',b'payload(config, 130)'))
  E.OLD=old.parent;o=E.overlay();ids=o.prompt_ids(dict(model_type='qwen3_5',text_config=dict(vocab_size=200000)),2048);self.assertEqual(ids,[1000+j%257 for j in range(2048)])
  with self.assertRaises(ValueError):o.prompt_ids(dict(model_type='qwen3_5',text_config=dict(vocab_size=200000)),129)
  self.assertEqual(len(o.prompt_ids(dict(model_type='qwen3_5',text_config=dict(vocab_size=200000)),16)),16)
  upstream=P/'actual011';v=o.native_argv(upstream,8252);self.assertEqual(v[v.index('--max-model-len')+1],'4096');self.assertEqual(v[v.index('--max-num-batched-tokens')+1],'2048');self.assertEqual(v[v.index('--max-num-seqs')+1],'1')
  sp=importlib.util.spec_from_file_location('_native072_contract',P/'parser_probe.py');A=importlib.util.module_from_spec(sp);sp.loader.exec_module(A);self.assertTrue(A.native_argv_contract(v,o,upstream)['worker_cls_unique'])
 def test_10_full_nine_decode_and_budget_negative(self):
  from decode_coverage072 import check
  from tensor_budget072 import bounds
  ps=['L%d'%i for i in range(48)];notes=[dict(prefix=p,prefill_tokens=2048,step=s)for p in ps for s in range(9)];self.assertEqual(check(notes,ps)['rows'],432)
  for bad in(notes[:-1],notes[:-1]+[notes[0]],[dict(n,step=9)if i==0 else n for i,n in enumerate(notes)]):
   with self.assertRaises(ValueError):check(bad,ps)
  b=bounds();self.assertLess(b['all_tensor_logical_bound'],b['raw_and_control_cap']);self.assertFalse(b['no_dedup_savings_assumed']is False);self.assertFalse(b['cache_log_fit_guaranteed']);self.assertEqual(b['decode_steps'],9)
 def test_11_actual_original_create_inspect_memory_contract(self):
  from resource_controls073 import run
  self.assertTrue(run()['wrong_cap_rejected'])
 def test_12_resource_trial_and_observer_consistent(self):
  from resource_budget073 import contract
  v=contract();self.assertEqual(v['model_initial_GiB'],40.5);self.assertEqual(v['model_guest_GiB'],32);self.assertFalse(v['new2K_peak_proved']);self.assertGreater(v['incremental_trial_headroom_bytes'],4*2**30)
  text=(P/'memory_observer.py').read_text();self.assertIn('else MODEL_GUEST_GIB',text);self.assertNotIn('else 48',text)
  m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes());self.assertEqual(m['model_RAM_GiB'],40.5);self.assertEqual(m['resource_trial073'],v);self.assertEqual(m['budgets']['total_output_GiB'],12)
  self.assertEqual(m['cap48_resource']['guest_model_GiB'],32);self.assertEqual(m['cap48_resource']['model_floor_GiB'],40.5)
  import memory_observer as M
  good={'memory.failcnt':'0','memory.oom_control':'under_oom 0\noom_kill 0\noom_kill_local 0'};self.assertTrue(M.no_memory_failure('v1',good))
  for bad in(dict(good,**{'memory.failcnt':'1'}),dict(good,**{'memory.oom_control':'under_oom 0\noom_kill 1'}),{}):
   with self.assertRaises(M.ResourceMemoryFault):M.no_memory_failure('v1',bad)
  self.assertTrue(M.no_memory_failure('v2',{'memory.events':'oom 0\noom_kill 0'}))
  with self.assertRaises(M.ResourceMemoryFault):M.no_memory_failure('v2',{'memory.events':'oom 1\noom_kill 0'})
 def test_13_actual_installed_snapshot_live_and_cleanup_missing(self):
  import memory_observer as M
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);cg=root/'own-cgroup';cg.mkdir();proc=root/'proc'/'123';proc.mkdir(parents=True);(proc/'cgroup').write_bytes(b'1:memory:/docker/OWNCID\n');rows=[]
   original_path=Path
   def path(value):return root/'proc'if str(value)=='/proc'else original_path(value)
   def put(limit='34359738368',events=True):
    for p in cg.iterdir():p.unlink()
    if limit is not None:(cg/'memory.limit_in_bytes').write_bytes(str(limit).encode())
    if events:
     (cg/'memory.failcnt').write_bytes(b'0');(cg/'memory.oom_control').write_bytes(b'under_oom 0\noom_kill 0\n')
   class Owned:
    def __init__(self):self.cid='OWNCID';self.out=root;self.secondary=[];self._mxr_resource_profile='native-model';self.stopped=0;self.remove=False
    def inspect(self):return({'State':{'Pid':123,'Running':True}},{'actual_software_fixture':True})
    def observe(self,label,initial=False,cleanup=False):return 'original-observe'
    def create_native(self,model,cpu):return 'original-create'
    def cleanup(self):
     self.stopped+=1
     if self.remove:
      for p in cg.iterdir():p.unlink()
      cg.rmdir()
     return 'original-stop'
   def write(p,row):rows.append(row);return {'path':str(p),'software_only':True}
   c=types.SimpleNamespace(GIB=2**30,write=write);M.install(Owned,c,None)
   with unittest.mock.patch.object(M,'Path',side_effect=path),unittest.mock.patch.object(M,'locate',return_value=('v1',cg)):
    put();own=Owned();self.assertEqual(own.create_native(True,False),'original-create');self.assertEqual(rows[-1]['schema'],'mxr.cap48.actual-memory-cgroup/v1')
    for limit,events in((None,True),('unparseable',True),('51539607552',True),('34359738368',False)):
     put(limit,events)
     with self.assertRaises(M.ResourceMemoryFault):own.observe('live-negative')
     self.assertTrue(rows[-1]['counter_unavailable_not_zero'])
    put();own.remove=True;self.assertEqual(own.cleanup(),'original-stop');self.assertEqual(own.stopped,1);self.assertFalse(own.secondary);self.assertTrue(rows[-1]['counter_unavailable_not_zero']);self.assertIn('departed',rows[-1]['error'])
    with self.assertRaises(M.ResourceMemoryFault):Owned().observe('live-path-gone')
    cg.mkdir();put();other=Owned();other.create_native(True,False);put(None);self.assertEqual(other.cleanup(),'original-stop');self.assertEqual(other.stopped,1);self.assertTrue(other.secondary);self.assertTrue(all('resource-memory-hard-failure'in s for s in other.secondary));self.assertTrue(rows[-1]['counter_unavailable_not_zero'])
 def test_14_source_pinned_reference_path_not_ambient_dirname(self):
  m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes());old=json.loads((P/'evidence/SOURCE_TEMPLATE067.json').read_bytes());sr=m['baseline067_source']
  with tempfile.TemporaryDirectory()as td:
   root=Path(td)/'actual-v1-067';root.mkdir();paths={sr['path']:root/'SOURCE_TEMPLATE.json'};paths[sr['path']].write_bytes((P/'evidence/SOURCE_TEMPLATE067.json').read_bytes())
   for n in('boundary_oracle.py','independent_block_reference.py','lossless_raw.py','deferred_registry.py'):
    paths[old['files'][n]['path']]=root/n;(root/n).write_bytes((P/n).read_bytes())
   def reader(r):
    if r['path']not in paths:raise ValueError('missing precise mounted reference')
    return paths[r['path']].read_bytes()
   self.assertEqual(len(baseline_math(m,reader)),4)
   bad=copy.deepcopy(m);bad['baseline067_source']['path']=sr['path'].replace('-v1-','-')
   with self.assertRaises(ValueError):baseline_math(bad,reader)
   bad=copy.deepcopy(m);bad['dependencies']=[r for r in bad['dependencies']if r!=old['files']['boundary_oracle.py']]
   with self.assertRaises(ValueError):baseline_math(bad,reader)
   (root/'boundary_oracle.py').write_bytes(b'changed\n')
   with self.assertRaises(ValueError):baseline_math(m,reader)
 def test_15_actual_aggregate_software_relative_frontdoor(self):
  import software
  m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes());IPC=software.aggregate_source_frontdoor(m)
  self.assertEqual(m['files']['ipc_controls.py']['sha256'],'6f815ee70eee276f2a5c8f6ffd7d3ba82e754eb9aac55ee7d5408100241037a2');self.assertTrue(callable(IPC.run));self.assertIn(IPC.SCANNER_REF,m['dependencies'])
  bad=copy.deepcopy(m);del bad['files']['ipc_controls.py']
  with self.assertRaises(ValueError):software.aggregate_source_frontdoor(bad)
  bad=copy.deepcopy(m);bad['files']['ipc_controls.py']['sha256']='0'*64
  with self.assertRaises(ValueError):software.aggregate_source_frontdoor(bad)
  bad=copy.deepcopy(m);bad['dependencies'].remove(IPC.SCANNER_REF)
  with self.assertRaises(ValueError):software.aggregate_source_frontdoor(bad)
 def test_16_actual_cpu_parser_overlay_environment_chain(self):
  m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes());component=Path(m['plugin_source']['path']).parent if sys.platform=='linux'else P.parent/'mxr-block-refinement-new48h-044';donor=P.parent/'mxr-r118-capture-launch-20261013-003'
  # The whole original source/entry mirror and actual parser_environment run;
  # there is no test-side environment_original assignment or fake E object.
  argv=[sys.executable,'-I','-B',str(P/'entry_cold_controls.py'),'--entry-source',str(P/'entry.py'),'--component-root',str(component),'--donor-root',str(donor),'--parser-source',str(P/'parser_probe.py')]
  r=subprocess.run(argv,capture_output=True,text=True,timeout=30);self.assertEqual(r.returncode,0,r.stderr);value=json.loads(r.stdout);self.assertTrue(value['actual_parser_environment']);self.assertTrue(value['original_environment_bound_by_overlay']);self.assertTrue(value['current_interpreter_discovery']);self.assertFalse(value['NPU'])
  with tempfile.TemporaryDirectory()as td:
   bad=Path(td)/'entry.py';body=(P/'entry.py').read_bytes();self.assertEqual(body.count(b';o.environment_original=o.environment'),1);bad.write_bytes(body.replace(b';o.environment_original=o.environment',b''));args=list(argv);args[args.index('--entry-source')+1]=str(bad)
   r=subprocess.run(args,capture_output=True,text=True,timeout=30);self.assertNotEqual(r.returncode,0);self.assertIn('environment_original',r.stderr)
 def test_17_registry_moved_to_admitted_N1_and_actual_host_consumer(self):
  metadata=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes());self.assertFalse(metadata['local_software']['CPU_actual_general_plugins_probe_pending']);self.assertTrue(metadata['local_software']['actual_N1_general_plugins_probe_pending'])
  sp=importlib.util.spec_from_file_location('_actual073R5host',P/'host_ticket.py');H=importlib.util.module_from_spec(sp);sp.loader.exec_module(H);sr={'path':'source','bytes':1,'sha256':'a'}
  cpu=dict(schema='mxr.devicefree-source-argv-pending-registry/v073r5',source=sr,actual_registry_pending=True,actual_CPU_registry_plugin_child=None,receiver_registered=False,runtime_parser_executed=False,NPU_initialized=False,Devices=[]);self.assertTrue(H.registry_boundary(None,'cpu',cpu,sr))
  for bad in(dict(cpu,actual_registry_pending=False),dict(cpu,actual_CPU_registry_plugin_child={'fake':'pass'})):
   with self.assertRaises(ValueError):H.registry_boundary(None,'cpu',bad,sr)
  child=dict(schema='mxr.actual-registry-plugin-child/v073r6',source=sr,full_install_deferred=True,no_worker_runtime_receipt=True,receiver_registered=True,model_forward_executed=False,NPU_numeric=False,model_qualified=False,actual_visible_devices='0,1,2,3');rr=dict(path=str(H.OUT/'candidate'/'N1_REGISTRY_CHILD.json'),bytes=1,sha256='b');n1=dict(schema='mxr.actual-native-preflight/v073r5',source=sr,registry_stage='N1-after-all4-tiny-before-parser-and-weights',actual_N1_registry_plugin_child=rr);seen=[]
  child['actual_cann']=dict(bootstrap_source_ref=dict(path=str(H.LOW/'kivi-direct-d8-fp32-model-boundary-r87-v1-011'/'cann_python.py'),bytes=4503,sha256='cee927f1107fe6714e86ab1dceecafeff800980a00b8df9fcc47ff6831ba5104'),helper_sha='cee927f1107fe6714e86ab1dceecafeff800980a00b8df9fcc47ff6831ba5104',isolated_child_explicit_path=True)
  def read(r):self.assertEqual(r,rr);seen.append(r);return child
  self.assertTrue(H.registry_boundary(types.SimpleNamespace(obj=read),'n1',n1,sr));self.assertEqual(seen,[rr])
  for key,value in(('source',{}),('actual_visible_devices',''),('full_install_deferred',False),('model_forward_executed',True)):
   bad=dict(child,**{key:value})
   with self.assertRaises(ValueError):H.registry_boundary(types.SimpleNamespace(obj=lambda r:bad),'n1',n1,sr)
  tree=ast.parse((P/'parser_probe.py').read_bytes());cpu_static=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='cpu_static');self.assertNotIn("load('registry_child_probe.py').run",ast.get_source_segment((P/'parser_probe.py').read_text(),cpu_static));main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main');body=ast.get_source_segment((P/'parser_probe.py').read_text(),main);self.assertLess(body.index('canaries=tiny_canaries()'),body.index("registry_child=load('registry_child_probe.py').run"));self.assertLess(body.index("registry_child=load('registry_child_probe.py').run"),body.index("api=importlib.import_module('vllm.entrypoints.openai.api_server')"))
 def test_18_actual_isolated_child_CANN_bootstrap_source_and_order(self):
  def module(n):
   s=importlib.util.spec_from_file_location('_actual073R6_'+n[:-3],P/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
  E=module('entry.py');A=module('registry_child_probe.py');E.OLD=Path(E.OLD)if sys.platform=='linux'else P.parent/'mxr-r118-capture-launch-20261013-003'
  text=(P/'registry_child_probe.py').read_text();tree=ast.parse(text);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main');body=ast.get_source_segment(text,main);self.assertLess(body.index('cann=installed_cann(E)'),body.index('from vllm.plugins import load_general_plugins'));self.assertIn("guest=E.private('guest_capture_entry.py',o)",text)
  with tempfile.TemporaryDirectory()as td:
   E.LOW=Path(td);up=E.LOW/'kivi-direct-d8-fp32-model-boundary-r87-v1-011';up.mkdir();(up/'cann_python.py').write_bytes(b'raise AssertionError("must never load unpinned helper")\n')
   with self.assertRaisesRegex(ValueError,'helper source mismatch'):A.installed_cann(E)
  self.assertNotIn('acl',sys.modules)
if __name__=='__main__':unittest.main()
