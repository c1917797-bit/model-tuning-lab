"""One explicit source-bound6GiB policy delta; frozen reader math/factory unchanged.
No modification of the donor module globals. Capacity is checked from the actual
native initialized cache and recorded before candidate prefill/reader installation.
"""
import ast,hashlib,sys
from pathlib import Path
import bridge_contract as B
def capture_registry():
    """Explicit original own+dependency load; raw_sink is not a capture-own file."""
    C=B.bootstrap();W,_=C.writer_modules();manifest=C.obj(W.CAPTURE)
    for name in("io_contract","current_contract","tp_provider_current","post_rope_current","raw_sink","text_input_current",
      "runtime_capture_current"):
        rows=manifest["dependencies"]if name in("io_contract","raw_sink")else manifest["files"]
        matches=[r for r in rows if r["path"].endswith("/"+name+".py")]
        B.need(len(matches)==1,"one exact actual registry transitive module: "+name)
        module=C.load(name,matches[0])
    return module
def factory_type(C):
    rows=C.obj(B.READER)["files"];row=next(x for x in rows if x["path"].endswith("/model_runtime.py"))
    donor=sys.modules["model_runtime"];B.need(C.ref(donor.__file__)==row,"exact frozen model factory donor")
    tree=ast.parse(C.read(row),row["path"]);original=ast.dump(tree,include_attributes=False)
    policies=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=="policy"]
    B.need(len(policies)==1,"exact single inherited model policy")
    nodes=[n for n in ast.walk(policies[0])if isinstance(n,ast.Constant)and n.value==10]
    B.need(len(nodes)==1,"one declared native cache-budget literal, no mathematical delta")
    nodes[0].value=6
    messages=[n for n in ast.walk(policies[0])if isinstance(n,ast.Constant)and isinstance(n.value,str)and "retained10GiB"in n.value]
    B.need(len(messages)==1,"one policy annotation");messages[0].value=messages[0].value.replace("retained10GiB","retained6GiB")
    namespace=dict(__name__="_skvq_model_explicit6g_factory",__file__=row["path"])
    exec(compile(ast.fix_missing_locations(tree),row["path"],"exec"),namespace)
    namespace["capture_registry"]=capture_registry
    return namespace["Factory"],dict(donor_ref=row,original_ast_sha256=hashlib.sha256(original.encode()).hexdigest(),
      adapted_ast_sha256=hashlib.sha256(ast.dump(tree,include_attributes=False).encode()).hexdigest(),
      delta="policy native cache literal10->6GiB plus annotation; explicit own+dependency registry loader",
      registry_loader_ref=C.ref(__file__),math_changed=False)
def geometry(worker,registry,C,source):
    from native_binding import sources
    origins=sources();runner=worker.model_runner;config=runner.kv_cache_config
    B.need(type(config.num_blocks)is int and config.num_blocks>0,"actual native KVCacheConfig blocks")
    context=runner.compilation_config.static_forward_context;records=[];names=set()
    layer_specs=runner._get_layer_kv_cache_specs(config)
    for logical,(_,child)in sorted(registry.items()):
        matches=[(i,g,name)for i,g in enumerate(config.kv_cache_groups)for name in g.layer_names
          if context.get(name)is child]
        B.need(len(matches)==1,"exact actual FA native layer/group owner")
        gid,g,name=matches[0];spec=layer_specs[name]
        B.need(name not in names and type(spec.block_size)is int and spec.block_size>0 and
          (spec.num_kv_heads,spec.head_size,str(spec.dtype))==(1,256,"torch.bfloat16")and
          config.num_blocks*spec.block_size>=33792,"actual unmodified native FA capacity covers33792 at6GiB")
        names.add(name);views=child.kv_cache
        B.need(len(views)==1 and isinstance(views[0],(tuple,list))and len(views[0])==2,
          "actual original native bound K/V pair; no reconstructed allocation")
        descriptors=[]
        for t in views[0]:
            storage=t.untyped_storage()
            B.need(t.dtype==spec.dtype and t.device.type=="npu"and t.numel()>=33792*256,
              "actual bound native full capacity A16 typed view")
            descriptors.append(dict(shape=list(t.shape),stride=list(t.stride()),dtype=str(t.dtype),device=str(t.device),
              storage_offset=t.storage_offset(),storage_data_ptr=storage.data_ptr(),storage_nbytes=storage.nbytes(),
              data_ptr=t.data_ptr(),logical_bytes=t.numel()*t.element_size()))
        records.append(dict(logical_layer=logical,native_name=name,group=gid,block_size=spec.block_size,
          logical_capacity=config.num_blocks*spec.block_size,views=descriptors))
    allocations=[dict(size=t.size,shared_by=list(t.shared_by))for t in config.kv_cache_tensors]
    B.need(len(records)==16 and all(type(x["size"])is int and x["size"]>0 for x in allocations)and
      sum(x["size"]for x in allocations)<=6*2**30,"actual allocator declared physical slabs within common6GiB")
    return dict(schema="skvq.model-reader.native-geometry/v1",source_ref=source,reader_source_ref=B.READER,
      actual_runtime_origins=origins,rank=worker.rank,num_blocks=config.num_blocks,FA=records,
      physical_allocations=allocations,physical_declared_bytes=sum(x["size"]for x in allocations),
      native_cache_budget_bytes=6*2**30,minimum_logical_capacity=33792,
      compact_additional_per_rank_upper_bytes=16*(2*(33792*67+2*33792*4*2+133*256*2+256*3*4)+16),
      reader_temporary_per_rank_live_bytes=2*6*33792*2+1536*2,
      GDN48_original_allocation_retained=True,HBM_peak_unknown_and_actual3GiB_reserve_gate_required=True,
      **B.false_scopes())
class Factory:
    def __init__(self,worker,reader_ref,prompt_ref,root,source):
        C=B.bootstrap();original=capture_registry()
        actual=original.actual_worker(worker);original.deployed_sources();_,registry,_=original.registry_for(actual)
        # Persist before rejecting; never guess geometry from scheduler block_size.
        raw=dict(source_ref=source,reader_source_ref=B.READER,rank=worker.rank,
          num_blocks=getattr(worker.model_runner.kv_cache_config,"num_blocks",None))
        parent=Path(root).parent;before=C.atomic(parent/("NATIVE_GEOMETRY_PRE-rank%d.json"%worker.rank),raw)
        value=geometry(worker,registry,C,source)
        self.geometry_ref=C.atomic(parent/("NATIVE_GEOMETRY-rank%d.json"%worker.rank),dict(**value,before_ref=before))
        cls,self.delta=factory_type(C)
        self.inner=cls(worker,reader_ref,prompt_ref,root,B.READER["sha256"])
        C.atomic(Path(root)/"EXPLICIT_FACTORY_DELTA.json",dict(source_ref=source,reader_source_ref=B.READER,
          geometry_ref=self.geometry_ref,**self.delta))
    def __getattr__(self,name):return getattr(self.inner,name)
