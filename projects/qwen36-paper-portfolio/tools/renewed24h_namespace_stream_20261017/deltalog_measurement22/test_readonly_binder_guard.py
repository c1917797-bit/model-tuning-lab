"""Only software argv/proc fixtures; no real resource admission or numerical PASS."""
import ast,hashlib,json,os,subprocess,sys,tempfile,types,unittest
from pathlib import Path,PurePosixPath
from unittest.mock import patch
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import readonly_binder_guard as G

class GuardControls(unittest.TestCase):
 def argv(self):
  core='/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061';r=dict(path=core+'/run-numeric16-MAIN-20261016-NEW24H-088-repair6-repair2-001/RESULT.json',bytes=1667,sha256='7b10472808da9c409dca97e4f36ff577cf4d090db95c90b556d0bf680f4d25fe')
  tr=dict(sha256='a'*64);program=str(P/'bind_source.py')
  argv=['/usr/bin/python3','-I','-B',program,'--execute','--template-sha256',tr['sha256']]
  for key in G.OPTIONS[1:]:argv +=[key,json.dumps(r)]
  return argv,program,tr,r
 def test_complete_binder_argv_old_predicate_false_positive(self):
  argv,program,tr,r=self.argv();self.assertTrue(G.parse_arguments(argv,program,tr))
  self.assertTrue(G.original_match([a.encode()for a in argv],b'/old/088',[str(PurePosixPath(r['path']).parent)]))
  evidence=json.loads((P/'READONLY_ARGV_BOUNDARIES.json').read_bytes());actual=evidence['old_R18_exact_registered_bind_argv']
  self.assertTrue(G.parse_arguments(actual,actual[3],evidence['old_R18_template']))
  old_leaf=str(PurePosixPath(json.loads(actual[10])['path']).parent)
  self.assertTrue(G.original_match([a.encode()for a in actual],b'/old/088',[old_leaf]))
  # Source-proved future host/guest CLI data is outside the closed088 command
  # prefix. No non-binder exception is installed for these execution paths.
  for value in(evidence['capture_source'],evidence['upstream_source']):
   self.assertFalse(G.original_match([value.encode()],b'/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-sameinitial-native-contract-new24h-v1-088-repair6-repair2',[old_leaf]))
 def test_unknown_execution_and_extra_arguments_retain_rejection(self):
  a,p,tr,r=self.argv()
  bad=[a+['--output','/old/leaf'],a[:3]+['/unknown/run.py']+a[4:],a[:1]+['-c','print(1)']+a[3:],a[:1]+['-m','old.producer']+a[3:],a[:1]+a[2:]]
  x=list(a);x[8]='null';bad.append(x)
  x=list(a);x[8]=json.dumps(dict(r,unexpected=True));bad.append(x)
  x=list(a);x[4]='--source-audit';bad.append(x)
  for x in bad:
   with self.subTest(argv=x):self.assertFalse(G.parse_arguments(x,p,tr))
 def scan_fixture(self,allow,write_fd=False,write_map=False):
  temp=tempfile.TemporaryDirectory();root=Path(temp.name);proc=root/'123';proc.mkdir();(proc/'fd').mkdir();(proc/'fdinfo').mkdir();argv,_,_,r=self.argv();b=b'\0'.join(x.encode()for x in argv)+b'\0';(proc/'cmdline').write_bytes(b);(proc/'maps').write_text('')
  protected=str(PurePosixPath(r['path']).parent)
  if write_fd:
   (proc/'fd/7').write_text('');(proc/'fdinfo/7').write_text('flags:\t02\n')
  if write_map:(proc/'maps').write_text('1000-2000 rw-s 0 00:01 1 '+protected+'/tensor.pt\n')
  raw=(P/'readonly_guard_original119.py').read_text(encoding='utf8');K=types.ModuleType('_fixture119');K.__file__=str(P/'readonly_guard_original119.py');exec(compile(raw,K.__file__,'exec'),K.__dict__)
  K.Path=lambda x:root if x=='/proc'else Path(x);K.SOURCE=dict(path='/old/088/SOURCE_MANIFEST.json');K.leaf=lambda i:PurePosixPath(protected);K.PHASES=('a','b','c')
  seal=types.SimpleNamespace(canonical=lambda sr:(K,{}),failclosed_tree=lambda text:text)
  guard=G.Guard.__new__(G.Guard);guard.accept=lambda p,b:allow;guard.install(seal);K,_=seal.canonical({})
  original_link=os.readlink
  with patch.object(os,'O_ACCMODE',3,create=True),patch.object(os,'readlink',side_effect=lambda p:protected+'/tensor.pt'if Path(p)==proc/'fd/7'else original_link(p)):
   try:return K.no_writers()
   finally:temp.cleanup()
 def test_same_PID_FD_and_maps_are_not_exempt(self):
  self.assertTrue(self.scan_fixture(True)['no_original_commands'])
  with self.assertRaisesRegex(ValueError,'original088'):self.scan_fixture(False)
  with self.assertRaisesRegex(ValueError,'write FD'):self.scan_fixture(True,write_fd=True)
  with self.assertRaisesRegex(ValueError,'writable retained'):self.scan_fixture(True,write_map=True)
 def test_exact_program_exe_and_stable_process_identity(self):
  argv,program,tr,r=self.argv();g=G.Guard.__new__(G.Guard);g.argv=argv;g.program=dict(path=program,bytes=Path(program).stat().st_size,sha256=hashlib.sha256(Path(program).read_bytes()).hexdigest());g.template=tr;g.exe=Path(sys.executable).resolve();g.verified=[];g.pid=123;g.start='100'
  def checked(x):
   if x==g.program:self.assertEqual(hashlib.sha256(Path(x['path']).read_bytes()).hexdigest(),x['sha256'])
   else:self.assertIn(x,(tr,r))
  g.O=types.SimpleNamespace(obj_file=checked,obj=checked,need=lambda v,m:None if v else (_ for _ in()).throw(ValueError(m)))
  with tempfile.TemporaryDirectory()as d:
   p=Path(d)/'123';p.mkdir();b=b'\0'.join(a.encode()for a in argv)+b'\0';(p/'cmdline').write_bytes(b);(p/'stat').write_text('123 (python) '+' '.join(['R']+['0']*18+['100']))
   original_readlink=G.os.readlink
   def only_proc_exe(values):
    values=iter(values)
    def readlink(path,*args,**kwargs):
     if Path(path)==p/'exe':return next(values)
     return original_readlink(path,*args,**kwargs)
    return readlink
   with patch.object(G.os,'readlink',side_effect=only_proc_exe([sys.executable,sys.executable])):self.assertTrue(g.accept(p,b))
   with patch.object(G.os,'readlink',side_effect=only_proc_exe([sys.executable,'/changed/python'])),self.assertRaises(ValueError):g.accept(p,b)
   with patch.object(G.os,'readlink',side_effect=only_proc_exe(['/unknown/python'])):self.assertFalse(g.accept(p,b))
   self.assertFalse(g.accept(Path(d)/'124',b))
   g.start='101';self.assertFalse(g.accept(p,b));g.start='100'
   mutated=b.replace(b'--execute',b'--unknown');self.assertFalse(g.accept(p,mutated))
 def test_actual_fresh_I_default_off_no_binder_exception(self):
  q=subprocess.run([sys.executable,'-I','-B',str(P/'bind_source.py')],capture_output=True,text=True,timeout=10)
  self.assertEqual(q.returncode,0,q.stderr);self.assertEqual(q.stdout.strip(),'disabled')

if __name__=='__main__':unittest.main()
