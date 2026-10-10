"""Source-derived native QKV regression; explicit software tensor/TP surrogate.
No Torch/native group/model import. Does not prove actual worker parameter values.
"""
import argparse,ast,copy,hashlib,importlib.util,json,os,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import current_contract as C
import qkv_projection_current as q
import loader_order_current as loader
import order_oracle_current as oracle
REVIEW=None
def source(name):return (HERE/name).read_text()
def raw(module):
    pin=next(p for p in q.PINS if p["module"]==module)
    path=(REVIEW/Path(pin["snapshot"]["path"]).name)if REVIEW else Path(pin["snapshot"]["path"])
    if REVIEW and module==q.UTILITY:path=REVIEW.parent/"c159-skvq009-source-repair/utils.py"
    value=path.read_bytes()
    C.require(len(value)==pin["snapshot"]["bytes"]and hashlib.sha256(value).hexdigest()==pin["snapshot"]["sha256"],"actual entire image660 source")
    return value.decode(),path
def cls(text,name):
    rows=[x for x in ast.parse(text).body if isinstance(x,ast.ClassDef)and x.name==name]
    C.require(len(rows)==1,"exact original class");return copy.deepcopy(rows[0])
def exec_nodes(module,definitions,path):
    body=[ast.ImportFrom(module="__future__",names=[ast.alias(name="annotations")],level=0)]+definitions
    exec(compile(ast.fix_missing_locations(ast.Module(body=body,type_ignores=[])),str(path),"exec"),module.__dict__)
def native_surrogate(rank=0):
    """Execute unchanged original class bodies; only Torch tensors/TP calls are surrogates."""
    class Module:
        def __init__(self):pass
        def register_parameter(self,name,value):setattr(self,name,value)
    class ModelWeightParameter:
        def __init__(self,data,input_dim,output_dim,weight_loader):
            self.shape=data;self.input_dim=input_dim;self.output_dim=output_dim;self.weight_loader=weight_loader
            self.tp_rank=rank;self.tp_size=4;self.dtype="torch.bfloat16"
            self.device=types.SimpleNamespace(type="npu")
        def data_ptr(self):return 123
        def untyped_storage(self):return types.SimpleNamespace(data_ptr=lambda:123)
        def storage_offset(self):return 0
    ModelWeightParameter.__module__=q.PARAMETER;ModelWeightParameter.__qualname__="ModelWeightParameter"
    torch=types.SimpleNamespace(empty=lambda *shape,**kw:shape,get_default_dtype=lambda:"torch.bfloat16",
        ops=types.SimpleNamespace(vllm=types.SimpleNamespace(unquantized_gemm=lambda x,w,b:("original-native-call",x))))
    modules={}
    for pin in q.PINS:
        module=types.ModuleType(pin["module"]);text,path=raw(pin["module"])
        module.__file__=str(path);module.__spec__=importlib.util.spec_from_file_location(pin["module"],path)
        modules[pin["module"]]=module
    c=modules[q.CUSTOM];c.nn=types.SimpleNamespace(Module=Module);c.logger=types.SimpleNamespace(debug=lambda *a:None)
    c.op_registry={};c.op_registry_oot={}
    exec_nodes(c,[cls(raw(q.CUSTOM)[0],"PluggableLayer")],c.__file__)
    m=modules[q.PUBLIC];m.PluggableLayer=c.PluggableLayer;m.LinearMethodBase=object
    m.divide=lambda x,n:x//n;m.get_tensor_model_parallel_rank=lambda:rank
    m.get_tensor_model_parallel_world_size=lambda:4;m.torch=torch
    m.ModelWeightParameter=ModelWeightParameter;m.set_weight_attrs=lambda obj,kw:[setattr(obj,k,v)for k,v in kw.items()]
    tree=ast.parse(raw(q.PUBLIC)[0])
    assignment=next(x for x in tree.body if isinstance(x,ast.Assign)and any(isinstance(t,ast.Name)and t.id=="WEIGHT_LOADER_V2_SUPPORTED"for t in x.targets))
    exec_nodes(m,[copy.deepcopy(assignment)]+[cls(raw(q.PUBLIC)[0],n)for n in
      ("UnquantizedLinearMethod","LinearBase","ColumnParallelLinear","QKVParallelLinear")],m.__file__)
    a=modules[q.ASCEND];a.__dict__.update({n:getattr(m,n)for n in
      ("UnquantizedLinearMethod","LinearBase","ColumnParallelLinear","QKVParallelLinear","WEIGHT_LOADER_V2_SUPPORTED")})
    a.nn=types.SimpleNamespace(Module=Module);a.torch=torch;a.divide=m.divide
    a.get_parallel_op=lambda *args:(None,rank,4)
    exec_nodes(a,[cls(raw(q.ASCEND)[0],n)for n in
      ("AscendUnquantizedLinearMethod","AscendLinearBase","AscendColumnParallelLinear","AscendQKVParallelLinear")],a.__file__)
    modules[q.PARAMETER].ModelWeightParameter=ModelWeightParameter
    modules[q.OP].get_parallel_op=a.get_parallel_op
    u=modules[q.UTILITY];u.REGISTERED_ASCEND_OPS={"QKVParallelLinear":a.AscendQKVParallelLinear}
    u._ASCEND_CUSTOMOP_IS_REIGISTERED=True;c.op_registry_oot["QKVParallelLinear"]=a.AscendQKVParallelLinear
    with patch.dict(sys.modules,modules):
        projected=m.QKVParallelLinear(hidden_size=2048,head_size=256,total_num_heads=48,total_num_kv_heads=4,
          bias=False,params_dtype="torch.bfloat16",prefix="model.layers.3.self_attn.qkv_proj")
    outer=types.SimpleNamespace(qkv_proj=projected,attn_output_gate=True,num_heads=6,num_kv_heads=1,
      head_dim=256,total_num_heads=24,total_num_kv_heads=4,hidden_size=2048)
    return modules,outer
