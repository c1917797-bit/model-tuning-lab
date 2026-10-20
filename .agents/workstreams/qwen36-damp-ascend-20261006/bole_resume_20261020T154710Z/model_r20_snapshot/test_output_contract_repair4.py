"""Real cold host CLI: output admission only, no resource/HAL substitution."""
import hashlib,json,subprocess,sys,unittest
from pathlib import Path
import contract090 as C
from repair14_ledger import previous_text
P=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
 def test_real_cold_host_output_contract_accepts_only_new_model_and_CPU(self):
  commands=json.loads((P/'COMMANDS.json').read_bytes())
  for key in('model','CPU'):
   actual=commands[key];host_index=next(i for i,value in enumerate(actual)if value.endswith('/host090.py'))
   argv=[sys.executable,'-I','-B',str(P/'host090.py'),*actual[host_index+1:],'--output-contract-only']
   output=argv[argv.index('--output')+1]
   self.assertEqual(output,C.OUTPUT_POSIX if key=='model'else C.CPU_OUTPUT_POSIX)
   result=subprocess.run(argv,capture_output=True,text=True,timeout=20)
   self.assertEqual(result.returncode,0,result.stderr)
   self.assertEqual(json.loads(result.stdout),dict(output=output,NPU=False,contract_only=True))
  for identity in('repair2','repair3-projection','repair4-output-contract'):
   for suffix in('MAIN','CPU-MAIN'):
    old='/opt/host/vnf/austinov/run-bole-root-repeat-witness-'+identity+'-20261017-001-'+suffix+'-NEW24H_001'
    result=subprocess.run([sys.executable,'-I','-B',str(P/'host090.py'),'--output-contract-only','--output',old],capture_output=True,text=True,timeout=20)
    self.assertNotEqual(result.returncode,0);self.assertIn('exact unique Linux owned output',result.stderr)
  for invalid in(C.OUTPUT_POSIX+'/child','relative','C:\\wrong'):
   result=subprocess.run([sys.executable,'-I','-B',str(P/'host090.py'),'--output-contract-only','--output',invalid],capture_output=True,text=True,timeout=20)
   self.assertNotEqual(result.returncode,0);self.assertIn('exact unique Linux owned output',result.stderr)
 def test_complete_inverse_and_source_command_output_joins(self):
  m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes());commands=json.loads((P/'COMMANDS.json').read_bytes())
  sr=dict(path=m['root']+'/SOURCE_TEMPLATE.json',bytes=(P/'SOURCE_TEMPLATE.json').stat().st_size,sha256=hashlib.sha256((P/'SOURCE_TEMPLATE.json').read_bytes()).hexdigest())
  self.assertEqual(commands['source'],sr);self.assertEqual(json.loads(commands['bind'][commands['bind'].index('--reviewed-template-ref')+1]),sr)
  self.assertEqual(commands['required_sameimage_software_cases'],150)
  self.assertEqual(m['output_root'],C.OUTPUT_POSIX);self.assertEqual(m['model_receipt_root'],C.OUTPUT_POSIX+'/dense/receipts')
  for key,output in(('model',C.OUTPUT_POSIX),('CPU',C.CPU_OUTPUT_POSIX)):
   self.assertEqual(commands[key][commands[key].index('--output')+1],output)
   self.assertEqual(commands[key][commands[key].index('--execute')-1],m['root']+'/host090.py')
  proof=json.loads((P/'OUTPUT_CONTRACT_EDITS_R4.json').read_bytes())
  for name,row in proof.items():
   actual=previous_text(P/name).encode('utf8');self.assertEqual(dict(bytes=len(actual),sha256=hashlib.sha256(actual).hexdigest()),row['after'])
   text=actual.decode('utf8')
   for edit in reversed(row['edits']):
    self.assertEqual(text.count(edit['after']),1);text=text.replace(edit['after'],edit['before'])
   self.assertEqual(dict(bytes=len(text.encode()),sha256=hashlib.sha256(text.encode()).hexdigest()),{k:row['original'][k]for k in('bytes','sha256')})
  self.assertEqual(m['output_contract_repair4']['runtime_changes'],['contract090.py','owned_substrate.py'])
if __name__=='__main__':unittest.main()
