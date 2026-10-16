"""Unseen deterministic decode-graph recipes, not a generated PASS receipt."""
def recipe(t,batch,steps):
 if batch not in(1,16)or steps not in(16,160):raise ValueError('B1/B16 fixed16->160 domain')
 gen=t.Generator().manual_seed(2610169401+batch);slots=2*batch+4
 initial=(t.randn((slots,12,128,128),generator=gen)*.005).float();events=[]
 for step in range(steps):
  # Reassign storage slots on fixed tensor metadata without graph recapture.
  ids=[(step//9+j)% (slots-2)for j in range(batch)]
  resets={}
  if step in(5,33,73,113):resets[ids[0]]=t.zeros_like(initial[0])if step%2 else(t.randn(initial[0].shape,generator=gen)*.005).float()
  inputs=dict(query=t.nn.functional.normalize(t.randn((batch,4,128),generator=gen),dim=-1).bfloat16(),key=t.nn.functional.normalize(t.randn((batch,4,128),generator=gen),dim=-1).bfloat16(),value=(t.randn((batch,12,128),generator=gen)*.2).bfloat16(),g=-(.002+.18*t.rand((batch,12),generator=gen)),beta=t.sigmoid(t.randn((batch,12),generator=gen)).bfloat16())
  events.append(dict(inputs=inputs,sequence=t.tensor([0]+[1]*batch,dtype=t.int32),ids=t.tensor(ids,dtype=t.int32),resets=resets))
 return initial,events
