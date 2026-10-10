"""Actual source-policy/producer/independent-consumer regression; no Torch/NPU.
Positive enum/getter objects are named fixtures only, not a runtime admission.
"""
import ast,copy,hashlib,importlib.util,json,sys,tempfile,unittest
from enum import IntEnum
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import current_contract as C
import n1_format as F
def donor_policy():
    remote=Path(F.POLICY["path"])
    local=Path("C:/Users/Huawei/AppData/Local/Packages/sandbox.{48fdcea7-5947-498c-a068-4bc4cdaddb04}/AC/Temp/kivi-c132-reviewed-source/model-deps/format_policy.py")
    path=remote if remote.is_file()else local
    raw=path.read_bytes()
    if len(raw)!=F.POLICY["bytes"]or hashlib.sha256(raw).hexdigest()!=F.POLICY["sha256"]:
        raise ValueError("exact immutable original enum policy")
    spec=importlib.util.spec_from_file_location("_skvq_n1_software_policy",path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
P=donor_policy()
class Format(IntEnum):ND=2;NZ=29
Format.__module__="torch_npu.npu._format"
class Foreign(IntEnum):ND=2
SOURCE=dict(path="/actual/current/SOURCE_MANIFEST.json",bytes=123,sha256="a"*64)
IDENTITY=dict(pid=123,start_ticks=456,cgroup="0::/docker/fixture",argv=["fixture"],cmdline_sha256="b"*64)
def qualification():
    chain={n:dict(path="/archive/"+n+".py",bytes=865 if n=="format"else 1,sha256=h)for n,h in P.CHAIN.items()}
    origin=dict(path="/actual-image/torch_npu/npu/_format.py",bytes=865,sha256=P.FORMAT_SHA)
    return dict(policy_ref=F.POLICY,
      binding=dict(module="torch_npu",attribute="get_npu_format",runtime_path=origin["path"],archive_ref=chain["format"],patch_chain=chain),
      observation=dict(wrapper_origin=origin,enum_origin=origin,original_op_repr="fixture original packet",
        original_op_type="fixture.packet",original_schemas={"":"fixture schema"},compiled_schema_independently_consumed=False,device_correctness_checked=False))
class Tests(unittest.TestCase):
    def capture(self,actual,value):
        saved=[]
        def publish(path,obj):
            saved.append(copy.deepcopy(obj));return dict(path=str(path),bytes=1,sha256="c"*64)
        with patch.object(F,"policy",return_value=P):
            serial,ref=F.observe_then_check(actual,value,Format,rank=0,source=SOURCE,identity=IDENTITY,after_identity=IDENTITY,
              qualification=qualification(),destination=Path("/actual/RAW.json"),publish=publish)
        return saved[0],serial,ref
    def test01_original_policy_positive_enum_producer_to_independent_consumer(self):
        raw,serial,ref=self.capture([4.,5.],Format.ND)
        self.assertEqual(raw["format"]["actual_type"],P.FORMAT_TYPE)
        checked=[]
        with patch.object(F,"policy",return_value=P),patch.object(C,"checked",side_effect=lambda r:checked.append(r)or r):
            self.assertEqual(F.consume_raw(raw,serial,rank=0,source=SOURCE,identity=IDENTITY,after_identity=IDENTITY),raw)
        self.assertEqual({r["sha256"]for r in checked},set(P.CHAIN.values()))
        self.assertTrue(raw["recorded_before_qualification_assertions"])
    def test02_exact_native_enum_rejects_builtin_bool_foreign_NZ(self):
        for value in(2,True,Foreign.ND,Format.NZ):
            with self.subTest(value=repr(value)),self.assertRaises(ValueError):
                self.capture([4.,5.],value)
    def test03_raw_persisted_before_arithmetic_failure_not_guessed_format(self):
        saved=[]
        with patch.object(F,"policy",return_value=P),self.assertRaisesRegex(ValueError,"arithmetic"):
            F.observe_then_check([4.,6.],Format.ND,Format,rank=2,source=SOURCE,identity=IDENTITY,after_identity=IDENTITY,
                qualification=qualification(),destination=Path("/actual/RAW.json"),publish=lambda p,v:saved.append(v)or {})
        self.assertEqual(len(saved),1);self.assertEqual(saved[0]["output"],[4.,6.]);self.assertEqual(saved[0]["format"]["enum_member"],"ND")
    def test04_raw_persisted_before_format_failure_and_nonfinite_evidence(self):
        for actual,value in(([4.,5.],2),([float("nan"),5.],Format.ND)):
            saved=[]
            with patch.object(F,"policy",return_value=P),self.assertRaises(ValueError):
                F.observe_then_check(actual,value,Format,rank=0,source=SOURCE,identity=IDENTITY,after_identity=IDENTITY,
                  qualification=qualification(),destination=Path("/actual/RAW.json"),publish=lambda p,v:saved.append(v)or {})
            self.assertEqual(len(saved),1);json.dumps(saved[0],allow_nan=False)
    def test05_independent_raw_rejects_arithmetic_type_source_rank_and_identity_mutations(self):
        raw,serial,_=self.capture([4.,5.],Format.ND)
        mutations=(("output",[4.,6.]),("source_ref",dict(SOURCE,sha256="d"*64)),("rank",1),
            ("after_identity",dict(IDENTITY,start_ticks=457)),("format",dict(raw["format"],actual_type="builtins.int")),
            ("recorded_before_qualification_assertions",False))
        for field,value in mutations:
            bad=copy.deepcopy(raw);bad[field]=value
            with patch.object(F,"policy",return_value=P),patch.object(C,"checked",side_effect=lambda r:r),self.assertRaises(ValueError):
                F.consume_raw(bad,serial,rank=0,source=SOURCE,identity=IDENTITY,after_identity=IDENTITY)
    def test06_full_six_chain_no_legacy_union_and_foreign_origin_rejected(self):
        raw,serial,_=self.capture([4.,5.],Format.ND)
        for mode in("legacy-labels","missing-exports","wrong-sha","origin"):
            bad=copy.deepcopy(raw);q=bad["qualification"]
            if mode=="legacy-labels":q["binding"]["patch_chain"]["manager"]=q["binding"]["patch_chain"].pop("patch_manager")
            elif mode=="missing-exports":del q["binding"]["patch_chain"]["exports"]
            elif mode=="wrong-sha":q["binding"]["patch_chain"]["root"]["sha256"]="d"*64
            else:q["observation"]["wrapper_origin"]["sha256"]="d"*64
            with patch.object(F,"policy",return_value=P),patch.object(C,"checked",side_effect=lambda r:r),self.assertRaises(ValueError):
                F.consume_raw(bad,serial,rank=0,source=SOURCE,identity=IDENTITY,after_identity=IDENTITY)
    def test07_actual_tiny_body_calls_real_getter_and_persists_raw_before_final(self):
        tree=ast.parse((HERE/"n1_check.py").read_bytes());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=="tiny")
        text=ast.unparse(fn)
        self.assertIn("F.qualify",text);self.assertIn("fmt = getter(y)",text)
        self.assertLess(text.index("F.observe_then_check"),text.index("'ACTUAL_TINY_CHECKED'"))
        self.assertNotIn("int(fmt)",text);self.assertNotIn("type(fmt)",text)
        parent=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=="main")
        self.assertIn("consume_row(x, source)",ast.unparse(parent))
        consumer=ast.unparse(ast.parse((HERE/"consume_host.py").read_bytes()))
        self.assertIn("consume_row(nv, source)",consumer)
    def test08_no_host_open_of_container_site_package_and_default_OFF_no_Torch(self):
        raw,serial,_=self.capture([4.,5.],Format.ND)
        checked=[]
        with patch.object(F,"policy",return_value=P),patch.object(C,"checked",side_effect=lambda r:checked.append(r)or r):
            F.consume_raw(raw,serial,rank=0,source=SOURCE,identity=IDENTITY,after_identity=IDENTITY)
        self.assertNotIn("/actual-image/torch_npu/npu/_format.py",[r["path"]for r in checked])
        self.assertNotIn("torch",sys.modules);self.assertNotIn("torch_npu",sys.modules)
def main():
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    return 0 if result.wasSuccessful()else 1
if __name__=="__main__":raise SystemExit(main())
