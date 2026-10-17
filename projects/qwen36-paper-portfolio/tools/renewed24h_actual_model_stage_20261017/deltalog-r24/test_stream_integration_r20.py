"""Actual Lease.open path, with explicit synthetic storage/CID boundary only."""
import importlib.util,json,os,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
import model_snapshot_budget as B
import stream_closed_tree as S
from stream_seal_adapter import AuthenticatedMetadata,ActualRows,ExpectedRows

FIXTURE='''
import types
original=types.SimpleNamespace(closed_stat=lambda unused,row:None)
def install(C,m,S):
 closed=m['closed']
 def commitment(root,ledger):
  for row in closed:original.closed_stat(None,row)
  return S.total(),60*2**30
 S.commitment=commitment
 return types.SimpleNamespace(final_verify=lambda unused:None)
B=types.SimpleNamespace(install=install)
def prior_policy(K):
 C=None;m=K.fixture_m;S=K.policy
 B.install(C,m,S)
 proof=S.check()
 return S,proof
'''
def write(p,v):p.write_text(json.dumps(v,sort_keys=True),encoding='utf8');return S.file_ref(p)
def index(root,p):
 rows=[]
 for q in sorted(root.iterdir()):
  a=q.stat();rows.append(dict(relative_path=q.name,bytes=a.st_size,mtime_ns=a.st_mtime_ns,inode=a.st_ino,device=a.st_dev,sha256=S.file_ref(q)['sha256']))
 return write(p,dict(root=str(root),files=rows))

