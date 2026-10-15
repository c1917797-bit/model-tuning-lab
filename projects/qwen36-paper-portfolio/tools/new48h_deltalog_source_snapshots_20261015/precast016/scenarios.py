"""Default-OFF device-free lifecycle event generator, not an NPU producer."""
import argparse,json,sys
SCHEMA='deltalog.request-lifecycle/v1'
def plan(batch=16,steps=160,graph=False):
 if batch not in(1,16)or steps not in(160,1024):raise ValueError('registered coverage')
 slots=2*batch+4;active={i:'initial-'+str(i)for i in range(batch)};events=[]
 # Every retired slot is later reused under a DIFFERENT request identity.
 for step in range(steps):
  action=[]
  if batch==1:
   if step in(31,79):
    slot=0;action.append(dict(op='retire',slot=slot,request=active.pop(slot)))
   if step in(32,80):
    active[0]='new-'+str(step);action.append(dict(op='join',slot=0,request=active[0],initial='nonzero'if step==32 else'zero'))
  else:
   if step==31:
    for slot in range(1,16,2):action.append(dict(op='retire',slot=slot,request=active.pop(slot)))
   if step==32:
    for slot in range(16,24):active[slot]='joined-'+str(slot);action.append(dict(op='join',slot=slot,request=active[slot],initial='nonzero'))
   if step==63:
    for slot in range(16,24):action.append(dict(op='retire',slot=slot,request=active.pop(slot)))
   if step==64:
    for slot in range(1,16,2):active[slot]='reused-'+str(slot);action.append(dict(op='join',slot=slot,request=active[slot],initial='zero'))
  ids=sorted(active)
  if ids:ids=ids[step%len(ids):]+ids[:step%len(ids)]
  events.append(dict(step=step,actions=action,ids=ids,requests=[active[i]for i in ids],checkpoint=step in(6,7,8,14,15,16,53,159,1023)))
 return dict(schema=SCHEMA,batch=batch,steps=steps,slots=slots,guards=[slots-2,slots-1],events=events,graph_enabled=graph,
             graph_contract='separate captured key for each actual batch; reset after warmup/capture; never advance oracle for warmup'if graph else'not required for eager qualification',
             algorithm_math_changed=False,source_identity_required=True,model_qualified=False)
def main():
 if '--execute'not in sys.argv:print('disabled');return 0
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--batch',type=int,choices=(1,16),required=True);p.add_argument('--steps',type=int,choices=(160,1024),default=160);p.add_argument('--graph',action='store_true');p.add_argument('--output',required=True);a=p.parse_args()
 with open(a.output,'x')as f:json.dump(plan(a.batch,a.steps,a.graph),f,sort_keys=True,allow_nan=False)
 return 0
if __name__=='__main__':raise SystemExit(main())
