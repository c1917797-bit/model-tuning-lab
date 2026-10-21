"""C1 first-request service ownership; observes native counters and object identity."""
from dataclasses import dataclass
from model_entry import Owner,need,tensor_id
import transaction

import g3_fia_contract as DOMAIN
@dataclass
class Frame:
 owner:object
 tokens:tuple
 real_input_ids:tuple
 scheduled_nodes:int
 ordinal:int
 closed:bool=False

class LiveOwner:
 def __init__(self,runner,bindings,initial_owner,*,max_steps=3,output_budget=4):
  need(type(initial_owner)is Owner and initial_owner.slot==0 and initial_owner.length==131 and
       initial_owner.version==0 and type(initial_owner.generation)is int and initial_owner.generation==1,'bounded G1 native C1/131 request entry')
  need(type(max_steps)is int and type(output_budget)is int and output_budget in(4,1024)and max_steps==output_budget-1,'explicit frozen G2 step/output bounds')
  self.output_budget=output_budget
  self.runner=runner;self.bindings=bindings;self.initial=initial_owner
  self.request=runner.requests.get(initial_owner.request)
  need(self.request is not None,'strong actual native request')
  self.version=0;self.length=131;self.max_steps=max_steps;self.steps=0
  self.frame=None;self.pending=None;self.retired=False;self.draft_root=None;self.children=None
  self.acknowledgements=[]
  self.registrations={};self.fa_registrations={}
  self.check_request()
  for binding in bindings:
   if binding['kind']=='gdn':
    binding['slot_binding'].check(initial_owner)
    self.registrations[id(binding)]=binding['slot_binding']
   else:
    need(binding['kind']=='fa','only actual hybrid cache kinds')
    group=runner.kv_cache_config.kv_cache_groups[binding['group']]
    table=runner.input_batch.block_table[binding['group']]
    obj=binding['layer'].self_attn.attn
    self.fa_registrations[id(binding)]=dict(obj=obj,group=group,table=table,
     row=tuple(binding['table']),key=tensor_id(binding['key']),value=tensor_id(binding['value']),
     geometry=(table.blocks_per_phys_block,table.logical_block_size,table.physical_block_size,
               table.block_size,table.use_hybrid_blocks,table.pcp_world_size,table.dcp_world_size))
    self.check_fa(binding)
    DOMAIN.allocation(table=binding['table'],physical_blocks=self.request.block_ids[binding['group']],
        ratio=table.blocks_per_phys_block,physical_size=table.physical_block_size,kernel_size=table.block_size,use_hybrid=table.use_hybrid_blocks)
 def check_request(self):
  r=self.runner;rid=self.initial.request
  need(not self.retired and r.requests.get(rid)is self.request and r.input_batch.req_ids==[rid]and
       r.input_batch.req_id_to_index=={rid:0},'same strongly held actual C1 request and native row')
  return rid
 def record_draft(self,root,children):
  self.check_request()
  need(type(root)is int and root>=0 and type(children)is tuple and len(children)==2 and
       all(type(x)is int and x>=0 for x in children)and children[0]!=children[1],
       'genuine finite native first-MTP top2 result')
  self.draft_root=root;self.children=children
 def make_frame(self,scheduler_output,num_scheduled_tokens):
  rid=self.check_request();r=self.runner;batch=r.input_batch
  need(self.frame is None,'previous native sample output must close its frame')
  need(self.draft_root is not None and self.children is not None,'actual preceding MTP proposal')
  length=int(batch.num_computed_tokens_cpu[0]);without_spec=int(batch.num_tokens_no_spec[0])
  if self.pending is not None:
   root=int(batch.token_ids_cpu[0,length])
   proof=transaction.acknowledge(self.pending,request_id=rid,request_object=r.requests[rid],
    expected_request=self.request,actual_computed_tokens=length,
    actual_tokens_without_spec=without_spec,actual_next_root=root,actual_live_ids=batch.req_ids.copy())
   self.acknowledgements.append(proof)
   self.length=self.pending['next_length'];self.version=self.pending['next_version'];self.pending=None
  need(length==self.length and without_spec==length+1 and 131<=length<=131+self.output_budget-2,
       'actual current computed length and one unprocessed native bonus')
  need(self.steps<self.max_steps,'bounded service step count')
  need(set(scheduler_output.num_scheduled_tokens)=={rid}and len(num_scheduled_tokens)==1,
       'one actual scheduled request')
  count=int(num_scheduled_tokens[0]);drafts=tuple(scheduler_output.scheduled_spec_decode_tokens.get(rid,()))
  need(count==scheduler_output.num_scheduled_tokens[rid]and 1<=count<=3 and len(drafts)==count-1,
       'actual scheduled root plus admitted draft rows')
  need(drafts==self.children[:count-1],'native scheduler admits only actual preceding MTP children')
  actual=tuple(int(x)for x in batch.token_ids_cpu[0,length:length+count].tolist())
  tokens=(self.draft_root,*self.children)
  need(actual==tokens[:count],'actual native input IDs match root and admitted children')
  owner=Owner(rid,self.initial.generation,0,length,self.version)
  self.frame=Frame(owner,tokens,actual,count,self.steps);self.steps+=1
  return self.frame
 def current(self):
  rid=self.check_request();f=self.frame
  need(f is not None and not f.closed and f.owner.request==rid,'one current open target frame')
  need(int(self.runner.input_batch.num_computed_tokens_cpu[0])==f.owner.length,
       'native computed counter unchanged during target verification')
  for binding in self.bindings:
   if binding['kind']=='fa':self.check_fa(binding)
  return f.owner
 def check_fa(self,binding):
  self.check_request();r=self.runner;s=self.fa_registrations[id(binding)]
  group=binding['group'];obj=binding['layer'].self_attn.attn
  need(obj is s['obj']and r.kv_cache_config.kv_cache_groups[group]is s['group']and
       binding['prefix']in s['group'].layer_names and
       r.input_batch.block_table[group]is s['table'],
       'same live native FA layer/group and CPU block table')
  table=s['table'];cpu=table.get_cpu_tensor();count=int(table.num_blocks_per_row[0])
  row=tuple(int(x)for x in cpu[0,:count].tolist())
  ratio=table.blocks_per_phys_block
  geometry=(ratio,table.logical_block_size,table.physical_block_size,table.block_size,
            table.use_hybrid_blocks,table.pcp_world_size,table.dcp_world_size)
  need(type(ratio)is int and ratio>0 and geometry==s['geometry']and
       table.logical_block_size==table.block_size==128 and
       table.physical_block_size==ratio*128 and type(table.use_hybrid_blocks)is bool and
       table.pcp_world_size==table.dcp_world_size==1,'same actual native FA physical/kernel geometry')
  physical=tuple(self.request.block_ids[group])
  need(physical and all(type(x)is int and x>=0 for x in physical),
       'actual strongly held request physical block allocation')
  expanded=tuple(p*ratio+j for p in physical for j in range(ratio))if table.use_hybrid_blocks else physical
  need(cpu.device.type=='cpu'and count==len(s['row'])and row==s['row']and
       tuple(binding['table'])==row and expanded==row,
       'same current allocated FA pages from actual request and CPU owner row')
  need(len(obj.kv_cache)==2 and
       tensor_id(binding['key'])==s['key']==tensor_id(obj.kv_cache[0])==tensor_id(obj.impl.key_cache)and
       tensor_id(binding['value'])==s['value']==tensor_id(obj.kv_cache[1])==tensor_id(obj.impl.value_cache),
       'actual registered FA storage remains live layer and backend cache aliases')
  return row
 def fa_proof(self,binding):
  row=self.check_fa(binding);table=self.fa_registrations[id(binding)]['table']
  return dict(schema='bole.service-live-FA-owner/v1',request=self.initial.request,
   generation=self.initial.generation,request_object_id=id(self.request),logical_owner_slot=0,group=binding['group'],prefix=binding['prefix'],
   table_object_id=id(table),layer_object_id=id(binding['layer'].self_attn.attn),
   blocks_per_phys_block=table.blocks_per_phys_block,kernel_block_size=table.logical_block_size,
   physical_block_size=table.physical_block_size,use_hybrid_blocks=table.use_hybrid_blocks,
   pcp_world_size=table.pcp_world_size,dcp_world_size=table.dcp_world_size,
   request_physical_blocks=tuple(self.request.block_ids[binding['group']]),CPU_table=row,
   cache_identities=(tensor_id(binding['key']),tensor_id(binding['value'])))
 def validate(self,owner):
  need(self.current()==owner,'current exclusive owner at all-layer validation')
  for binding in self.bindings:
   if binding['kind']=='gdn':self.physical(binding,owner)
   else:self.check_fa(binding)
  return True
 def physical(self,binding,owner):
  need(self.current()==owner,'same current service owner')
  # Initial native metadata was validated before the first service step.
  # Its device buffers may be reused by the next native metadata builder;
  # current ownership comes from the live request/group/table/arena objects.
  initial=self.registrations.get(id(binding));r=self.runner
  need(initial is binding['slot_binding']and initial is not None and
       initial.layer is binding['layer'].linear_attn and initial.request is self.request and
       initial.request_epoch==owner.generation==self.initial.generation,
       'same actually registered layer and strong request')
  need(r.kv_cache_config.kv_cache_groups[initial.group]is initial.group_object and
       initial.prefix in initial.group_object.layer_names and
       r.input_batch.block_table[initial.group]is initial.table,
       'same live native Mamba group and CPU block table')
  n=int(initial.table.num_blocks_per_row[0]);cpu=initial.table.get_cpu_tensor()
  row=tuple(int(x)for x in cpu[0,:n].tolist())
  need(cpu.device.type=='cpu'and row==initial.CPU_row and
       tuple(self.request.block_ids[initial.group])==row,
       'same actual allocated Mamba physical ownership')
  slot=initial.physical_slot
  need(slot==binding['physical_slot']and slot in row and
       tensor_id(initial.layer.kv_cache[0])==initial.conv_identity and
       tensor_id(initial.layer.kv_cache[1])==initial.state_identity,
       'same source-registered actual slot and arena storage')
  return slot
 def publication(self,value):
  need(self.frame is not None and not self.frame.closed and self.pending is None and
       value['owner']==self.frame.owner and value['cache_published']is True and
       value['scheduler_ack_pending']is True,'one complete actual cache publication')
  self.pending=value
 def close_frame(self,actual_req_ids,actual_emitted):
  rid=self.check_request();f=self.frame
  need(f is not None and self.pending is not None and actual_req_ids==[rid]and
       tuple(actual_emitted)==tuple(self.pending['emitted_tokens']),
       'actual native ModelRunnerOutput hands precisely the selected output to engine')
  f.closed=True;self.frame=None
 def retire(self,finished_req_ids):
  rid=self.initial.request;r=self.runner
  need(self.output_budget//2<=self.steps<=self.max_steps and len(self.request.output_token_ids)==self.output_budget,'G2 real multi-step exact output retirement')
  need(not self.retired and rid in finished_req_ids and rid not in r.requests and
       rid not in r.input_batch.req_ids and self.frame is None,
       'actual native finished request removed from request and batch owners')
  self.retired=True
  # Final acknowledgement needs the independent HTTP/worker-journal join.
  # A removed request has no next native computed-counter observation.
  return dict(schema='bole.service-owner-native-retirement/v1',request=rid,
   generation=self.initial.generation,steps=self.steps,
   next_counter_acknowledgements=list(self.acknowledgements),
   final_ack_by_retirement_pending=self.pending is not None,
   last_publication=None if self.pending is None else dict(
    owner=self.pending['owner'],next_length=self.pending['next_length'],
    next_version=self.pending['next_version'],emitted_tokens=self.pending['emitted_tokens']),
   scheduler_committed_independently=False,final_success=False)

