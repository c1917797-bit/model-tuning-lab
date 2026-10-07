import ast,copy,json,subprocess,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import contract as c
def sample(batch,horizon):
 # Explicit synthetic software-contract rows, NEVER a device receipt.
 cases=[]
 for mode,trial in c.MODES:
  lengths=[0]*(batch+3);rows=[];merges=0
  for i in range(160):
   active=(0,1,3,7,12,15,16,16)[i%8] if batch==16 and mode=="graph" else batch
   reset=(i//16)%(batch+3) if i in (64,112) else None
   if reset is not None:lengths[reset]=0
   for token in range(active):
    slot=(token+i)%(batch+3)
    if lengths[slot]==horizon-1:lengths[slot]=0;merges+=1
    else:lengths[slot]+=1
   rows.append(dict(step=i+1,active=active,reset_slot=reset,passed=True,
    **{k:True for k in c.GUARDS},all_logs_bitwise_outside_new_U={k:True for k in c.LOGS},
    output_error=0.0,complete_state_l2=0.0,max_per_head_l2=0.0,
    raw_step=dict(file="raw-step-b%d-%s-t%d-step%d.pt"%(batch,mode,trial,i+1),
     step=i+1,retained=False,bytes=1,sha256="0"*64),finite_scope=c.FINITE_SCOPE,
    native_expected_defined_rows=active,native_expected_undefined_padding_rows=batch-active,
    native_padding_values_rewritten=False,finite_buffer_checks={k:True for k in c.FINITE_BUFFERS}))
  cases.append(dict(batch=batch,mode=mode,trial=trial,status="passed",steps=rows,
   resets=2,merges=merges,max_output_error=0.0,max_state_l2=0.0,max_head_l2=0.0))
 return dict(schema="kvbp.short-horizon-native-gate/v4",status="single_batch_kernel_native_eager_graph_pass",
  finite_scope=c.FINITE_SCOPE,candidate_namespace=c.NAMESPACE,materialization_interval=8,
  storage_log_capacity=16,cases=cases)
class Gate(unittest.TestCase):
 def test_full_source_closure(self):
  m,s=c.source_admission({"path":str(HERE/"SOURCE_MANIFEST.json"),"sha256":c.sha(HERE/"SOURCE_MANIFEST.json")})
  self.assertEqual(len(s),84)
 def test_h8_replay_software_contract(self):
  for b in (1,16):self.assertEqual(c.validate_cases(sample(b,8),b)["changing_feedback_steps"],640)
 def test_h16_replay_rejected_not_promoted(self):
  for b in (1,16):
   with self.assertRaises(ValueError):c.validate_cases(sample(b,16),b)
 def test_unchanged_thresholds(self):
  for key,value in (("output_error",.003031),("complete_state_l2",2.00001e-6),("max_per_head_l2",2.00001e-6)):
   s=sample(16,8);s["cases"][0]["steps"][0][key]=value
   with self.assertRaises(ValueError):c.validate_cases(s,16)
 def test_bad_finite_and_padding(self):
  for key,value in (("native_padding_values_rewritten",True),("finite_buffer_checks",{})):
   s=sample(16,8);s["cases"][0]["steps"][0][key]=value
   with self.assertRaises(ValueError):c.validate_cases(s,16)
 def test_default_OFF_real_CLI(self):
  p=subprocess.run([sys.executable,"-B",str(HERE/"run.py")],capture_output=True,text=True)
  self.assertEqual(p.returncode,0,p.stderr);self.assertFalse(json.loads(p.stdout)["npu_executed"])
 def test_syntax(self):
  for p in HERE.glob("*.py"):ast.parse(p.read_text(),filename=str(p))
if __name__=="__main__":unittest.main()
