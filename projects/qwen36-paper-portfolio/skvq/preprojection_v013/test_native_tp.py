"""Transparent source-derived stdlib regressions, never native/HCCL/model authority."""
import argparse,ast,copy,hashlib,importlib.util,json,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import tp_provider_current as tp
import current_contract as C
REVIEW=None
def own(name):return (HERE/name).read_text()
def native(name):
    pins=tp.NATIVE_PINS
    row=next(p["snapshot"]for p in pins if Path(p["snapshot"]["path"]).name==name)
    path=(REVIEW/name)if REVIEW else Path(row["path"])
    raw=path.read_bytes()
    C.require(len(raw)==row["bytes"]and hashlib.sha256(raw).hexdigest()==row["sha256"],"whole exact native source")
    return raw.decode()
def node(text,name):
    rows=[n for n in ast.walk(ast.parse(text))if isinstance(n,(ast.ClassDef,ast.FunctionDef))and n.name==name]
    C.require(len(rows)==1,"unique exact source node");return rows[0]
def qualification():
    return {"schema":"skvq.actual-native-tp-class/v1",
      "public_source":{"module":tp.PARALLEL_MODULE,"path":"/vllm-workspace/vllm/vllm/distributed/parallel_state.py","sha256":tp.PARALLEL_SHA},
      "runtime_origins":{p["module"]:{"module":p["module"],"path":p["runtime_path"],"sha256":p["snapshot"]["sha256"]}for p in tp.NATIVE_PINS},
      "class_module":tp.PATCH_MODULE,"class_name":"GroupCoordinatorPatch",
      "direct_base_module":tp.PARALLEL_MODULE,"direct_base_name":"GroupCoordinator",
      "public_alias_is_exact_patch":True,"original_registration_retained":True,
      "original_getters":list(tp.GETTERS),"methods":{n:{"module":tp.PATCH_MODULE,"name":n,
        "path":next(p["runtime_path"]for p in tp.NATIVE_PINS if p["module"]==tp.PATCH_MODULE)}for n in tp.PATCH_METHODS},
      "TP_STATE_PATCHED":False,"group_construction_or_collective_called":False,"live_TP_groups_verified":False}
def group_fixture():
    class Group:pass
    group=Group();group.unique_name="tp:0";group.world_size=4;group.ranks=[0,1,2,3]
    group.rank_in_group=0;group.rank=0;group.local_rank=0;group.device=0;group.backend="hccl"
    group.cpu_group=object();group.device_group=object()
    module=types.SimpleNamespace(GroupCoordinator=Group,_groups={"tp:0":lambda:group})
    dist=types.SimpleNamespace(get_process_group_ranks=lambda g:list(group.ranks),
      get_rank=lambda group:0,get_world_size=lambda group:4,
      get_backend=lambda g:"gloo"if g is group.cpu_group else "hccl")
    return module,group,dist
def source_reader(path):
    if path==tp.PARALLEL_SOURCE:return tp.PARALLEL_SHA
    return next(p["snapshot"]["sha256"]for p in tp.NATIVE_PINS if p["snapshot"]["path"]==path)
