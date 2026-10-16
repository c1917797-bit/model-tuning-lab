"""Real NPUGraph decode replay seam. Caller must hold an existing Owned lease.

No device selection, container creation or admission is performed here.
Production13-argument op only inside capture. All evidence/debug work is out.
Not a full mixed-native-prefill graph qualification.
"""
FIELDS=('base','k_log','u_log','lambda_log','decay','length')
INPUTS=('query','key','value','g','beta')

def need(v,m):
 if not v:raise ValueError(m)

def snap(args):return [x.detach().cpu().clone()for x in args]

class Replay:
 def __init__(self,t,op,args):
  need(len(args)==13 and all(x.device.type=='npu'for x in args),'actual13arg NPU storage only')
  self.t,self.op,self.args=t,op,args;self.ptrs=[x.data_ptr()for x in args]
  initial=[x.clone()for x in args]
  # Compilation/warmup is necessary but must not spend logical initial state.
  for _ in range(3):op(*args)
  t.npu.synchronize()
  for x,y in zip(args,initial):x.copy_(y)
  self.graph=t.npu.NPUGraph()
  with t.npu.graph(self.graph):
   self.output=op(*args)
  t.npu.synchronize()
  for x,y in zip(args,initial):x.copy_(y)
  t.npu.synchronize()

 def replay(self):
  need([x.data_ptr()for x in self.args]==self.ptrs,'all captured input/state/metadata pointers unchanged')
  before=snap(self.args)
  self.graph.replay();self.t.npu.synchronize()
  after=snap(self.args);out=self.output.detach().cpu().clone()
  need([x.data_ptr()for x in self.args]==self.ptrs,'no replay pointer mutation')
  return before,after,out

def inspect_step(t,R,PRE,before,after,out,debug_after,debug_out,precast,ledger):
 """Independent recurrence ledger; reset/joins are supplied by explicit events."""
 state=dict(zip(FIELDS,before[5:11]));actual=dict(zip(FIELDS,after[5:11]));debug=dict(zip(FIELDS,debug_after[5:11]));ids=before[12].tolist()
 need(len(ids)==len(set(ids))and before[11].tolist()==[0]+[1]*len(ids),'actual singleton sequence and unique slots')
 need(all(PRE.bits(t,a,b)for a,b in zip(before[:5]+before[11:],after[:5]+after[11:])),'input and sequence/id bytes immutable')
 need(all(PRE.bits(t,a,b)for a,b in zip(before[:5]+before[11:],debug_after[:5]+debug_after[11:])),'debug input and sequence/id bytes immutable')
 need(all(PRE.bits(t,actual[n],debug[n])for n in FIELDS)and PRE.bits(t,out,debug_out),'actual graph vs outside-debug production transparency')
 inp=dict(zip(INPUTS,before[:5]));truth=[];errors=[]
 for j,s in enumerate(ids):
  ledger[s],y=R.advance(t,ledger[s],inp,j);truth.append(y)
  represented=R.restore(t,actual,s);den=float(ledger[s].norm());num=float((represented-ledger[s]).norm());errors.append(num/den if den else(0. if num==0 else float('inf')))
 readout=PRE.evaluate(t,precast,out,t.stack(truth));invariants=R.invariant(t,state,actual,ids)
 inactive=[s for s in range(state['base'].shape[0])if s not in ids]
 invariants['inactive_exact_bytes']=all(PRE.bits(t,state[k][inactive],actual[k][inactive])for k in FIELDS)
 invariants['append_base_exact_bytes']=all(PRE.bits(t,state['base'][s],actual['base'][s])for s in ids if int(state['length'][s,0,0])<7)
 invariants['metadata_padding_exact_bytes']=all(PRE.bits(t,state[k][ids,:,start:],actual[k][ids,:,start:])for k,start in(('length',1),('decay',1),('lambda_log',7)))
 passed=readout['passed']and all(__import__('math').isfinite(e)and e<=R.STATE_LIMIT for e in errors)and all(invariants.values())
 return dict(readout=readout,state_relative_l2=errors,invariants=invariants,passed=passed,reference='independent cumulative CPU64; precast empirical existing fixed gate',full_mixed_graph_qualified=False)

def run_admitted(t,prod,debug,args,events,R,PRE,sink,deadline):
 """Call only from existing admitted069 Owned NPU child after source/DSO load.

 events: per-step exact CPU5inputs+sequence+ids and explicit resets {slot:FP32}.
 debug14arg executes AFTER replay on independent copies of pre-replay state.
 sink must preserve each raw before a failing predicate is raised.
 """
 import time
 need(type(deadline)in(int,float)and time.time()<deadline<=1792220533,'existing owner deadline within fixed24h')
 session=Replay(t,prod,args);ledger=args[5].detach().cpu().double().clone();rows=[]
 for step,event in enumerate(events):
  need(time.time()<deadline,'fixed graph child deadline; no automatic extension')
  need(set(event)=={'inputs','sequence','ids','resets'},'typed exact graph input event')
  for slot,value in event['resets'].items():
   need(type(slot)is int and 0<=slot<args[5].shape[0]and value.dtype==t.float32 and tuple(value.shape)==tuple(args[5][slot].shape),'explicit new slot initial state')
   args[5][slot].copy_(value.to(args[5].device));ledger[slot]=value.double().clone()
   for x in args[6:11]:x[slot].zero_()
  for dst,name in zip(args[:5],INPUTS):dst.copy_(event['inputs'][name].to(dst.device))
  args[11].copy_(event['sequence'].to(args[11].device));args[12].copy_(event['ids'].to(args[12].device));t.npu.synchronize()
  before,after,out=session.replay()
  # Actual debug DSO, not CPU reconstruction or graph-time Python callback.
  da=[x.to(args[0].device)for x in before];side=t.empty_like(session.output,dtype=t.float32);dz=debug(*da,side);t.npu.synchronize()
  debug_after=snap(da);debug_out=dz.cpu().clone();precast=side.cpu().clone()
  try:row=inspect_step(t,R,PRE,before,after,out,debug_after,debug_out,precast,ledger)
  except BaseException as error:row=dict(passed=False,primary=repr(error),full_mixed_graph_qualified=False)
  raw=sink(step,dict(event=event,before=before,after=after,output=out,debug_after=debug_after,debug_output=debug_out,actual_precast_FP32=precast,pointer_before=session.ptrs,pointer_after=[x.data_ptr()for x in args],graph_type=type(session.graph).__module__+'.'+type(session.graph).__qualname__,metrics=row))
  rows.append(dict(step=step,raw=raw,metrics=row));need(row['passed'],'graph replay actual numerical/state/byte predicate; raw retained')
 return dict(schema='deltalog.actual-decode-graph-replay/v094',rows=rows,graph_replay_tested=True,full_mixed_graph_qualified=False,qualified=False)
