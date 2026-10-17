import ast,copy,json,subprocess,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import common116 as C,authority_preflight as A
class Controls(unittest.TestCase):
 def test_actual_serialized_authority_all_three_runtime_boundaries(self):
  authority=C.obj(C.ref(P/'evidence/ACTUAL_AUTHORITY.json'));A.validate(authority)
  for name,var in(('owned_cpu116.py','authority'),('owner116.py','auth'),('common116.py','a')):
   tree=ast.parse((P/name).read_bytes());calls=[n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='need'and n.args and 'explicit-renewed24h'in ast.unparse(n.args[0])]
   if name=='common116.py':self.assertEqual(len(calls),1)
   else:
    self.assertEqual(len(calls),1);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main');branch=next(n for n in ast.walk(main)if isinstance(n,ast.If)and isinstance(n.test,ast.Attribute)and n.test.attr=='source_audit');self.assertLess(calls[0].lineno,branch.lineno)
   def execute(value):
    scope=dict(need=C.need,START=1792226600,CUT=1792313000,ar={'actual':'ref'},gm={'authority_ref':{'actual':'ref'}});scope[var]=value
    if name=='common116.py':
     import time
     scope['time']=time
    exec(compile(ast.fix_missing_locations(ast.Module(body=[ast.Expr(calls[0])],type_ignores=[])),str(P/name),'exec'),scope)
   execute(authority)
   for bad in(dict(authority,schema='ascend.paper-portfolio.new24h-authority/v1'),dict(authority,start_epoch=1792134133),dict(authority,cutoff_epoch=1792220533)):
    with self.assertRaises(ValueError):execute(bad)
 def test_actual_early_CLI_wrong_ref_rejects_before_resources(self):
  for bad in({},dict(path='/wrong/authority.json',bytes=3012,sha256='0'*64)):
   z=subprocess.run([sys.executable,'-I','-B',str(P/'authority_preflight.py'),'--execute','--authority-ref',json.dumps(bad)],capture_output=True,text=True,timeout=10);self.assertNotEqual(z.returncode,0);self.assertNotIn('unrecognized arguments',z.stderr);self.assertIn('exact actual authority Ref3',z.stderr)
if __name__=='__main__':unittest.main()
