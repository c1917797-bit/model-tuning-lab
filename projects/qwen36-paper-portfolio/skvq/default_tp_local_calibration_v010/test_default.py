"""Local stdlib-only cross-module regressions; no library/native calibration PASS.
The named Torch zip fixture only constructs an original serialization grammar.
It is never imported as a runtime binding or fed to any NPU admission.
"""
import ast,copy,hashlib,importlib.util,io,json,os,pickle,struct,subprocess,sys,tempfile,types,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import common as C
import calibration_inputs as I
import cluster_oracle as O
import cluster_producer as P
import consume as R
import torch_zip_int64 as Z
WRITER_LOCAL=Path("C:/Users/Huawei/AppData/Local/Temp/c150-independent-backup/skvq-writer-v1-004/source/qwen36_skvq_writer/calibration.py")
def load_writer():
    path=Path(C.WRITER_CALIBRATION["path"])
    if not path.is_file():path=WRITER_LOCAL
    raw=path.read_bytes()
    if len(raw)!=C.WRITER_CALIBRATION["bytes"]or hashlib.sha256(raw).hexdigest()!=C.WRITER_CALIBRATION["sha256"]:
        raise ValueError("immutable actual writer bytes")
    name="_skvq_calibration_local_actual_writer";spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module
def global_features():
    return {l:dict(min=[-float(i+1)for i in range(1024)],max=[float(i+2)for i in range(1024)])for l in C.LAYERS}
