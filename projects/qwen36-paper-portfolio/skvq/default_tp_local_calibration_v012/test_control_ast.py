"""Actual source/retained JSON regressions, not full-raw or fit authority."""
import ast,copy,hashlib,json,sys,types,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import control_ast as A

def actual(row,local_root):
    path=Path(row["path"])
    if not path.is_file():path=Path(local_root)/path.name
    raw=path.read_bytes()
    if len(raw)!=row["bytes"] or hashlib.sha256(raw).hexdigest()!=row["sha256"]:
        raise ValueError("exact actual source, no substitute")
    return raw

def control_raw():
    return actual(A.CONTROL,"C:/Users/Huawei/AppData/Local/Temp/skvq-preprojection-current72h-20261010-014")

def reader_raw():
    return actual(A.READER,"C:/Users/Huawei/AppData/Local/Temp/skvq-capture014-offline-consumer-20261011-004")

def archive(name,size,sha):
    raw=(HERE/("EVIDENCE_"+name)).read_bytes()
    if len(raw)!=size or hashlib.sha256(raw).hexdigest()!=sha:raise ValueError("exact original archive bytes")
    return json.loads(raw)

def host():
    return archive("DERIVED004_HOST_RESULT.json",22920,"151cb47d83516c844a0b714faf30067b1e5c48d74bd386214f3e1475d4ddb0ff")

def native():
    return types.SimpleNamespace(donor_source_ref=copy.deepcopy(A.CONTROL),
      donor_class_ast_sha256=A.control_proof(control_raw())["native_sha256"])

def actual_guard(raw,Controller,record):
    tree=A.adapt_reader_tree(raw)
    function=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=="consume")
    guard=next(x for x in function.body if isinstance(x,ast.Expr) and isinstance(x.value,ast.Call)
      and len(x.value.args)==2 and isinstance(x.value.args[1],ast.Constant)
      and x.value.args[1].value=="original immutable Control AST safety inherited, not old algorithm PASS")
    scope={"D":types.SimpleNamespace(need=A.need),"Controller":Controller,"host":record,
      "_strict_legacy_control_digest":lambda c:A.controller_digest(c,control_raw())}
    exec(compile(ast.Module(body=[guard],type_ignores=[]),A.READER["path"],"exec"),scope)

