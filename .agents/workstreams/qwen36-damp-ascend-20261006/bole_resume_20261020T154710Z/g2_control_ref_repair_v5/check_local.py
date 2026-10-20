"""Execute exact test method AST in a supplied reference test namespace.

This host-only check adapts local fixture paths; actual same-image imports the
complete new test module from its new source and reruns all258 cases.
"""
import argparse
import ast
import importlib.util
from pathlib import Path
import sys
import unittest


def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--check',action='store_true');p.add_argument('--baseline-root',type=Path);a=p.parse_args()
 if not a.check:print('{"enabled":false,"NPU":false}');return 0
 if a.baseline_root is None or not a.baseline_root.is_absolute():raise ValueError('explicit actual local reference root')
 base=a.baseline_root;new=Path(__file__).with_name('test_g2_builder.py');sys.path.insert(0,str(base))
 spec=importlib.util.spec_from_file_location('exact_ref_reader_control_namespace',base/'test_g2_builder.py');env=importlib.util.module_from_spec(spec);spec.loader.exec_module(env)
 before=ast.parse((base/'test_g2_builder.py').read_bytes());after=ast.parse(new.read_bytes())
 old=next(n for n in before.body if isinstance(n,ast.ClassDef));changed=next(n for n in after.body if isinstance(n,ast.ClassDef));methods={n.name:n for n in changed.body if isinstance(n,ast.FunctionDef)}
 for n in old.body:
  if isinstance(n,ast.FunctionDef)and n.name!='test_CPU3_derivation_retains_complete_original_create_inspect_resource_checks':
   assert ast.dump(n,include_attributes=False)==ast.dump(methods[n.name],include_attributes=False),n.name
 marker="  spec=importlib.util.spec_from_file_location('_g2_test_external'"
 left=(base/'test_g2_builder.py').read_text();right=new.read_text();assert left[left.index(marker):]==right[right.index(marker):]
 exec(compile(ast.Module(body=[n for n in after.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))],type_ignores=[]),str(new),'exec'),env.__dict__)
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(env.BuilderTests))
 if not result.wasSuccessful()or result.testsRun!=7:raise ValueError('all five original and two new declared-ref controls required')
 print('{"original_assertions_preserved":true,"controlled_local_cases":7,"NPU":false}')
 return 0

if __name__=='__main__':raise SystemExit(main())
