import ast,copy,hashlib,importlib.util,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import common095 as C,owner095 as O,owned_cpu095 as CPU
class Tests(unittest.TestCase):
 def test_exact_unchanged_Lane_methods(self):
  donor=P.parent/'deltalog-split-scale-numeric-new24h-20261016-069-repair1/host.py';nodes=O.exact_methods(C.ref(donor));tree=ast.parse(donor.read_bytes());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main');ge=next(n for n in main.body if isinstance(n,ast.ClassDef)and n.name=='GE')
  for n in nodes:self.assertEqual(ast.dump(n),ast.dump(next(v for v in ge.body if getattr(v,'name',None)==n.name)))
 def test_CPU_actual_create_and_Docker_wrapper(self):
  argv=CPU.create_argv(7,{'/src':('/src',False),'/out':('/adakv-results',True)},{'ASCEND_RT_VISIBLE_DEVICES':''},'test',['-I','-B','cpu095.py'])
  self.assertNotIn('--device',argv);self.assertIn('--read-only',argv);self.assertEqual(argv[argv.index('--memory')+1],str(8*2**30));self.assertEqual(CPU.docker_argv(['/usr/bin/docker','ps'])[:3],['/usr/bin/prlimit','--as=unlimited','--'])
  with self.assertRaises(ValueError):CPU.docker_argv(['/bin/sh','docker'])
 def test_actual_DEVICE_to_SMI_join(self):
  cid='a'*64;plan={'sha256':'b'};argv=['python','-I'];proof=dict(physical=5,namespace_pids=[99,1],start_ticks=88,cgroup='/docker/'+cid,argv=argv);dv=dict(logical=0,physical_declared_by_plan=5,plan=plan,canary=[4.,5.],physical_proof_must_be_host_owned=True,cgroup='/docker/'+cid,pid=1,stat='1 (python) '+' '.join(['R']+['0']*18+['88']))
  self.assertEqual(O.device_proof(dv,dict(owned_process_proofs=[proof]),plan,cid,argv),proof)
  for key,value in(('physical',4),('namespace_pids',[99,2]),('start_ticks',89),('cgroup','foreign'),('argv',['foreign'])):
   q=dict(proof);q[key]=value
   with self.assertRaises(ValueError):O.device_proof(dv,dict(owned_process_proofs=[q]),plan,cid,argv)
 def test_whole_parent_cap_and_missing_source_reject(self):
  with tempfile.TemporaryDirectory()as td:
   p=Path(td);(p/'cpu').mkdir();(p/'numeric').mkdir();(p/'cpu/x').write_bytes(b'abc');(p/'numeric/x').write_bytes(b'def');self.assertEqual(CPU.output_scan(p),6);self.assertEqual(O.scan(p),6);r=C.ref(p/'cpu/x');C.checked(r);r['sha256']='0'*64
   with self.assertRaises(ValueError):C.checked(r)
 def test_cold_ON_actual_source_build_mount_fixture_to_CPU_dependency(self):
  # Real CPU entry/main + all real source/Ref readers, not mocked C.source or
  # Meta results. Deliberately stop at first torch import: NOT compiled Meta.
  with tempfile.TemporaryDirectory()as td:
   td=Path(td);auth=td/'authority.json';auth.write_text(json.dumps(dict(start_epoch=1792134133,cutoff_epoch=1792220533)));library=td/'software-only-not-a-DSO';library.write_bytes(b'not loaded');kernel=td/'kernel.json';kernel.write_text('{}');build=td/'build.json';build.write_text(json.dumps(dict(schema='deltalog-split-scale-actual-build/v051',source_manifest=C.ref(kernel),primary=None,Devices=[],artifacts=[dict(library=C.ref(library)),dict(library=C.ref(library))])))
   m=dict(schema='deltalog.graph-owned-source/v095',root=str(P),default_enabled=False,prepared_only=False,files={q.name:C.ref(q)for q in P.glob('*.py')},authority_ref=C.ref(auth),build_ref=C.ref(build),kernel_source_ref=C.ref(kernel),production_library=C.ref(library),debug_library=C.ref(library))
   src=td/'SOURCE.json';src.write_text(json.dumps(m));wrapper=td/'cold.py';wrapper.write_text("import sys,builtins,importlib.util,json\nfrom pathlib import Path\np=Path(sys.argv[1]);sys.path.insert(0,str(p.parent))\ns=importlib.util.spec_from_file_location('actual095cpu',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)\nold=builtins.__import__\ndef imp(name,*a,**k):\n if name=='torch':raise SystemExit(73)\n return old(name,*a,**k)\nbuiltins.__import__=imp\nsys.argv=[str(p),*sys.argv[2:]]\nm.main()\n")
   env=dict(os.environ,TORCH_DEVICE_BACKEND_AUTOLOAD='0',ASCEND_RT_VISIBLE_DEVICES='')
   argv=[sys.executable,'-I','-B',str(wrapper),str(P/'cpu095.py'),'--execute','--source-ref',json.dumps(C.ref(src)),'--output',str(td/'preflight')]
   r=subprocess.run(argv,capture_output=True,text=True,env=env,timeout=20);self.assertEqual(r.returncode,73,r.stderr)
   bad=json.loads(src.read_text());bad['files']['graph094.py']['sha256']='0'*64;src.write_text(json.dumps(bad));argv[argv.index('--source-ref')+1]=json.dumps(C.ref(src));r=subprocess.run(argv,capture_output=True,text=True,env=env,timeout=20);self.assertNotEqual(r.returncode,73);self.assertIn('exact bytes/SHA',r.stderr)
 def test_cold_default_OFF_all_entries(self):
  for n in('bind095.py','owned_cpu095.py','owner095.py','cpu095.py','guest095.py','consume095.py'):
   r=subprocess.run([sys.executable,'-I','-B',str(P/n)],capture_output=True,text=True,timeout=10);self.assertEqual(r.returncode,0,r.stderr)
if __name__=='__main__':unittest.main()
