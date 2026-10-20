"""Independent reader metadata controls for the actual observed12x hybrid geometry."""
import copy,unittest,importlib.util
from pathlib import Path
import consume_service as reader
_here=Path(__file__).resolve().parent
_source=(_here/'sourceio.py')if(_here/'sourceio.py').is_file()else(_here.parent/'sourceio.py')
_spec=importlib.util.spec_from_file_location('service_fa_owner_test_sourceio',_source)
sourceio=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(sourceio)
reader.C=sourceio
from consume_service import fa_owner

class Tests(unittest.TestCase):
 def fixture(self):
  owner=dict(request='software-fixture',generation=1,slot=0,length=131)
  identities=[['key-storage'],['value-storage']]
  proof=dict(schema='bole.service-live-FA-owner/v1',request=owner['request'],generation=1,logical_owner_slot=0,
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

 def test_wrong_generation_and_replayed_prior_epoch_fail_closed(self):
  for current,captured in ((1,2),(2,1),(1,True),(True,1)):
   before,after,row,owner=self.fixture()
   owner['generation']=current
   before['ownership']['generation']=captured
   after['ownership']['generation']=captured
   with self.assertRaises(ValueError):fa_owner(before,after,row,owner)
 def test_same_physical_pages_with_fresh_second_generation_are_valid(self):
  before,after,row,owner=self.fixture()
  owner['generation']=2
  before['ownership']['generation']=after['ownership']['generation']=2
  self.assertTrue(fa_owner(before,after,row,owner))
 def test_after_owner_epoch_cannot_change(self):
  before,after,row,owner=self.fixture()
  after['ownership']['generation']=2
  with self.assertRaises(ValueError):fa_owner(before,after,row,owner)

if __name__=='__main__':unittest.main()