def qualification():
    return dict(schema="skvq.actual-native-QKV-class/v1",
      runtime_origins={p["module"]:dict(module=p["module"],path=p["runtime_path"],sha256=p["snapshot"]["sha256"])for p in q.PINS},
      class_module=q.ASCEND,class_name="AscendQKVParallelLinear",direct_base_module=q.PUBLIC,
      direct_base_name="QKVParallelLinear",original_OOT_registration=True,quant_method="AscendUnquantizedLinearMethod",
      constructor_loader_branch="legacy",parameter_class="ModelWeightParameter",methods=copy.deepcopy(oracle.METHODS),
      weights_loading_executed_by_qualification=False,projection_called=False,live_TP_parameter_geometry_verified=False)
def checked_qualification():
    original=Path.read_bytes
    snapshots={p["snapshot"]["path"]:raw(p["module"])[0].encode()for p in q.PINS}
    def reader(path):return snapshots.get(path.as_posix(),None)if path.as_posix()in snapshots else original(path)
    return patch.object(Path,"read_bytes",reader)
def record(rank=0):
    modules,outer=native_surrogate(rank)
    with patch.dict(sys.modules,modules),patch.dict(os.environ,{"QWEN36_SKVQ_TP4_CAPTURE_ENABLE":"1"}),patch.object(
      loader,"qualified",return_value=(modules[q.ASCEND].AscendQKVParallelLinear,qualification())):
        result=loader.actual(outer,rank)
    return modules,outer,result
