"""No actual raw consumption: replay/integrity/bounded representation controls."""
import ast,copy,hashlib,json,sys,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import readset127 as R
def ref(path,n=1):return dict(path=path,bytes=n,sha256='1'*64)
def checked(r):
 p=Path(r['path']);b=p.read_bytes()
 if len(b)!=r['bytes']or hashlib.sha256(b).hexdigest()!=r['sha256']:raise ValueError('wrong actual index hash')
 return p
class ReadsetControls(unittest.TestCase):
 def build(self,root):
  calls=[];w=R.Writer(root/'new.sqlite',lambda r:calls.append(r['path']))
  for name in('/data/c','/data/a','/other/b'):w.add(ref(name))
  w.add(ref('/data/a'));d=w.emit(root/'index.jsonl');w.close();return d,calls
 def test_actual_writer_replay_and_counts(self):
  with tempfile.TemporaryDirectory()as td:
   d,calls=self.build(Path(td));rs=R.Readset([ref('/source/base')],d,checked)
   expected=['/source/base','/data/a','/data/c','/other/b']
   for _ in range(4):self.assertEqual([r['path']for r in rs],expected)
   self.assertEqual(len(rs),4);self.assertEqual(rs.parents,('/data','/other','/source'));self.assertEqual(calls,['/data/c','/data/a','/other/b'])
 def test_conflicting_duplicate_not_silently_deduped(self):
  with tempfile.TemporaryDirectory()as td:
   w=R.Writer(Path(td)/'new.sqlite',lambda r:None);w.add(ref('/data/a'))
   try:
    with self.assertRaises(ValueError):w.add(ref('/data/a',2))
   finally:w.close()
 def test_wrong_index_hash_count_parents_reject(self):
  with tempfile.TemporaryDirectory()as td:
   d,_=self.build(Path(td))
   for change in('hash','count','parents'):
    bad=copy.deepcopy(d)
    if change=='hash':bad['index_ref']['sha256']='0'*64
    elif change=='count':bad['entries']+=1
    else:bad['parents']=['/wrong'];bad['parent_count']=1
    with self.assertRaises(ValueError):list(R.Index(bad,checked))
 def test_missing_or_changed_index_no_skip(self):
  with tempfile.TemporaryDirectory()as td:
   d,_=self.build(Path(td));it=iter(R.Index(d,checked));next(it)
   p=Path(d['index_ref']['path']);p.write_bytes(p.read_bytes()+b' ')
   with self.assertRaises(ValueError):list(it)
   p.unlink()
   with self.assertRaises(FileNotFoundError):list(R.Index(d,checked))
 def test_oversized_incomplete_relative_unknown_rows_reject(self):
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);d,_=self.build(root)
   for b in(b'x'*(R.MAX_LINE+2),b'{}\n',json.dumps(ref('relative')).encode()+b'\n'):
    p=root/'bad.jsonl';p.write_bytes(b);bad=copy.deepcopy(d);bad['index_ref']=dict(path=p.as_posix(),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
    with self.assertRaises((ValueError,json.JSONDecodeError)):list(R.Index(bad,checked))
 def test_real_host_has_no_full_result_list_comprehension(self):
  tree=ast.parse((P/'host.py').read_bytes())
  self.assertFalse(any(isinstance(n,ast.ListComp)and isinstance(n.elt,ast.Call)and isinstance(n.elt.func,ast.Name)and n.elt.func.id=='validate_ref_streamed'for n in ast.walk(tree)))
  text=(P/'runtime127.py').read_text();self.assertIn('R.Readset(',text);self.assertNotIn("*m['recovery_refs']",text)
  self.assertIn("result.pop('recovery_refs',None)",(P/'bind127.py').read_text())
