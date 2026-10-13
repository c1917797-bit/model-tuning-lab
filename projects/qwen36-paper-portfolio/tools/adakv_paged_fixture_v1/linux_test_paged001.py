"""NEW fixture-only Linux launcher for frozen paged001's SAME29 tests."""
from __future__ import annotations
import argparse,ast,hashlib,json,sys,unittest
from pathlib import Path
TEST_SHA="4a505ccd98ac5f2050997e97018727d4c7ef9db7127d2aabfdf4c4f455c7f18d"
CAND_SHA="16f069c78e0b929fda1ce6e1f394f8067a88ff28237e2c13b722ea9e01a7b507"
EVID_SHA="c57c02000ba30fea33670ceedc28894a5bc8977df8a4426393ddb46ba6356734"
def need(x,m):
 if not x:raise ValueError(m)
def transform(text):
 tree=ast.parse(text);original=ast.dump(tree,include_attributes=False);changed=[]
 for n in tree.body:
  if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
   name=n.targets[0].id
   if name in("ROOT","MIRROR","DONOR"):
    changed.append((n,n.value));n.value=ast.parse("_TEST_ROOT"if name=="ROOT"else"_CORE_SERVICE"if name=="DONOR"else"_UNUSED_MIRROR").body[0].value
 class Fixture(ast.NodeTransformer):
  def visit_Call(self,n):
   if isinstance(n.func,ast.Attribute)and n.func.attr=="read_bytes"and ast.unparse(n.func.value)=="MIRROR / 'multi_request_candidate.actual-wire.json'":
    replacement=ast.copy_location(ast.Call(func=ast.Name(id="_read_candidate_wire",ctx=ast.Load()),args=[],keywords=[]),n)
    replacements.append((replacement,n));return replacement
   return self.generic_visit(n)
 replacements=[];tree=Fixture().visit(tree)
 need(len(changed)==3 and len(replacements)==3,"only exact three paths and three fixture reads")
 saved=dict((id(a),b)for a,b in replacements)
 class Undo(ast.NodeTransformer):
  def visit_Call(self,n):
   if id(n)in saved:return saved[id(n)]
   return self.generic_visit(n)
 restore=Undo().visit(tree)
 for n,value in changed:n.value=value
 need(ast.dump(restore,include_attributes=False)==original,"whole suite inverse AST, all29 assertions original")
 # Reapply from the original tree; do not mutate the proved inverse.
 tree=ast.parse(text)
 for n in tree.body:
  if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id in("ROOT","MIRROR","DONOR"):
   name=n.targets[0].id;n.value=ast.parse("_TEST_ROOT"if name=="ROOT"else"_CORE_SERVICE"if name=="DONOR"else"_UNUSED_MIRROR").body[0].value
 return ast.fix_missing_locations(Fixture().visit(tree))
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true");p.add_argument("--paged-root");p.add_argument("--core-root");a=p.parse_args(argv)
 if not a.execute:print(json.dumps(dict(enabled=False,software_only=True,NPU=False)));return 0
 root=Path(a.paged_root).resolve();core=Path(a.core_root).resolve();test=root/"test_paged.py"
 raw=test.read_bytes();need(hashlib.sha256(raw).hexdigest()==TEST_SHA,"frozen actual29 suite")
 candidate=core/"plugin/qwen36_adakv_ascend/multi_request_candidate.py";evidence=core/"tools/adakv_grouped_service_v1/adakv_grouped_service/evidence.py"
 need(hashlib.sha256(candidate.read_bytes()).hexdigest()==CAND_SHA and hashlib.sha256(evidence.read_bytes()).hexdigest()==EVID_SHA,"real Linux frozen CORE fixture bytes")
 def candidate_wire():return json.dumps(dict(text=candidate.read_bytes().decode())).encode()
 # Distinct private test module; no source file/global rewrite or numerical permission.
 import types
 m=types.ModuleType("_paged001_linux_fixture_suite");m.__file__=str(Path(__file__).resolve());sys.modules[m.__name__]=m
 m.__dict__.update(_TEST_ROOT=root,_CORE_SERVICE=evidence.parent,_UNUSED_MIRROR=core,_read_candidate_wire=candidate_wire)
 before=set(sys.modules);exec(compile(transform(raw.decode()),str(test),"exec"),m.__dict__)
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(m))
 need(result.testsRun==29,"full original29, no skip/sampling")
 need(not any(x=="torch"or x.startswith("torch.")or x=="torch_npu"or x.startswith("torch_npu.")for x in set(sys.modules)-before),"stdlib/NumPy only")
 return 0 if result.wasSuccessful()else 1
if __name__=="__main__":raise SystemExit(main())

