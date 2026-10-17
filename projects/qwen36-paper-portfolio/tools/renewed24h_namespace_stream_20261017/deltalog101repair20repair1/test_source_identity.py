"""Actual prepared/bound metadata controls; no mock PASS or card access."""
import copy,json,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
from packet_contract import ROOT,OUTPUT,IDENTITY,SOFTWARE_CASES
def check(m,c):
 def need(v,msg):
  if not v:raise ValueError(msg)
 need(m['root']==ROOT,'exact R5 self root')
 need(m['runtime_identity']==IDENTITY,'exact R5 runtime owner/container/run identity')
 need(m['output_root']==c['output']==OUTPUT,'actual template and COMMANDS unique R5 output')
 need(m['software_cases']==SOFTWARE_CASES,'actual metadata software count, producer and source share single constant')
 import packet_predecessor as B
 need(m['reviewed_domain_template_ref']==B.TEMPLATE_REF and m['reviewed_domain_files']==B.FILES,'exact final043 predecessor')
 need('test_source_identity.py'in m['files']and m['files']['test_source_identity.py']['path']==ROOT+'/test_source_identity.py','new metadata controls visible in actual guest readset')
 need(all(r['path']==ROOT+'/'+k for k,r in m['files'].items()),'all own files R5 scope')
 for r in m['dependencies']:
  need('/deltalog-model-directRNE-smoke-v1-MODEL036R2'not in r['path']and '/deltalog-model-directRNE-smoke-v1-MODEL036-repair2'not in r['path'],'no residual selfR2 dependency')
 for mode,entry in(('binding','bind_source.py'),('sourceaudit','host_ticket.py'),('execute','host_ticket.py')):
  need(ROOT+'/'+entry in c[mode]['args'],'actual command invokes same reviewed R5 source')
 return True
def actual():
 path=P/'SOURCE_MANIFEST.json'
 if not path.exists():path=P/'SOURCE_TEMPLATE.json'
 return json.loads(path.read_bytes()),json.loads((P/'COMMANDS.json').read_bytes())
class MetadataControls(unittest.TestCase):
 def test_actual_template_or_bound_source_matches_commands(self):
  m,c=actual();self.assertTrue(check(m,c))
  self.assertIs(c['not_executable'],True);self.assertEqual(c['execution_ticket'],'COMMANDS_FINAL.json')
  args=c['binding']['args'];self.assertEqual(args[args.index('--template-sha256')+1],'NON_EXECUTABLE_INDEX_USE_COMMANDS_FINAL_TEMPLATE_SHA256')
  import hashlib
  final=json.loads((P/'COMMANDS_FINAL.json').read_bytes());raw=(P/'SOURCE_TEMPLATE.json').read_bytes()
  expected=dict(path=ROOT+'/SOURCE_TEMPLATE.json',bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
  self.assertEqual(final['template'],expected);argv=final['bind']['argv'];self.assertEqual(argv[argv.index('--template-sha256')+1],expected['sha256'])
  self.assertEqual(final['payload_source'],final['postconsumer_input_ticket']['payload_source'])
 def test_actual_oldR2_output_rejected(self):
  m,c=actual();m=copy.deepcopy(m);m['output_root']='/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-deltalog-MODEL036R2-main-NEW48H_MODEL036R2_001'
  with self.assertRaisesRegex(ValueError,'output'):check(m,c)
 def test_actual_oldR2_runtime_fields_rejected(self):
  m,c=actual()
  for key,value in(('owner','deltalog-MODEL036R2-new48h-MAIN-20261015-001'),('container_prefix','deltalog-MODEL036R2-'),('run_id','NEW48H_MODEL036R2_001')):
   bad=copy.deepcopy(m);bad['runtime_identity'][key]=value
   with self.assertRaisesRegex(ValueError,'runtime'):check(bad,c)
