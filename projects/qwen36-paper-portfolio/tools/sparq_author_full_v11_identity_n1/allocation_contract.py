"""Actual ANN long-domain allocator contracts. Stdlib/no device initialization.
Projected bounds are admission constraints, never measured memory saving/PASS.
"""
import math
BATCHES=tuple(range(1,17));FA=tuple(range(3,64,4))
BLOCK,DIM,HEADS,BUDGET,RANK=128,256,6,128,32
MIN_PAGES=(32768+1024+127)//128
MAX_PAGES=40960//128
AUX_CEILING=2*1024**3
def require(ok,msg):
 if not ok:raise ValueError(msg)
def shape_plan(pages,geometry=None):
 geometry_pages(pages,geometry)
 b=16;n=pages*BLOCK
 return {"rows":((b,pages),8),"lengths":((b,),4),"logical":((n,),8),"logical_page":((b,n),8),
  "offset":((n,),8),"batch_index":((b,),8),"pa_table":((b,1),4),"budget_tensor":((b,),4),
  "key":((b+1,128,1,256),2),"value":((b+1,128,1,256),2),
  "output":((b,6,256),4),"corrected":((b,6,256),2),"importance":((b,256),2),
  "channels":((b,32),8),"scale":((b,6),2),"score":((b,6,n),4),
  "ranking":((b,n),4),"rank_input":((b,6,n),4),"selected":((b,128),8),"valid":((b,n),1),
  "selected_valid":((b,128),1),"alpha":((b,6),4),"weights":((b,6,128),4),"mean_off":((b,256),4)}
ROW_VIEWS=("rows","lengths","logical_page","batch_index","pa_table","budget_tensor","output","corrected",
 "importance","channels","scale","score","ranking","rank_input","selected","valid","selected_valid","alpha","weights","mean_off")
FIXED_VIEWS=("logical","offset","key","value")
def guarded_bytes(pages,geometry=None):return sum((math.prod(s)+128)*size for s,size in shape_plan(pages,geometry).values())
def transient_upper(pages):
 # Conservative simultaneous BF16 channel gather, physical int64 maps, raw
 # scores/masks, FP32 scores/softmax/topk and vendor temporary upper allowance.
 # FP32 selected V, FP32 residual result and FP32 meanOFF are additionally
 # counted; no BF16 selector widening or candidate-only native reduction.
 # Real FULL pool peak remains mandatory; this estimate does not prove a fit.
 n=pages*128
 return 16*n*(32*2+8*4+6*(2*3+4*4)+4*3)+256*1024**2+16*128*256*4+16*6*256*4+16*256*4
def budget_admission(pages,other_owned,current,baseline,peak,geometry=None):
 require(all(type(v) is int and v>=0 for v in (other_owned,current,baseline,peak)) and peak>=current>=baseline,
  "actual same-process native KV+48GDN backed baseline/current/peak, not os.cpu_count or projected HBM")
 owned=guarded_bytes(pages,geometry)+other_owned
 require(owned+transient_upper(pages)<=AUX_CEILING and current-baseline<=AUX_CEILING and peak-baseline<=AUX_CEILING,
  "all16FA/all16batch pool+guarded+transient within common actual aux2GiB, never memory saving claim")
 return {"guarded_ANN_owner_bytes":guarded_bytes(pages,geometry),"other_owned_bytes":other_owned,"transient_upper_bytes":transient_upper(pages),
  "actual_current_delta":current-baseline,"actual_peak_delta":peak-baseline,"aux_ceiling":AUX_CEILING,"fit_measured":False,"model_ready":False}

