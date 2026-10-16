import hashlib,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
import anchor_transform127 as T
import entry127 as E

class AnchorTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.original=Path(os.environ['SOURCE127_ORIGINAL']).read_bytes()
 def test_whole_body_inverse(self):
  text,_=T.transform(self.original)
  self.assertEqual(T.inverse(text),self.original)
  self.assertEqual(text.count("raw(anchors[batch])['pid']"),0)
  self.assertEqual(text.count('anchor_pids[batch]'),3)
 def test_wrong_source(self):
  with self.assertRaisesRegex(ValueError,'exact reviewed'):T.transform(self.original+b'\n')
 def test_all_original_rows_and_sidecars_still_present(self):
  text,_=T.transform(self.original)
  for line in self.original.decode().splitlines():
   if not any(old in line for old,_ in T.EDITS):self.assertIn(line,text.splitlines())
  for token in ('CPU600s','2*steps+31','2*steps+8',"transition['local_transition_pass']","checked_side['passed']","v['passed']"):
   self.assertIn(token,text)
 def test_actual_anchor_statement_gate_before_cache(self):
  text,_=T.transform(self.original)
  line=next(x.strip() for x in text.splitlines() if 'previous[batch]=D.initial_anchor' in x)
  # Execute the actual transformed statement suffix; an original gate failure must
  # not install metadata, and later source PID mutation cannot mutate the cache.
  statement=line[line.index('previous[batch]='):]
  class D:
   fail=True
   @classmethod
   def initial_anchor(cls,*args):
    if cls.fail:raise ValueError('original anchor hard failure')
    return 'original validated previous'
  ns=dict(D=D,t=None,anchor={'pid':{'pid':42}},sr=None,r=None,m=None,batch=16,previous={},anchor_pids={},json=json)
  with self.assertRaisesRegex(ValueError,'original anchor'):exec(statement,ns)
  self.assertEqual(ns['anchor_pids'],{})
  D.fail=False;exec(statement,ns);ns['anchor']['pid']['pid']=99
  self.assertEqual(ns['anchor_pids'][16],{'pid':42})
  self.assertEqual(ns['previous'][16],'original validated previous')
 def test_ref_hash_and_missing_ref_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'x';p.write_bytes(b'original')
   good=dict(path=str(p),bytes=8,sha256=hashlib.sha256(b'original').hexdigest())
   self.assertEqual(E.checked(good),b'original')
   with self.assertRaises(ValueError):E.checked(dict(good,bytes=7))
   p.unlink()
   with self.assertRaises(FileNotFoundError):E.checked(good)
 def test_actual_I_ON_pending_before_torch(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'source.json';p.write_text(json.dumps(dict(consumer_contract_schema='deltalog.anchor-consumer-source/v127',bound=False)),encoding='utf8')
   ref=dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
   argv=[sys.executable,'-I','-B',str(P/'entry127.py'),'--execute','--consumer-source-ref',json.dumps(ref)]
   for n in ('producer-source-ref','producer-ref','strict-ref'):argv+=['--'+n,'{}']
   argv+=['--output',str(Path(td)/'never.json')]
   result=subprocess.run(argv,capture_output=True,text=True)
   self.assertNotEqual(result.returncode,0)
   self.assertIn('pending original terminal category',result.stderr)
   self.assertFalse((Path(td)/'never.json').exists())
if __name__=='__main__':unittest.main()
