"""Whole original source inverse + complete-scan races; no backend or device."""
import ast,errno,hashlib,json,os,shutil,tempfile,types,unittest
from pathlib import Path
from unittest import mock
import output_scan131r8 as M
P=Path(__file__).parent

def actual_safety():
 path=P/'evidence/original025_safety_host.py';tree=ast.parse(path.read_bytes());cls=next(x for x in tree.body if isinstance(x,ast.ClassDef)and x.name=='Controller');method=next(x for x in cls.body if isinstance(x,ast.FunctionDef)and x.name=='resources')
 S=types.ModuleType('actual025_scan_fixture');S.__file__=str(path);S.Path=Path;S.json=json;S.shutil=shutil;S.os=os;S.RESERVE=8*2**30;S.HOST_MEM=512*2**20;S.MEM=48*2**30;S.WORKSPACE=32*2**30
 S.DOCKER='/usr/bin/docker';S.c=types.SimpleNamespace(require=M.need);S.H=types.SimpleNamespace(cpu_view=lambda pid:{'host':True},daemon_view=lambda:{'daemon':True});S.cpu_admission=lambda h,d:dict(stable=True)
 exec(compile(ast.Module(body=[method],type_ignores=[]),str(path),'exec'),S.__dict__);S.Controller=type('Controller',(),dict(resources=S.__dict__.pop('resources')))
 return S

