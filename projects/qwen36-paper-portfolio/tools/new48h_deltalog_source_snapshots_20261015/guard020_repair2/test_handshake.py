"""Run the actual GE.wait_ge body, not a separately reimplemented predicate."""
import ast,copy,pathlib,tempfile,types,unittest
P=pathlib.Path(__file__).resolve().parent
class Handshake(unittest.TestCase):
 def run_body(self,mode='delayed',mutation=None):
  tree=ast.parse((P/'host.py').read_bytes())
  node=next(n for n in ast.walk(tree) if isinstance(n,ast.ClassDef) and n.name=='GE')
  body=copy.deepcopy(next(n for n in node.body if isinstance(n,ast.FunctionDef) and n.name=='wait_ge'))
  writes=[];calls=[];active='a'*64;sr={'source':1};ar={'authority':1};plan={'sha256':'b'*64}
  dv=dict(stat='1 (python3) '+' '.join(['S']+['0']*18+['7']),pid=1,physical=4,logical=0,visible='0',plan=plan,canary=[4.,5.],cgroup='/docker/'+active)
  proof=dict(physical=4,namespace_pids=[123,1],start_ticks=7,cgroup='/docker/'+active,argv=['python','real-entry'])
  if mutation:mutation(dv,proof)
  def need(x,msg):
   if not x:raise ValueError(msg)
  with tempfile.TemporaryDirectory() as td:
   output=pathlib.Path(td);child=output/'result';child.mkdir();(child/'DEVICE.json').touch()
   def obj(r):return dv if pathlib.Path(r).name=='DEVICE.json' else dict(source=sr,authority=ar,observation_complete=True)
   ns=dict(time=types.SimpleNamespace(monotonic=lambda:0,sleep=lambda _:None),a=types.SimpleNamespace(physical_device=4),obj=obj,ref=lambda p:str(p),need=need,write=lambda p,v:writes.append(pathlib.Path(p).name),sr=sr,ar=ar)
   exec(compile(ast.fix_missing_locations(ast.Module(body=[body],type_ignores=[])),str(P/'host.py'),'exec'),ns)
   class Fake:
    def create(self,stage):return child
    def inspect(self,cid):
     calls.append(cid);return {},{'State':dict(Running=len(calls)<3,ExitCode=0)}
    def observe(self,stage):
     if mode=='absent':return {'owned_process_proofs':[]}
     if mode=='mismatch':return {'owned_process_proofs':[dict(proof,start_ticks=8)]}
     return {'owned_process_proofs':[] if len(calls)==1 else [proof]}
   f=Fake();f.output=output;f.active=active;f.plan_ref=plan;f.expected_child_argv=['python','real-entry']
   try:result=ns['wait_ge'](f,'numeric')
   except ValueError as e:return dict(error=str(e),writes=writes,calls=len(calls))
   return dict(result=result,writes=writes,calls=len(calls))
 def test_delayed_real_body(self):
  r=self.run_body();self.assertNotIn('error',r);self.assertEqual(r['writes'].count('MAIN_ARM.json'),1);self.assertEqual(r['calls'],3)
 def test_absent_never_arms(self):
  r=self.run_body('absent');self.assertIn('error',r);self.assertNotIn('MAIN_ARM.json',r['writes'])
 def test_mismatch_never_arms(self):
  r=self.run_body('mismatch');self.assertIn('error',r);self.assertNotIn('MAIN_ARM.json',r['writes'])
 def test_wrong_physical(self):
  r=self.run_body(mutation=lambda d,p:d.update(physical=5));self.assertIn('error',r);self.assertNotIn('MAIN_ARM.json',r['writes'])
 def test_wrong_plan(self):
  r=self.run_body(mutation=lambda d,p:d.update(plan={}));self.assertIn('error',r);self.assertNotIn('MAIN_ARM.json',r['writes'])
 def test_wrong_canary(self):
  r=self.run_body(mutation=lambda d,p:d.update(canary=[0.,0.]));self.assertIn('error',r);self.assertNotIn('MAIN_ARM.json',r['writes'])
 def test_wrong_argv(self):
  r=self.run_body(mutation=lambda d,p:p.update(argv=['other']));self.assertIn('error',r);self.assertNotIn('MAIN_ARM.json',r['writes'])
if __name__=='__main__':unittest.main()
