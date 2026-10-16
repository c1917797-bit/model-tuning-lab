"""Execute actual controller/base_lane/safety composition, no Lane instance."""
import hashlib,importlib.util,json,linecache,sys,types,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;T=P.parent;sys.path.insert(0,str(P))
def module(p,n):
 s=importlib.util.spec_from_file_location(n,p);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
def construct(old=False):
 template=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes())
 if sys.platform=='linux':
  H=module(P/'regression/old_owner112.py','old_controller')if old else module(P/'owner112.py','new_controller')
  md=H.obj(template['donor_source']);own=template
 else:
  own=template;dp=template['donor_host']['path'];pp=template['dependencies']['pipeline']['path'];D=Path(dp).parent if ':'in dp else T/'deltalog-split-scale-numeric-new24h-20261016-069-repair1';V=Path(pp).parent if ':'in pp else T/'deltalog-new48h-v7-20261014-001';H=module(P/'regression/old_owner112.py'if old else P/'owner112.py','actual_controller_'+str(old));sp=template['donor_source']['path'];md=json.loads((Path(sp)if ':'in sp else D/'SOURCE_TEMPLATE.json').read_bytes())
  candidates=list(P.rglob('*.py'))+list(D.glob('*.py'))+[V/'pipeline.py',V/'cpu_capacity.py'];index={hashlib.sha256(p.read_bytes()).hexdigest():p for p in candidates}
  def path(r):
   p=index[r['sha256']];b=p.read_bytes();assert len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'];return p
  def loader(r,n):
   v=module(path(r),n)
   if r==own['donor_host']:v.checked=lambda q:path(q).read_bytes();v.load=loader
   return v
  H.checked=path;H.load=loader
  # inspect.getsource uses the actual unchanged compile filename supplied by
  # base_lane; linecache contains the exact hash-verified original PIPE text.
  text=(V/'pipeline.py').read_text(encoding='utf-8')
  linecache.cache['/cache/cch/qwen36-paper-preparation-20261007/lowbit/_draft_damp_operator_reuse/NEW48H/deltalog-v7-20261014-001/pipeline.py']=(len(text),None,text.splitlines(True),'pipeline.py')
 args=types.SimpleNamespace(owner_ref={'software':'constructor-only-not-a-receipt'},output=Path('/no-output-created'),guest_cpu=0,whole_deadline=0)
 GE,d,storage,seal=H.controller(own,args,md,md,[])
 assert GE.__name__=='GE'and callable(GE.create)and callable(GE.observe)and callable(GE.wait079)
 assert d.OWNER==H.OWNER and args.__dict__==dict(owner_ref={'software':'constructor-only-not-a-receipt'},output=Path('/no-output-created'),guest_cpu=0,whole_deadline=0)
 return GE
class Tests(unittest.TestCase):
 def test_old_actual_controller_rejects_modified_adapter(self):
  with self.assertRaisesRegex(AssertionError,'exact original scope source'):construct(True)
 def test_new_actual_controller_constructs_full_private_GE(self):self.assertEqual(construct(False).__name__,'GE')
 def test_composition_mutated_adapter_rejected(self):
  import patch_scope112 as K
  raw=(P/'scope_adapter112.py').read_bytes();self.assertEqual(hashlib.sha256(K.original(raw)).hexdigest(),K.ORIGINAL_SHA)
  with self.assertRaises(AssertionError):K.original(raw+b'\n')
if __name__=='__main__':unittest.main()
