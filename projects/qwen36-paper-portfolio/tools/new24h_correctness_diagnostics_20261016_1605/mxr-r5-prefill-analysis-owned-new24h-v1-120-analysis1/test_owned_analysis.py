import ast,copy,importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('_tested120analysisowner',P/'owned_analysis.py');O=importlib.util.module_from_spec(s);s.loader.exec_module(O)


class Controls(unittest.TestCase):
 def test_01_cold_actual_entry_and_owner(self):
  for leaf in('owned_analysis.py','analysis_entry.py'):
   for flags in([],['--help']):
    p=subprocess.run([sys.executable,'-I','-B',str(P/leaf),*flags],capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stderr)
 def test_02_inherited_resource_and_cleanup_math(self):
  m=json.loads((P/'SOURCE_MANIFEST.json').read_bytes());r=m['inherited_owner_source_ref'];p=Path(r['path'])if sys.platform=='linux'else P.parent/'mxr-r5-prefill-counterfactual-new24h-120-repair2/owned/owned_cpu120.py'
  if sys.platform=='linux':p=Path(O.obj(r)['files']['owned_cpu120.py']['path'])
  old=ast.parse(p.read_bytes());new=ast.parse((P/'owned_analysis.py').read_bytes())
  for name in('storage_check','docker_argv','output_scan','create_argv','inspect_owned','closure'):
   find=lambda t:next(n for n in t.body if isinstance(n,ast.FunctionDef)and n.name==name)
   self.assertEqual(ast.dump(find(old)),ast.dump(find(new)))
  text=(P/'owned_analysis.py').read_text();self.assertIn("cleanup_seconds=max(1,min(90",text);self.assertIn("signal.alarm(1000)",text);self.assertNotIn('--device',O.create_argv(7,{'/x':('/x',False)},dict(ASCEND_RT_VISIBLE_DEVICES=''),'test',['-I','x.py']))
 def test_03_real_child_argv_and_fixed_stage(self):
  m=json.loads((P/'SOURCE_MANIFEST.json').read_bytes());cmd=O.child_command(m,m['actual_stage_ref'])
  self.assertEqual(cmd[:2],['-I','-B']);self.assertEqual(cmd[2],m['files']['analysis_entry.py']['path']);self.assertEqual(json.loads(cmd[cmd.index('--stage-ref')+1]),m['actual_stage_ref'])
  with self.assertRaisesRegex(ValueError,'fixed actual'):
   O.child_command(m,dict(m['actual_stage_ref'],sha256='0'*64))
 def test_04_report_contract_rejects_fake_qualification_or_missing_tiles(self):
  with tempfile.TemporaryDirectory()as td:
   cases=[dict(case_id=str(i))for i in range(3)];p=Path(td)/'g.json';p.write_bytes(json.dumps(dict(cases=cases)).encode());r=O.ref(p);ar=dict(path='/software',bytes=1,sha256='0'*64)
   own=dict(guest_source=r,analysis_source_ref=ar,actual_stage_ref=ar)
   d=dict(schema='mxr.prefill-source-and-round-cell-analysis/v120-analysis1',source=ar,stage_ref=ar,NPU=False,qualification=False,performance=False,task=False,reference_validity_resolved=False,cases=[dict(case=c,tiles=[{}]*384,qualification=False)for c in cases],original_consumer=dict(source=r,candidate_anchor_bitwise=True,old_R5_FAIL_preserved=True),owned_software=dict(source=ar,tests=22,passed=True))
   O.receive_report(d,own,ar)
   out=Path(td);numerical=dict(d);software=numerical.pop('owned_software');(out/'ANALYSIS120A1.json').write_bytes(json.dumps(numerical).encode());(out/'SOFTWARE_CONTROLS.json').write_bytes(json.dumps(software).encode())
   receipt=dict(schema='mxr.prefill-analysis-owned-child/v120-analysis1',source=ar,analysis_source=ar,stage_ref=ar,analysis_ref=O.ref(out/'ANALYSIS120A1.json'),software=software,NPU=False,qualified=False)
   (out/'ANALYSIS_RECEIPT.json').write_bytes(json.dumps(receipt).encode());O.receive_files(out,own,ar)
   (out/'ANALYSIS120A1.json').write_bytes(json.dumps(dict(numerical,reference_validity_resolved=True)).encode())
   with self.assertRaisesRegex(ValueError,'byte/source join'):O.receive_files(out,own,ar)
   for change in(lambda x:x.update(qualification=True),lambda x:x.update(reference_validity_resolved=True),lambda x:x['cases'][0]['tiles'].pop(),lambda x:x['cases'].pop(),lambda x:x['owned_software'].update(tests=21)):
    z=copy.deepcopy(d);change(z)
    with self.assertRaises(ValueError):O.receive_report(z,own,ar)
 def test_05_new_source_and_complete_RO_inventory(self):
  m=json.loads((P/'SOURCE_MANIFEST.json').read_bytes());self.assertEqual(m['software_cases'],O.SOFTWARE_CASES);self.assertIn('analysis_source_ref',m);self.assertEqual(m['actual_stage_ref']['bytes'],5414)
  text=(P/'owned_analysis.py').read_text()
  self.assertIn("*original['files'].values()",text);self.assertIn("*analysis['files'].values()",text);self.assertIn("own['actual_CPU_owner_ref']",text)
  self.assertNotIn('NPUowner_success',text);self.assertTrue(m['original_NPU_parent_FAIL_preserved'])


if __name__=='__main__':unittest.main()
