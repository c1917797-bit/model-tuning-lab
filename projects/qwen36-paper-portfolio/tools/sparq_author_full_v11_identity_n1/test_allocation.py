"""Stdlib source/allocation/order contracts; not numerical/model acceptance."""
import ast,math,unittest
from pathlib import Path
import allocation_contract as c
class Allocation(unittest.TestCase):
 def test_all_pages_not_numeric18(self):
  for n in (264,320):
   plan=c.shape_plan(n)
   self.assertEqual(len(plan),24) # New independent persistent FP32 long rank_input.
   self.assertEqual(plan["rank_input"],((16,6,n*128),4))
   others=sum((math.prod(s)+128)*size for name,(s,size) in plan.items() if name!="rank_input")
   self.assertEqual(c.guarded_bytes(n)-others,(16*6*n*128+128)*4)
   self.assertIn("rank_input",c.ROW_VIEWS)
   self.assertGreaterEqual(c.transient_upper(n),256*1024**2)
  with self.assertRaises(ValueError):c.shape_plan(18)
 def test_guard_accounting_full_owner_not_sum_batch16(self):
  plan=c.shape_plan(320)
  self.assertEqual(c.guarded_bytes(320),sum((math.prod(s)+128)*v for s,v in plan.values()))
  self.assertEqual(plan["key"],((17,128,1,256),2))
 def test_everyfield_view_or_fixed(self):
  self.assertEqual(set(c.ROW_VIEWS)|set(c.FIXED_VIEWS),set(c.shape_plan(320)))
  self.assertFalse(set(c.ROW_VIEWS)&set(c.FIXED_VIEWS))
 def test_exact_budget_no_memory_saving_claim(self):
  p=c.budget_admission(320,0,1000,1000,1000)
  self.assertFalse(p["fit_measured"]);self.assertFalse(p["model_ready"])
 def test_actual_peak_excess_fails(self):
  with self.assertRaises(ValueError):c.budget_admission(320,0,1000,1000,1000+c.AUX_CEILING+1)
 def test_actual_otherowned_excess_fails(self):
  with self.assertRaises(ValueError):c.budget_admission(320,c.AUX_CEILING,1000,1000,1000)
 def test_phase_copy_before_next_layer(self):
  t=c.Turn();t.begin(1,16,"capture");t.acquire("layers.3",3)
  with self.assertRaises(ValueError):t.acquire("layers.7",7)
  t.output_copied("layers.3",3,True,True);t.acquire("layers.7",7)
 def test_alias_or_wrongprefix_rejected(self):
  for args in (("layers.3",3,False,True),("layers.7",3,True,True),("layers.3",3,True,False)):
   t=c.Turn();t.begin(1,1,"warmup");t.acquire("layers.3",3)
   with self.assertRaises(ValueError):t.output_copied(*args)
 def test_sixteen_fa_realorder_noreplay_PASS(self):
  t=c.Turn();t.begin(1,16,"capture")
  for l in c.FA:t.acquire("layers.%d"%l,l);t.output_copied("layers.%d"%l,l,True,True)
  out=t.end();self.assertFalse(out["graph_replay_observed"]);self.assertFalse(out["model_ready"])
 def test_partial_FA_cannot_finish(self):
  t=c.Turn();t.begin(1,1,"capture");t.acquire("layers.3",3);t.output_copied("layers.3",3,True,True)
  with self.assertRaises(ValueError):t.end()
 def test_algorithm_not_defined_again(self):
  source=(Path(__file__).parent/"long_workspace.py").read_text();tree=ast.parse(source)
  self.assertFalse(any(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=="run" for n in ast.walk(tree)))
  self.assertIn("type(ws).run is numeric.ANNWorkspace.run",source)
 def test_fixed_unused_row16_not_rowbatch(self):
  source=(Path(__file__).parent/"long_workspace.py").read_text()
  self.assertIn("self.key[16:17]",source);self.assertIn("self.value[16:17]",source)
  self.assertNotIn("self.key[batch:batch+1]",source)

