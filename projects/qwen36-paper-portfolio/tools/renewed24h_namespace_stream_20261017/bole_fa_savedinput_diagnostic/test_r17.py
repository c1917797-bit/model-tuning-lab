"""Actual small saved evidence only; no raw tensor or live namespace claim."""
import ast,base64,copy,hashlib,json,subprocess,sys,tempfile,unittest
from pathlib import Path,PurePosixPath
import plan as R,recovery_io as C
P=Path(__file__).resolve().parent

class Tests(unittest.TestCase):
 def packet(self):
  p=json.loads((P/'evidence/SMALL_METADATA_FIXTURES.json').read_bytes())
  self.assertIs(p['no_raw_hash_or_tensor_read'],True)
  by={}
  for row in p['files']:
   r=row['ref'];b=base64.b64decode(''.join(row['content_b64_chunks']),validate=True);row['content']=b.decode('utf8')
   self.assertEqual(len(b),r['bytes']);self.assertEqual(hashlib.sha256(b).hexdigest(),r['sha256']);self.assertNotIn(r['path'],by);by[r['path']]=row
  self.assertEqual(len(by),19);return p,by

 def test_actual19_small_records_exactbytes_and_snapshot_signal_namespace_join(self):
  p,by=self.packet();root=str(R.ROOT)+'/dense/receipts/'
  values=[json.loads(x['content'])for path,x in by.items()if '/worker-'in path]
  bindings=json.loads(by[p['owner_summary']['worker_bindings']['path']]['content'])
  signals=[json.loads(x['content'])for path,x in by.items()if '/SIGNAL-'in path]
  self.assertEqual(len(values),4);self.assertEqual(len(signals),4)
  for v in values:
   self.assertEqual(v['source_ref'],R.SOURCE);self.assertIs(v['native_core'],True);self.assertIs(v['native_inverse'],True);self.assertIs(v['allow_hf32'],False)
   matches=[b for b in bindings if b['guest']==v];self.assertEqual(len(matches),1)
   matches2=[s for s in signals if s['actual_process']==matches[0]['host']];self.assertEqual(len(matches2),1)
   s=matches2[0];self.assertEqual(s['actual_process']['namespace_pids'][-1],v['pid']);self.assertIn(s['owned_cid'],v['cgroup'])
  self.assertEqual({b['host']['physical']for b in bindings},{4,5,6,7})

 def test_real_snapshot_reader_actualmetadata_and_missing_source_hash_binding_negatives(self):
  p,by=self.packet();bindings_ref=p['owner_summary']['worker_bindings'];parent=R.ROOT/'dense/receipts'
  native=P/'evidence/ORIGINAL_NATIVE_RECEIPT_R17.py';nr=C.ref(native)
  snapshot_paths=[PurePosixPath(path)for path in by if '/worker-'in path]
  class Root:
   def glob(self,pattern):
    self_pattern=pattern
    if self_pattern!='worker-*-snapshot-*.json':raise AssertionError(pattern)
    return snapshot_paths
  class IO:
   need=staticmethod(C.need)
   @staticmethod
   def ref(path):return by[str(path)]['ref']
   @staticmethod
   def checked(r):
    if r==nr:return C.checked(nr)
    row=by[r['path']];b=row['content'].encode();C.need(row['ref']==r and len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'],'actual small fixture exact Ref3');return r
   @staticmethod
   def obj(r):IO.checked(r);return json.loads(by[r['path']]['content'])
  m=dict(files={'native_receipt090.py':nr})
  self.assertEqual(len(R.snapshots(IO,m,bindings_ref,Root())[1]),4)
  for key,value in(('source_ref',dict(R.SOURCE,sha256='0'*64)),('native_core',False),('allow_hf32',True)):
   target=snapshot_paths[0];old=by[str(target)];v=json.loads(old['content']);v[key]=value;b=json.dumps(v).encode();by[str(target)]=dict(ref=dict(path=str(target),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()),content=b.decode())
   with self.assertRaises(ValueError):R.snapshots(IO,m,bindings_ref,Root())
   by[str(target)]=old
  with self.assertRaises(ValueError):R.snapshots(IO,m,dict(bindings_ref,sha256='0'*64),Root())
  saved=snapshot_paths.pop()
  with self.assertRaises(ValueError):R.snapshots(IO,m,bindings_ref,Root())
  snapshot_paths.append(saved)
  old=by[bindings_ref['path']];v=json.loads(old['content']);v[0]['host']['physical']=5;b=json.dumps(v).encode();newref=dict(bindings_ref,bytes=len(b),sha256=hashlib.sha256(b).hexdigest());by[bindings_ref['path']]=dict(ref=newref,content=b.decode())
  with self.assertRaises(ValueError):R.snapshots(IO,m,newref,Root())

 def test_actual_terminal_source_argv_whole_bytes_mismatch_no_alias_to_R16(self):
  r=C.ref(P/'evidence/BOLE_R17_TERMINAL_OPERATION_FINAL.json');v=R.terminal(C,r)
  self.assertEqual(v['operationId'],'exec-000000000000127e')
  with tempfile.TemporaryDirectory()as td:
   for label in('source','output','operation'):
    bad=copy.deepcopy(v);record=bad['operation']['result']['record']
    if label=='source':record['args'][8]=json.dumps(dict(R.SOURCE,sha256='0'*64))
    elif label=='output':record['args'][-1]+='-not-original'
    else:bad['operationId']='exec-other'
    with self.assertRaises(ValueError):R.terminal(C,C.write(Path(td)/(label+'.json'),bad))

 def test_original_plan_and_new_diagnostic_keep_full_saved_raw(self):
  self.assertIn("refs.extend([rr,v['raw']",(P/'plan.py').read_text())
  self.assertIn("for rank,pair in enumerate(proof['ranks'])",(P/'recover.py').read_text())
  self.assertIn("D.diagnose(t,raw)",(P/'recover.py').read_text())

if __name__=='__main__':unittest.main()
