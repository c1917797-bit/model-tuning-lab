"""Real local fixed-source/file checks, not NPU/library qualification."""
import ast,copy,hashlib,importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def ref(p):
 b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
class DomainFrontdoor(unittest.TestCase):
 def manifest(self):
  D=load('_actual_domain_static_controls',P/'domain_consumer.py')
  # Local ordinary-file endpoint fixtures only. Same-image entry instead
  # checks the unchanged actual probe/library Refs in the real source.
  m=dict(files={n:ref(P/n)for n in D.PINNED},probe_ref=ref(P/'test_domain_frontdoor.py'),library_ref=ref(P/'test_producer_frontdoor.py'))
  return D,m
 def test_current_real_source_and_complete_fixed_pins(self):
  D,m=self.manifest();value=D.static_proof(m);self.assertTrue(value['pinned_static_source']);self.assertFalse(value['native_chunk_runtime_identity_proven'])
 def test_actual_old_pin_rejected_and_changed_file_rejected(self):
  D,m=self.manifest();old=dict(D.PINNED,**{'producer.py':'8884b0011dad98a7ba8e256acb985c78c17f8e408c7a57f45f9fca2665a8844d'})
  with patch.object(D,'PINNED',old):
   with self.assertRaisesRegex(ValueError,'producer.py'):D.static_proof(m)
  with tempfile.TemporaryDirectory()as td:
   p=Path(td)/'producer.py';p.write_bytes((P/'producer.py').read_bytes()+b'# wrong source\n');m['files']['producer.py']=ref(p)
   with self.assertRaisesRegex(ValueError,'producer.py'):D.static_proof(m)
 def test_actual_child_error_receipt_precedes_failure(self):
  G=load('_actual_pair_error_receipt',P/'consume_pair.py');sr={'source':'software'};pr={'producer':'software'}
  from test_collection_contract import complete
  producer=complete();producer['source']=sr;realrun=subprocess.run
  def failing(argv,**kw):
   return realrun([sys.executable,'-I','-B','-c',"import sys;sys.stderr.write('REAL_CHILD_FAILURE\\n');raise SystemExit(7)"],**kw)
  with tempfile.TemporaryDirectory()as td:
   out=Path(td)/'PAIR.json';argv=[str(P/'consume_pair.py'),'--execute','--source-ref',json.dumps(sr),'--producer-ref',json.dumps(pr),'--output',str(out)]
   with patch.object(sys,'argv',argv),patch.object(G.C,'source',return_value={}),patch.object(G.C,'obj',return_value=producer),patch.object(G.subprocess,'run',side_effect=failing):
    with self.assertRaisesRegex(ValueError,'independent child failed'):G.main()
   r=json.loads((Path(td)/'CHILD-01-consume.json').read_bytes());self.assertEqual(r['returncode'],7);self.assertEqual(r['stderr'],'REAL_CHILD_FAILURE\n');self.assertFalse(out.exists())
 def test_cpu_actual_static_before_torch_and_receipt_link(self):
  body=(P/'entry.py').read_text();self.assertLess(body.index('actual_domain.static_proof(m)'),body.index('import torch'));self.assertIn('actual_domain_static_proof',body)
if __name__=='__main__':unittest.main()
