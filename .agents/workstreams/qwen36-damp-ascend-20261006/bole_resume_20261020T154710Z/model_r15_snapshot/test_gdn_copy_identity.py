"""Actual producer AST replay; explicit software classes, never backend proof."""
import ast,hashlib,inspect,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import sourceio as C,gdn_copy_identity as G,root_repeat_witness as W

def fixture():
 paths=dict(gdn=P/'evidence/gdn.py',patch=P/'evidence/root_witness_actual_patch.py',
            target=P/'evidence/qwen_gdn_linear_attn.py',base=P/'evidence/gdn_base.py')
 mods={k:types.ModuleType(n)for k,n in G.NAMES.items()}
 for k,m in mods.items():m.__file__=str(paths[k]);sys.modules[m.__name__]=m
 base=mods['base'];exec(compile('class GatedDeltaNetAttention: pass',str(paths['base']),'exec'),base.__dict__)
 B=base.GatedDeltaNetAttention
 for key,name,methods in [('gdn','AscendGatedDeltaNetAttention',{'forward','_forward_core','_warmup_prefill_kernels'}),('target','QwenGatedDeltaNetAttention',{'forward'})]:
  tree=ast.parse(paths[key].read_bytes());original=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name==name)
  node=ast.ClassDef(name=name,bases=original.bases,keywords=original.keywords,
    body=[n for n in original.body if isinstance(n,ast.FunctionDef)and n.name in methods],decorator_list=[])
  # Only class constructors/decorators/backend dependencies are substituted.
  # Real complete method bodies and line/code locations are compiled untouched.
  mods[key].__dict__.update(GatedDeltaNetAttention=B,torch=types.SimpleNamespace(Tensor=object))
  exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(paths[key]),'exec'),mods[key].__dict__)
  if key=='gdn':
   # Python3.12 uses module import information when compiling attribute calls.
   # Extracted-class AST loses that context. Use the unchanged complete-source
   # CodeType, without executing any source imports/constructors/backend.
   mods[key]._software_subset_forward_code=mods[key].AscendGatedDeltaNetAttention.forward.__code__
   complete=G.native_code(C,C.ref(paths[key]))
   full_forward=types.FunctionType(complete,mods[key].__dict__,'forward')
   full_forward.__qualname__='AscendGatedDeltaNetAttention.forward'
   mods[key].AscendGatedDeltaNetAttention.forward=full_forward
 target=mods['target'].QwenGatedDeltaNetAttention;origin=mods['gdn'].AscendGatedDeltaNetAttention
 p=mods['patch'];p.__dict__.update(_GDNBaseCls=target,AscendGatedDeltaNetAttention=origin)
 tree=ast.parse(paths['patch'].read_bytes())
 assignment=next(n for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='_GDN_PATCH_TARGET'for t in n.targets))
 branch=next(n for n in tree.body if isinstance(n,ast.If)and ast.unparse(n.test)=='is_310p()')
 exec(compile(ast.fix_missing_locations(ast.Module(body=[assignment,*branch.orelse],type_ignores=[])),str(paths['patch']),'exec'),p.__dict__)
 return mods,{k:C.ref(v)for k,v in paths.items()},target()

class Tests(unittest.TestCase):
 def setUp(self):self.before={n:sys.modules.get(n)for n in G.NAMES.values()}
 def tearDown(self):
  for n,m in self.before.items():
   if m is None:sys.modules.pop(n,None)
   else:sys.modules[n]=m
 def test_actual_producer_copy_reproduces_old_receiver_failure(self):
  mods,refs,obj=fixture();f=obj.forward.__func__;origin=mods['gdn'].AscendGatedDeltaNetAttention
  self.assertIs(f,origin.forward);self.assertFalse(isinstance(obj,origin));self.assertFalse(hasattr(f,'__wrapped__'))
  complete=G.native_code(C,refs['gdn']);self.assertEqual(f.__code__,complete)
  subset=mods['gdn']._software_subset_forward_code
  if sys.version_info[:2]==(3,12):
   self.assertNotEqual(subset,complete)
   self.assertNotEqual(subset.co_code,complete.co_code)
   self.assertEqual(subset.co_names,complete.co_names)
  with self.assertRaisesRegex(ValueError,'exact active native class/receiver'):W.plain(C,obj.forward,refs['gdn'],'AscendGatedDeltaNetAttention')
  saved=[];self.assertIs(G.validate(C,obj.forward,refs,saved.append),f.__code__)
  self.assertTrue(saved[0]['passed']);self.assertTrue(all(saved[0]['checks'].values()))
 def test_replacements_and_error_record_before_rejection(self):
  for variant in ('target','receiver','module','globals','code','wrapper'):
   mods,refs,obj=fixture();q=mods['target'];g=mods['gdn'];f=obj.forward.__func__
   if variant=='target':q.QwenGatedDeltaNetAttention=type('ForeignTarget',(),{})
   elif variant=='receiver':obj=g.AscendGatedDeltaNetAttention()
   elif variant=='module':sys.modules[G.NAMES['gdn']]=types.ModuleType(G.NAMES['gdn'])
   elif variant=='globals':
    replacement=types.FunctionType(f.__code__,dict(f.__globals__),f.__name__);replacement.__qualname__=f.__qualname__
    obj.forward=types.MethodType(replacement,obj)
   elif variant=='code':f.__code__=f.__code__.replace(co_firstlineno=f.__code__.co_firstlineno+1)
   else:f.__wrapped__=f
   saved=[]
   with self.assertRaises(ValueError,msg=variant):G.validate(C,obj.forward,refs,saved.append)
   self.assertEqual(len(saved),1);self.assertFalse(saved[0]['passed']);self.assertTrue(saved[0]['actual_class'])
 def test_actual_worker_object_selection_and_unknown_source_refuse(self):
  tree=ast.parse((P/'evidence/qwen3_5.py').read_bytes());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='Qwen3_5DecoderLayer')
  assignments=[n for n in ast.walk(cls)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Attribute)and t.attr=='linear_attn'for t in n.targets)]
  self.assertEqual(len(assignments),1);self.assertEqual(ast.unparse(assignments[0].value.func),'QwenGatedDeltaNetAttention')
  mods,refs,obj=fixture();refs['target']=dict(refs['target'],sha256='0'*64);saved=[]
  with self.assertRaises(ValueError):G.validate(C,obj.forward,refs,saved.append)
  self.assertFalse(saved[0]['checks']['target_canonical_module_source'])
  self.assertEqual(mods['gdn'].AscendGatedDeltaNetAttention.forward.__closure__,None)
if __name__=='__main__':unittest.main()
