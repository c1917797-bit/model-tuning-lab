"""Stdlib complete aggregate seams; no simulated native/model PASS."""
import ast,copy,os,sys,unittest
import math,allocation_contract,component_handoff as h
from pathlib import Path
from unittest.mock import patch
import source_contract as c,common,bridge,ann_fa_consumer as fa
ROOT=Path(__file__).resolve().parent
def text(name):return (ROOT/name).read_text()
class Aggregate(unittest.TestCase):
 def test_default_OFF_no_runtime(self):
  with patch.dict(os.environ,{"QWEN36_SPARQ_STOCK_FULL_ENABLED":"0"}):
   self.assertFalse(bridge.install_from_env()["model_ready"])
  self.assertNotIn("torch",sys.modules);self.assertNotIn("torch_npu",sys.modules)
 def test_current_four_shard50_and_original_native42_not_old_single_grant(self):
  s=text("source_contract.py")
  self.assertIn("sparq.author-ann-disjoint4-numeric/v1",s)
  self.assertNotIn("sparq.complete-token-component/v9-author-ann-FP32-compensation",s)
  self.assertEqual(h.source_interfaces()["source_count"],42)
  self.assertEqual(h.shard_source_interfaces()["source_count"],50)
  self.assertEqual(h.proposed_source_interfaces()["precision_contract"],c.AUTHOR_PROTOCOL)
  for predicate in ('x.get("cases")==128','x.get("changing_feedback_steps")==20480','x.get("partial_cases_used")==0'):
   self.assertIn(predicate,s)
  self.assertNotIn("sparq.complete-token-component/v7-fp32-support",s)
 def test_exact_author_source_pins(self):
  source_path="/cache/cch/qwen36-paper-preparation-20261007/sparse/MAIN-sparq-official-ann-source-20261008-1040-001/ann_attention.py"
  result_path=str(Path(source_path).parent/"SOURCE_RESULT.json")
  self.assertEqual(c.PINS[source_path],"2b07afe06ff1dd6627f1a255be585c82a632f7bbdb7bf606f4ff2f8b260b6b74")
  actual=c.obj(dict(path=result_path,sha256=c.PINS[result_path]))
  self.assertEqual(actual["commit"],"554ea6db219405becbdc0a126984a19f181bdc69")
  self.assertEqual(actual["source"],dict(path=source_path,sha256=c.PINS[source_path],bytes=14750))
  self.assertFalse(actual["algorithm_pass"]);self.assertFalse(actual["npu_executed"])
 def test_worker_bootstrap_and_original_writer_before_forward(self):
  s=text("bridge.py")
  self.assertLess(s.index("import vllm_ascend.ops"),s.index("import vllm_ascend.attention.attention_v1"))
  self.assertIn('from ann_model_state import ANNState',s)
  self.assertIn('return original_outer(impl,layer,*args,**kwargs)',s)
  self.assertNotIn("ReshapeCacheOperation(",s)
 def test_all16_original_outputs_copied_before_shared_reuse(self):
  s=text("ann_model_state.py")
  self.assertIn("tuple(self.forward_order)==common.FA",s)
  self.assertIn('original distinct-output copy before next shared arena FA',s)
  p=text("no_pa_full.py");self.assertLess(p.index(".copy_(got)"),p.index("copy_order()"))
 def test_meanOFF_only_not_false_meanON(self):
  s=text("ann_model_state.py");self.assertIn("author meanOFF",s)
  p=text("no_pa_full.py");self.assertIn("reallocation=False",p)
  self.assertIn("meanON_coverage_claimed=False",text("ann_model_oracle.py"))
 def test_native_long_full_domain_not_scratch_clamp(self):
  s=text("no_pa_full.py")
  node=next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name=="selector_topology")
  names=[n.func.attr for n in ast.walk(node) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
  self.assertNotIn("cpu",names);self.assertNotIn("item",names)
  self.assertIn("workspace.lengths.copy_(device_lengths)",ast.unparse(node))
 def test_literal_full_queryKV_not_candidate_support_reference(self):
  s=text("ann_model_oracle.py")
  self.assertIn("query[None],key[None],value[None],False,outside_capture=True",s)
  self.assertIn('reference["channels"][0]',s);self.assertIn('reference["indices"][0]',s)
  self.assertIn("conditional(t,query,key,value,dims,chosen,False)",s)
  self.assertNotIn("conditional(t,query,key,value,sample",s)
 def test_first_fault_primary_not_hidden_by_secondary_dump(self):
  self.assertIn('except BaseException as secondary:',text("ann_model_oracle.py"))
  self.assertIn('raw retention secondary=',text("ann_model_oracle.py"))
  self.assertIn("total<=256*1024**2",text("ann_model_oracle.py"))
 def test_full_vector_no_average_or_sample_acceptance(self):
  self.assertEqual((fa.RMS,fa.COS),(.005,.99998))
  with self.assertRaises(ValueError):fa.reductions([],{"passed":True,"finite":True})
  self.assertIn("full_dimensions=256",text("ann_model_oracle.py"))
  self.assertIn("for ah,eh in zip(av,ev)",text("ann_model_oracle.py"))
 def test_complete_model_FA_GDN_and_true_allocator_coverage(self):
  s=text("consume_model.py")
  self.assertIn('set(b["gdn"])=={str(i) for i in gdn_state.GDN}',s)
  self.assertIn('set(b["fa"])=={str(i) for i in range(3,64,4)}',s)
  self.assertIn('"actual-full-ann-oracle"',s)
  self.assertIn("coverage.consume_turn(rank,b,states)",s)
  self.assertIn("postmortem_full_qKV_replay=False",s)
 def test_formal_no_observer_or_literal_capture(self):
  self.assertIn('sample=self.snapshot(prefix,b,query.device) if self.diagnostic else None',text("ann_model_state.py"))
  self.assertIn("from ann_model_oracle import check_layer",text("ann_model_state.py"))
  self.assertIn('if self.diagnostic:',text("ann_model_state.py"))
  self.assertIn('mode=="diagnostic"',text("bridge.py"))
  self.assertIn('w["timing_debug_off"] is True',text("consume_service.py"))
 def test_common_exact_dense_FULL_not_candidate_eager(self):
  for arm in ("dense","candidate"):common.validate(copy.deepcopy(common.COMMON),arm)
  bad=copy.deepcopy(common.COMMON);bad["enforce_eager"]=True
  with self.assertRaises(ValueError):common.validate(bad,"candidate")
 def test_original_whole_receipt_no_fake_flattened_operation(self):
  self.assertIn("original_terminal(c.obj(terminal_ref),PEER)",text("consume_model.py"))
  self.assertIn('record["command"]',text("consume_model.py"))
  self.assertIn('actual_numerical_steps',text("source_contract.py"))
 def test_true_echos_keep_only_generated_tokenIDs(self):
  self.assertIn("return_token_ids=True,echo=True",text("bench.py"))
  p=Path("/cache/cch/qwen36-paper-preparation-20261007/sparse/source-openai-completion-660-20261008-0949-001/serving.py")
  c.bound(p,c.PINS[str(p)])
  s=p.read_text()
  self.assertIn("if request.echo and not has_echoed[i]",s)
  self.assertIn("as_list(output.token_ids)",s)
  self.assertIn("prompt_token_ids=prompt_token_ids_to_return",s)
 def test_final_missing_data_not_synthetic(self):
  import json
  x=json.loads(text("TASK_EVIDENCE.json"));self.assertFalse(x["ready"])
  self.assertFalse(x["synthetic_substitution_allowed"])
  self.assertIn('"LongBench-v2","GSM8K"',text("service_contract.py"))
class ModuleNamespace(unittest.TestCase):
 def test_actual_dataclass_dynamic_module_registered(self):
  import tempfile,dataclasses
  parent=Path("/cache/cch/qwen36-paper-preparation-20261007/sparse")
  with tempfile.TemporaryDirectory(dir=parent,prefix="ann-full-namespace-") as d:
   p=Path(d)/"d.py";p.write_text("from __future__ import annotations\nfrom dataclasses import dataclass\n@dataclass\nclass D:\n x: int=1\n")
   m=c.module(p,c.sha(p),"_ann_full_stdlib_dataclass")
   self.assertIs(sys.modules[m.D.__module__],m)
 def test_first_module_exception_preserved_and_registry_restored(self):
  import tempfile
  parent=Path("/cache/cch/qwen36-paper-preparation-20261007/sparse")
  with tempfile.TemporaryDirectory(dir=parent,prefix="ann-full-namespace-") as d:
   p=Path(d)/"bad.py";p.write_text("raise ValueError('original module failure')\n")
   name="_ann_full_stdlib_failed";old=object();sys.modules[name]=old
   try:
    with self.assertRaisesRegex(ValueError,"original module failure"):c.module(p,c.sha(p),name)
    self.assertIs(sys.modules[name],old)
   finally:sys.modules.pop(name,None)
class ActualANNEndBatchBinding(unittest.TestCase):
 """Real ANNState.end + real Registry; spies isolate only oracle/sync/output IO."""
 class Tensor:
  def __init__(self,shape,address):
   self.shape=tuple(shape);self.address=address;self.dtype="torch.int32";self.device="npu:0"
  def data_ptr(self):return self.address
  def untyped_storage(self):return self
  def storage_offset(self):return 0
  def nbytes(self):
   import math
   return math.prod(self.shape)*4
  def stride(self):
   import math
   return tuple(math.prod(self.shape[i+1:]) for i in range(len(self.shape)))
 class Lens:
  def __init__(self,test):self.test=test
  def __getitem__(self,key):return self.test.lengths[key.stop]
 def fixture(self):
  from types import SimpleNamespace as NS
  from ann_model_state import ANNState
  import no_pa_full as post
  self.lengths={b:self.Tensor((b,),20000+b*256) for b in (16,1,2)}
  names=["model.layers.%d.self_attn"%n for n in common.FA]
  bindings={p:dict(layer=n,impl_id=100+n) for p,n in zip(names,common.FA)}
  registry=post.Registry(bindings)
  params=NS(attn_params={b:[] for b in (16,1,2)},handles={b:[] for b in (16,1,2)},events={b:[] for b in (16,1,2)})
  state=ANNState.__new__(ANNState);state.diagnostic=True;state.Mode=NS(FULL="FULL",NONE="NONE")
  state.current=dict(dummy=False,batch=2,updated=True,actual_epoch=73,
   frame=[dict(rid="r0"),dict(rid="r1")],full_topology={p:[32768,32767] for p in names},request_ids=["r0","r1"])
  state.t=NS(npu=NS(current_stream=lambda:NS(synchronize=lambda:None)))
  state.registry=registry;state.bindings=bindings;state.acl=NS(get_graph_params=lambda:params)
  state.runner=NS(seq_lens=self.Lens(self),input_batch=NS(num_reqs=2))
  state.native_caches={};state.native_geometries={};state.capture_inputs={};state.snapshots={};state.tables={}
  key=self.Tensor((8192,128,1,256),700000);value=self.Tensor((8192,128,1,256),800000)
  for b in (16,1,2):
   for j,p in enumerate(names):
    table=self.Tensor((b,264),100000+b*10000+j*1024);state.tables[(p,b)]=table
    registry.capture(b,p,bindings[p]["impl_id"],self.Tensor((b,6,256),900000+j*8192),
     self.Tensor((b,6,256),1200000+j*8192),table,self.lengths[b],params)
    state.native_caches[(p,b)]=(key,value,table)
    state.native_geometries[(p,b)]=dict(current_table_identity=list(bridge.tensor_identity(table)),
     actual_native_key_identity=list(bridge.tensor_identity(key)),actual_native_value_identity=list(bridge.tensor_identity(value)),
     logical_pages_per_request=table.shape[1])
    state.capture_inputs[(p,b)]=(bridge.tensor_identity(table),bridge.tensor_identity(self.lengths[b]))
    state.snapshots[(p,b)]=NS(device_observation=lambda epoch:dict(epoch=epoch,counter_increment=1,guards=True))
  # Actual capture can leave the prefix-only dictionary on B1. Proposed end must
  # still read B2. The decoy preserves a deterministic failure in old end.
  for p in names:state.native_caches[p]=state.native_caches[(p,1)]
  registry.active=dict(batch=2,epoch=73,frame=state.current["frame"],POST_original_returned=True)
  state.replay_calls=[dict(original_call_returned=True)];state.arm="candidate";state.core=object()
  state.gdn_observer=NS(end=lambda ctx:[]);state.pending_scheduler={};state.model_entries=0
  state.mixed_fa={} # begin() owns this field in production; fixture bypasses begin.
  state.budget=lambda:{};state.emitted=[];state.emit=lambda kind,v:state.emitted.append((kind,v)) or {"kind":kind}
  ctx=NS(cudagraph_runtime_mode="FULL",attn_metadata={p:NS(block_tables=state.tables[(p,2)]) for p in names})
  return state,ctx,names
 def run_end(self,state,ctx):
  import ann_model_oracle as oracle
  observed=[]
  def spy(torch,sample,native,frame,lengths,prefix,epoch,root,core,geometry_proof):
   self.assertIs(geometry_proof,state.native_geometries[(prefix,2)])
   observed.append((prefix,native,len(frame),list(lengths)));return {}
  with patch.dict(os.environ,{"QWEN36_SPARQ_MODEL_TRACE_ROOT":"/cache/cch/unrun-end-spy","QWEN36_SPARQ_ACTUAL_RANK":"0"}):
   with patch.object(oracle,"check_layer",side_effect=spy):
    state.end(ctx)
  return observed
 def test_real_end_B16_then_B1_then_true_B2_uses_current_all16_tables(self):
  state,ctx,names=self.fixture();got=self.run_end(state,ctx)
  self.assertEqual([r[0] for r in got],names);self.assertEqual(len(got),16)
  for p,native,b,lengths in got:
   self.assertIs(native[2],state.tables[(p,2)]);self.assertEqual(native[2].shape,(2,264))
   self.assertEqual(b,2);self.assertEqual(lengths,[32768,32767])
  self.assertIsNone(state.current);self.assertIsNone(state.registry.active);self.assertEqual(state.model_entries,1)
 def test_same_shape_current_metadata_foreign_pointer_rejected_before_any_oracle(self):
  state,ctx,names=self.fixture();p=names[-1]
  ctx.attn_metadata[p].block_tables=self.Tensor((2,264),5550000)
  import ann_model_oracle as oracle
  with patch.object(oracle,"check_layer") as fn:
   with self.assertRaisesRegex(ValueError,"current-batch native table/current metadata/capture pointer"):state.end(ctx)
   self.assertEqual(fn.call_count,0)
 def test_same_shape_cached_table_foreign_pointer_rejected_before_any_oracle(self):
  state,ctx,names=self.fixture();p=names[-1];key,value,_=state.native_caches[(p,2)]
  state.native_caches[(p,2)]=(key,value,self.Tensor((2,264),6660000))
  import ann_model_oracle as oracle
  with patch.object(oracle,"check_layer") as fn:
   with self.assertRaisesRegex(ValueError,"current-batch native table/current metadata/capture pointer"):state.end(ctx)
   self.assertEqual(fn.call_count,0)

class ActualWrappedDummyProfile(unittest.TestCase):
 """Runs actual installed wrapper + ANNState, not a dict/helper substitute.
 Pinned stock outer AST is literal; memory/math/IO spies are stdlib-only and
 grant no native/algorithm/model PASS. Original NPU dummy source contract is
 independently pinned below; this fixture is not an installed runtime test.
 """
 def harness(self,fault=None):
  import contextlib,types,no_pa_full,ann_model_state,long_workspace,ann_snapshot
  from types import SimpleNamespace as NS
  stack=contextlib.ExitStack();self.addCleanup(stack.close)
  names=("torch","torch_npu","vllm_ascend","vllm_ascend.ops","vllm_ascend.attention",
   "vllm_ascend.attention.attention_v1","vllm_ascend.worker","vllm_ascend.worker.model_runner_v1",
   "vllm_ascend.compilation","vllm_ascend.compilation.acl_graph","vllm_ascend.ascend_config",
   "vllm","vllm.config","vllm.config.compilation","vllm.forward_context","vllm.distributed",
   "sparq_token_v4","sparq_token_v4.core")
  modules={name:types.ModuleType(name) for name in names}
  for name,module in modules.items():
   module.__path__=[]
   if "." in name:
    parent,leaf=name.rsplit(".",1)
    if parent in modules:setattr(modules[parent],leaf,module)
  stack.enter_context(patch.dict(sys.modules,modules))
  t=modules["torch"];a=modules["vllm_ascend.attention.attention_v1"]
  r=modules["vllm_ascend.worker.model_runner_v1"];acl=modules["vllm_ascend.compilation.acl_graph"]
  Mode=NS(FULL="FULL",NONE="NONE");modules["vllm.config.compilation"].CUDAGraphMode=Mode
  modules["vllm_ascend.ascend_config"].get_ascend_config=lambda:NS()
  dist=modules["vllm.distributed"];dist.get_tensor_model_parallel_rank=lambda:0
  dist.get_tensor_model_parallel_world_size=lambda:4
  memory=NS(current=100,peak=100,allocation_calls=0,budget_calls=0)
  def allocate(size):
   memory.current+=size;memory.peak=max(memory.peak,memory.current);memory.allocation_calls+=1
  t.bfloat16="torch.bfloat16";t.float32="torch.float32";t.int32="torch.int32"
  t.npu=NS(current_device=lambda:0,memory_allocated=lambda:memory.current,
   max_memory_allocated=lambda:memory.peak,memory_reserved=lambda:memory.current)
  a._EXTRA_CTX=NS(capturing=False,is_draft_model=False)
  a.AscendAttentionState=NS(DecodeOnly="decode")
  a.record_attention_compute_start=lambda:None
  acl.weak_ref_tensors=lambda x:x
  acl.get_graph_params=lambda:NS(attn_params={1:[]},handles={1:[]},events={1:[]})
  class Tensor:
   next_address=200000
   def __init__(self,shape,dtype):
    self.shape=tuple(shape);self.dtype=dtype;self.device=NS(type="npu")
    self.address=Tensor.next_address;Tensor.next_address+=1024
    self.storage_address=self.address;self.storage_bytes=__import__("math").prod(self.shape)*(4 if dtype==t.int32 else 2)
    self.fill_calls=[];self.copy_calls=0
   def data_ptr(self):return self.address
   def untyped_storage(self):return NS(data_ptr=lambda:self.storage_address,nbytes=lambda:self.storage_bytes)
   def storage_offset(self):return 0
   def stride(self):
    stride=[];n=1
    for dim in reversed(self.shape):stride.insert(0,n);n*=dim
    return tuple(stride)
   def fill_(self,value):self.fill_calls.append(value);return self
   def zero_(self):return self.fill_(0)
   def __getitem__(self,key):return self
   def __setitem__(self,key,value):self.copy_calls+=1
   def view(self,*shape):return self
   def copy_(self,other):self.copy_calls+=1;return self
  class Backend:
   def __init__(self):
    self.enable_hamming_sparse=False;self._use_layer_aware_fia_graph_replay=False
    self.num_heads=6;self.num_kv_heads=1;self.head_size=256
    self.enable_c8_quant=False;self.sinks=None;self.sliding_window=None;self.alibi_slopes=None
    self.is_kv_producer=False;self.kv_sharing_target_layer_name=None
    self.key_cache=Tensor((8192,128,1,256),t.bfloat16)
    self.value_cache=Tensor((8192,128,1,256),t.bfloat16)
  Backend.__module__=a.__name__
  # Exact whole-source SHA checked by real verified_sources(), no rewritten None
  # branch or architecture stub. Future annotations avoid unrelated type imports.
  sources=no_pa_full.verified_sources()
  node=copy.deepcopy(no_pa_full.method(sources["attention_v1.py"],"AscendAttentionBackendImpl","forward"))
  namespace={"__name__":a.__name__}
  tree=ast.Module(body=[ast.ImportFrom(module="__future__",names=[ast.alias(name="annotations")],level=0),node],type_ignores=[])
  exec(compile(ast.fix_missing_locations(tree),"<pinned-stock-outer-AST>","exec"),namespace)
  Backend.forward=namespace["forward"]
  def unused_impl(*args,**kwargs):raise AssertionError("stock impl spy must not run in selected ANN warmup")
  unused_impl.__module__=a.__name__;Backend.forward_impl=unused_impl
  def update_graph(*args,**kwargs):return None
  update_graph.__module__=a.__name__;Backend.update_graph_params=staticmethod(update_graph)
  a.AscendAttentionBackendImpl=Backend
  class Runner:
   def __init__(self):
    self.layers=[(Backend(),NS(layer_name="model.layers.%d.self_attn"%n,_k_scale_float=1.,_v_scale_float=1.)) for n in common.FA]
    self.returned=object();self.original_calls=0;self.state=None;self.ctx=None;self.outputs=[]
   def _update_states(self,*args,**kwargs):return None
   def _prepare_inputs(self,*args,**kwargs):return None
   def _dummy_run(self,num_tokens,**kwargs):
    self.original_calls+=1;self.state=bridge._LOCAL.state;self.profile=kwargs.get("is_profile",False)
    self.ctx=NS(cudagraph_runtime_mode=Mode.NONE,attn_metadata=None)
    self._model_forward(num_tokens)
    if self.profile and fault=="mint-baseline":self.state.baseline_allocated=0
    return self.returned
   def _model_forward(self,num_tokens,*args,**kwargs):
    for impl,layer in self.layers:
     metadata=None
     if not self.profile or fault=="native-profile-metadata":
      table=Tensor((1,320),t.int32);table.address=self.table.address
      table.storage_address=self.table.storage_address;table.storage_bytes=self.table.storage_bytes
      metadata=NS(attn_state="decode",block_tables=table,causal=True,num_actual_tokens=1,num_prefills=0,model_runner_type="generate")
      if fault=="missing-model-runner-type":del metadata.model_runner_type
     out=Tensor((1,6,256),t.bfloat16);self.outputs.append(out)
     impl.forward(layer,Tensor((1,6,256),t.bfloat16),None,None,[impl.key_cache,impl.value_cache],metadata,out)
    return self.returned
  Runner.__module__=r.__name__
  for name in ("_update_states","_prepare_inputs","_dummy_run","_model_forward"):getattr(Runner,name).__module__=r.__name__
  r.NPUModelRunner=Runner;r.SEQ_LEN_WITH_MAX_PA_WORKSPACE=6144
  runner=Runner()
  # Transparent initialized-owner/layout spies; never fake native computation.
  class BlockTable:
   def get_device_tensor(self):return runner.table
  class MultiGroupBlockTable:
   def __getitem__(self,i):return self.block_tables[i]
  class NPUInputBatch:pass
  BlockTable.__module__=MultiGroupBlockTable.__module__="vllm_ascend.worker.block_table"
  NPUInputBatch.__module__="vllm_ascend.worker.npu_input_batch"
  runner.table=Tensor((16,320),t.int32)
  bt=BlockTable();bt.is_mamba_group=False;bt.pcp_world_size=bt.dcp_world_size=1
  bt.max_num_reqs=16;bt.physical_block_size=bt.logical_block_size=bt.block_size=128
  bt.blocks_per_phys_block=1;bt.use_hybrid_blocks=False;bt.max_num_blocks_per_req=320;bt.kernel_sizes=[128]
  multi=MultiGroupBlockTable();multi.block_tables=[bt]
  ib=NPUInputBatch();ib.block_table=multi;ib.max_num_reqs=16;ib.max_model_len=40960
  runner.input_batch=ib;runner.max_model_len=40960;runner.use_cp=False;runner.kernel_block_sizes=[[128]]
  runner.kv_cache_config=NS(kv_cache_groups=[NS(layer_names=[layer.layer_name for _,layer in runner.layers],
   kv_cache_spec=NS(block_size=128))],num_blocks=8192)
  modules["vllm.forward_context"].get_forward_context=lambda:runner.ctx
  class Arena:
   def __init__(self,device,pages,*args,geometry=None):
    self.geometry=geometry;self.pages=pages;self.capacity=pages*128
    self.bytes=common.AUX_CEILING+1 if fault=="over-budget" else 4096
    allocate(self.bytes)
   def view(self,b):
    return NS(mean_off=Tensor((b,256),t.float32))
  class Pool:
   def __init__(self,*args):allocate(512)
   def bytes(self):return 512
   def view(self,b):return NS(before=lambda q:None,after=lambda *args:None)
  def math_spy(torch,arena,b,query,kc,vc,table,lens,out,zero,copied):
   copied();return out,arena.view(b),object(),object(),object()
  runner.seq_lens=Tensor((16,),t.int32) # production selected_forward slices the real host lengths.
  original_budget=ann_model_state.ANNState.budget
  def tracked_budget(state):
   memory.budget_calls+=1;return original_budget(state) # real strong budget
  import identity_bridge
  # Configuration observation spy only in this existing software harness.
  # Never used by N1/frontend/actual TP workers; cannot grant runtime authority.
  for obj,name,value in (
   (identity_bridge,"flag",lambda:dict(disable_request_id_randomization=True,environment_value="1",processor_source_sha256=identity_bridge.ASSIGN_SHA)),
   (c,"source",lambda *args:({},{})),(c,"actual_component",lambda *args:{}),
   (c,"runtime_sources",lambda *args:None),(c,"event",lambda *args:{}),
   (common,"validate_runner",lambda *args:True),
   (bridge.gdn_source,"sources",lambda:{}),(bridge.gdn_source,"runtime",lambda:{}),
   (bridge.gdn_observer,"Observer",lambda *args:NS()),
   (bridge.replay,"wrap_original_acl",lambda *args:None),
   (long_workspace,"build",lambda torch:Arena),(ann_snapshot,"Pool",Pool),
   (no_pa_full,"author_forward",math_spy),(ann_model_state.ANNState,"budget",tracked_budget)):
   stack.enter_context(patch.object(obj,name,value))
  stack.enter_context(patch.object(bridge,"_PATCHED",False))
  stack.enter_context(patch.dict(os.environ,{"QWEN36_SPARQ_STOCK_FULL_ENABLED":"1",
   "QWEN36_SPARQ_MODEL_MODE":"diagnostic","QWEN36_SPARQ_MODEL_ARM":"candidate"}))
  got=bridge.install_from_env();self.assertTrue(got["installed"]);self.assertFalse(got["model_ready"])
  return runner,memory
 def test_actual_profile_calls_all16_literal_None_forward_without_native_authority(self):
  runner,memory=self.harness()
  got=runner._dummy_run(40960,is_profile=True)
  self.assertIs(got,runner.returned);state=runner.state
  self.assertEqual(len(state.bindings),16);self.assertEqual(len(runner.outputs),16)
  self.assertTrue(all(t.fill_calls==[0] for t in runner.outputs))
  self.assertIsNone(state.baseline_allocated);self.assertIsNone(state.baseline_peak)
  self.assertIsNone(state.arena);self.assertIsNone(state.registry);self.assertIsNone(state.current)
  self.assertEqual((state.workspaces,state.snapshots,state.capture_inputs),({},{},{}))
  self.assertEqual(state.capture_batches,set());self.assertEqual((memory.allocation_calls,memory.budget_calls),(0,0))
  self.assertEqual(state.dummy_depth,0);self.assertFalse(bridge._LOCAL.profile_metadata_none)
 def test_actual_noncapture_native_warmup_keeps_allocation_and_real_budget(self):
  runner,memory=self.harness()
  got=runner._dummy_run(1,is_profile=False,force_attention=True,uniform_decode=True,cudagraph_runtime_mode="NONE")
  self.assertIs(got,runner.returned);state=runner.state
  self.assertEqual(state.baseline_allocated,100);self.assertIsNotNone(state.arena)
  self.assertEqual(len(state.snapshots),16);self.assertEqual(len(state.workspaces),16)
  self.assertEqual(tuple(state.forward_order),common.FA);self.assertIsNotNone(state.registry)
  self.assertEqual(state.capture_batches,set());self.assertGreater(memory.budget_calls,0)
  self.assertEqual(memory.allocation_calls,17);self.assertEqual(state.dummy_depth,0)
 def test_profile_native_metadata_or_minted_baseline_is_rejected(self):
  for fault,message in (("native-profile-metadata","original FA metadata must be None"),
    ("mint-baseline","cannot mint native baseline/warmup/capture authority")):
   with self.subTest(fault=fault):
    runner,memory=self.harness(fault)
    with self.assertRaisesRegex(ValueError,message):runner._dummy_run(40960,is_profile=True)
    self.assertEqual(memory.allocation_calls,0);self.assertEqual(runner.state.capture_batches,set())
    self.assertEqual(runner.state.dummy_depth,0);self.assertFalse(bridge._LOCAL.profile_metadata_none)
 def test_original_capture_admission_and_overbudget_warmup_remain_failclosed(self):
  runner,memory=self.harness()
  with self.assertRaisesRegex(ValueError,"actual all16 FA noncapture warmup"):
   runner._dummy_run(1,is_graph_capturing=True,uniform_decode=True,cudagraph_runtime_mode="FULL")
  self.assertEqual(runner.original_calls,0)
  runner,memory=self.harness("over-budget")
  with self.assertRaisesRegex(ValueError,"actual allb/all16FA graph pool"):
   runner._dummy_run(1,force_attention=True,uniform_decode=True,cudagraph_runtime_mode="NONE")
  self.assertGreater(memory.budget_calls,0);self.assertEqual(runner.state.capture_batches,set())
  self.assertEqual(runner.state.dummy_depth,0)


class LongDomainReferenceContracts(unittest.TestCase):
 def proof(self,physical=128):
  pages=(40960+physical-1)//physical
  return dict(schema="sparq.initialized-native-FA-geometry/v1",stock_physical_to_logical=True,
   context_parallel_size=1,logical_block_size=128,physical_block_size=physical,
   max_model_len=40960,physical_pages_per_request=pages,
   logical_pages_per_request=pages*(physical//128))
 def test_actual_registered_domain_not_component2304(self):
  import long_independent_oracle as oracle
  for physical,capacity in ((128,40960),(1536,41472)):
   p=self.proof(physical)
   d=oracle.domain(p["logical_pages_per_request"],p,32768+1024)
   self.assertEqual((d["capacity"],d["performance_total_tokens"],d["logical_model_max"]),(capacity,33792,40960))
   self.assertEqual(d["current_sentinel"],33791)
 def test_full40960_and_short39_never_dropped(self):
  import long_independent_oracle as oracle
  p=self.proof(1536)
  for n in (1,39,32768,33792,40960):
   d=oracle.domain(324,p,n)
   self.assertEqual(d["live_length"],n);self.assertEqual(d["current_sentinel"],n-1)
 def test_bool_zero_overlogical_and_fake324_rejected(self):
  import long_independent_oracle as oracle
  for n in (False,0,40961,41472):
   with self.assertRaises(ValueError):oracle.domain(324,self.proof(1536),n)
  for pages in (18,320,True):
   with self.assertRaises(ValueError):oracle.domain(pages,self.proof(1536),39)
 def test_actual_native_CP_and_maxlen_contracts_failclosed(self):
  import long_independent_oracle as oracle
  for key,value in (("context_parallel_size",2),("max_model_len",33792),
   ("logical_block_size",256),("stock_physical_to_logical",False)):
   p=self.proof(1536);p[key]=value
   with self.assertRaises(ValueError):oracle.domain(324,p,32768)
 def test_actual_serializer_to_consumer_domain_positive_and_disagreement(self):
  import long_independent_oracle as oracle
  p=self.proof(1536);d=oracle.domain(324,p,39)
  d["cropped_vs_registered_difference_tokens"]=[2,37]
  self.assertEqual(oracle.consume_domain(d,39)["live_length"],39)
  for key,value in (("capacity",2304),("current_sentinel",41471),("own_inputs",False),
   ("candidate_rank_or_score_used",True),("performance_total_tokens",32768)):
   wrong=copy.deepcopy(d);wrong[key]=value
   with self.assertRaises(ValueError):oracle.consume_domain(wrong,39)
 def test_cropped_difference_remains_diagnostic_complete_not_nonzero_tolerance(self):
  import long_independent_oracle as oracle
  p=self.proof();d=oracle.domain(320,p,39)
  for values in ([2,2],[-1],[39],[False]):
   d["cropped_vs_registered_difference_tokens"]=values
   with self.assertRaises(ValueError):oracle.consume_domain(d,39)
 def test_long_persistent_rank_input_all_views_actual_byte_accounting(self):
  p=allocation_contract.shape_plan(320)
  self.assertEqual(p["rank_input"],((16,6,40960),4))
  self.assertIn("rank_input",allocation_contract.ROW_VIEWS)
  self.assertEqual(set(allocation_contract.ROW_VIEWS)|set(allocation_contract.FIXED_VIEWS),set(p))
  self.assertEqual(allocation_contract.guarded_bytes(320),sum((math.prod(shape)+128)*size for shape,size in p.values()))
 def test_exact_two_stage_equal_and_original_BF16_perhead_reference_source(self):
  s=text("long_independent_oracle.py");tree=ast.parse(s)
  calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and
   isinstance(n.func.value,ast.Name) and n.func.value.id=="torch" and n.func.attr=="equal"]
  self.assertEqual(len(calls),2)
  self.assertIn("for query in q:",s);self.assertIn("padded.sum(0)[:n]",s)
  self.assertNotIn("import ann_workspace",s);self.assertNotIn("import long_workspace",s)
  self.assertIn('padded[:,n-1]=torch.finfo(torch.float32).max',s)
  self.assertNotIn(".item(",s)
 def test_real_model_caller_complete_buffers_and_native_geometry_not_2304(self):
  tree=ast.parse(text("ann_model_oracle.py"))
  calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and
   isinstance(n.func.value,ast.Name) and n.func.value.id=="long_reference" and n.func.attr=="source_legality"]
  self.assertEqual(len(calls),1);call=calls[0];self.assertEqual(len(call.args),10)
  self.assertEqual(ast.unparse(call.args[5]),"sample.score[i]")
  self.assertEqual(ast.unparse(call.args[6]),"sample.ranking[i]")
  self.assertEqual(ast.unparse(call.args[7]),"pages")
  self.assertIn("pages=len(tables[i]);proof=geometry_proof",text("ann_model_oracle.py"))
 def test_new_model_clock_source_and_original_whole_consumers_not_old_authority(self):
  self.assertEqual(c.execution_clock()["total_cutoff_epoch"],1791788425)
  self.assertEqual(c.NATIVE_EXECUTION_CLOCK["repair_cutoff_epoch"],1791615625)
  for f in ("host_run.py","consume_model.py","consume_service.py","full_entry.py"):
   self.assertIn("execution_clock",text(f))
  self.assertEqual(h.CURRENT["sha256"],"eb7ed908879c6bdea7fab670bcf83e570a7439045e2d8e5c4535c6a41611f528")
  self.assertEqual(h.manifest(c.obj(h.CURRENT),h.CURRENT)["source_count"],42)
 def test_live_source_drift_and_old_source_count_cannot_grant(self):
  m=c.obj(h.CURRENT)
  for key,value in (("source_count",41),):
   bad=copy.deepcopy(m);bad[key]=value
   with self.assertRaises(ValueError):h.manifest(bad,h.CURRENT)
  bad=copy.deepcopy(m);bad["execution_clock"]["owner"]="old-ba508"
  with self.assertRaises(ValueError):h.manifest(bad,h.CURRENT)

class CurrentBatchGeometryBeforeOracle(ActualANNEndBatchBinding):
 # Uses the REAL end; only independent oracle/IO/synchronization are spied.
 def test_missing_current_batch_geometry_rejected_before_any_oracle(self):
  state,ctx,names=self.fixture();del state.native_geometries[(names[-1],2)]
  import ann_model_oracle as oracle
  with patch.object(oracle,"check_layer") as fn:
   with self.assertRaisesRegex(ValueError,"current-batch initialized geometry"):state.end(ctx)
   self.assertEqual(fn.call_count,0)
 def test_same_shape_wrong_geometry_pointer_rejected_before_any_oracle(self):
  state,ctx,names=self.fixture();state.native_geometries[(names[-1],2)]["current_table_identity"][0]+=1
  import ann_model_oracle as oracle
  with patch.object(oracle,"check_layer") as fn:
   with self.assertRaisesRegex(ValueError,"current actual geometry pointers"):state.end(ctx)
   self.assertEqual(fn.call_count,0)


class ActualTurnPublication(unittest.TestCase):
 """REAL ANNState.end; only full oracle/IO/sync remain transparent spies."""
 def test_real_end_merges_registry_model_ready_false_without_duplicate_keyword(self):
  helper=ActualANNEndBatchBinding();state,ctx,names=helper.fixture()
  state.budget=lambda:dict(model_ready=False)
  observed=helper.run_end(state,ctx)
  self.assertEqual(len(observed),16)
  event=next(v for kind,v in state.emitted if kind=="actual-full-turn")
  self.assertFalse(event["model_ready"]);self.assertFalse(event["full64_layer_numeric_verified"])
  self.assertTrue(event["completed"]);self.assertEqual(event["arm"],"candidate")
  self.assertEqual(event["ACL_replays"],state.replay_calls)
  self.assertIsNone(state.current);self.assertEqual(state.model_entries,1)
 def test_registry_model_ready_true_is_rejected_not_silently_overwritten(self):
  helper=ActualANNEndBatchBinding();state,ctx,names=helper.fixture()
  original=state.registry.end_replay
  def erroneous_record(*args,**kwargs):
   return dict(original(*args,**kwargs),model_ready=True)
  with patch.object(state.registry,"end_replay",side_effect=erroneous_record):
   with self.assertRaisesRegex(ValueError,"registry record cannot grant model-ready"):helper.run_end(state,ctx)
  self.assertFalse(any(kind=="actual-full-turn" for kind,_ in state.emitted))
  self.assertIsNotNone(state.current);self.assertEqual(state.model_entries,0)
class ActualStockMetadataType(unittest.TestCase):
 def test_missing_model_runner_type_fails_real_stock_outer_before_native_warmup(self):
  helper=ActualWrappedDummyProfile();self.addCleanup(helper.doCleanups)
  runner,memory=helper.harness("missing-model-runner-type")
  with self.assertRaisesRegex(AttributeError,"model_runner_type"):
   runner._dummy_run(1,is_profile=False,force_attention=True,uniform_decode=True,cudagraph_runtime_mode="NONE")
  self.assertEqual(memory.allocation_calls,0);self.assertIsNone(runner.state.baseline_allocated)
  self.assertEqual(runner.state.capture_batches,set());self.assertEqual(runner.state.dummy_depth,0)

if __name__=="__main__":unittest.main()
