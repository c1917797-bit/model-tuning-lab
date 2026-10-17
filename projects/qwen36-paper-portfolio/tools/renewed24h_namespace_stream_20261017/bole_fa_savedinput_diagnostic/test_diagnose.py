"""Independent small CPU fixture, never saved model data or NPU proof."""
import ast,sys,unittest
from pathlib import Path
import torch as t
import diagnose as D
class Tests(unittest.TestCase):
 def test_ancestor_paths_exclude_sibling_and_padding_independently(self):
  q=t.zeros(3,6,256);k=t.zeros(8,256);v=t.zeros(8,256);v[:,0]=t.tensor([2,4,8,16,32,64,128,256])
  mask=t.ones(3,8,dtype=t.bool);mask[:,:2]=False;mask[1,2]=False;mask[2,3]=False
  out=D.matrix(t,q,k,v,mask,t.float64)
  for actual,expected in zip(out[:,0,0].tolist(),[3,14/3,22/3]):self.assertAlmostEqual(actual,expected,places=13)
  self.assertTrue(t.equal(out[:,:,1:],t.zeros_like(out[:,:,1:])))
 def test_full_saved_layout_protocol_wrong_mask_is_reported_not_silently_fixed(self):
  q=t.zeros(3,6,256,dtype=t.bfloat16);k=t.zeros(3,1,256,dtype=t.bfloat16);v=t.zeros_like(k)
  pk=t.zeros(131,256,dtype=t.bfloat16);pv=t.zeros_like(pk);pv[:,0]=1
  sk=t.zeros(2,128,1,256,dtype=t.bfloat16);sv=t.zeros_like(sk);sv.reshape(-1,1,256)[:131,0]=pv
  native=dict(query=q.permute(1,0,2).unsqueeze(0).contiguous(),key=sk.permute(0,2,1,3).contiguous(),value=sv.permute(0,2,1,3).contiguous(),block_table=t.tensor([[0,1]],dtype=t.int32))
  mask=t.ones(1,1,3,256,dtype=t.bool);mask[:,:,:,:132]=False;mask[0,0,1,132]=False;mask[0,0,2,133]=False;native['atten_mask']=mask
  truth=D.matrix(t,q,sk.reshape(-1,256),sv.reshape(-1,256),mask[0,0],t.float64).to(t.bfloat16)
  captures={};anchors=[];paths=[dict(child=c,steps=[])for c in(1,2)]
  for layer in range(3,64,4):
   captures[layer]=dict(query=q.reshape(3,-1),key=k.reshape(3,-1),value=v.reshape(3,-1),output=truth,trial=dict(native_before=native,scratch_k=sk,scratch_v=sv,native_layout={}))
   anchors.append(dict(layer=layer,physical_pages=[9,4],key=sk.clone(),value=sv.clone()))
   for path in paths:
    while len(path['steps'])<2:path['steps'].append(dict(node=0 if not path['steps']else path['child'],context=dict(captures={})))
    for step in path['steps']:
     n=step['node'];selected=(0,)if n==0 else(0,n)
     ck=t.cat((pk,k[list(selected),0]));cv=t.cat((pv,v[list(selected),0]))
     out=t.stack([D.direct(t,q[n,h],ck,cv,t.float64)for h in range(6)]).to(t.bfloat16)
     step['context']['captures'][layer]=dict(query=q[n].reshape(1,-1),key=k[n].reshape(1,-1),value=v[n].reshape(1,-1),after_key=ck.unsqueeze(1),after_value=cv.unsqueeze(1),output=out)
  raw=dict(schema='bole.actual-three-node-model-capture/v1',scheduler_committed=False,initial_FA_pages=anchors,tree_context=dict(captures=captures),native=paths)
  result=D.diagnose(t,raw);self.assertEqual(len(result['rows']),16)
  self.assertTrue(all(all(r['input_bit_joins'].values())for r in result['rows']))
  native['atten_mask'][0,0,2,132]=False
  broken=D.diagnose(t,raw)
  self.assertFalse(broken['rows'][0]['input_bit_joins']['full_ancestor_padding_mask'])
  self.assertFalse(broken['qualified'])
 def test_no_candidate_reference_or_npu_import_and_default_off(self):
  tree=ast.parse(Path(D.__file__).read_bytes())
  imports=[n.name for x in ast.walk(tree)if isinstance(x,ast.Import)for n in x.names]
  self.assertNotIn('adapter',imports);self.assertNotIn('torch_npu',imports)
  self.assertIn('torch',imports)
if __name__=='__main__':unittest.main()