class Compatibility(unittest.TestCase):
    def test01_actual_host39_record_equals_strict_projection(self):
        p=A.control_proof(control_raw());self.assertEqual(p["legacy_sha256"],host()["exact_original_control_class_ast_sha256"])
        self.assertEqual(p["empty_type_params"],16 if sys.version_info[:2]==(3,12) else 0)
    def test02_projection_does_not_mutate_execution_tree(self):
        n=ast.parse(control_raw()).body;node=next(x for x in n if isinstance(x,ast.ClassDef) and x.name=="Control")
        before=ast.dump(node,include_attributes=True);A.project(node)
        self.assertEqual(ast.dump(node,include_attributes=True),before)
    def test03_nonempty_type_params_rejected(self):
        n=ast.parse("def x(): pass").body[0];n._fields=tuple(k for k in n._fields if k!="type_params")+("type_params",);n.type_params=[ast.Name(id="T",ctx=ast.Load())]
        with self.assertRaises(ValueError):A.project(n)
    def test04_unknown_owner_type_params_rejected(self):
        n=ast.Name(id="x",ctx=ast.Load());n._fields+=("type_params",);n.type_params=[]
        with self.assertRaises(ValueError):A.project(n)
    def test05_mutated_original_source_rejected(self):
        with self.assertRaises(ValueError):A.control_digest(control_raw()+b"\n")
    def test06_non_type_params_structure_not_normalized(self):
        n=ast.parse(control_raw());node=next(x for x in n.body if isinstance(x,ast.ClassDef) and x.name=="Control")
        changed=copy.deepcopy(node);changed.name="Changed"
        self.assertNotEqual(A.digest(A.project(changed)),A.CONTROL_39)
    def test07_original_controller_digest_checked_before_projection(self):
        self.assertEqual(A.controller_digest(native(),control_raw()),A.CONTROL_39)
    def test08_wrong_controller_native_hash_rejected(self):
        c=native();c.donor_class_ast_sha256="0"*64
        with self.assertRaises(ValueError):A.controller_digest(c,control_raw())
    def test09_wrong_control_ref_rejected(self):
        c=native();c.donor_source_ref["path"]+=".alias"
        with self.assertRaises(ValueError):A.controller_digest(c,control_raw())
    def test10_complete_real_reader_only_one_expression_changed(self):
        raw=reader_raw();tree=A.adapt_reader_tree(raw)
        class Revert(ast.NodeTransformer):
            count=0
            def visit_Call(self,node):
                if isinstance(node.func,ast.Name) and node.func.id=="_strict_legacy_control_digest":
                    self.count+=1;return ast.Attribute(value=ast.Name(id="Controller",ctx=ast.Load()),attr="donor_class_ast_sha256",ctx=ast.Load())
                return self.generic_visit(node)
        reverse=Revert();restored=reverse.visit(tree)
        self.assertEqual(reverse.count,1);self.assertEqual(ast.dump(restored,include_attributes=False),ast.dump(ast.parse(raw),include_attributes=False))
    def test11_wrong_original_reader_bytes_rejected(self):
        with self.assertRaises(ValueError):A.adapt_reader_tree(reader_raw()+b"\n")
    def test12_actual_full_consumer_guard_and_host_original(self):
        actual_guard(reader_raw(),native(),host())
        if sys.version_info[:2]==(3,12):self.assertNotEqual(native().donor_class_ast_sha256,host()["exact_original_control_class_ast_sha256"])
    def test13_actual_host_hash_mutation_still_rejected(self):
        record=host();record["exact_original_control_class_ast_sha256"]="0"*64
        with self.assertRaises(ValueError):actual_guard(reader_raw(),native(),record)
    def test14_actual_failed_cal010_not_promoted(self):
        old=archive("CAL010_HOST_RESULT.json",23338,"24b9c9466934b435c9ca8f4c251c0f840ca0bb43adba6cf5d71fd5635d0d54c1")
        self.assertIsNotNone(old["primary"]);self.assertEqual(old["exact_original_control_class_ast_sha256"],A.CONTROL_39)
        whole=archive("DERIVED004_DERIVED_WHOLE.json",3556,"3e0ad278a807703c6db30a6243e352d015fe401a9e71aecd1952b2317e7a0e4d")
        self.assertTrue(whole["original_failed_whole_preserved"]);self.assertFalse(whole["original_failed_whole_succeeded"])
        self.assertEqual(whole["host_result_ref"]["sha256"],"151cb47d83516c844a0b714faf30067b1e5c48d74bd386214f3e1475d4ddb0ff")
    def test15_source_exact_author_body_legacy_digest(self):
        bundle=json.loads((HERE/"author_sources.json").read_bytes());raw=next(x["text"].encode() for x in bundle["files"] if x["name"]=="calibration.py")
        self.assertEqual(A.author_digest(raw),A.AUTHOR_39)
        with self.assertRaises(ValueError):A.author_digest(raw+b"\n")
    def test16_author_compile_execution_tree_not_projected(self):
        text=(HERE/"cluster_producer.py").read_text();tree=ast.parse(text)
        fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=="extract")
        self.assertIn('compile(ast.Module(body=[node],type_ignores=[])',ast.get_source_segment(text,fn))
        self.assertNotIn('project(node)',ast.get_source_segment(text,fn))
    def test17_producer_and_consumer_use_same_source_bound_author_digest(self):
        for name in ("cluster_producer.py","consume.py"):
            text=(HERE/name).read_text();self.assertIn('author_digest(',text)
        self.assertNotIn('ast.dump(node,include_attributes=False)',(HERE/"consume.py").read_text())
    def test18_current_cpu_class_safety_body_unchanged(self):
        import test_cpu_host as T
        c=T.cls();self.assertEqual(c.donor_class_ast_sha256,A.CONTROL_39)
        self.assertEqual(c.__mro__[1].validate.__code__.co_filename,T.real_donor()["path"])

def main():
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Compatibility))
    return 0 if result.wasSuccessful() else 1
if __name__=="__main__":raise SystemExit(main())