class NativeTP(unittest.TestCase):
    def test01_default_import_has_no_native_or_Torch(self):
        self.assertNotIn("torch",sys.modules);self.assertNotIn(tp.PATCH_MODULE,sys.modules)
        self.assertEqual(tp.main([]),None)
    def test02_exact_actual_native_replacement_chain(self):
        raw=native("patch__worker__patch_distributed.py");tree=ast.parse(raw)
        cls=node(raw,"GroupCoordinatorPatch")
        self.assertEqual([ast.dump(x)for x in cls.bases],[ast.dump(ast.Name(id="GroupCoordinator",ctx=ast.Load()))])
        aliases=[n for n in tree.body if isinstance(n,ast.Assign)and
          any(ast.unparse(t)=="vllm.distributed.parallel_state.GroupCoordinator"for t in n.targets)]
        self.assertEqual(len(aliases),1);self.assertEqual(ast.unparse(aliases[0].value),"GroupCoordinatorPatch")
        self.assertIn("from vllm.distributed.parallel_state import GroupCoordinator, _get_unique_name, _register_group",raw)
    def test03_actual_method_body_returns_int_without_creating_PG(self):
        raw=native("patch__worker__patch_distributed.py")
        fn=copy.deepcopy(node(raw,"_init_device_communicator"));original=ast.dump(fn.body[0])
        fn.returns=None
        for arg in fn.args.args:arg.annotation=None
        calls=[]
        ns={"torch":types.SimpleNamespace(npu=types.SimpleNamespace(current_device=lambda:2)),
          "NPUCommunicator":lambda **kw:calls.append(kw)}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),"exact-native-method-body","exec"),ns)
        shell=types.SimpleNamespace(use_device_communicator=False)
        ns["_init_device_communicator"](shell)
        self.assertIs(type(shell.device),int);self.assertEqual(shell.device,2);self.assertFalse(calls)
        self.assertEqual(ast.dump(fn.body[0]),original)
    def test04_true_integer_not_bool_or_Torch_device(self):
        for value in (False,True,"0",types.SimpleNamespace(type="npu",index=0)):
            with self.assertRaises(ValueError):tp.logical_device(types.SimpleNamespace(device=value,local_rank=0),0,"tp")
    def test05_logical_device_mismatch_hard_refusal(self):
        for values in ((0,1,0),(1,1,0),(0,0,True),(4,4,4)):
            with self.assertRaises(ValueError):tp.logical_device(types.SimpleNamespace(device=values[0],local_rank=values[1]),values[2],"tp")
    def test06_real_snapshot_function_hccl_gloo_strict(self):
        module,group,dist=group_fixture()
        result=tp.group_snapshot(module,group,dist,"tp",4,0)
        self.assertEqual(result["logical_device"],0);self.assertEqual(result["process_groups"]["device"]["backend"],"hccl")
        dist.get_backend=lambda g:"gloo"
        with self.assertRaises(ValueError):tp.group_snapshot(module,group,dist,"tp",4,0)
    def test07_foreign_subclass_and_unregistered_groups_rejected(self):
        module,group,dist=group_fixture()
        class Foreign(type(group)):pass
        foreign=Foreign();foreign.__dict__.update(group.__dict__)
        with self.assertRaises(ValueError):tp.group_snapshot(module,foreign,dist,"tp",4,0)
        module._groups={}
        with self.assertRaises(ValueError):tp.group_snapshot(module,group,dist,"tp",4,0)
    def test08_wrong_PG_members_or_ranks_rejected(self):
        module,group,dist=group_fixture()
        dist.get_process_group_ranks=lambda g:[0,2,1,3]
        with self.assertRaises(ValueError):tp.group_snapshot(module,group,dist,"tp",4,0)
    def test09_all_original_getters_and_source_pins_preserved(self):
        self.assertEqual(len(tp.GETTERS),8);self.assertEqual(len(tp.NATIVE_PINS),8)
        for pin in tp.NATIVE_PINS:native(Path(pin["snapshot"]["path"]).name)
        raw=own("tp_provider_current.py")
        for needle in ("cls.__bases__==(original,)","ps.GroupCoordinator is cls","patch._register_group is ps._register_group",
          "ps._TP_STATE_PATCHED is False","dist.is_initialized()","type(group.device)is int"):
            self.assertIn(needle,raw)
    def test10_postrope_provider_not_stale(self):
        self.assertIn("from tp_provider_current import",own("post_rope_current.py"))
        self.assertNotIn("from tp_provider import",own("post_rope_current.py"))
        for name in ("runtime_capture_current.py","projection_tap_current.py"):
            self.assertNotIn("from post_rope_live import",own(name))
        self.assertIn("from tp_provider_current import",own("runtime_capture_current.py"))
    def test11_N1_real_representation_before_weights_and_raw_before_gate(self):
        raw=own("tp_provider_current.py");fn=node(raw,"preweights");text=ast.unparse(fn)
        self.assertIn("utility.adapt_patch(is_global_patch=False)",text)
        self.assertIn("cls._init_device_communicator(shell)",text)
        self.assertIn("shell.use_device_communicator = False",text)
        gate=next(n for n in ast.walk(fn)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and
            n.func.id=="require"and len(n.args)>1 and isinstance(n.args[1],ast.Constant)and
            n.args[1].value=="real original native method returns true int logical device0")
        self.assertLess(text.index("representation_ref = publish"),text.index(ast.unparse(gate)))
        entry=own("n1_check.py")
        self.assertLess(entry.index("all(not child.is_alive()"),entry.index("native_tp.preweights"))
        self.assertIn('native_tp.consume_preweights(cfg["native_tp_qualification"],source,read)',own("consume_host.py"))
    def test12_independent_consumer_every_rank_and_event(self):
        raw=own("consume_capture_current.py")
        self.assertIn("consume_identity(identity,rank)",raw);self.assertIn('consume_identity(proof["rank"],rank)',raw)
        self.assertIn('donor("consume_capture",HERE/"consume_capture_current.py")',own("consume_stage.py"))
        self.assertIn('ref in manifest["files"]',own("consume_stage.py"))
    def test13_no_candidate_math_in_derived_consumer(self):
        raw=own("consume_capture_current.py")
        for name in ("tensor","stats"):
            derived=ast.dump(node(raw,name))
            manifest=json.loads((HERE/"SOURCE_MANIFEST.json").read_text())
            ref=next(r for r in manifest["dependencies"]if r["path"].endswith("/skvq-calibration-capture-chain-v1-001/consume_capture.py"))
            path=(REVIEW.parent/"c150-independent-backup/skvq-calibration-capture-chain-v1-001/consume_capture.py")if REVIEW else Path(ref["path"])
            if REVIEW:path=Path(str(REVIEW.parent/"c150-independent-backup/skvq-calibration-capture-chain-v1-001/consume_capture.py"))
            original=path.read_bytes()
            self.assertEqual(hashlib.sha256(original).hexdigest(),ref["sha256"])
            self.assertEqual(derived,ast.dump(node(original.decode(),name)))
        imports=[n for n in ast.walk(ast.parse(raw))if isinstance(n,(ast.Import,ast.ImportFrom))]
        names=[n.module for n in imports if isinstance(n,ast.ImportFrom)]+[a.name for n in imports if isinstance(n,ast.Import)for a in n.names]
        self.assertFalse(any(n and ("torch" in n or "candidate" in n)for n in names))
    def test14_identity_rejects_bad_backend_without_source_bypass(self):
        ident={"schema":"SKVQ_LIVE_TP_IDENTITY_V1","native_group_class":qualification(),
          "public_TP_rank":0,"pid":123,"pid_start_ticks":99,"groups":{}}
        for name in ("tp","world","pp","dp","pcp","dcp"):
            world=4 if name in ("tp","world")else 1;members=list(range(4))if world==4 else [0]
            ident["groups"][name]={"members":members,"global_rank":0,"world_size":world,
              "rank_in_group":0,"local_rank":0,"logical_device":0,"device":"0","device_type":"npu",
              "device_representation":"source-defined-int-logical-index",
              "process_groups":{s:{"members":members,"world_size":world,"rank_in_group":0,"backend":b}
                for s,b in (("cpu","gloo"),("device","hccl"))}}
        with patch.object(tp,"consume_class",return_value=qualification()):
            self.assertIs(tp.consume_identity(ident,0),ident)
            ident["groups"]["tp"]["process_groups"]["device"]["backend"]="nccl"
            with self.assertRaises(ValueError):tp.consume_identity(ident,0)
    def test15_latched_failure_and_source_signature(self):
        provider=tp.RankProvider()
        with patch.object(tp,"observe",side_effect=ValueError("first real refusal")):
            with self.assertRaises(ValueError):provider()
        with patch.object(tp,"observe")as observe:
            with self.assertRaises(ValueError):provider()
            observe.assert_not_called()
        self.assertIn("native_group_class",[n.value for n in ast.walk(node(own("tp_provider_current.py"),"RankProvider"))if isinstance(n,ast.Constant)])
    def test16_no_group_init_or_collective_in_N1_observer(self):
        fn=node(own("tp_provider_current.py"),"preweights")
        calls=[ast.unparse(n.func)for n in ast.walk(fn)if isinstance(n,ast.Call)]
        for bad in ("cls","dist.init_process_group","torch.distributed.init_process_group","torch.distributed.new_group"):
            self.assertNotIn(bad,calls)
        self.assertIn("object.__new__",calls);self.assertIn("cls._init_device_communicator",calls)
def main(argv=None):
    global REVIEW
    p=argparse.ArgumentParser();p.add_argument("--review-native-root",type=Path);a=p.parse_args(argv)
    REVIEW=a.review_native_root
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(NativeTP))
    return 0 if result.wasSuccessful()else 1
if __name__=="__main__":sys.exit(main())
