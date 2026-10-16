"""CPU software ABI controls, not actual saved-frame or NPU qualification."""
import copy,importlib.util,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import diagnose as D
class Tests(unittest.TestCase):
 def test_selected_flush_dead_payload_not_false_failure(self):
  import torch as t
  state=dict(base=t.zeros(3,12,128,128),k_log=t.zeros(3,4,7,128,dtype=t.bfloat16),u_log=t.zeros(3,12,7,128),lambda_log=t.zeros(3,12,16),decay=t.zeros(3,12,16),length=t.zeros(3,12,16,dtype=t.int32));state['length'][1,:,0]=1;state['decay'][1,:,0]=-.3;after={k:v.clone()for k,v in state.items()};after['base'][1].fill_(.1);after['length'][1].zero_();after['decay'][1].zero_();after['k_log'][1,:,1:]=float('nan');after['u_log'][1,:,1:]=float('nan')
  value=D.flush_join(t,state,after,1);self.assertTrue(value['selected_live_u_bitwise']);self.assertGreater(value['selected_dead_u_NaN_count'],0)
  for which in('live','lambda','outside'):
   bad={k:v.clone()for k,v in after.items()}
   if which=='live':bad['u_log'][1,0,0,0]=1.
   if which=='lambda':bad['lambda_log'][1,0,0]=1.
   if which=='outside':bad['base'][0,0,0,0]=-0.
   with self.assertRaises(ValueError):D.flush_join(t,state,bad,1)
 def test_real_capture_fingerprint_and_alias_contract(self):
  import torch as t
  inputs={'q':t.zeros(1,64,4,128,dtype=t.bfloat16),'k':t.zeros(1,64,4,128,dtype=t.bfloat16),'v':t.zeros(1,64,12,128,dtype=t.bfloat16),'g':t.zeros(1,64,12),'beta':t.zeros(1,64,12,dtype=t.bfloat16),'initial_state':t.zeros(1,12,128,128),'cu_seqlens':t.tensor([0,64],dtype=t.int32),'use_qk_l2norm_in_kernel':True};pc=dict(inputs=inputs,output=t.zeros(1,64,12,128,dtype=t.bfloat16),final_state=t.zeros(1,12,128,128));operands={k:({'value':v}if type(v)is bool else{'actual':D.fingerprint(v),'captured':D.fingerprint(v)})for k,v in inputs.items()};proof=dict(module_file={'sha256':D.CHUNK_SHA},counter=90,pid=1,original_id=3,gdn_alias_id=3,chunk_alias_id=3,controls={});before=dict(proof,operands=operands);after=dict(proof,counter=91,input_fingerprints={k:D.fingerprint(v)for k,v in inputs.items()if type(v)is not bool});pc['native_call']=dict(schema='deltalog.native-chunk-dispatch/v030',actual_original_call_returned=True,before=before,after=after,returned_state=D.fingerprint(pc['final_state']),returned_output=D.fingerprint(pc['output']))
  self.assertTrue(D.actual_chunk_capture(pc)['returns_joined'])
  bad=copy.deepcopy(pc);bad['native_call']['after']['original_id']=4
  with self.assertRaises(ValueError):D.actual_chunk_capture(bad)
  bad=copy.deepcopy(pc);bad['inputs']['q'][0,0,0,0]=1
  with self.assertRaises(ValueError):D.actual_chunk_capture(bad)
if __name__=='__main__':unittest.main()
