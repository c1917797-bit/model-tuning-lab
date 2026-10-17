"""Actual TP4 diagnostic agreement; no scheduler transaction or new process."""
import hashlib
from model_entry import need


def agree(torch,group,owner,tokens,terminal,*,device,phase):
 need(group.world_size==4 and 0<=group.rank_in_group<4,
      'actual single TP4 group, not independent singleton simulation')
 need(type(phase)is int and phase in(0,1,2,3)and
      (terminal is None or type(terminal)is int and terminal in(0,1,2)),
      'fixed diagnostic agreement phases and root/child/cancel path')
 digest=hashlib.sha256(owner.request.encode('utf8')).digest()
 identity=[int.from_bytes(digest[i:i+8],'big',signed=True)for i in range(0,32,8)]
 values=[*identity,owner.generation,owner.slot,owner.length,owner.version,
         *tokens,-1 if terminal is None else terminal,phase,48,16]
 row=torch.tensor([values],dtype=torch.int64,device=device)
 gathered=group.all_gather(row,dim=0)
 need(tuple(gathered.shape)==(4,len(values))and gathered.dtype==torch.int64,
      'actual original native TP group all_gather shape')
 need(bool(torch.equal(gathered,gathered[:1].expand_as(gathered))),
      'all4 same request generation/root/tree/path and complete64 traversal')
 return dict(schema='bole.actual-TP4-three-node-agreement/v1',phase=phase,
             rows=gathered.detach().cpu(),rank=group.rank_in_group,
             scheduler_committed=False)


def temporary_writeback(torch,bridge,proposal,*,group,tokens,current_owner):
 """Verify real accepted-path destinations, then restore ALL original bytes.

 This is a synchronous diagnostic cache transaction, NOT scheduler commit.
 Any failure propagates; the existing owner must stop the failed worker.
 Native generation may continue only after verified restoration on all4.
 """
 from model_entry import tensor_id
 need(proposal['schema']=='bole.actual-model-selected-path-staging/v1'and
      proposal['published']is False and proposal['model_ready']is False and
      current_owner()==proposal['owner'],'fresh staged actual cache writes')
 owner=proposal['owner'];path=proposal['processed_nodes']
 need(path in((),(0,),(0,1),(0,2)),'only actual inclusive-root accepted path')
 terminal=None if not path else path[-1]
 rows=proposal['writes'];need(len(rows)==(0 if not path else 128),
      '48 recurrent+48conv+16K+16V complete accepted-path destinations')
 device=bridge.bindings[0]['conv'].device
 before=agree(torch,group,owner,tokens,terminal,device=device,phase=1)
 expected={(b['index'],k):b for b in bridge.bindings for k in(('conv','state')if b['kind']=='gdn'else('key','value'))}
 need(not path or {(r['layer'],r['kind'])for r in rows}==set(expected),'all and only64 layer destination kinds')
 handles=[]
 for row in rows:
  arena=row['arena'];need(tensor_id(arena)==row['arena_identity'],'same actual destination view')
  binding=expected[(row['layer'],row['kind'])]
  need(arena is binding[row['kind']],'write targets actual registered layer object, not same-shape substitute')
  if row['kind']in('conv','state'):
   slot=bridge._physical_slot(binding,owner)
   need(row['slot']==row['physical_slot']==slot and row['group']==binding['group']and row['logical_owner_slot']==owner.slot and
        row['slot_binding']is binding['slot_binding']and row['slot_binding_identity']==binding['slot_binding'].identity(),
        'exact live per-layer group/physical slot, never global logical owner slot')
   dest=arena[row['slot']];index=None
  else:
   dest=arena;index=row['indices']
   planned=[binding['table'][(owner.length+i)//128]*128+(owner.length+i)%128 for i in range(len(path))]
   need(index.cpu().tolist()==planned,'exact actual accepted-path physical KV slots')
  actual=dest if index is None else dest[index//128,index%128]
  need(bridge.N.bits(torch,actual,row['before'])and actual.shape==row['after'].shape and actual.dtype==row['after'].dtype,
       'prevalidate each actual destination before touching first arena')
  handles.append((row,dest,index))
 bridge._validate_bindings(owner)
 modified=[];first_fault=None;after_bits=[];restored_bits=[]
 try:
  for row,dest,index in handles:
   # Mark before enqueueing a device write: even a partial failing write must
   # be included in restoration attempts. No exception is converted to PASS.
   modified.append((row,dest,index))
   if index is None:dest.copy_(row['after'])
   else:dest[index//128,index%128]=row['after']
  for row,dest,index in handles:
   actual=dest if index is None else dest[index//128,index%128]
   need(bridge.N.bits(torch,actual,row['after']),'actual staged writeback bitwise')
   after_bits.append(actual.clone())
  applied=agree(torch,group,owner,tokens,terminal,device=device,phase=2)
 except BaseException as e:first_fault=e
 finally:
  restoration_errors=[]
  for row,dest,index in reversed(modified):
   try:
    if index is None:dest.copy_(row['before'])
    else:dest[index//128,index%128]=row['before']
   except BaseException as error:restoration_errors.append(repr(error))
 if restoration_errors:raise ValueError('actual rollback failed: '+repr(restoration_errors))from first_fault
 if first_fault is not None:raise first_fault
 for row,dest,index in handles:
  actual=dest if index is None else dest[index//128,index%128]
  need(bridge.N.bits(torch,actual,row['before']),'actual original native cache restored bitwise')
  restored_bits.append(actual.clone())
 need(current_owner()==owner,'original request/generation still owns restored arena')
 bridge._validate_bindings(owner)
 restored=agree(torch,group,owner,tokens,terminal,device=device,phase=3)
 return dict(schema='bole.actual-accepted-path-writeback-restore/v1',
             before_agreement=before,applied_agreement=applied,
             restored_agreement=restored,actual_applied=after_bits,
             actual_restored=restored_bits,scheduler_committed=False,
             model_ready=False,production_ready=False)
