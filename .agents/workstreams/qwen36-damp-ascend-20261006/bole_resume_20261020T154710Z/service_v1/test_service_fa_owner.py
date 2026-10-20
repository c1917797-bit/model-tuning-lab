"""Independent reader metadata controls for the actual observed12x hybrid geometry."""
import copy,unittest
from consume_service import fa_owner

class Tests(unittest.TestCase):
 def fixture(self):
  owner=dict(request='software-fixture',slot=0,length=131)
  identities=[['key-storage'],['value-storage']]
  proof=dict(schema='bole.service-live-FA-owner/v1',request=owner['request'],logical_owner_slot=0,
   blocks_per_phys_block=12,kernel_block_size=128,physical_block_size=1536,
   use_hybrid_blocks=True,pcp_world_size=1,dcp_world_size=1,
   request_physical_blocks=[1],CPU_table=list(range(12,24)),cache_identities=identities)
  before=dict(ownership=proof,physical_pages=[12,13]);after=copy.deepcopy(before)
  row=dict(actual_cache_identities=copy.deepcopy(identities))
  return before,after,row,owner
 def test_independent_reader_joins_observed12x_physical_to_kernel_expansion(self):
  self.assertTrue(fa_owner(*self.fixture()))
 def test_wrong_request_geometry_page_row_and_cache_alias_fail_closed(self):
  for key,value in(('request','foreign'),('blocks_per_phys_block',1),
    ('request_physical_blocks',list(range(12,24))),('CPU_table',[1]),
    ('cache_identities',[['detached'],['value-storage']])):
   before,after,row,owner=self.fixture()
   before['ownership'][key]=value;after['ownership'][key]=copy.deepcopy(value)
   with self.assertRaises(ValueError):fa_owner(before,after,row,owner)
  before,after,row,owner=self.fixture();after['physical_pages']=[12,14]
  with self.assertRaises(ValueError):fa_owner(before,after,row,owner)

if __name__=='__main__':unittest.main()
