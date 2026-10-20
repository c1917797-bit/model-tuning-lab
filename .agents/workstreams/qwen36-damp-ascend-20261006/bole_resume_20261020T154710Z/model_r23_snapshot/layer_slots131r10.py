"""Frozen first-prefill per-layer native group/physical-slot binding.

Owner.slot is only the C1 logical request row. This object is live-only and
must never enter serialized tensors/evidence; identity() exports primitives.
"""
from dataclasses import dataclass
from model_entry import need,tensor_id

@dataclass(frozen=True,eq=False)
class Binding:
 prefix:str
 group:int
 physical_slot:int
 runner:object
 request_id:str
 request:object
 group_object:object
 table:object
 CPU_row:tuple
 metadata:object
 layer:object
 conv_identity:tuple
 state_identity:tuple
 length:int
 def identity(self):
  return dict(prefix=self.prefix,group=self.group,physical_slot=self.physical_slot,logical_owner_slot=0,
   request_id=self.request_id,request_object_id=id(self.request),group_object_id=id(self.group_object),table_object_id=id(self.table),
   metadata_object_id=id(self.metadata),layer_object_id=id(self.layer),length=self.length)
 def check(self,owner):
  r=self.runner
  need(owner.request==self.request_id and owner.slot==0 and owner.length==self.length,
       'same first-prefill logical request owner; physical slot never taken from Owner.slot')
  need(r.requests.get(self.request_id)is self.request and r.input_batch.req_ids==[self.request_id]and r.input_batch.req_id_to_index=={self.request_id:0},'same live strong C1 request and row')
  need(r.kv_cache_config.kv_cache_groups[self.group]is self.group_object and self.prefix in self.group_object.layer_names and
       r.input_batch.block_table[self.group]is self.table,'same actual layer/native group/table binding')
  n=int(self.table.num_blocks_per_row[0]);cpu=self.table.get_cpu_tensor();need(cpu.device.type=='cpu'and n==len(self.CPU_row)and tuple(int(x)for x in cpu[0,:n].tolist())==self.CPU_row,'same complete committed CPU slot row')
  need(tuple(self.request.block_ids[self.group])==self.CPU_row,'actual unchanged native Mamba physical allocation')
  m=self.metadata;conv=m.non_spec_prefill_metadata.causal_conv1d;ci=conv.cache_indices
  selected=ci if ci.ndim==1 else ci[:,0]
  need(m.prefill_state_indices.cpu().tolist()==[self.physical_slot]and m.non_spec_state_indices_tensor.cpu().tolist()==[self.physical_slot]and selected.cpu().tolist()==[self.physical_slot],
       'actual native SSM/conv metadata selects frozen per-layer physical slot')
  observation=getattr(self.layer,'_bole_pure_prefill_observation',None)
  need(type(observation)is dict and observation['metadata']is m and observation['request']is self.request and observation['slot']==self.physical_slot,
       'same actual completed native prefill observation')
  need(tensor_id(self.layer.kv_cache[0])==self.conv_identity and tensor_id(self.layer.kv_cache[1])==self.state_identity,'same actual layer arenas; no view substitution')
  return self.physical_slot

def physical(binding,owner):
 value=binding.get('slot_binding')
 need(type(value)is Binding and binding['kind']=='gdn'and value.layer is binding['layer'].linear_attn and
      value.group==binding['group']and value.physical_slot==binding['physical_slot'],'exact frozen per-layer slot binding, not an integer permit')
 return value.check(owner)