def row():
    labels=[i//64 for i in range(256)]
    return dict(labels=labels,centers=[[float(g),float(g)]for g in range(4)],permutation=list(range(256)),cluster_st_inds=[0,64,128,192,256])
def zip_fixture():
    # The fake globals are only a Pickler grammar witness; the independent Safe
    # reader reconstructs allowed storage/tensor structures without those modules.
    module=types.ModuleType("torch");utils=types.ModuleType("torch._utils")
    storage_type=type("LongStorage",(),{});storage_type.__module__="torch";module.LongStorage=storage_type
    def rebuild(*args):raise AssertionError("fixture rebuild must not execute")
    rebuild.__name__=rebuild.__qualname__="_rebuild_tensor_v2";rebuild.__module__="torch._utils";utils._rebuild_tensor_v2=rebuild
    class Stored:
        def __init__(self,key,values):self.key=key;self.values=values
    class Tensor:
        def __init__(self,storage):self.storage=storage
        def __reduce__(self):return rebuild,(self.storage,0,(len(self.storage.values),),(1,),False,None)
    stores={}
    def tensor(key,values):
        stores[key]=Stored(key,values);return Tensor(stores[key])
    original=dict(reorder_indices=[(tensor("0",list(range(256))),tensor("1",list(range(256))))],
      cluster_st_inds=[(tensor("2",[0,64,128,192,256]),tensor("3",[0,64,128,192,256]))])
    class Pickler(pickle.Pickler):
        def persistent_id(self,obj):
            if type(obj)is Stored:return("storage",storage_type,obj.key,"cpu",len(obj.values))
            return None
    pickled=io.BytesIO()
    with patch.dict(sys.modules,{"torch":module,"torch._utils":utils}):
        Pickler(pickled,protocol=2).dump(original)
    result=io.BytesIO()
    with zipfile.ZipFile(result,"w",compression=zipfile.ZIP_STORED)as z:
        z.writestr("archive/data.pkl",pickled.getvalue());z.writestr("archive/byteorder",b"little")
        for key,value in stores.items():z.writestr("archive/data/"+key,struct.pack("<"+"q"*len(value.values),*value.values))
    return result.getvalue()
class Default(unittest.TestCase):
    def test01_all_actual_own_python_compile_and_six_original_raw_identities(self):
        for f in HERE.glob("*.py"):compile(f.read_bytes(),str(f),"exec")
        value=json.loads((HERE/"author_sources.json").read_bytes())
        self.assertEqual(value["commit"],"fdfc7ec315c16293f68dd771850b47f5199787fc")
        self.assertEqual({r["name"]for r in value["files"]},{"calibration.py","KV_process.py","KVcache_manager.py","calib_config.py","README.md","LICENSE"})
        for r in value["files"]:
            b=r["text"].encode();self.assertEqual(len(b),r["bytes"]);self.assertEqual(hashlib.sha256(b).hexdigest(),r["sha256"])
    def test02_actual_global1024_to_all4_local256_preserves_whole_range(self):
        values=global_features();whole=I.features(values)
        for rank in range(4):
            local=I.split_rank(whole,rank)
            for layer in C.LAYERS:
                self.assertEqual(local[layer]["feature_shape"],[256,2])
                self.assertEqual(local[layer]["min"],values[layer]["min"][rank*256:(rank+1)*256])
                self.assertEqual(local[layer]["max"],values[layer]["max"][rank*256:(rank+1)*256])
        for layer in C.LAYERS:
            self.assertEqual(sum((I.split_rank(whole,r)[layer]["min"]for r in range(4)),[]),values[layer]["min"])
    def test03_missing_nonfinite_inverted_and_bool_extrema_reject(self):
        for mode in("missing","nan","inverted","bool","short"):
            value=global_features();l=C.LAYERS[0]
            if mode=="missing":del value[l]
            elif mode=="nan":value[l]["min"][3]=float("nan")
            elif mode=="inverted":value[l]["min"][3]=99.
            elif mode=="bool":value[l]["min"][3]=False
            else:value[l]["max"].pop()
            with self.subTest(mode=mode),self.assertRaises(ValueError):I.features(value)
        with self.assertRaises(ValueError):I.split_rank(global_features(),True)
    def test04_explicit_original_FP16_and_named_BF16_exact_CPU32_only(self):
        self.assertEqual(C.feature_dtype("torch.float16","original"),"torch.float16")
        self.assertEqual(C.feature_dtype("torch.bfloat16","bf16-exact-cpu32"),"torch.float32")
        for args in(("torch.bfloat16","original"),("torch.float16","bf16-exact-cpu32"),("torch.float32","original")):
            with self.assertRaises(ValueError):C.feature_dtype(*args)
    def test05_independent_all256_label_permutation_and_cuts(self):
        result=O.validate([[float(i//64),float(i//64)]for i in range(256)],row(),4)
        self.assertEqual(result["counts"],[64]*4);self.assertEqual(result["all_channel_mapping_checked"],256)
        self.assertEqual(result["fp64_nearest_center_disagreements"],[])
    def test06_independent_mapping_rejects_duplicate_bool_wrong_cuts_and_empty(self):
        for mode in("duplicate","bool","cuts","empty","label"):
            r=row()
            if mode=="duplicate":r["permutation"][1]=r["permutation"][0]
            elif mode=="bool":r["labels"][0]=True
            elif mode=="cuts":r["cluster_st_inds"]=[0,63,128,192,256]
            elif mode=="empty":r["labels"]=[0]*256
            else:r["permutation"][0],r["permutation"][65]=r["permutation"][65],r["permutation"][0]
            with self.assertRaises(ValueError):O.validate([[0.,0.]]*256,r,4)
    def test07_original_torch_zip_grammar_is_independently_decoded_without_Torch(self):
        b=zip_fixture();value=Z.parse_bytes(b)
        self.assertEqual(value["reorder_indices"][0][0]["storage_int64"],list(range(256)))
        self.assertEqual(value["cluster_st_inds"][0][1]["storage_int64"],[0,64,128,192,256])
        self.assertNotIn("torch",sys.modules)
    def test08_torch_zip_forbidden_global_traversal_endian_and_oversize_reject(self):
        for mode in("global","traversal","endian","size"):
            target=io.BytesIO()
            with zipfile.ZipFile(target,"w")as z:
                z.writestr("archive/byteorder",b"big"if mode=="endian"else b"little")
                z.writestr("archive/data.pkl",b"cos\nsystem\n."if mode=="global"else b"N.")
                if mode=="traversal":z.writestr("archive/../escape",b"x")
            raw=target.getvalue()
            if mode=="size":raw=b"x"*(4*1024*1024+1)
            with self.subTest(mode=mode),self.assertRaises(ValueError):Z.parse_bytes(raw)
    def test09_actual_author_AST_body_only_not_teacher_or_smooth_function(self):
        bundle=json.loads((HERE/"author_sources.json").read_bytes());raw=next(x for x in bundle["files"]if x["name"]=="calibration.py")
        with tempfile.TemporaryDirectory()as tmp:
            path=Path(tmp)/"calibration.py";path.write_bytes(raw["text"].encode());ref=C.reference(path)
            fn,info=P.extract(ref,types.SimpleNamespace(Tensor=object),object())
            node=next(n for n in ast.parse(raw["text"]).body if isinstance(n,ast.FunctionDef)and n.name=="get_reorder_indices")
            self.assertEqual(info["ast_sha256"],hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest())
            self.assertEqual(fn.__code__.co_name,"get_reorder_indices")
            self.assertTrue(info["function_body_unmodified"]);self.assertFalse(info["other_author_functions_imported_or_called"])
    def test10_real_writer_loader_cross_module_named_TP_artifact(self):
        module=load_writer();bundle=dict(capture_producer_ref=dict(path="/fixture/capture",bytes=1,sha256="a"*64),
            model_identity=dict(model_sha256="b"*64),host_result_ref=dict(path="/fixture/host",bytes=1,sha256="c"*64))
        packet=dict(path="/fixture/SOURCE_MANIFEST",bytes=1,sha256="d"*64)
        for rank in range(4):
            axis={s:dict(global_permutation=list(range(rank*256,(rank+1)*256)),starts=[0,64,128,192,256],smooth=[1.]*256,unified_clip=.95)for s in("K","V")}
            value=R.artifact(bundle,packet,packet,packet,module.AUTHOR_COMMIT,rank,C.LAYERS[0],axis)
            with tempfile.TemporaryDirectory()as tmp:
                p=Path(tmp)/"actual.json";p.write_text(json.dumps(value));ref=C.reference(p)
                with patch.object(C,"writer_calibration",return_value=module):
                    result=R.consume_writer_artifact(ref,bundle=bundle,rank=rank,layer=C.LAYERS[0])
                self.assertTrue(result["actual_original_writer_loader_executed"]);self.assertFalse(result["native_writer_executed"])
                for layout in result["axes"].values():self.assertEqual(layout["clip"],.95);self.assertEqual(layout["smooth"],[1.]*256)
    def test11_real_writer_loader_rejects_crossrank_and_clip_mutation(self):
        module=load_writer();bundle=dict(capture_producer_ref=dict(path="/fixture/capture",bytes=1,sha256="a"*64),model_identity=dict(model_sha256="b"*64),host_result_ref={})
        packet=dict(path="/fixture/MF",bytes=1,sha256="d"*64)
        axis={s:dict(global_permutation=list(range(256)),starts=[0,64,128,192,256],smooth=[1.]*256,unified_clip=.95)for s in("K","V")}
        value=R.artifact(bundle,packet,packet,packet,module.AUTHOR_COMMIT,0,C.LAYERS[0],axis)
        for mode in("crossrank","clip","native-claim","smooth"):
            bad=copy.deepcopy(value)
            if mode=="crossrank":bad["K"]["global_permutation"][0]=256
            elif mode=="clip":bad["K"]["unified_clip"]=.94
            elif mode=="native-claim":bad["native_ready"]=True
            else:bad["smooth_enabled"]=True
            with tempfile.TemporaryDirectory()as tmp:
                path=Path(tmp)/"bad.json";path.write_text(json.dumps(bad));ref=C.reference(path)
                with patch.object(C,"writer_calibration",return_value=module),self.assertRaises(ValueError):
                    R.consume_writer_artifact(ref,bundle=bundle,rank=0,layer=C.LAYERS[0])
    def test12_old_failed_whole_CPUonly_and_partial_capture_never_upgrade(self):
        base=dict(schema="skvq.current72h.preprojection.whole/v1",status="FULL_CAPTURE_PREPROJECTION_ORIGINAL_CONSUMED_NOT_CALIBRATED",
            source_ref=C.CAPTURE,whole_capture_consumed=True,actual_capture_only=True,native_ready=False,model_ready=False)
        for field,value in(("status","FAILED"),("source_ref",dict(C.CAPTURE,sha256="0"*64)),("whole_capture_consumed",False),("native_ready",True)):
            wrong=dict(base,**{field:value})
            with patch.object(I,"bound",return_value=wrong),patch.object(I,"donor",side_effect=AssertionError("must reject before donor")):
                with self.assertRaises(ValueError):I.inputs({})
    def test13_current_capture014_pins_and_fixedcutoff_not_old_failure_authority(self):
        self.assertTrue(C.CAPTURE["path"].endswith("skvq-preprojection-current72h-v1-014/SOURCE_MANIFEST.json"))
        self.assertEqual(C.CAPTURE["sha256"],"9c7b1118b1cd1f2a20ab7fde0ecb98031bf14289c9c795c18f48de9cdb805acd")
        self.assertEqual(C.CUT,1791788425)
        body=(HERE/"calibration_inputs.py").read_text();self.assertIn('precheck(whole_ref)',body)
        self.assertEqual(C.DERIVED["sha256"],"f843ee6bd7b5e90cfc6066600f4e2177860fe310eaa8f8e1cdeff5fb6d6d26d2")
    def test14_clean_default_OFF_producer_and_consumer_do_not_import_or_create(self):
        for name in("cluster_producer.py","consume.py","library_probe.py"):
            value=subprocess.run([sys.executable,"-I","-B",str(HERE/name)],capture_output=True,text=True,timeout=5)
            self.assertEqual(value.returncode,0,value.stderr);result=json.loads(value.stdout)
            self.assertIs(result["default_enabled"],False);self.assertIs(result["native_ready"],False)
        self.assertNotIn("torch",sys.modules);self.assertNotIn("torch_npu",sys.modules)
    def test15_production_fit_preserves_author_args_RNG_and_raw_before_fit(self):
        text=(HERE/"cluster_producer.py").read_text()
        self.assertIn('self.inner=KMeans(*a,**kw)',text);self.assertIn('kw=={"n_init":10}',text)
        self.assertLess(text.index('pre=publish(stage/"RAW_PRE.json"'),text.index("fitted=self.inner.fit(x)"))
        self.assertEqual(text.count("torch.set_num_interop_threads(1)"),1)
        self.assertNotIn("np.random.seed(",text);self.assertNotIn("random_state=",text)
        self.assertIn("actual_threadpools",text);self.assertIn("permutation",text)
        consumer=(HERE/"consume.py").read_text();self.assertIn("decode(pt",consumer)
        self.assertIn('parameters["random_state"]is None',consumer);self.assertIn("consume_writer_artifact(ar",consumer)
        self.assertIn("len(artifacts)==len(writer_handoffs)==64",consumer)
    def test16_real_library_seam_required_in_fresh_child_before_any_fit(self):
        text=(HERE/"cluster_producer.py").read_text();consumer=(HERE/"consume.py").read_text()
        self.assertIn('--library-ref-json',text)
        self.assertLess(text.index('dependency=verify(library_ref,packet_ref)'),text.index('import torch,numpy'))
        self.assertIn('match_loaded(dependency)',text)
        self.assertIn('actual_library_probe_ref',text);self.assertIn('actual_library_probe_ref',consumer)
        probe=(HERE/"library_probe.py").read_text()
        self.assertIn('TORCH_DEVICE_BACKEND_AUTOLOAD',probe);self.assertIn('C.cpu_only()',probe)
        self.assertIn('actual_sklearn_KMeans',probe);self.assertNotIn('import torch_npu',probe)
    def test17_actual_library_gate_rejects_model_authority_or_missing_sources(self):
        import library_probe as L
        from test_module_snapshots import fixture,publish
        with tempfile.TemporaryDirectory()as tmp,fixture(tmp)as(root,packet,original,ref,paths,reader):
            self.assertEqual(L.verify(ref,packet),original)
            for field,value in(('model_ready',True),('NPU_initialized',True),('Devices_empty',False),('actual_modules',{}),('actual_cpu_threads',dict(intra=2,interop=1))):
                bad=dict(original,**{field:value})
                changed=publish(root/"library"/("LIBRARY_BAD-"+field+".json"),bad)
                with self.assertRaises(ValueError):L.verify(changed,packet)
    def test18_actual_current_capture_complete_closure_and_all_three_donor_pins(self):
        manifest=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
        self.assertEqual(manifest["capture_source_ref"],C.CAPTURE)
        deps={x["path"]:x for x in manifest["dependencies"]}
        for filename,want in manifest["capture_source_bindings"].items():
            self.assertEqual(want,deps[want["path"]])
            self.assertEqual(C.CAPTURE_BINDINGS[filename],want)
            self.assertEqual(Path(want["path"]).parent,Path(C.CAPTURE["path"]).parent)
        self.assertEqual(set(manifest["capture_source_bindings"]),set(C.CAPTURE_BINDINGS))
        self.assertEqual(deps[C.CAPTURE["path"]],C.CAPTURE)
        self.assertFalse(any("skvq-preprojection-current72h-v1-007/"in p for p in deps))
        entry=json.loads((HERE/"ENTRY.json").read_bytes())
        self.assertEqual(entry["prerequisite"]["capture_source"],C.CAPTURE)
    def test19_old007_source_whole_and_new_source_only_still_refused_before_any_donor(self):
        base=dict(schema="skvq.current72h.preprojection.whole/v1",status="FULL_CAPTURE_PREPROJECTION_ORIGINAL_CONSUMED_NOT_CALIBRATED",
          source_ref=C.CAPTURE,whole_capture_consumed=True,actual_capture_only=True,native_ready=False,model_ready=False)
        cases=[dict(base,source_ref=dict(C.CAPTURE,path="/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-preprojection-current72h-v1-007/SOURCE_MANIFEST.json")),
          dict(base,source_ref={"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-preprojection-current72h-v1-011/SOURCE_MANIFEST.json","bytes":70555,"sha256":"9b28ccde647d5cdc702bac17af35a6723b30714956375ebd2f62244ad812af70"}),
           dict(base,status="FAILED"),dict(base,whole_capture_consumed=False),dict(base,actual_capture_only=False)]
        for value in cases:
            with patch.object(I,"bound",return_value=value),patch.object(I,"donor",side_effect=AssertionError("old/partial must fail before donor")):
                with self.assertRaises(ValueError):I.inputs({})
    def test20_actual_guest_mount_root_exists_but_only_new_children_are_created(self):
        entry=json.loads((HERE/"ENTRY.json").read_bytes())
        with tempfile.TemporaryDirectory()as tmp:
            parent=Path(tmp).absolute();declared=parent/"source";declared.mkdir()
            host=parent/Path(entry["cpu_workload"]["output"]).parent.name;host.mkdir();stage=host/"work";stage.mkdir()
            with patch.object(C,"ROOT",declared):
                self.assertEqual(C.stage_root(stage),stage)
                child=C.output_root(stage/"library");self.assertTrue(child.is_dir())
                with self.assertRaises(ValueError):C.output_root(child)
                with self.assertRaises(ValueError):C.output_root(stage)
                with self.assertRaises(ValueError):C.output_root(stage/"source")
                old=parent/"run-skvq-default-tp-local-001-negative";old.mkdir()
                with self.assertRaises(ValueError):C.output_root(old/"producer")
        self.assertNotIn("torch",sys.modules);self.assertNotIn("torch_npu",sys.modules)
    def test21_actual_aggregate_child_argv_all_current_sources_and_one_guest_RW_root(self):
        import cpu_entry as E
        entry=json.loads((HERE/"ENTRY.json").read_bytes());stage=Path(entry["cpu_workload"]["output"])
        rows=E.plans(entry["source"],Path(entry["prerequisite"]["actual_successful_capture_whole_ref_json"]),stage,"bf16-exact-cpu32")
        self.assertEqual([r[0]for r in rows],["LIBRARY","PRODUCER","INDEPENDENT"])
        for label,argv,result in rows:
            self.assertEqual(argv[:3],[sys.executable,"-I","-B"])
            self.assertEqual(argv[argv.index("--source-manifest-sha256")+1],entry["source"]["sha256"])
            self.assertIn(Path(argv[3]).name,("library_probe.py","cluster_producer.py","consume.py"))
            self.assertIn(stage,result.parents)
        self.assertEqual(rows[1][1][rows[1][1].index("--library-ref-json")+1],str(stage/"LIBRARY_REF.json"))
        self.assertEqual(rows[2][1][rows[2][1].index("--root")+1],str(stage/"producer"))
        self.assertEqual(entry["source"]["path"],(C.ROOT/"SOURCE_MANIFEST.json").as_posix())
    def test22_actual_child_body_retains_failure_stdio_and_never_uses_success_fixture(self):
        import cpu_entry as E
        with tempfile.TemporaryDirectory()as tmp:
            stage=Path(tmp).absolute();seen=[]
            atomic=types.SimpleNamespace(publish_bytes=lambda p,b:seen.append((p.name,b))or dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
            def publish(p,v):seen.append((p.name,copy.deepcopy(v)));return dict(path=str(p),bytes=1,sha256="a"*64)
            value=types.SimpleNamespace(stdout=b"actual original failed stdout",stderr=b"actual failure",returncode=7)
            with patch.object(C,"atomic",return_value=atomic),patch.object(C,"publish",side_effect=publish),patch.object(E.subprocess,"run",return_value=value):
                with self.assertRaisesRegex(ValueError,"actual fresh CPU child failed"):E.child("PRODUCER",["real-argv"],stage/"missing.json",stage,E.time.monotonic()+5,{})
            self.assertEqual(seen[0][1],b"actual original failed stdout");self.assertEqual(seen[1][1],b"actual failure")
            self.assertEqual(seen[2][1]["exit_code"],7);self.assertFalse(seen[2][1]["timed_out"])
    def test23_actual_aggregate_default_OFF_and_failed_whole_blocks_before_fitting(self):
        import cpu_entry as E
        r=subprocess.run([sys.executable,"-I","-B",str(HERE/"cpu_entry.py")],capture_output=True,text=True,timeout=5)
        self.assertEqual(r.returncode,0,r.stderr);self.assertFalse(json.loads(r.stdout)["default_enabled"])
        source=dict(path="/fixture/manifest",bytes=1,sha256="a"*64)
        with tempfile.TemporaryDirectory()as tmp:
            ref=Path(tmp)/"WHOLE_REF.json";ref.write_text(json.dumps({"source":"failed007"}))
            env={k:"1"for k in("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS","NUMEXPR_NUM_THREADS")}
            env["TORCH_DEVICE_BACKEND_AUTOLOAD"]="0"
            with patch.dict(os.environ,env),patch.object(C,"source",return_value=source),patch.object(C,"cpu_only"),patch.object(I,"inputs",side_effect=ValueError("failed010 whole")),patch.object(E,"child",side_effect=AssertionError("must not run")):
                with self.assertRaisesRegex(ValueError,"failed010 whole"):E.run(source["sha256"],ref,Path(tmp)/"not-created","bf16-exact-cpu32")
            self.assertFalse((Path(tmp)/"not-created").exists())
def main():
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Default));return 0 if r.wasSuccessful()else 1
if __name__=="__main__":raise SystemExit(main())