class Tests(unittest.TestCase):
 def test_actual_host_load_before_mkdir_then_first_pin_and_replacement_reject(self):
  host=(P/'host090.py').read_text()
  self.assertLess(host.index('c,S,H,pairs=load(a.output)'),host.index('a.output.mkdir'))
  with tempfile.TemporaryDirectory()as td:
   root=Path(td)/'fresh';self.assertFalse(root.exists())
   S=actual_safety();M.install(S.c,S,root);scan=S._SCAN_BUDGET
   self.assertIsNone(scan.identity);self.assertFalse(root.exists())
   root.mkdir(mode=0o700);leaf=root/'dense';leaf.mkdir();(leaf/'actual').write_bytes(b'123')
   ctl=types.SimpleNamespace(out=leaf,remaining=lambda **kwargs:1.)
   self.assertEqual(scan.used(ctl),3);pinned=scan.identity;self.assertEqual(pinned,M.root_identity(root))
   root.rename(Path(td)/'retained-original');root.mkdir();leaf.mkdir()
   self.assertNotEqual(M.root_identity(root),pinned)
   with self.assertRaises(ValueError):scan.used(ctl)
   self.assertEqual(scan.identity,pinned)
 def setup_scan(self,td):
  root=Path(td);leaf=root/'dense';leaf.mkdir();(leaf/'real').write_bytes(b'abc')
  ctl=types.SimpleNamespace(out=leaf,remaining=lambda **kwargs:1.)
  scan=M.Scanner(root)
  return root,leaf,ctl,scan
 def invoke(self,scan,ctl):
  if os.name!='nt':return scan.used(ctl)
  original=M.os.open
  def open_(p,flags,*args):
   if Path(p).is_dir():return original(Path(p)/'OUTPUT-SCAN-RACES.jsonl',os.O_RDWR)
   return original(p,flags,*args)
  with mock.patch.object(M.os,'open',side_effect=open_):return scan.used(ctl)
 def test_complete_success_and_all_bytes(self):
  with tempfile.TemporaryDirectory()as td:
   root,leaf,ctl,scan=self.setup_scan(td);nested=leaf/'compiler';nested.mkdir();(nested/'x').write_bytes(b'12345')
   self.assertEqual(self.invoke(scan,ctl),sum(p.stat().st_size for p in root.rglob('*')if p.is_file()));self.assertEqual(ctl._output_scan_last['attempts'],1);self.assertFalse(ctl._output_scan_last['atomic_snapshot'])
 def test_inside_enoent_restarts_entire_tree_and_journal_is_counted(self):
  with tempfile.TemporaryDirectory()as td:
   root,leaf,ctl,scan=self.setup_scan(td);real=os.scandir;calls=[]
   def scandir_(path):
    calls.append(Path(path))
    if len(calls)==1:
     class Gone:
      def stat(self,**kwargs):raise FileNotFoundError(errno.ENOENT,'removed entry stat',str(leaf/'bishengir-compile-example'))
     class Context:
      def __enter__(self):return iter([Gone()])
      def __exit__(self,*args):pass
     return Context()
    return real(path)
   with mock.patch.object(M.os,'scandir',scandir_):total=self.invoke(scan,ctl)
   journal=leaf/'OUTPUT-SCAN-RACES.jsonl';self.assertEqual(total,3+journal.stat().st_size);self.assertEqual(calls[:2],[root,root]);self.assertEqual(ctl._output_scan_last['attempts'],2)
   row=json.loads(journal.read_bytes());self.assertTrue(row['partial_sum_discarded']);self.assertEqual(row['errno'],2)
 def test_third_enoent_fails_closed_without_partial_sum(self):
  with tempfile.TemporaryDirectory()as td:
   root,leaf,ctl,scan=self.setup_scan(td);count=[]
   def scandir_(*args):
    count.append(1)
    raise FileNotFoundError(2,'gone',str(leaf/'gone'))
   with mock.patch.object(M.os,'scandir',scandir_):
    with self.assertRaises(FileNotFoundError):self.invoke(scan,ctl)
   self.assertEqual(len(count),3);self.assertFalse(hasattr(ctl,'_output_scan_last'));self.assertEqual(len((leaf/'OUTPUT-SCAN-RACES.jsonl').read_text().splitlines()),3)
 def test_outside_unknown_permission_and_deadline_reject(self):
  with tempfile.TemporaryDirectory()as td:
   root,leaf,ctl,scan=self.setup_scan(td)
   for error in(FileNotFoundError(2,'outside',str(root.parent/'foreign')),FileNotFoundError(2,'unknown'),PermissionError(13,'denied',str(leaf/'real'))):
    with mock.patch.object(M.os,'scandir',side_effect=error):
     with self.assertRaises((ValueError,PermissionError)):self.invoke(scan,ctl)
   ctl.remaining=lambda **kwargs:0.
   with self.assertRaises(ValueError):self.invoke(scan,ctl)
   self.assertFalse((leaf/'OUTPUT-SCAN-RACES.jsonl').exists())
 def test_actual_whole_source_inverse_and_wrong_source_refuse(self):
  raw=(P/'evidence/original025_safety_host.py').read_bytes();result=M.derive(raw)
  self.assertEqual(result.replace(M.REPLACEMENT,M.EXPRESSION).encode(),raw)
  self.assertEqual(result.count('used='+M.REPLACEMENT),1)
  with self.assertRaises(ValueError):M.derive(raw+b'\n')
 def test_actual_resources_body_installed_preserves_limits_and_summary(self):
  with tempfile.TemporaryDirectory()as td:
   root,leaf,ctl,scan=self.setup_scan(td);S=actual_safety()
   M.install(S.c,S,root);obj=S.Controller();obj.out=leaf;obj.cpu=None;obj.remaining=lambda **kwargs:1.;obj.call=lambda *a:({'stdout':'{"NCPU":8}'},{'engine':'unchanged'});obj.rss=lambda:{'rss':'unchanged'}
   old=Path.read_text
   def read(p,*a,**kw):
    if p.as_posix()=='/proc/meminfo':return 'MemAvailable: 200000000 kB\nMemTotal: 300000000 kB\nHugetlb: 0 kB\nSwapTotal: 0 kB\nSwapFree: 0 kB\n'
    return old(p,*a,**kw)
   with mock.patch.object(Path,'read_text',read),mock.patch.object(shutil,'disk_usage',return_value=types.SimpleNamespace(free=100*2**30)):
    value=obj.resources();self.assertEqual(value['output_bytes'],3);self.assertEqual(value['rss'],'unchanged');self.assertEqual(value['output_allowance_bytes'],32*2**30);self.assertEqual(value['output_scan']['attempts'],1)
    with mock.patch.object(S._SCAN_BUDGET,'used',return_value=32*2**30+1):
     with self.assertRaises(ValueError):obj.resources()

if __name__=='__main__':unittest.main()