class NativeQKV(unittest.TestCase):
    def test01_source_complete_compile_no_runtime_import(self):
        for p in q.PINS:compile(raw(p["module"])[0],p["snapshot"]["path"],"exec")
        self.assertNotIn("torch",sys.modules)
        self.assertEqual(len(q.PINS),6)
    def test02_original_OOT_new_returns_native_not_public(self):
        modules,outer=native_surrogate()
        self.assertIs(type(outer.qkv_proj),modules[q.ASCEND].AscendQKVParallelLinear)
        self.assertIsNot(type(outer.qkv_proj),modules[q.PUBLIC].QKVParallelLinear)
    def test03_original_all4_constructor_and_legacy_geometry(self):
        for rank in range(4):
            modules,outer,r=record(rank);p=outer.qkv_proj
            self.assertEqual(p.output_sizes,[12288,1024,1024]);self.assertEqual(p.output_partition_sizes,[3072,256,256])
            self.assertIs(p.weight.weight_loader.__func__,modules[q.PUBLIC].QKVParallelLinear.weight_loader)
            self.assertEqual(p.weight.shape,(3584,2048));self.assertEqual(p.tp_rank,rank)
            with checked_qualification():self.assertEqual(oracle.consume_record(r,rank),list(range(rank*256,(rank+1)*256)))
    def test04_actual_constructor_not_public_v2(self):
        text=raw(q.ASCEND)[0];self.assertIn("AscendUnquantizedLinearMethod()",text)
        for rank in range(4):
            modules,outer=native_surrogate(rank)
            self.assertNotIn(type(outer.qkv_proj.quant_method).__name__,modules[q.PUBLIC].WEIGHT_LOADER_V2_SUPPORTED)
            self.assertIs(outer.qkv_proj.weight.weight_loader.__func__,modules[q.PUBLIC].QKVParallelLinear.weight_loader)
    def test05_original_Ascend_forward_semantics_retained(self):
        modules,outer=native_surrogate()
        with patch.dict(sys.modules,modules),patch.object(q,"qualified",return_value=(modules[q.ASCEND].AscendQKVParallelLinear,qualification())):
            fn=q.forward(outer.qkv_proj);self.assertEqual(fn("actual-input"),(("original-native-call","actual-input"),None))
    def test06_foreign_subclass_and_own_override_hard_reject(self):
        modules,outer=native_surrogate();base=modules[q.ASCEND].AscendQKVParallelLinear
        with patch.dict(sys.modules,modules),patch.object(q,"qualified",return_value=(base,qualification())):
            outer.qkv_proj.forward=lambda x:x
            with self.assertRaises(ValueError):q.forward(outer.qkv_proj)
            del outer.qkv_proj.forward
            class Foreign(base):pass
            outer.qkv_proj=object.__new__(Foreign)
            with self.assertRaises(ValueError):q.forward(outer.qkv_proj)
    def test07_parameter_rank_shape_and_custompath_reject(self):
        for field,value in (("tp_rank",1),("tp_size",2),("custom_op",object()),("return_bias",False),("skip_bias_add",True)):
            modules,outer=native_surrogate();setattr(outer.qkv_proj,field,value)
            with patch.dict(sys.modules,modules),patch.dict(os.environ,{"QWEN36_SKVQ_TP4_CAPTURE_ENABLE":"1"}),patch.object(
              loader,"qualified",return_value=(modules[q.ASCEND].AscendQKVParallelLinear,qualification())):
                with self.assertRaises(ValueError):loader.actual(outer,0)
        modules,outer=native_surrogate();outer.qkv_proj.weight.shape=(3583,2048)
        with patch.dict(sys.modules,modules),patch.dict(os.environ,{"QWEN36_SKVQ_TP4_CAPTURE_ENABLE":"1"}),patch.object(
          loader,"qualified",return_value=(modules[q.ASCEND].AscendQKVParallelLinear,qualification())):
            with self.assertRaises(ValueError):loader.actual(outer,0)
    def test08_real_raw_observation_independently_consumed(self):
        modules,outer,r=record()
        observed=q.observation(outer);logical="model.layers.3.self_attn";identity={"pid":123};source_ref={"path":"/actual/source"}
        value=dict(schema="skvq.QKV-install-before-qualification/v1",source_ref=source_ref,rank=0,identity=identity,
          observed={logical:observed})
        with checked_qualification():self.assertIs(oracle.consume_install_raw(value,0,identity,{logical:r},source_ref),value)
    def test09_raw_typed_bool_rank_and_wrong_class_reject(self):
        modules,outer,r=record();logical="model.layers.3.self_attn";observed=q.observation(outer)
        value=dict(schema="skvq.QKV-install-before-qualification/v1",source_ref={},rank=0,identity={},
          observed={logical:observed})
        for field,mutant in (("tp_rank",dict(type="builtins.bool",value=False)),("gather_output",dict(type="builtins.bool",value=True))):
            wrong=copy.deepcopy(value);wrong["observed"][logical]["fields"][field]=mutant
            with checked_qualification(),self.assertRaises(ValueError):oracle.consume_install_raw(wrong,0,{}, {logical:r},{})
        value["observed"][logical]["actual_class"]="foreign.QKV"
        with checked_qualification(),self.assertRaises(ValueError):oracle.consume_install_raw(value,0,{}, {logical:r},{})
    def test10_independent_native_source_and_branch_reject(self):
        for field,value in (("class_name","QKVParallelLinear"),("constructor_loader_branch","v2"),("parameter_class","Parameter"),
          ("original_OOT_registration",False)):
            wrong=qualification();wrong[field]=value
            with checked_qualification(),self.assertRaises(ValueError):oracle.consume_qualification(wrong)
        wrong=qualification();wrong["runtime_origins"][q.ASCEND]["sha256"]="0"*64
        with checked_qualification(),self.assertRaises(ValueError):oracle.consume_qualification(wrong)
    def test11_raw_before_strict_install_gate(self):
        text=source("loader_bridge_current.py")
        self.assertLess(text.index("raw=original.publish_json"),text.index("record=actual("))
        self.assertLess(text.index("observation(outer)"),text.index("record=actual("))
        tap=source("projection_tap_current.py");self.assertIn("original=original_forward(p)",tap)
        self.assertIn("old(*args,**kwargs)",tap)
    def test12_real_N1_beforeweights_and_consumer_edge(self):
        text=source("n1_check.py")
        self.assertLess(text.index("actual all4 tiny completed"),text.index("native_qkv.preweights"))
        self.assertIn('consume_qkv_preweights(cfg["native_qkv_qualification"],source,read)',source("consume_host.py"))
        calls=[ast.unparse(n.func)for n in ast.walk(ast.parse(source("qkv_projection_current.py")))if isinstance(n,ast.Call)]
        self.assertNotIn("torch.empty",calls);self.assertNotIn("cls",calls)
    def test13_exact_current_consumer_names_not_old_cached_oracle(self):
        text=source("consume_stage.py")
        self.assertIn('donor("order_oracle_current",HERE/"order_oracle_current.py")',text)
        self.assertIn('donor("consume_loader_current",HERE/"consume_loader_current.py")',text)
        self.assertNotIn('donor("order_oracle",ORDER/',text)
        self.assertIn("consume_install_raw(",source("consume_loader_current.py"))
    def test14_unchanged_independent_channel_formula_and_all_events(self):
        text=source("order_oracle_current.py")
        for needle in ('[head*256+d for head in [rank] for d in range(256)]','list(range(1024))',
          'v["legacy_kv_shard_rank"]==rank'):self.assertIn(needle,text)
        self.assertIn("events==16384",source("consume_loader_current.py"))
        self.assertNotIn("from loader_order_current",text);self.assertNotIn("import qkv_projection_current",text)
    def test15_observation_rejects_missing_geometry_after_persist(self):
        modules,outer,r=record();del outer.qkv_proj.disable_tp
        value=q.observation(outer)
        self.assertEqual(value["fields"]["disable_tp"]["unreadable"],"AttributeError")
        logical="model.layers.3.self_attn";event=dict(schema="skvq.QKV-install-before-qualification/v1",source_ref={},
          rank=0,identity={},observed={logical:value})
        with checked_qualification(),self.assertRaises(ValueError):oracle.consume_install_raw(event,0,{}, {logical:r},{})
    def test16_original_public_math_functions_remain_byte_AST(self):
        original=raw(q.PUBLIC)[0];self.assertIn("rank // self.num_kv_head_replicas",original)
        derived=source("loader_order_current.py")
        self.assertIn('p._get_shard_offset_mapping("k")==3072',derived)
        self.assertIn("legacy_kv_shard_rank",derived)
        self.assertNotIn("weight_loader_v2(",derived)
    def test17_complete_real_qualifier_on_original_class_bodies(self):
        modules,outer=native_surrogate()
        fn=next(x for x in ast.parse(raw(q.OP)[0]).body if isinstance(x,ast.FunctionDef)and x.name=="get_parallel_op")
        exec_nodes(modules[q.OP],[copy.deepcopy(fn)],modules[q.OP].__file__)
        modules[q.ASCEND].get_parallel_op=modules[q.OP].get_parallel_op
        origins={n:dict(module=n,path=m.__file__,sha256=next(p["snapshot"]["sha256"]for p in q.PINS if p["module"]==n))
          for n,m in modules.items()}
        with patch.dict(sys.modules,modules),patch.object(q,"origin",side_effect=lambda name:(modules[name],origins[name])):
            actual,value=q.qualified()
            self.assertIs(actual,modules[q.ASCEND].AscendQKVParallelLinear)
            self.assertEqual(value["constructor_loader_branch"],"legacy")
            self.assertEqual(set(value["methods"]),set(oracle.METHODS))
            modules[q.CUSTOM].op_registry_oot["QKVParallelLinear"]=modules[q.PUBLIC].QKVParallelLinear
            with self.assertRaisesRegex(ValueError,"actual original OOT registry"):q.qualified()
    def test18_exact_forward_source_guard_rejects_foreign_function(self):
        modules,outer=native_surrogate()
        fn=modules[q.ASCEND].AscendQKVParallelLinear.forward
        self.assertEqual(q.function(fn,"forward",q.ASCEND,modules[q.ASCEND].__file__)["name"],"forward")
        with self.assertRaises(ValueError):q.function(lambda x:x,"forward",q.ASCEND,modules[q.ASCEND].__file__)
def main(argv=None):
    global REVIEW
    ap=argparse.ArgumentParser();ap.add_argument("--review-native-qkv-root",type=Path);a=ap.parse_args(argv);REVIEW=a.review_native_qkv_root
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(NativeQKV))
    return 0 if result.wasSuccessful()else 1
if __name__=="__main__":sys.exit(main())
