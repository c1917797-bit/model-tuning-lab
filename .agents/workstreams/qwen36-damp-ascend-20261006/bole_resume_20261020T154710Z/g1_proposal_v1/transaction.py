"""Permanent selected-path cache publication for an owned service experiment.

No launcher or device setup. Scheduler acknowledgement is a separate observed
event; all-rank cache agreement alone never certifies scheduler commitment.
"""
from model_entry import need,tensor_id
import tp_consensus as TP

def publish(torch,bridge,proposal,*,group,tokens,scheduled_nodes,target_next,remaining_output_tokens,current_owner):
 need(proposal['schema']=='bole.actual-model-selected-path-staging/v1'and
      proposal['published']is False and proposal['model_ready']is False and
      current_owner()==proposal['owner'],'fresh complete staged model proposal')
 owner=proposal['owner'];path=tuple(proposal['processed_nodes'])
 need(path in((0,),(0,1),(0,2)),'one actual noncancelled inclusive-root path')
 terminal=path[-1];rows=proposal['writes']
 decision=proposal['decision'];emitted=tuple(decision.emitted_tokens)
 need(type(remaining_output_tokens)is int and remaining_output_tokens>=1 and
      len(emitted)<=remaining_output_tokens and
      (remaining_output_tokens!=1 or terminal==0),'actual remaining output budget before permanent writes')
 need(type(scheduled_nodes)is int and 1<=scheduled_nodes<=3 and
      len(tokens)==3 and tokens[1]!=tokens[2]and len(target_next)==scheduled_nodes and
      all(type(x)is int and x>=0 for x in(*tokens,*target_next))and terminal<scheduled_nodes,
      'exact admitted target IDs and genuine distinct draft children')
 need((decision.request_id,decision.generation,decision.slot,decision.root)==
      (owner.request,owner.generation,owner.slot,0)and
      tuple(decision.accepted_draft_nodes)==path[1:]and
      emitted==tuple(tokens[i]for i in path[1:])+(target_next[terminal],)and
      (terminal==0 or target_next[0]==tokens[terminal]),
      'exact decision owner, accepted child identities and actual target bonus')
 need(tuple(decision.processed_nodes)==path and decision.terminal==terminal and
      len(emitted)==len(path)and len(decision.accepted_draft_nodes)==len(path)-1 and
      emitted[-1]==decision.bonus_token and decision.cancelled is False,
      'accepted cache advance includes root, emitted stream includes bonus')
 expected={(b['index'],kind):b for b in bridge.bindings
           for kind in(('conv','state')if b['kind']=='gdn'else('key','value'))}
 need(len(rows)==128 and {(r['layer'],r['kind'])for r in rows}==set(expected),
      'all and only128 real destinations across64 layers')
 handles=[]
 for row in rows:
  binding=expected[(row['layer'],row['kind'])];arena=row['arena']
  need(arena is binding[row['kind']]and tensor_id(arena)==row['arena_identity'],
       'actual registered destination and storage identity')
  if row['kind']in('state','conv'):
   slot=bridge._physical_slot(binding,owner)
   need(row['slot']==row['physical_slot']==slot and row['group']==binding['group']and
        row['logical_owner_slot']==owner.slot and
        row['slot_binding']is binding['slot_binding']and
        row['slot_binding_identity']==binding['slot_binding'].identity(),
        'actual per-layer slot identity')
   dest=arena[slot];index=None
  else:
   dest=arena;index=row['indices']
   planned=[binding['table'][(owner.length+i)//128]*128+(owner.length+i)%128
            for i in range(len(path))]
   need(index.cpu().tolist()==planned,'only actual accepted physical KV positions')
  actual=dest if index is None else dest[index//128,index%128]
  need(bridge.N.bits(torch,actual,row['before'])and actual.shape==row['after'].shape and
       actual.dtype==row['after'].dtype,'all destinations prevalidated before first write')
  handles.append((row,dest,index))
 bridge._validate_bindings(owner)
 device=handles[0][1].device
 need(group.world_size==4 and 0<=group.rank_in_group<4,'actual TP4 service group')
 values=[scheduled_nodes,*target_next,*([-1]*(3-len(target_next))),
         terminal,len(emitted),*emitted,*([-1]*(2-len(emitted))),remaining_output_tokens]
 decision_row=torch.tensor([values],dtype=torch.int64,device=device)
 agreed=group.all_gather(decision_row,dim=0)
 need(tuple(agreed.shape)==(4,len(values))and agreed.dtype==torch.int64 and
      bool(torch.equal(agreed,agreed[:1].expand_as(agreed))),
      'actual all4 agree admitted target IDs and complete emitted stream including bonus')
 decision_agreement=dict(schema='bole.service-TP4-output-decision/v1',
  rows=agreed.detach().cpu(),rank=group.rank_in_group,
  columns=('scheduled_nodes','target_next0','target_next1','target_next2',
           'terminal','emitted_count','emitted0','emitted1','remaining_output_tokens'))
 before=TP.agree(torch,group,owner,tokens,terminal,device=device,phase=1)
 modified=[];applied_values=[]
 try:
  need(current_owner()==owner,'owner unchanged after actual TP consensus')
  for row,dest,index in handles:
   modified.append((row,dest,index))
   if index is None:dest.copy_(row['after'])
   else:dest[index//128,index%128]=row['after']
  for row,dest,index in handles:
   actual=dest if index is None else dest[index//128,index%128]
   need(bridge.N.bits(torch,actual,row['after']),'actual permanent write bitwise')
   applied_values.append(actual.clone())
  bridge._validate_bindings(owner)
  need(current_owner()==owner,'owner unchanged at publication barrier')
  applied=TP.agree(torch,group,owner,tokens,terminal,device=device,phase=2)
 except BaseException as primary:
  errors=[]
  for row,dest,index in reversed(modified):
   try:
    if index is None:dest.copy_(row['before'])
    else:dest[index//128,index%128]=row['before']
   except BaseException as error:errors.append(repr(error))
  for row,dest,index in handles:
   try:
    actual=dest if index is None else dest[index//128,index%128]
    need(bridge.N.bits(torch,actual,row['before']),'failure restoration bitwise')
   except BaseException as error:errors.append(repr(error))
  if errors:raise ValueError('publication failure restoration errors '+repr(errors))from primary
  raise
 return dict(schema='bole.service-cache-publication/v1',owner=owner,
  processed_nodes=path,emitted_tokens=emitted,next_length=owner.length+len(path),
  next_version=owner.version+1,before_agreement=before,applied_agreement=applied,
  decision_agreement=decision_agreement,scheduled_nodes=scheduled_nodes,target_next=tuple(target_next),
  remaining_output_tokens=remaining_output_tokens,
  actual_applied=applied_values,cache_published=True,
  scheduler_committed=False,scheduler_ack_pending=True)

def acknowledge(publication,*,request_id,request_object,expected_request,
                actual_computed_tokens,actual_tokens_without_spec,
                actual_next_root,actual_live_ids):
 need(publication['cache_published']is True and publication['scheduler_ack_pending']is True,
      'one pending actual cache publication')
 owner=publication['owner']
 need(request_id==owner.request and request_object is expected_request and
      actual_live_ids==[request_id],'same strongly held live C1 request at acknowledgement')
 need(type(actual_computed_tokens)is int and
      actual_computed_tokens==publication['next_length']and
      actual_tokens_without_spec==publication['next_length']+1 and
      actual_next_root==publication['emitted_tokens'][-1],
      'actual next native scheduler input acknowledges cache length and unprocessed bonus')
 receipt=dict(schema='bole.service-native-scheduler-ack/v1',
  request=request_id,previous_version=owner.version,version=publication['next_version'],
  computed_tokens=actual_computed_tokens,next_root=actual_next_root,
  scheduler_committed=True,whole_model_qualification=False,final_success=False)
 publication['scheduler_ack_pending']=False
 publication['scheduler_committed']=True
 return receipt