class InitializedNativeGeometry(unittest.TestCase):
 """Real geometry observer and allocator contracts; stdlib shape/pointer spies,
 no Torch/native operation or numerical/model success is synthesized."""
 def fixture(self,physical=1536):
  from types import SimpleNamespace as NS
  class Tensor:
   def __init__(self,shape,address=1000,storage=1000,nbytes=20736,dtype="int32"):
    self.shape=tuple(shape);self.address=address;self.storage=storage;self.nbytes=nbytes
    self.dtype=dtype;self.device="npu:0"
   def data_ptr(self):return self.address
  def identity(x):
   stride=[];n=1
   for dim in reversed(x.shape):stride.insert(0,n);n*=dim
   return (x.address,x.storage,0,x.nbytes,x.shape,tuple(stride),x.dtype,x.device)
  prefix="model.layers.3.self_attn";ratio=physical//128;raw=(40960+physical-1)//physical;width=raw*ratio
  owner=Tensor((16,width),nbytes=16*width*4);table=Tensor((2,width),nbytes=16*width*4)
  key=Tensor((5000*ratio,128,1,256),address=9000,storage=9000,nbytes=5000*ratio*128*256*2,dtype="bf16")
  value=Tensor(key.shape,address=900000,storage=900000,nbytes=key.nbytes,dtype="bf16")
  class BlockTable:
   def get_device_tensor(self):return owner
  class MultiGroupBlockTable:
   def __getitem__(self,i):return self.block_tables[i]
  class NPUInputBatch:pass
  BlockTable.__module__=MultiGroupBlockTable.__module__="vllm_ascend.worker.block_table"
  NPUInputBatch.__module__="vllm_ascend.worker.npu_input_batch"
  bt=BlockTable();bt.is_mamba_group=False;bt.pcp_world_size=bt.dcp_world_size=1;bt.max_num_reqs=16
  bt.physical_block_size=physical;bt.logical_block_size=bt.block_size=128;bt.blocks_per_phys_block=ratio
  bt.use_hybrid_blocks=ratio>1;bt.max_num_blocks_per_req=raw;bt.kernel_sizes=[128]
  multi=MultiGroupBlockTable();multi.block_tables=[bt]
  ib=NPUInputBatch();ib.block_table=multi;ib.max_num_reqs=16;ib.max_model_len=40960
  runner=NS(input_batch=ib,use_cp=False,max_model_len=40960,kernel_block_sizes=[[128]],
   kv_cache_config=NS(kv_cache_groups=[NS(layer_names=[prefix],kv_cache_spec=NS(block_size=physical))],num_blocks=5000))
  metadata=NS(block_tables=table)
  return runner,prefix,key,value,metadata,2,NS(int32="int32"),identity
 def test_actual_observer_derives324_and_keeps_legacy_unproven_bound(self):
  args=self.fixture();proof=c.observe_native_geometry(*args)
  self.assertEqual((proof["physical_pages_per_request"],proof["blocks_per_physical"],proof["logical_pages_per_request"]),(27,12,324))
  self.assertEqual(c.shape_plan(324,proof)["rows"],((16,324),8))
  self.assertFalse(c.budget_admission(324,0,100,100,100,proof)["model_ready"])
  with self.assertRaises(ValueError):c.shape_plan(324)
  with self.assertRaises(ValueError):c.shape_plan(320,proof)
 def test_real_metadata_same_shape_foreign_pointer_storage_or_stride_rejected(self):
  for field in ("address","storage"):
   args=self.fixture();setattr(args[4].block_tables,field,999999)
   with self.subTest(field=field),self.assertRaisesRegex(ValueError,"stock table view"):
    c.observe_native_geometry(*args)
  args=self.fixture();args[4].block_tables.shape=(2,320)
  with self.assertRaisesRegex(ValueError,"table shape"):c.observe_native_geometry(*args)
 def test_actual_nested_receiver_not_GPU_or_flat_kernel_sizes(self):
  args=self.fixture();args[0].kernel_block_sizes=[128]
  with self.assertRaisesRegex(ValueError,"nested kernel_sizes"):c.observe_native_geometry(*args)
  args=self.fixture();args[0].input_batch=type("InputBatch",(),dict(__module__="vllm.v1.worker.gpu_input_batch"))()
  with self.assertRaises(ValueError):c.observe_native_geometry(*args)
 def test_source_ratio_width_and_actual_native_key_backing_failclosed(self):
  for fault in ("ratio","physical_spec","native_backing"):
   args=self.fixture();runner=args[0];bt=runner.input_batch.block_table[0]
   if fault=="ratio":bt.blocks_per_phys_block=1
   elif fault=="physical_spec":runner.kv_cache_config.kv_cache_groups[0].kv_cache_spec.block_size=128
   else:args[2].shape=args[3].shape=(100,128,1,256)
   with self.subTest(fault=fault),self.assertRaises(ValueError):c.observe_native_geometry(*args)
 def test_non_CP1_Mamba_bool_dimensions_and_altered_maxlen_rejected(self):
  for fault in ("CP","Mamba","maxlen"):
   args=self.fixture();runner=args[0];bt=runner.input_batch.block_table[0]
   if fault=="CP":bt.dcp_world_size=2
   elif fault=="Mamba":bt.is_mamba_group=True
   else:runner.max_model_len=32768
   with self.subTest(fault=fault),self.assertRaises(ValueError):c.observe_native_geometry(*args)
  with self.assertRaises(ValueError):c.logical_pages(True,128,40960,27)
  with self.assertRaises(ValueError):c.logical_pages(1500,128,40960,28)
 def test_literal_stock_receiver_split_formula_and_no_candidate_converter(self):
  import source_contract as sc
  npu="/cache/cch/qwen36-paper-preparation-20261007/MAIN-native-input-config-source-660-20261009-001/npu_input_batch.py"
  table="/cache/cch/qwen36-paper-preparation-20261007/recurrent/h8-model-tp4-v2-cpu-ledger/source_blobs/ascend_block_table.py"
  sc.bound(npu,sc.PINS[npu]);sc.bound(table,sc.PINS[table])
  n=Path(npu).read_text();b=Path(table).read_text()
  self.assertIn("kernel_sizes=kernel_block_sizes",n);self.assertIn("kernel_block_sizes: list[list[int]]",n)
  self.assertIn("max_num_blocks_per_req * self.blocks_per_phys_block",b)
  self.assertIn("base_logical = phys_block * self.blocks_per_phys_block",b)
  s=(Path(__file__).parent/"allocation_contract.py").read_text();tree=ast.parse(s)
  node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=="observe_native_geometry")
  calls=[x.func.attr for x in ast.walk(node) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute)]
  self.assertFalse(set(calls)&{"cpu","item","copy_","numpy","_convert_physical_to_logical_blocks"})

if __name__=="__main__":unittest.main()
