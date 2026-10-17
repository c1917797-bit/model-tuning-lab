"""Software/kernel read-only controls. No model, Docker or process signals."""
import ast,hashlib,os,stat,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import frontend_namespace131r18 as N
import identity_owner as I
P=Path(__file__).resolve().parent

class Tests(unittest.TestCase):
 def test_real_frontend_function_namespace_probe_and_stable_identity_contract(self):
  # Actual complete frontend() control, explicit software proc fixture. The
  # Linux tests below separately exercise real kernel magic links/FD resolver.
  cid='a'*64;pid=9001;initpid=9000;rawargv=b'/container/python\0-I\0server.py\0'
  def statline(pid,start):return str(pid)+' (python frontend) '+' '.join(['S']+['0']*18+[str(start)]+['0']*5)
  content={
   f'/proc/{initpid}/status':'Name: init\nNSpid:\t9000\t1\n',
   f'/proc/{pid}/status':'Name: python\nNSpid:\t9001\t57\n',f'/proc/{pid}/stat':statline(pid,123),
   f'/proc/{pid}/cgroup':'0::/docker/'+cid+'\n',f'/proc/{pid}/cmdline':rawargv,
   f'/proc/{initpid}/stat':statline(initpid,99),f'/proc/{initpid}/cgroup':'0::/docker/'+cid+'\n'}
  class Proc:
   def __init__(self,path):self.path=str(path)
   def __truediv__(self,v):return Proc(self.path+'/'+str(v))
   def read_text(self):return content[self.path]
   def read_bytes(self):return content[self.path]
  class C:
   PY=N.PY
   @staticmethod
   def require(v,m):N.need(v,m)
  class Controller:
   def __init__(self):self.cid=cid;self.inspects=0
   def inspect(self):self.inspects+=1;return dict(Id=cid,State=dict(Running=True,Pid=initpid)),{'software_inspect':self.inspects}
   def call(self,*a):return dict(exit_code=0,stdout='PID\n9000\n9001\n'),{'software_top':True}
  event=dict(identity=dict(pid=57,start_ticks=123,cgroup='guest-original'))
  proof=dict(namespace_executable='/usr/local/python3.12.13/bin/python3.12',executable={'sha256':'software-digest'})
  controller=Controller()
  with patch.object(I,'Path',Proc),patch.object(N,'verify',return_value=proof)as probe:
   out=I.frontend(C,SimpleNamespace(DOCKER='/usr/bin/docker'),controller,event)
   self.assertEqual(probe.call_args[0][0].path,'/proc/9001');self.assertEqual(probe.call_args[0][1].path,'/proc/9000')
   self.assertEqual(out['host']['executable'],proof['namespace_executable']);self.assertEqual(controller.inspects,2)
  for changed,value in ((f'/proc/{pid}/cgroup','0::/foreign'),(f'/proc/{pid}/stat',statline(pid,124))):
   old=content[changed];content[changed]=value
   with patch.object(I,'Path',Proc),patch.object(N,'verify',side_effect=AssertionError('must refuse before exe read')):
    with self.assertRaises(ValueError):I.frontend(C,SimpleNamespace(DOCKER='/usr/bin/docker'),Controller(),event)
   content[changed]=old
  def mutate(proc,init,expected):content[f'/proc/{pid}/cmdline']=rawargv+b'changed\0';return proof
  with patch.object(I,'Path',Proc),patch.object(N,'verify',side_effect=mutate):
   with self.assertRaises(ValueError):I.frontend(C,SimpleNamespace(DOCKER='/usr/bin/docker'),Controller(),event)

 def test_actual_r17_failure_shape_never_host_resolve_or_basename(self):
  owner=(P/'identity_owner.py').read_text();tree=ast.parse(owner)
  self.assertFalse(any(isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='resolve'for n in ast.walk(tree)))
  self.assertIn('NS.verify(p,init,c.PY)',owner);self.assertNotIn("exe.name.startswith",owner)
  self.assertEqual(N.guest_parts('/usr/local/python3.12.13/bin/python3.12'),['usr','local','python3.12.13','bin','python3.12'])
  for value in ('relative/python','//usr/bin/python','/usr/../bin/python','/usr/bin/python (deleted)','/usr\\bin/python','/usr/bin/python\x00'):
   with self.assertRaises(ValueError):N.guest_parts(value)
  # Exact independent review counterexample: sub can itself point elsewhere;
  # lexical sub/.. cancellation would differ from real kernel resolution.
  for value in ('sub/../python3.12','../bin/python3','/safe/../python3'):
   with self.assertRaises(ValueError):N.symlink_parts(value)
  self.assertEqual(N.symlink_parts('python3.12'),['python3.12'])

 @unittest.skipUnless(os.name=='posix','Linux sameimage mandatory: real proc magic links/openat cannot be certified on Windows')
 def test_actual_linux_proc_exe_root_fd_and_complete_stream(self):
  # The immutable guest's actual executable has the original025 PY spelling;
  # local nonmatching Linux hosts fail explicitly rather than claim image proof.
  self.assertTrue(Path(N.PY).is_file(),'requires actual immutable guest interpreter installation')
  proof=N.verify(Path('/proc/self'),Path('/proc/self'),N.PY)
  self.assertGreater(proof['executable']['bytes'],0)
  self.assertEqual(len(proof['executable']['sha256']),64)
  self.assertFalse(proof['pre_registered_binary_digest'])

 @unittest.skipUnless(os.name=='posix','Linux sameimage mandatory: real dirfd/symlink path walk')
 def test_actual_linux_namespace_absolute_symlink_escapes_wrong_binary_deleted_and_race(self):
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);(root/'guest/bin').mkdir(parents=True);binary=root/'guest/bin/python3.12';binary.write_bytes(b'actual software executable bytes');binary.chmod(0o755)
   os.symlink('/guest/bin/python3.12',root/'guest/bin/python3')
   # Absolute /guest/... does NOT exist on the host. Resolve from pinned root.
   rootfd=os.open(root,os.O_RDONLY|os.O_DIRECTORY)
   try:
    fd,canonical=N.root_open(rootfd,'/guest/bin/python3')
    try:self.assertEqual(canonical,'/guest/bin/python3.12');self.assertEqual(N.file_proof(fd)['sha256'],hashlib.sha256(binary.read_bytes()).hexdigest())
    finally:os.close(fd)
    os.symlink('../../../outside',root/'guest/bin/escape')
    os.symlink('loop',root/'guest/bin/loop')
    (root/'other/sub').mkdir(parents=True);os.symlink('/other/sub',root/'guest/bin/sub');os.symlink('sub/../python3.12',root/'guest/bin/ambiguous')
    for name in ('/guest/bin/escape','/guest/bin/loop','/guest/bin/python3 (deleted)','/guest/bin/ambiguous'):
     with self.assertRaises((ValueError,FileNotFoundError)):N.root_open(rootfd,name)
    original=os.stat
    def race(path,*a,**kw):
     value=original(path,*a,**kw)
     if path=='python3.12'and kw.get('follow_symlinks')is False:binary.write_bytes(b'changed between stat and open')
     return value
    with patch.object(os,'stat',side_effect=race):
     with self.assertRaises(ValueError):N.root_open(rootfd,'/guest/bin/python3.12')
   finally:os.close(rootfd)

 @unittest.skipUnless(os.name=='posix','Linux sameimage mandatory: executable mode and unlinked open inode')
 def test_stream_hash_identity_wrong_extent_unlinked_and_not_executable_reject(self):
  with tempfile.TemporaryDirectory()as td:
   path=Path(td)/'python';path.write_bytes(b'x'*200);path.chmod(0o755);fd=os.open(path,os.O_RDONLY)
   try:
    out=N.file_proof(fd);self.assertEqual(out['bytes'],200)
    with patch.object(N,'MAX_BINARY',199):
     with self.assertRaises(ValueError):N.file_proof(fd)
    path.chmod(0o644)
    with self.assertRaises(ValueError):N.file_proof(fd)
    path.chmod(0o755);path.unlink()
    with self.assertRaises(ValueError):N.file_proof(fd)
   finally:os.close(fd)
  # OS mode semantics differ on Windows; actual executable-bit enforcement is
  # certified only by the mandatory Linux controls above, not chmod simulation.

if __name__=='__main__':unittest.main()