class Integration(unittest.TestCase):
 def test_actual_lease_open_hot_and_full_final(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);roots=[];rr=[]
   for n in range(15):
    q=p/('closed%02d'%n);q.mkdir();(q/'data').write_bytes(b'original');roots.append(str(q));rr.append(index(q,p/('tree%02d.json'%n)))
   closed=[dict(leaf=q,tree_ref=r,frozen_bytes=8)for q,r in zip(roots[:13],rr[:13])]
   phases=[dict(leaf=q,tree_ref=r,frozen_bytes=8)for q,r in zip(roots[13:],rr[13:])]
   ledger=dict(reservations=[dict(leaf=r['leaf'],stage='numeric',budget_bytes=33*2**30)for r in phases]);lr=write(p/'ledger.json',ledger)
   er=write(p/'evidence.json',dict(baseline_ledger_ref=lr,phases=phases,states_after=[]))
   mr=write(p/'model.json',dict(firstdecode_contract=dict(prior_r23_terminal_evidence_ref={'synthetic_fixture':True},closed_readset=dict(retained_tree_roots=roots,refs=rr,prior_released_empty_r22={'synthetic_fixture':True},prior_released_empty_r23={'synthetic_fixture':True}))))
   fixture=p/'source_fixture.py';fixture.write_text(FIXTURE,encoding='utf8');spec=importlib.util.spec_from_file_location('_lease_fixture_r20',fixture);f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
   calls=dict(original_stat=0,full_tree=0,inspect=0,writers=0)
   def stat_old(unused,row):calls['original_stat']+=1;S.verify(row['tree_ref'],row['leaf'],full=False)
   f.original.closed_stat=stat_old
   def total():return sum(x.stat().st_size for x in p.rglob('*')if x.is_file())
   policy=types.SimpleNamespace(total=total)
   def check():
    t,c=policy.commitment(p,ledger);return dict(used_bytes=t,committed_bytes=c,filesystem_free_bytes=10**12)
   policy.check=check
   def tree(root,full):
    calls['full_tree']+=int(full);return ActualRows(str(root),full)
   def canonical(unused):return K,{}
   ws={'calls':calls};exec("def no_writers():\n calls['writers']+=1\n return {}\n",ws)
   K=types.SimpleNamespace(policy=policy,fixture_m=dict(closed=closed),read=B.obj,no_writers=ws['no_writers'],calls=calls,inspect_all=lambda:[],tree=tree)
   seal=types.SimpleNamespace(canonical=canonical,latest=lambda K:lr,prior_policy=f.prior_policy,__file__=str(fixture),inventory=S.metadata,read_tree=lambda K,r:dict(root=roots[rr.index(r)],files=ExpectedRows(r,roots[rr.index(r)],1)))
   def validate(er,sr):
    unused,proof=seal.prior_policy(K)
    for row in phases:S.verify(row['tree_ref'],row['leaf'],full=True)
    return B.obj(er),proof
   # Lease compiles a private validate function with seal's source globals.
   # Build that exact outer fixture with explicit globals, not a free PASS.
   def source_validate(er,sr):
    unused,proof=prior_policy(K)
    for row in phases:STREAM.verify(row['tree_ref'],row['leaf'],full=True)
    return obj(er),proof
   scope=dict(prior_policy=seal.prior_policy,K=K,phases=phases,STREAM=S,obj=B.obj)
   exec("def validate(er,sr):\n unused,proof=prior_policy(K)\n for row in phases:STREAM.verify(row['tree_ref'],row['leaf'],full=True)\n return obj(er),proof\n",scope)
   seal.validate=scope['validate']
   seal.__dict__.update(scope);seal.B=f.B
   opt=p/'opt';opt.mkdir();newleaf=p/'new';journal=p/'journal'
   import prior_empty_r19,renewed_closed_reader101r19,prior_released_empty_r20r1,prior_released_empty_r21
   fakefcntl=types.SimpleNamespace(LOCK_EX=1,LOCK_NB=2,flock=lambda *a:None)
   modules=patch.dict(sys.modules,{'fcntl':fakefcntl})if os.name=='nt'else patch.dict(sys.modules,{})
   with modules,patch.object(B,'ROOT',p),patch.object(B,'LEAF',newleaf),patch.object(B,'JOURNAL',journal),patch.object(prior_empty_r19,'validate',return_value=dict(schema='synthetic-fixture-only',current_no_writers=None)),patch.object(renewed_closed_reader101r19,'check',return_value={'synthetic_fixture':True}),patch.object(B.os,'O_NOFOLLOW',getattr(os,'O_NOFOLLOW',0),create=True):
    # Explicit synthetic storage/CID boundary for the newly typed prior CPU;
    # its actual original documents are tested separately, not invented here.
    prior_patch=patch.object(prior_released_empty_r20r1,'validate',return_value=dict(schema='synthetic-fixture-only',current_no_writers=None))
    prior_patch.start();self.addCleanup(prior_patch.stop)
    prior21_patch=patch.object(prior_released_empty_r21,'validate',return_value=dict(schema='synthetic-fixture-only',current_no_writers=None));prior21_patch.start();self.addCleanup(prior21_patch.stop)
    import prior_released_empty_r22
    prior22_patch=patch.object(prior_released_empty_r22,'validate',return_value=dict(schema='synthetic-fixture-only',numeric_qualified=False));prior22_patch.start();self.addCleanup(prior22_patch.stop)
    import prior_released_empty_r23
    prior23_patch=patch.object(prior_released_empty_r23,'validate',return_value=dict(schema='synthetic-fixture-only',candidate_created=True,numeric_qualified=False));prior23_patch.start();self.addCleanup(prior23_patch.stop)
    lease=B.Lease(seal,{},er,mr,{},opt,lambda root:0).open()
    try:
     before=calls['original_stat'];lease.check();lease.check();self.assertEqual(calls['original_stat'],before)
     self.assertEqual(before,13)
     with self.assertRaisesRegex(ValueError,'released before'):lease.close(False)
     lease.close(True);self.assertEqual(calls['full_tree'],3)
     # Immutable baseline is not changed by mutation of the caller's old rows.
     closed[0]['frozen_bytes']=9
     with self.assertRaisesRegex(ValueError,'exact originally'):lease.check()
     closed[0]['frozen_bytes']=8
     (Path(roots[0])/'extra').write_bytes(b'x')
     with self.assertRaisesRegex(ValueError,'metadata'):lease.check()
     (Path(roots[0])/'extra').unlink()
     # Even restoring bytes does not restore ctime; never rebaseline.
     with self.assertRaisesRegex(ValueError,'metadata'):lease.check()
    finally:lease.release()

 def test_replayable_full_eof_not_one_shot(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);root=p/'root';root.mkdir();(root/'a').write_bytes(b'a');r=index(root,p/'tree.json');e=ExpectedRows(r,str(root),1)
   self.assertEqual(list(e),list(e));self.assertTrue(ActualRows(str(root),True)==e)
   data=json.loads((p/'tree.json').read_bytes());data['extra']='unknown';write(p/'tree.json',data)
   with self.assertRaises(ValueError):list(e)
if __name__=='__main__':unittest.main()
