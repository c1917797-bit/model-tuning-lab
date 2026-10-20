"""Portable assembly and original dynamic-command/readset closure controls."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import sourceio as C
import g3_readset as R
spec=importlib.util.spec_from_file_location('g3_preparer_pure',P/'prepare_g3.py');B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)

class PrepareTests(unittest.TestCase):
 def fixture(self,parent=False,dependencies=(),predecessor=None):
  td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);root=Path(td.name)
  (root/'sourceio.py').write_bytes((P/'sourceio.py').read_bytes())
  cc=P/'command_contract.py'
  if parent:
   cc=P.parent/'g2_long_output/command_contract.py'
   if not cc.exists():cc=C.checked(C.obj(C.obj(C.ref(P/'SOURCE_TEMPLATE.json'))['g3_predecessor']['source'])['files']['command_contract.py'])
  (root/'command_contract.py').write_bytes(cc.read_bytes())
  (root/'bind_model.py').write_text("import sourceio as C\ndef readset(sr):\n m=C.obj(sr);return [sr,m['prepared_template'],*m['files'].values()]\n")
  old=C.write(root/'HISTORICAL.json',dict(required_sameimage_software_cases=154));template=C.write(root/'SOURCE_TEMPLATE.json',dict(synthetic_fixture=True))
  m=dict(root=str(root),output_root=str(root/'OUT'),files={n:C.ref(root/n)for n in('sourceio.py','bind_model.py','command_contract.py')},
   dependencies=list(dependencies),component_refs={},prepared_template=template,service_required_sameimage_software_cases=242 if parent else 274,
   command_scope=dict(schema='bole.post-binding-command-readset/v2',file='COMMANDS.json',generated_after_binding=True,
    included_in_actual_host_readset=True,historical_ref=old,compatibility_file='COMMANDS_G2.json'if parent else'COMMANDS_G3.json'))
  if predecessor is not None:m['g3_predecessor']=predecessor
  sr=C.write(root/'SOURCE_BOUND.json',m)
  helper=importlib.util.spec_from_file_location('g3_fixture_commands',root/'command_contract.py');cc=importlib.util.module_from_spec(helper);helper.loader.exec_module(cc)
  commands=dict(schema='bole.G1-actual-bound-commands/v2',source=template,bound_source=sr,
   required_sameimage_software_cases=m['service_required_sameimage_software_cases'],historical_required_sameimage_software_cases=154,
   legacy_entrypoints_retained_for_inverse_tests_only=True,actual_G1_execution_claimed=False,
   **cc.expected(str(root),m['output_root'],sr,template,{}))
  commands.update(dict(G2_stream_protocol=True,actual_G2_execution_claimed=False)if parent else dict(G3_stream_protocol=True,actual_G3_execution_claimed=False))
  commandref=C.write(root/'COMMANDS.json',commands)
  C.write(root/m['command_scope']['compatibility_file'],dict(source=sr,template=template,commands=commandref,
   model=commands['model'],CPU=commands['CPU'],required_sameimage_software_cases=m['service_required_sameimage_software_cases']))
  return root,json.loads(json.dumps(sr,sort_keys=True))
 def test_advisory_path_is_lineage_only_but_wrong_hash_or_symlink_still_rejected(self):
  td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);root=Path(td.name);path=root/'one.py';path.write_text('exact reviewed source\n')
  expected=dict(C.ref(path),path='/advisory/workspace/one.py')
  self.assertEqual(B.portable_inventory(root,'one.py',expected),C.ref(path))
  with self.assertRaises(ValueError):B.portable_inventory(root,'one.py',dict(expected,sha256='0'*64))
  path.rename(root/'real.py');path.symlink_to(root/'real.py')
  with self.assertRaises(ValueError):B.portable_inventory(root,'one.py',expected)
 def test_sorted_ref_collects_original_commands_without_relaxing_actual_argv(self):
  root,sr=self.fixture();result=R.collect(sr)
  self.assertTrue(result['source_and_commands_unchanged']);self.assertTrue(result['original_unreconstructed_call']['rejected'])
  path=root/'COMMANDS.json';value=json.loads(path.read_text());value['CPU'][-1]+='-foreign';path.write_text(json.dumps(value))
  with self.assertRaises(ValueError):R.collect(sr)
 def test_full_parent_dynamic_readset_is_required_and_missing_inherited_file_fails(self):
  parent,ps=self.fixture(True);old=R.collect(ps)['refs'];td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);root=Path(td.name)
  extra={key:C.write(root/(key+'.json'),{})for key in('owner_result','qualification','source_audit')};p=dict(source=ps,**extra)
  current,sr=self.fixture(dependencies=[*old,*p.values()],predecessor=p);self.assertEqual(R.audit(sr)['missing'],[])
  omitted=next(r for r in old if Path(r['path']).name=='COMMANDS_G2.json')
  bad,bs=self.fixture(dependencies=[r for r in[*old,*p.values()]if r!=omitted],predecessor=p)
  with self.assertRaisesRegex(ValueError,'closure missing/conflicting'):R.audit(bs)

if __name__=='__main__':unittest.main()
