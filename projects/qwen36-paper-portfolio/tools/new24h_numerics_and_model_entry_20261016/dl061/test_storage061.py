import ast,copy,hashlib,json,pathlib,subprocess,sys,tempfile,unittest
P=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(P));import storage061 as S
class Storage(unittest.TestCase):
 def test_untracked_actual_and_reservation_overlap(self):
  g=S.GIB
  self.assertEqual(S.committed_bytes(2*g,[g,g],[33*g,33*g]),66*g)
  self.assertEqual(S.committed_bytes(22*g,[g,g],[33*g,33*g]),86*g)
  self.assertGreater(S.committed_bytes(22*g,[g,g],[33*g,33*g]),S.LIMIT)
  self.assertEqual(S.committed_bytes(50*g,[40*g,5*g],[33*g,33*g]),78*g)
  self.assertGreater(S.committed_bytes(53*g,[40*g,5*g],[33*g,33*g]),S.LIMIT)
  for total,actual,budgets in((1,[2],[33]),(True,[],[]),(1,[True],[33]),(1,[1],[-1])):
   with self.assertRaises(ValueError):S.committed_bytes(total,actual,budgets)
 def test_combined_budget_not_perphase(self):
  def row(n,kind):return dict(leaf=str(S.ROOT/n),stage=kind,budget_bytes=(33 if kind=='numeric'else 1)*S.GIB)
  ledger=dict(reservations=[row('cpu','cpu'),row('16','numeric'),row('160','numeric')]);self.assertEqual(S.reserved(ledger),67*S.GIB)
  with self.assertRaises(ValueError):S.reserved(dict(reservations=ledger['reservations']+[row('extra','numeric')]))
  for bad in(-1,True,80*S.GIB):
   x=copy.deepcopy(ledger);x['reservations'][0]['budget_bytes']=bad
   with self.assertRaises(ValueError):S.reserved(x)
 def test_live_reserve_actual_tree(self):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d);(p/'x').write_bytes(b'abc');self.assertEqual(S.check(p,free=S.FREE)['used_bytes'],3)
   with self.assertRaises(ValueError):S.check(p,free=S.FREE-1)
 def test_storage_authority_pending_and_wrong(self):
  from window056 import AUTH
  r=dict(path='/actual/authority.json',bytes=1,sha256='f'*64);a=dict(schema='ascend.paper-experiment.storage-authority/v1',output_root=str(S.ROOT),max_total_bytes=S.LIMIT,min_free_bytes=S.FREE,current_authority_ref=AUTH)
  self.assertEqual(S.authority(r,lambda _:a),a)
  for k,v in(('output_root','/opt/varlib/kubelet'),('max_total_bytes',S.LIMIT+1),('min_free_bytes',S.FREE-1),('current_authority_ref',{})):
   x=dict(a);x[k]=v
   with self.assertRaises(ValueError):S.authority(r,lambda _:x)
 def test_real_cold_cli_and_host_inverse(self):
  from inverse061 import undo
  old=P.parent/'deltalog-split-scale-numeric-new24h-20261016-056-revision1'
  for n in json.loads((P/'EDITS061.json').read_bytes()):
   self.assertEqual(undo(n,(P/n).read_bytes().decode()),(old/n).read_bytes().decode(),n)
  for n in('run052.py','bind052.py','host.py'):
   x=subprocess.run([sys.executable,'-I','-B',str(P/n)],capture_output=True,text=True);self.assertEqual(x.returncode,0,x.stderr)
  tree=ast.parse((P/'host.py').read_bytes());text=ast.unparse(tree)
  self.assertIn('storage.reserve(out.parent, out, a.stage, obj',text);self.assertIn('storage.check(a.output.parent)',text)
if __name__=='__main__':unittest.main()
