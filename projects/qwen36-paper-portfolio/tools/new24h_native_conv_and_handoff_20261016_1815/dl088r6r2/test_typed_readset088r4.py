import json,sys,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import bridge_io as C,typed_readset088r4 as R
class Tests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.p=Path(self.tmp.name);self.n=0
 def put(self,v):
  self.n+=1;p=self.p/(str(self.n)+'.json');p.write_bytes(json.dumps(v).encode());return C.ref(p)
 def fixture(self):
  missing=dict(path=str(self.p/'not-present'),bytes=1,sha256='0'*64)
  owner=self.put(dict(schema='owner',supersedes_source_ref=missing,image_ref=missing,files=[dict(path='build_pair.py',bytes=1,sha256='0'*64)]))
  tree=self.put(dict(root=str(self.p),files=[]));receipt=self.put(dict(stdout='actualCID',identity=missing));authority=self.put(dict(schema='authority'))
  phase=dict(owner_ref=owner,tree_ref=tree,receipts=[dict(create_ref=receipt,cleanup_ref=receipt)])
  e=self.put(dict(schema='deltalog.closed-phase-storage-evidence/v119',baseline_ledger_ref=self.put(dict(schema='ledger',supersedes_source_ref=missing)),authority_ref=authority,phases=[phase]*3))
  return e,owner,missing
 def test_actual_reader_opaque_receipts_not_generic_provenance(self):
  e,owner,missing=self.fixture();r=R.Reader(C);r.evidence(e,119)
  self.assertIn(owner,list(r.refs.values()));self.assertNotIn(missing,list(r.refs.values()))
 def test_required_missing_host_ref_fails(self):
  e,owner,missing=self.fixture();v=C.obj(e);v['phases'][0]['tree_ref']=missing
  with self.assertRaises(Exception):R.Reader(C).evidence(self.put(v),119)
 def test_unknown_schema_fails(self):
  e,_,_=self.fixture();v=C.obj(e);v['schema']='unknown'
  with self.assertRaisesRegex(ValueError,'schema'):R.Reader(C).evidence(self.put(v),119)
 def test_required_relative_is_not_skipped(self):
  e,_,_=self.fixture();v=C.obj(e);v['authority_ref']=dict(path='authority.json',bytes=1,sha256='0'*64)
  with self.assertRaisesRegex(ValueError,'absolute'):R.Reader(C).evidence(self.put(v),119)
 def test_opaque_container_still_hash_bound(self):
  e,owner,_=self.fixture();Path(owner['path']).write_bytes(b'changed')
  with self.assertRaises(ValueError):R.Reader(C).evidence(e,119)
 def test_missing_required_field_not_permissive(self):
  e,_,_=self.fixture();v=C.obj(e);del v['phases'][0]['receipts']
  with self.assertRaises(KeyError):R.Reader(C).evidence(self.put(v),119)
if __name__=='__main__':unittest.main()
