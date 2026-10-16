"""Six source/metadata controls; no device emulation or qualification."""
import ast,copy,hashlib,importlib.util,json,re,subprocess,sys,tempfile,types,unittest
from pathlib import Path,PurePosixPath
from unittest.mock import patch
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
def load(name):
 s=importlib.util.spec_from_file_location('_047test_'+name[:-3],P/name);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class Contract(unittest.TestCase):
 def test_actual_full_native_argv_and_cold_preflight_import(self):
  import dis,symtable
  fixed=load('parser_probe.py');body=(P/'parser_probe.py').read_text();table=symtable.symtable(body,str(P/'parser_probe.py'),'exec')
  scope=next(x for x in table.get_children()if x.get_name()=='main');self.assertFalse(scope.lookup('importlib').is_local())
  instructions=list(dis.get_instructions(fixed.main));calls=[x for x in instructions if x.argval=='importlib'];self.assertTrue(calls);self.assertTrue(all(x.opname=='LOAD_GLOBAL'for x in calls))
  original=body.replace(' import importlib.metadata as plugin_metadata\n',' import importlib.metadata\n').replace('for dist in plugin_metadata.distributions(path=[str(component_root)])','for dist in importlib.metadata.distributions(path=[str(component_root)])')
  prior={};exec(compile(original,'actual062-parser-scope-negative','exec'),dict(__file__=str(P/'parser_probe.py')),prior);oldcode=list(dis.get_instructions(prior['main']))
  firstload=next(i for i,x in enumerate(oldcode)if x.argval=='importlib'and x.opname.startswith('LOAD_FAST'));firststore=next(i for i,x in enumerate(oldcode)if x.argval=='importlib'and x.opname=='STORE_FAST');self.assertLess(firstload,firststore)
  # Retain the actual source's first importlib call and later local-import
  # statement in a software-only prefix. Import only stdlib json, no HAL/vLLM.
  def prefix(source):
   tree=ast.parse(source);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main');call=next(n for n in ast.walk(fn)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and isinstance(n.func.value,ast.Name)and n.func.value.id=='importlib'and n.func.attr=='import_module');call=copy.deepcopy(call);call.args=[ast.Constant('json')]
   imp=next(n for n in ast.walk(fn)if isinstance(n,ast.Import)and n.names[0].name=='importlib.metadata');imp=copy.deepcopy(imp)
   small=ast.FunctionDef(name='prefix',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=[ast.Assign(targets=[ast.Name(id='result',ctx=ast.Store())],value=call),imp,ast.Return(value=ast.Name(id='result',ctx=ast.Load()))],decorator_list=[])
   module=ast.fix_missing_locations(ast.Module(body=[small],type_ignores=[]));ns={'importlib':__import__('importlib')};exec(compile(module,'actual-source-parser-import-prefix','exec'),ns);return ns['prefix']
  with self.assertRaises(UnboundLocalError):prefix(original)()
  self.assertEqual(prefix(body)().__name__,'json')
  E=load('entry.py');Q=load('parser_probe.py');E.OLD=P.parent/'mxr-r118-capture-launch-20261013-003'
  if not E.OLD.is_dir():E.OLD=Path('/cache/cch/qwen36-paper-preparation-20261007/lowbit/mxr-r118-capture-launch-20261013-003')
  o=E.overlay();up=P/'actual011';native=o.native_argv(up,8252)
  self.assertNotEqual(native[-2:],['--worker-cls',o.NATIVE_WORKER])
  self.assertEqual(Q.native_argv_contract(native,o,up)['worker_cls'],o.NATIVE_WORKER)
  self.assertEqual(native[-6:],['--load-format','safetensors','--safetensors-load-strategy','lazy','--model-loader-extra-config','{"enable_multithread_load":false}'])
  changes=[native+['--worker-cls',o.NATIVE_WORKER],native[:],native[:],native+['--unknown','x'],native[:],native+['--load-format','safetensors']]
  changes[1][changes[1].index('--worker-cls')+1]='foreign.Worker'
  i=changes[2].index('--worker-cls');del changes[2][i:i+2]
  changes[4][changes[4].index('--max-num-seqs')+1]='16'
  for bad in changes:
   with self.assertRaises(ValueError):Q.native_argv_contract(bad,o,up)
  # Actual isolated module execution (not a fixture-inserted sys.path) must make
  # the same sibling import used by --preflight available before filesystem IO.
  code="import runpy,sys;runpy.run_path(sys.argv[1],run_name='source_only_preflight');import combined_budget;assert combined_budget.INITIAL==int(227.5*2**30);print('actual-preflight-sibling-import')"
  r=subprocess.run([sys.executable,'-I','-B','-c',code,str(P/'raw_filesystem.py')],cwd=P.parent,capture_output=True,text=True,timeout=10)
  self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(r.stdout.strip(),'actual-preflight-sibling-import')

 def test_live_new24h_authority_and_all_executed_clocks(self):
  A=load('authority_contract.py');b=(P/'authority/NEW24H_AUTHORITY_20261016.json').read_bytes();v=A.validate(A.REF,b)
  self.assertEqual((A.START,A.CUT),(1792134133,1792220533));self.assertEqual(v['cutoff_epoch']-v['start_epoch'],86400)
  old=dict(A.REF,sha256='71211e77fc870a8c94a7f80424925e38e1e092b9374d3a6a1066960ea74fbf99')
  with self.assertRaises(ValueError):A.validate(old,b)
  with self.assertRaises(ValueError):A.validate(A.REF,b.replace(b'1792220533',b'1792135097'))
  H=load('host_ticket.py');E=load('entry.py');B=load('atomic/barrier.py')
  self.assertEqual((H.START,H.CUT,E.START,E.CUT,B.CUT),(A.START,A.CUT,A.START,A.CUT,A.CUT));self.assertEqual(H.AUTH_SHA,E.AUTH_SHA);self.assertEqual(H.AUTH_SHA,A.REF['sha256'])
  m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes());self.assertEqual(m['window'],dict(start=A.START,cutoff=A.CUT));self.assertEqual(m['authority_ref'],A.REF);self.assertIn(A.REF,m['dependencies']);self.assertNotEqual(m['historical_authority_ref'],A.REF)
  # The old baseline must retain its original bytes/window, not be extended.
  self.assertIn(b'START,CUT=1791962297,1792135097',(P/'baseline048/entry.py').read_bytes())
 def test_actual044_metadata_discovery_and_single_installer_environment(self):
  root=P.parent/'mxr-block-refinement-new48h-044'
  if not root.is_dir():root=Path(json.loads((P/'SOURCE_MANIFEST.json').read_bytes())['plugin_source']['path']).parent
  code="import importlib.util,json,sys;s=importlib.util.spec_from_file_location('discovery',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);print(json.dumps(m.static_discovery(sys.argv[2]),sort_keys=True))"
  r=subprocess.run([sys.executable,'-I','-B','-c',code,str(P/'plugin_discovery.py'),str(root)],capture_output=True,text=True,timeout=15);self.assertEqual(r.returncode,0,r.stderr);v=json.loads(r.stdout);self.assertTrue(v['static_import']);self.assertFalse(v['register_called']);self.assertEqual(len(v['entrypoints']),2)
  with tempfile.TemporaryDirectory()as td:
   r=subprocess.run([sys.executable,'-I','-B','-c',code,str(P/'plugin_discovery.py'),td],capture_output=True,text=True,timeout=15);self.assertNotEqual(r.returncode,0);self.assertIn('both actual044 distribution entrypoints present',r.stderr)
  donor=P.parent/'mxr-r118-capture-launch-20261013-003'
  if not donor.is_dir():donor=Path('/cache/cch/qwen36-paper-preparation-20261007/lowbit/mxr-r118-capture-launch-20261013-003')
  cmd=[sys.executable,'-I','-B',str(P/'entry_cold_controls.py'),'--entry-source',str(P/'entry.py'),'--component-root',str(root),'--donor-root',str(donor)]
  r=subprocess.run(cmd,capture_output=True,text=True,timeout=20);self.assertEqual(r.returncode,0,r.stderr);cold=json.loads(r.stdout);self.assertTrue(cold['no_fixture_path_insertion']);self.assertTrue(cold['current_interpreter_discovery']);self.assertFalse(cold['register_called'])
  previous=P/'baseline048/entry.py';b=previous.read_bytes();self.assertEqual((len(b),hashlib.sha256(b).hexdigest()),(9940,'99fd5d43e9e987ad48ccbbf8bbaab6c075711ee240d9cee5b6480b203c8d6774'))
  cmd[cmd.index('--entry-source')+1]=str(previous);r=subprocess.run(cmd,capture_output=True,text=True,timeout=20);self.assertNotEqual(r.returncode,0);self.assertIn('same-interpreter plugin discovery absent',r.stderr)
  E=load('entry.py');D=load('plugin_discovery.py');s=importlib.util.spec_from_file_location('_048_real_common_env',root/'common_precision.py');cp=importlib.util.module_from_spec(s);s.loader.exec_module(cp)
  o=types.SimpleNamespace(environment_original=lambda base,*a:dict(base));m=dict(plugin_source={'software_only':True},raw_storage={'root':'/owned/raw'})
  with patch.object(E,'current',return_value=m),patch.dict(sys.modules,{'plugin_discovery':D}),patch.object(D,'component',return_value=(root,cp)):
   e=E.environment(o,{}, {},{'VLLM_PLUGINS':'ascend'},'/source','/owned','run')
  self.assertTrue(e['PYTHONPATH'].startswith(str(root)+':'));self.assertIn('mxr_common_precision044',e['VLLM_PLUGINS'].split(','));self.assertNotIn('mxr_block_refinement044',e['VLLM_PLUGINS'].split(','));self.assertIn('mxr_diag16_gdn_shadow',e['VLLM_PLUGINS'].split(','))
 def test_actual_two_leaf_candidate_create_inspect_and_foreign_RW_rejection(self):
  M=load('external_output_policy.py');source=Path('C:/Users/Huawei/AppData/Local/Temp/model036-controller-exact011-review/safety_host.py')
  if not source.is_file():
   manifest=P/'SOURCE_MANIFEST.json'
   if not manifest.exists():manifest=P/'SOURCE_TEMPLATE.json'
   source=Path(json.loads(manifest.read_bytes())['ownership_observation_refs']['safety']['path'])
  text,pairs=M.derive_safety(source.read_bytes());tree=ast.parse(text);nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in('create_argv','validate_inspect','labels','device_map')]
  c=types.SimpleNamespace(GIB=2**30,ROOT=Path('/repo'),IMAGE='sha256:image',require=M.need);n=dict(c=c,_EXTERNAL=M,MEM=48*2**30,OWNER='owner',PHYSICAL=(4,5,6,7),DOCKER='/usr/bin/docker',re=re,environment=lambda *a:dict(TMPDIR='/adakv-results',ASCEND_RT_VISIBLE_DEVICES='0,1,2,3'))
  exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual011-derived-create-inspect','exec'),n)
  e=dict(arm='candidate',algorithm_arm='capture',name='owner',cid='a'*64,source={'sha256':'x'},host_sha256='h',guest_cpus=[2,3,4,5],external_output_policy=True,external_output_root=M.OWN_CONTROL,mounts={'/adakv-results':(M.OWN_CONTROL+'/candidate',True),M.OWN_RAW:(M.OWN_RAW,True),'/source':('/source',False)})
  argv=n['create_argv'](e);self.assertIn('--read-only',argv);self.assertIn('max-size=16m',argv);self.assertIn('type=bind,source='+M.OWN_RAW+',destination='+M.OWN_RAW,argv)
  env=dict(n['environment'](),**M.environment(e));h=dict(ReadonlyRootfs=True,LogConfig=M.LOG,Privileged=False,Memory=48*2**30,MemorySwap=48*2**30,NanoCpus=4*10**9,CpusetCpus='2,3,4,5',IpcMode='private',NetworkMode='none',ShmSize=4*2**30,PidsLimit=2048,CapDrop=['ALL'],SecurityOpt=['no-new-privileges'],Devices=[dict(PathOnHost=p,PathInContainer=q,CgroupPermissions='rwm')for p,q in n['device_map']().items()])
  x=dict(Id=e['cid'],Image=c.IMAGE,Name='/owner',Config=dict(Image=c.IMAGE,Entrypoint=['/bin/bash'],Cmd=['-c','exec /bin/sleep infinity'],WorkingDir=str(c.ROOT),Labels=n['labels'](e),Env=[k+'='+v for k,v in env.items()]),HostConfig=h,Mounts=[dict(Type='bind',Destination=d,Source=p,RW=w)for d,(p,w)in e['mounts'].items()]);n['validate_inspect'](x,e)
  for mutate in(lambda z:z['mounts'].update({'/escape':('/foreign',True)}),lambda z:z['mounts'].update({M.OWN_RAW:(str(Path(M.OWN_RAW).parent),True)}),lambda z:z['mounts'].update({'/alias':(M.OWN_RAW,True)}),lambda z:z.update(arm='cpu-preflight')):
   bad=copy.deepcopy(e);mutate(bad)
   with self.assertRaises(ValueError):n['create_argv'](bad)
  bad=copy.deepcopy(x);bad['HostConfig']['ReadonlyRootfs']=False
  with self.assertRaises(ValueError):n['validate_inspect'](bad,e)
 def test_all_python_and_cold_I_entries(self):
  for f in P.rglob('*.py'):ast.parse(f.read_bytes())
  for n in('bind_source.py','host_ticket.py','entry.py','parser_probe.py','consume.py','software.py'):
   r=subprocess.run([sys.executable,'-I','-B',str(P/n)],capture_output=True,text=True,timeout=15);self.assertEqual(r.returncode,0,(n,r.stderr));self.assertFalse(json.loads(r.stdout)['enabled'])
 def test_one_opt_ledger_original_payload_and_reserve(self):
  C=load('combined_budget.py');self.assertEqual(C.INITIAL,int(227.5*2**30));C.check(C.INITIAL,0,0,True)
  for args in((C.INITIAL-1,0,0,True),(C.RESERVE-1,0,0,False),(C.INITIAL,C.CONTROL+1,0,False),(C.INITIAL,0,C.RAW+1,False)):
   with self.assertRaises(ValueError):C.check(*args)
 def test_helper_only_workspace_inverse(self):
  b=(P/'external_output_policy.py').read_bytes().split(b'\n\n# Source-frozen second payload leaf ONLY;')[0];original=b.replace(b'S.WORKSPACE==3*2**30',b'S.WORKSPACE==32*2**30');self.assertEqual((len(original),hashlib.sha256(original).hexdigest()),(7175,'f85f745cb9362d69e70cfd35a9c894d97fc7069297d3694c8b8c57107126191f'))
 def test_missing_actual_or_old012_cannot_qualify(self):
  A=load('admission047.py')
  for v in(None,{},dict(component_source={},component_owner={},component_terminal={},short_source={},short_owner={},short_terminal={})):
   with self.assertRaises((ValueError,KeyError,FileNotFoundError)):A.consume(v)
 def test_actual_template_to_original008_adapt(self):
  H=load('host_ticket.py');path=P/'SOURCE_MANIFEST.json';body=(path if path.exists()else P/'SOURCE_TEMPLATE.json').read_bytes();m=json.loads(body)
  self.assertEqual(m['runtime_identity']['owner'],m['runtime_identity']['run_id']);self.assertEqual(m['root'].split('/')[-1],P.name.replace('new24h-065','new24h-v1-065'))
  donor=Path('C:/Users/Huawei/AppData/Local/Temp/mxr-r118-proc-snapshot-repair-20261013-008/host_ticket.py')
  if not donor.exists():donor=Path(H.HOST_REF['path'])
  original=Path.read_bytes
  with patch.object(Path,'read_bytes',lambda q:body if q==P/'SOURCE_MANIFEST.json'else original(q)):
   text,pairs=H.adapt(donor.read_bytes().decode(),{},{});ast.parse(text)
   original_exact=H.exact;H.exact=lambda r:donor.read_bytes()if r==H.HOST_REF else original_exact(r)
   private,registered=H.bind({'software_contract_only':True},{},[])
   self.assertEqual(private.START,1792134133);self.assertEqual(private.CUTOFF,1792220533);self.assertEqual(private.PHASE,7200);self.assertEqual(private.CLEANUP_TOTAL,270);self.assertEqual(private.HERE,P);self.assertEqual(private.DEPLOY,H.DEPLOY);self.assertEqual(private.OUT,H.OUT);self.assertTrue(callable(private.run));self.assertEqual(len(registered),len(pairs))
  self.assertIn('PHASE, CLEANUP_TOTAL = 7200, 270',text);self.assertIn(H.OUT.as_posix(),text);self.assertIn('shared', (P/'combined_budget.py').read_text());self.assertGreater(len(pairs),25)
 def test_actual_worker_hook_and_complete_lifecycle(self):
  w=(P/'worker.py').read_text(encoding='utf8');c=(P/'consume.py').read_text(encoding='utf8')
  self.assertIn('block_refine.eager=observed',w);self.assertNotIn('safe_eager.eager=observed',w)
  self.assertIn('pool.max_bytes==512*1024**2',w);self.assertIn('boundaries=list(boundaries)',w)
  for x in("len(groups)==96 and len(decode)==192","actual prefill→decode same slot state","actual decode step1→step2 slot continuity","actual request exit/join slot reuse witnessed in every layer"):
   self.assertIn(x,c)
  self.assertIn("pass_gate=workout['pass']and workstate['pass']and am['pass']",c)
  self.assertIn('original_ideal_gate_pass',c)
  # Real observed callback ABI, without pretending a software callable is NPU.
  fn=next(n for n in ast.walk(ast.parse(w))if isinstance(n,ast.FunctionDef)and n.name=='observed');fn=copy.deepcopy(fn);fn.decorator_list=[]
  class Tensor:
   def detach(self):return self
   def cpu(self):return self
   def clone(self):return self
   def tolist(self):return[0,32768]
  f={};calls=[];t=Tensor();pool=types.SimpleNamespace(max_bytes=512*1024**2,max_entries=2)
  scope=dict(scope=types.SimpleNamespace(get=lambda:f),original_eager=lambda *a:(calls.append(a)or t),torch=types.SimpleNamespace(npu=types.SimpleNamespace(synchronize=lambda:None)),fingerprint=lambda *a:{'software_contract_only':True},need=lambda v,m:None if v else(_ for _ in()).throw(ValueError(m)),precision={'allow_hf32':False},plugin={'software_only':True})
  exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual047 observed callback','exec'),scope)
  self.assertIs(scope['observed']('solver',t,t,512,'bf16',pool,'backend',[0,32768]),t);self.assertEqual(len(calls),1);self.assertEqual(calls[0][-1],[0,32768]);self.assertIn('solve',f);self.assertEqual(f['block044']['pool_bytes'],512*1024**2)
 def test_actual_raw_parent_preflight_before_any_output_creation(self):
  F=load('raw_filesystem.py');C=load('combined_budget.py')
  cold=subprocess.run([sys.executable,'-I','-B',str(P/'raw_filesystem.py')],capture_output=True,text=True,timeout=10);self.assertEqual(cold.returncode,0,cold.stderr);self.assertEqual(json.loads(cold.stdout),dict(enabled=False,NPU=False))
  with tempfile.TemporaryDirectory()as td:
   root=Path(td).resolve();F.PARENT=root/'authorized';F.RAW=F.PARENT/'raw';out=root/'new-control'
   with patch.dict(sys.modules,{'combined_budget':C}),patch.object(F.os,'statvfs',return_value=types.SimpleNamespace(f_bavail=C.INITIAL,f_frsize=1),create=True):
    with self.assertRaisesRegex(ValueError,'MAIN must create exact authorized RAW parent'):F.preflight(out)
    self.assertFalse(out.exists());self.assertFalse(F.RAW.exists());self.assertFalse(F.PARENT.exists())
    F.PARENT.mkdir();note=F.preflight(out);self.assertTrue(note['parent_exists']);self.assertFalse(note['output_created']);self.assertFalse(out.exists());self.assertFalse(F.RAW.exists())
    out.mkdir()
    with self.assertRaisesRegex(ValueError,'never reuse failed output'):F.preflight(out)
    # The original prepare still owns only its exact RAW leaf after parent
    # preflight and inherited control mkdir, with the same complete ledger.
    result=F.prepare(out);self.assertEqual(result['budget'],216*2**30);self.assertTrue(F.RAW.is_dir())
    self.assertIn("leaf('raw_filesystem.py').preflight(OUT)",(P/'host_ticket.py').read_text())
 def test_actual_043R2_env_nullcwd_and_044_direct_terminals(self):
  A=load('admission047.py')
  for name,script in [('MXR043R2_TERMINAL_20261015.json','host_ticket.py'),('MXR044_TERMINAL_20261015.json','mainhost.py')]:
   path=P/'evidence'/name;b=path.read_bytes();tr=dict(path=str(path),bytes=len(b),sha256=hashlib.sha256(b).hexdigest());v=json.loads(b);r=v['operation']['result']['record']
   args=r['args'][2:]if script=='host_ticket.py'else r['args'];sr=dict(path=str(PurePosixPath(args[2]).parent/'SOURCE_MANIFEST.json'),bytes=87714,sha256='aba2ee727ab910f775028ec1ec9745b3fd06b57da133a14b059ff905badb7595')if script=='host_ticket.py'else A.argument_object(args[4])
   op='/opt/host/vnf/austinov/run-mxr-working-domain-model043-repair2-main-NEW48H_001/RESULT.json'if script=='host_ticket.py'else args[-1]+'/RESULT.json';owner=dict(path=op,bytes=1,sha256='not_needed_by_terminal_parser')
   self.assertTrue(A.terminal(tr,sr,owner,script))
   for mutate in (lambda z:z['operation']['result']['record'].update(cwd='/foreign'),lambda z:z['operation']['result']['record']['args'].insert(0,'LD_PRELOAD=/evil'),lambda z:z['operation'].update(targetPeerId='foreign'),lambda z:z['operation']['result']['record'].update(command='/bin/sh'),lambda z:z['operation']['result']['record'].update(exitCode=1)):
    bad=copy.deepcopy(v);mutate(bad)
    with patch.object(A,'obj',return_value=bad):
     with self.assertRaises((ValueError,KeyError)):A.terminal(tr,sr,owner,script)
   wrong=dict(sr,sha256='f'*64)
   with self.assertRaises(ValueError):A.terminal(tr,wrong,owner,script)
 def test_stricter_budget_actual_scanner_and_preserved_failure(self):
  C=load('combined_budget.py');self.assertEqual((C.CONTROL,C.RAW,C.RESERVE),(3*2**30,216*2**30,int(8.5*2**30)))
  m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes());self.assertEqual(m['budgets']['total_output_GiB'],3);self.assertEqual(m['raw_storage']['combined_opt_initial_GiB'],227.5)
  self.assertIn('no assurance caches/logs fit',m['resource_trial']['risk'])
  D=load('DERIVED_output_budget.py');self.assertEqual(D.LIMIT,3*2**30)
  with tempfile.TemporaryDirectory()as td:
   q=Path(td);f=q/'kept.log';f.write_bytes(b'01234567890');D.LIMIT=10
   if sys.platform=='linux':
    with self.assertRaises(ValueError):D.scan(q,socket_parent=[],ipc_source=D.IPC_SOURCE)
   else:
    # Windows cannot execute Linux dirfd fences. Same-image executes scan.
    with self.assertRaises(ValueError):D.consume(dict(schema='adakv.actual-output-budget-observation/v1',root=str(q),limit_bytes=10,output_bytes=11),q)
   self.assertEqual(f.read_bytes(),b'01234567890')
  expected={'consume.py':(10044,'54af4cbc64565e8f4622e949040c641fcd0af8afae353c69c00b4fdf125846cc'),'entry.py':(10156,'c1c9a099ed62e02b198ffc9ce8c61d949155162353bd5b3d206662305e7ae9cf'),'long_client.py':(3318,'b50e9cbccaa17d24df86c86942f642850d22b7c5dcdcb112ee2db5d739c24cbe'),'memory_observer.py':(3574,'4adb02fc2a906b54dfd6d16bdfd76fbb6a3a1811309a6a19a98a280a2b2b2dc1'),'stage_resources.py':(3452,'ee45ae8bbf121f16fb8ee02a7c3ff263d5ad5f93d155cc0d0c8113360fd60769'),'worker.py':(11134,'67559b0e97b3f0cad16325803f6f03f7878a40082a031a3c663aaffa398cd358')}
  # Exact sealed049 bytes, without requiring its sibling path/mount in guest.
  for n,want in expected.items():
   b=(P/n).read_bytes()
   if n=='entry.py':b=b.replace(b'1792134133,1792220533',b'1791962297,1792135097').replace(b'e8c373b6664a4bdd80012428b686227a6f15c0535b3c57a7654fb7996c02cf28',b'71211e77fc870a8c94a7f80424925e38e1e092b9374d3a6a1066960ea74fbf99')
   self.assertEqual((len(b),hashlib.sha256(b).hexdigest()),want,n+' protected math/lifecycle/original049 same-I path')
if __name__=='__main__':unittest.main()