def logical_pages(physical_block_size,logical_block_size,max_model_len,physical_pages):
 """Source-derived CP1 upper bound; no page-ID remapping or Tensor operation."""
 require(all(type(v) is int and v>0 for v in
  (physical_block_size,logical_block_size,max_model_len,physical_pages)),
  "actual positive native block dimensions, not bool")
 require(logical_block_size==BLOCK and physical_block_size%logical_block_size==0 and
  max_model_len==40960 and physical_pages==(max_model_len+physical_block_size-1)//physical_block_size,
  "registered40960 original CP1 physical allocator bound/kernel128")
 return physical_pages*(physical_block_size//logical_block_size)
def geometry_pages(pages,geometry=None):
 if geometry is None:
  require(type(pages) is int and MIN_PAGES<=pages<=MAX_PAGES,
   "legacy unproven metadata domain264..320; expanded native pages need initialized geometry")
  return pages
 require(type(geometry) is dict and geometry.get("schema")=="sparq.initialized-native-FA-geometry/v1" and
  geometry.get("stock_physical_to_logical") is True and type(geometry.get("context_parallel_size")) is int and geometry.get("context_parallel_size")==1 and
  geometry.get("logical_block_size")==BLOCK,"source-bound initialized stock FA geometry required")
 upper=logical_pages(geometry["physical_block_size"],geometry["logical_block_size"],
  geometry["max_model_len"],geometry["physical_pages_per_request"])
 require(type(pages) is int and MIN_PAGES<=pages==upper==geometry["logical_pages_per_request"],
  "exact actual stock expanded metadata width, not hand-set324")
 return pages
def observe_native_geometry(runner,prefix,key,value,metadata,batch,torch,identity):
 """Read host attrs/pointers only. Called at true native warmup/capture; no
 cpu/item/NumPy readback, no native writer, no conversion of IDs or mutation.
 Runtime source SHA verification precedes this function in the worker bridge.
 """
 ib=runner.input_batch
 require(type(ib).__module__=="vllm_ascend.worker.npu_input_batch" and type(ib).__name__=="NPUInputBatch",
  "actual deployed Ascend NPUInputBatch/MultiGroupBlockTable, not GPU substitute")
 multi=ib.block_table
 require(type(multi).__module__=="vllm_ascend.worker.block_table" and type(multi).__name__=="MultiGroupBlockTable",
  "actual deployed Ascend NPUInputBatch/MultiGroupBlockTable, not GPU substitute")
 groups=runner.kv_cache_config.kv_cache_groups
 matches=[i for i,g in enumerate(groups) if prefix in g.layer_names]
 require(len(matches)==1,"one actual native FA cache group owns layer prefix")
 gid=matches[0];group=groups[gid];bt=multi[gid]
 require(type(bt).__module__=="vllm_ascend.worker.block_table" and type(bt).__name__=="BlockTable" and
  bt.is_mamba_group is False and type(bt.pcp_world_size) is type(bt.dcp_world_size) is int and
  bt.pcp_world_size==bt.dcp_world_size==1 and runner.use_cp is False,
  "actual ordinary FA BlockTable CP1, no Mamba/CP mapping adaptation")
 require(type(batch) is int and batch in BATCHES and ib.max_num_reqs==16 and
  ib.max_model_len==runner.max_model_len==40960 and bt.max_num_reqs==16,
  "same registered all16 truebatch and actual max model length")
 kernel_sizes=runner.kernel_block_sizes
 require(type(kernel_sizes) is list and len(kernel_sizes)==len(groups) and
  type(kernel_sizes[gid]) is list and kernel_sizes[gid]==bt.kernel_sizes==[BLOCK],
  "actual receiver nested kernel_sizes per group/selected kernel128")
 physical=bt.physical_block_size;logical=bt.logical_block_size
 require(physical==group.kv_cache_spec.block_size and logical==bt.block_size==BLOCK and
  type(physical) is int and physical>0 and physical%BLOCK==0 and
  bt.blocks_per_phys_block==physical//BLOCK and type(bt.use_hybrid_blocks) is bool and
  bt.use_hybrid_blocks==(physical//BLOCK>1),"initialized selected physical/kernel/split ratio ABI")
 upper=logical_pages(physical,logical,ib.max_model_len,bt.max_num_blocks_per_req)
 owner=bt.get_device_tensor();table=metadata.block_tables
 require(tuple(owner.shape)==(16,upper) and tuple(table.shape)==(batch,upper) and
  owner.dtype==table.dtype==torch.int32 and owner.device==table.device==key.device==value.device,
  "actual stock full device table shape/dtype/device, no fake320 truncation")
 owner_id=identity(owner);table_id=identity(table)
 require(owner_id[:4]==table_id[:4] and owner_id[5:]==table_id[5:],
  "current metadata table is original first-B stock table view, not same-shape foreign pointer")
 require(tuple(key.shape)==tuple(value.shape) and tuple(key.shape[1:])==(BLOCK,1,DIM) and
  type(key.shape[0]) is int and key.shape[0]%bt.blocks_per_phys_block==0 and
  key.shape[0]>=runner.kv_cache_config.num_blocks*bt.blocks_per_phys_block,
  "native KV allocator reshape has original logical kernel-block backing")
 proof=dict(schema="sparq.initialized-native-FA-geometry/v1",stock_physical_to_logical=True,
  group_id=gid,physical_block_size=physical,logical_block_size=logical,context_parallel_size=1,
  max_model_len=ib.max_model_len,physical_pages_per_request=bt.max_num_blocks_per_req,
  logical_pages_per_request=upper,blocks_per_physical=bt.blocks_per_phys_block,
  table_owner_identity=list(owner_id),current_table_identity=list(table_id),
  actual_native_key_identity=list(identity(key)),actual_native_value_identity=list(identity(value)),
  model_ready=False)
 geometry_pages(upper,proof)
 return proof

class Turn:
 """Python capture/warmup output-copy ordering only, NOT replay evidence.
 Actual FULL replay must independently observe all16 per-layer device counters.
 """
 def __init__(self):self.active=None;self.order=[];self.pending=None
 def begin(self,epoch,batch,kind):
  require(self.active is None and type(epoch) is int and epoch>0 and type(batch) is int and batch in BATCHES and
   kind in ("warmup","capture"),"one original synchronous common stream turn; not virtual runtime authority")
  self.active=(epoch,batch,kind);self.order=[];self.pending=None
 def acquire(self,prefix,layer):
  require(self.active is not None and self.pending is None and layer in FA and layer not in self.order and
   type(prefix) is str and prefix,"shared arena cannot overwrite live prior-layer corrected/output scratch")
  self.pending=(prefix,layer);return self.active[1]
 def output_copied(self,prefix,layer,original_output_distinct,graph_nodes_enqueued_in_order):
  require(self.pending==(prefix,layer) and original_output_distinct is True and graph_nodes_enqueued_in_order is True,
   "original model output copy after ANN dot/residual before next layer; no workspace alias or stream reorder")
  self.order.append(layer);self.pending=None
 def end(self):
  require(self.active is not None and self.pending is None and tuple(self.order)==FA,
   "complete source-supported sixteen real FA original forward/copy order, no subset")
  result={"epoch":self.active[0],"batch":self.active[1],"kind":self.active[2],"FA_order":list(self.order),
   "graph_replay_observed":False,"model_ready":False};self.active=None;return result
