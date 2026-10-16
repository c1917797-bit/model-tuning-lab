"""Actual full2K tensor report ABI on CPU; fixtures are NEVER NPU evidence."""
import copy,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
C=load(P/'consume.py','_120_real_consumer_control');G=C.G
class Roundtrip(unittest.TestCase):
 def test_real_tensors_original_consumer_and_new_X2_working_fields(self):
  import torch
  torch.set_num_threads(1)
  with tempfile.TemporaryDirectory()as td:
   d=Path(td);Q=torch.zeros((1,2048,4,128),dtype=torch.bfloat16);V=torch.zeros((1,2048,12,128),dtype=torch.bfloat16);A=torch.zeros((1,2048,12,64),dtype=torch.float32);B=torch.zeros_like(A,dtype=torch.bfloat16)
   for begin in range(0,2048,64):B[0,begin:begin+64]=torch.eye(64,dtype=torch.bfloat16)[:,None,:].expand(64,12,64)
   S=torch.zeros((1,12,128,128),dtype=torch.float32);gate=torch.zeros((1,2048,12));cu=torch.tensor([0,2048],dtype=torch.int32)
   x=dict(q=Q,k=Q.clone(),v=V,g=gate,beta=torch.ones((1,2048,12),dtype=torch.bfloat16),initial_state=S,cu_seqlens=cu,scale=128**-.5,already_normalized=True)
   after={n:G.fp(torch,t)for n,t in x.items()if torch.is_tensor(t)}
   saved=dict(inputs=x,inputs_after=after,normalized_inputs=x,normalized_inputs_after=after,output=V,final_state=S,solve=dict(A=A,cu=cu,output=B),FP32_policy=dict(allow_hf32=False,common_to_all_arms=True),block044={})
   metric_source=json.loads((P/'SOURCE_MANIFEST.json').read_bytes())['original_metrics']
   if sys.platform!='linux':metric_source=G.ref(P.parent/'mxr-r118-capture-20261013-001/consume_capture.py')
   source_ref=dict(path='/software-only/not-a-qualified-source',bytes=1,sha256='0'*64)
   launch=dict(source=source_ref,build=source_ref,library=source_ref,symbol='call_mxr_y16_compensated');prereq=d/'software-only-prerequisite.json';prereq.write_text(json.dumps(launch))
   m=dict(original_metrics=metric_source,original_working_oracle=G.ref(P.parent/'mxr-two-residual-model-new24h-098-repair5/boundary_oracle.py')if sys.platform!='linux'else json.loads((P/'SOURCE_MANIFEST.json').read_bytes())['original_working_oracle'],variant_ref=source_ref,actual037_prerequisite=G.ref(prereq))
   m['files']={n:G.ref(P/n)for n in('direct_rne.py','third_residual125.py')};rows=[]
   for arm in G.ARMS:
    z=dict(arm=arm,A=A,G=gate,B=B,W=V,U=V,Hentry=torch.zeros((1,12,32,128,128),dtype=torch.bfloat16),Vnew=V.transpose(1,2).contiguous(),Hend_final=S,output=V,state=S,inputs_after={n:after[n]for n in('q','k','v','g','beta','initial_state','cu_seqlens')})
    if arm=='saved_candidate':z['actual_X2']=dict(variant_ref=source_ref,trace=None,solver_identity=launch)
    if arm=='third_residual':z['actual_X3']=dict(variant_ref=m['files']['third_residual125.py'],rounds=3,FP32_bmm_per_group=6,solver_identity=launch)
    path=d/(arm+'.pt');torch.save(z,path);rows.append(dict(arm=arm,raw=G.ref(path)))
   result=dict(rows=rows,candidate_anchor_bitwise=True,same_actual_A_G=True,raw_bytes=sum(r['raw']['bytes']for r in rows))
   stage=dict(schema='mxr.prefill-three-arm-stage/v084',source=source_ref,authority=G.AUTHORITY,primary=None,NPU=True,qualified=False,raw=G.RAW,result=result)
   report=C.consume_case(torch,m,stage,saved)
   self.assertFalse(report['qualification']);self.assertEqual(set(report['registered_working']),set(G.ARMS))
   self.assertTrue(all(v['state']['pass']and v['output']['pass']for v in report['registered_working'].values()))
   self.assertTrue(all(v is None for pair in report['pairs'].values()for v in pair['first_differing_chunk'].values()))
   bad=torch.load(rows[0]['raw']['path'],map_location='cpu',weights_only=True);bad['actual_X2']['variant_ref']=dict(source_ref,sha256='1'*64);torch.save(bad,rows[0]['raw']['path']);rows[0]['raw']=G.ref(rows[0]['raw']['path']);result['raw_bytes']=sum(r['raw']['bytes']for r in rows)
   with self.assertRaisesRegex(ValueError,'exact097R1 X2'):C.consume_case(torch,m,stage,saved)
if __name__=='__main__':unittest.main()
