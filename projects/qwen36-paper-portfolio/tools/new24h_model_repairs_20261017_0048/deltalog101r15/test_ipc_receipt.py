"""Software contract controls only; synthetic receipts confer no qualification."""
import ast,copy,json,types,unittest
from pathlib import Path
import ipc_receipt as R
class Receipt(unittest.TestCase):
 def fixture(self):
  sr=dict(path='/source',bytes=1,sha256='a');rr=dict(path='/owned/IPC_CONTROLS.json',bytes=2,sha256='b')
  proof=dict(schema='mxr.actual-Linux-IPC-original-scan-controls/v043-repair2',original_scanner=R.SCANNER_REF,NPU=False,**{k:True for k in R.FLAGS})
  cp=dict(source=sr,mode='cpu',NPU=False,pass_preflight=True,actual_rootfs_write_errno=30,software_controls=dict(discovered=R.SOFTWARE_CASES,executed=R.SOFTWARE_CASES,passed=True),actual_IPC_controls_ref=rr,actual_IPC_controls=proof)
  return sr,rr,proof,cp
 def test_exact_software_ABI(self):
  sr,rr,p,c=self.fixture();self.assertTrue(R.check(c,sr,lambda r:p,rr))
  # Execute the actual current host's child callback, not a parallel contract.
  root=Path(__file__).resolve().parent
  f=next(n for n in ast.walk(ast.parse((root/'host_ticket.py').read_bytes()))if isinstance(n,ast.FunctionDef)and n.name=='child')
  called=[];scope=dict(original_child=lambda *a,**k:called.append(a[2]),leaf=lambda name:R,sr=sr)
  exec(compile(ast.Module(body=[f],type_ignores=[]),'actual MODEL058 child','exec'),scope)
  ctl=types.SimpleNamespace(out=Path('/owned'))
  C=types.SimpleNamespace(ref=lambda path:rr if path.name=='IPC_CONTROLS.json'else'cpu',obj=lambda ref:p if ref==rr else c)
  scope['child'](ctl,C,'DL-cold-source',[],150,observe=False)
  self.assertEqual(called,['DL-cold-source'])
  bad=copy.deepcopy(c);bad['actual_rootfs_write_errno']=13;C.obj=lambda ref:p if ref==rr else bad
  with self.assertRaises(ValueError):scope['child'](ctl,C,'DL-cold-source',[],150,observe=False)
 def test_actual_proof_bool_and_file_drift_rejected(self):
  sr,rr,p,c=self.fixture()
  for key in R.FLAGS:
   bad=copy.deepcopy(p);bad[key]=False;cc=copy.deepcopy(c);cc['actual_IPC_controls']=bad
   with self.assertRaises(ValueError):R.check(cc,sr,lambda r:bad,rr)
  with self.assertRaises(ValueError):R.check(c,sr,lambda r:dict(p,NPU=True),rr)
 def test_source_count_rootfs_reference_drift_rejected(self):
  sr,rr,p,c=self.fixture()
  for mutate in (lambda x:x.update(actual_rootfs_write_errno=13),lambda x:x.update(source={}),lambda x:x['software_controls'].update(executed=68),lambda x:x.update(actual_IPC_controls_ref=dict(rr,path='/other'))):
   cc=copy.deepcopy(c);mutate(cc)
   with self.assertRaises(ValueError):R.check(cc,sr,lambda r:p,rr)
if __name__=='__main__':unittest.main()
