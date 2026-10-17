"""Real cheap CLI and original guard. No original raw/model receipts opened."""
import copy,hashlib,importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
import prebind_static as S,readset_guard101r8 as G
P=Path(__file__).resolve().parent

def metadata():
 raw=(P/'SOURCE_TEMPLATE.json').read_bytes();m=json.loads(raw)
 return m,dict(path=m['root']+'/SOURCE_TEMPLATE.json',bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

class CheapPrebind(unittest.TestCase):
 def test_original_actual_failure_and_exact_bound_phase_declaration(self):
  m,tr=metadata()
  self.assertNotIn('COMMANDS_FINAL.json',m['files'])
  with self.assertRaisesRegex(ValueError,'undeclared own read .*COMMANDS_FINAL.json'):G.check(m,P)
  bound,report=S.prepare(m,tr,P,runtime=False)
  self.assertIn('COMMANDS_FINAL.json',bound['files']);self.assertNotIn('COMMANDS_FINAL.json',m['files'])
  raw=(P/'COMMANDS_FINAL.json').read_bytes();r=bound['files']['COMMANDS_FINAL.json']
  self.assertEqual(r,dict(path=m['root']+'/COMMANDS_FINAL.json',bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
  self.assertEqual(report['guard']['files_checked'],sum(n.startswith('test_')and n.endswith('.py')for n in m['files']))
  self.assertIs(bound['prepared_only'],True);self.assertIs(report['qualified'],False);self.assertIs(report['closed_raw_reads'],False)

 def test_real_fresh_I_cheap_frontdoor_no_backend_or_external_dependency(self):
  m,tr=metadata()
  cp=subprocess.run([sys.executable,'-I','-B',str(P/'cheap_prebind.py'),'--execute','--template-sha256',tr['sha256']],capture_output=True,text=True,timeout=20)
  self.assertEqual(cp.returncode,0,cp.stderr);report=json.loads(cp.stdout)
  self.assertIs(report['NPU'],False);self.assertIs(report['resources_admitted'],False);self.assertIs(report['external_dependency_reads'],False)
  self.assertEqual(report['ticket']['path'],m['root']+'/COMMANDS_FINAL.json')
  bad=subprocess.run([sys.executable,'-I','-B',str(P/'cheap_prebind.py'),'--execute','--template-sha256','0'*64],capture_output=True,text=True,timeout=20)
  self.assertNotEqual(bad.returncode,0);self.assertIn('template SHA',bad.stderr)

 def clone(self,parent):
  m,tr=metadata();root=parent/'declared';root.mkdir()
  for name in(*m['files'],'SOURCE_TEMPLATE.json','COMMANDS_FINAL.json'):
   q=root/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((P/name).read_bytes())
  return root,m,tr

 def test_actual_file_mutation_missing_ticket_old_or_nested_argv_ref_rejected(self):
  for defect in('missing','old-template','nested-source','own-file','undeclared-test-read'):
   with self.subTest(defect=defect),tempfile.TemporaryDirectory()as td:
    root,m,tr=self.clone(Path(td));ticket=root/'COMMANDS_FINAL.json'
    if defect=='missing':ticket.unlink()
    elif defect in('old-template','nested-source'):
     final=json.loads(ticket.read_bytes())
     if defect=='old-template':final['template']['sha256']='0'*64
     else:final['postconsumer_input_ticket']['payload_source']['sha256']='0'*64
     ticket.write_text(json.dumps(final),encoding='utf8')
    elif defect=='own-file':
     q=root/'test_source_identity.py';q.write_bytes(q.read_bytes()+b'\n# unexpected own mutation\n')
    else:
     # A new missing read is not licensed by the bound ticket declaration.
     q=root/'test_extra_unlisted.py';q.write_text("from pathlib import Path\nP=Path(__file__).parent\nx=(P/'MISSING_EXTRA.json').read_bytes()\n",encoding='utf8')
     m['files'][q.name]=dict(path=m['root']+'/'+q.name,**S.fingerprint(q))
     template=root/'SOURCE_TEMPLATE.json';template.write_text(json.dumps(m),encoding='utf8');tr=dict(path=m['root']+'/SOURCE_TEMPLATE.json',**S.fingerprint(template))
     spec=json.loads((root/'COMMANDS_SPEC.json').read_bytes());final=S.expected_ticket(m,tr,root);ticket.write_text(json.dumps(final),encoding='utf8')
    with self.assertRaises((ValueError,FileNotFoundError)):S.prepare(m,tr,root,runtime=False)

 def test_binder_same_cheap_check_precedes_any_original_input_reads(self):
  text=(P/'bind_source.py').read_text()
  self.assertLess(text.index('STATIC.bind(O,m,tr,P)'),text.index("sr=json.loads(a.bridge_source_ref)"))
  self.assertLess(text.index('STATIC.bind(O,m,tr,P)'),text.index('F.bind_closed('))
  self.assertIn("m['files']=bound['files']",(P/'prebind_static.py').read_text())
  self.assertIn('for r in[*m[\'files\'].values()',text)

 def test_guard_exact_original_bytes_and_no_filename_exception(self):
  m,tr=metadata();r=m['parent_r20r1_guard_ref'];raw=(P/'readset_guard101r8.py').read_bytes()
  self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(r['bytes'],r['sha256']))
  self.assertNotIn('COMMANDS_FINAL.json',raw.decode());self.assertIn("declared=set(m['files'])",raw.decode())

if __name__=='__main__':unittest.main()
