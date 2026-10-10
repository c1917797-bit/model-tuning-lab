"""Bounded stdlib regression, fixture scope only; no Torch/NPU/capture/fit PASS."""
import ast,copy,hashlib,importlib.util,json,struct,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import writer_contract as C
import writer_inputs as I
import writer_byte_oracle as O
import writer_numeric as N
import writer_consume as R
DONOR=Path("C:/Users/Huawei/AppData/Local/Temp/c154-skvq-writer-source")
REMOTE=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-writer-v1-004/source/qwen36_skvq_writer")
DONOR_ROWS={"numeric.py":(1337,"2a666a76cff034ab9676503d10f6eba496b055ca776cdd1979b0287f1dd48ed0"),
 "codec.py":(3129,"ca92a69fa1fc698f4ab2d95aa30673e40c223b3b8b8f018c8283e9c6f93a17cb")}
def candidate_fixture():
    """Original scalar candidate is called ONLY by software differential test, not consumer."""
    root=REMOTE if REMOTE.is_dir()else DONOR
    package="_skvq_writer_differential_fixture"
    p=types.ModuleType(package);p.__path__=[str(root)];sys.modules[package]=p
    for file,(size,sha)in DONOR_ROWS.items():
        path=root/file;raw=path.read_bytes()
        if len(raw)!=size or hashlib.sha256(raw).hexdigest()!=sha:raise ValueError("original candidate fixture source")
        name=package+"."+path.stem;spec=importlib.util.spec_from_file_location(name,path)
        m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m)
    return sys.modules[package+".codec"]
class Layout:
    def __init__(self,value):
        self.permutation=tuple(value["permutation"]);self.starts=tuple(value["starts"])
        self.smooth=tuple(value["smooth"]);self.clip=value["clip"]
    def validate(self):return self
def layout(uneven=False):
    return dict(permutation=list(reversed(range(256))),starts=[0,1,17,111,256]if uneven else[0,64,128,192,256],
      smooth=[1.]*256,clip=.95)
def raw_rows(kind,tokens=4):
    return O.scalar_bytes([O.scalar(((i*17+t*31)%113-56)/19,kind)for t in range(tokens)for i in range(256)],kind)
def axis_fixture(kind="float16",bits=2,uneven=True):
    l=layout(uneven);start,stop,total=1,3,4;blob=raw_rows(kind,total)
    encoded=O.encode_scalar(blob[start*512:stop*512],l,bits,kind);n,widths=O.geometry(l,bits)
    widths={"payload":sum(widths),"scales":4*2,"zero_points":4*2};stored={}
    row=dict(tokens=total,middle=[start,stop],shape=[total,256],
      returned_bytes=(stop-start)*(widths["payload"]+16),before={},after={},input_after_ref="input")
    stored["input"]=blob
    for name,width in widths.items():
        before=bytes([165])*total*width;after=before[:start*width]+encoded[name]+before[stop*width:]
        row["before"][name]="before-"+name;row["after"][name]="after-"+name
        stored["before-"+name]=before;stored["after-"+name]=after
    return l,blob,row,stored
class Tests(unittest.TestCase):
    def test01_original_scalar_candidate_full_q2q4_a16_differential(self):
        candidate=candidate_fixture()
        for kind in("float16","bfloat16"):
            for bits in(2,4):
                for uneven in(False,True):
                    l=layout(uneven);raw=raw_rows(kind);vals=O.values(raw,kind)
                    rows=[vals[i:i+256]for i in range(0,len(vals),256)]
                    expected=O.encode_scalar(raw,l,bits,kind);p=candidate.pack(rows,"K",Layout(l),bits,kind)
                    self.assertEqual(expected,dict(payload=p.payload,scales=p.scales,zero_points=p.zero_points))
    def test02_uneven_group_padding_and_full_guard_success(self):
        for k in("float16","bfloat16"):
            for b in(2,4):
                l,raw,row,store=axis_fixture(k,b)
                checked=O.check_axis(row,raw,l,b,k,store.__getitem__)
                self.assertTrue(checked["exact_payload_scales_zero_points"])
    def test03_payload_scale_zero_each_middle_mutation_rejected(self):
        for name in("payload","scales","zero_points"):
            l,raw,row,store=axis_fixture();key="after-"+name;v=bytearray(store[key]);v[len(v)//2]^=1;store[key]=bytes(v)
            with self.assertRaisesRegex(ValueError,"exact original affine"):O.check_axis(row,raw,l,2,"float16",store.__getitem__)
    def test04_full_sink_recent_guard_each_rejected(self):
        for name in("payload","scales","zero_points"):
            for index in(0,-1):
                l,raw,row,store=axis_fixture();key="after-"+name;v=bytearray(store[key]);v[index]^=1;store[key]=bytes(v)
                with self.assertRaisesRegex(ValueError,"untouched"):O.check_axis(row,raw,l,2,"float16",store.__getitem__)
    def test05_full_original_input_mutation_rejected(self):
        l,raw,row,store=axis_fixture();v=bytearray(raw);v[0]^=1;store["input"]=bytes(v)
        with self.assertRaisesRegex(ValueError,"original inputs unchanged"):O.check_axis(row,raw,l,2,"float16",store.__getitem__)
    def test06_return_bytes_and_incomplete_raw_rejected(self):
        l,raw,row,store=axis_fixture();row["returned_bytes"]+=1
        with self.assertRaisesRegex(ValueError,"writer bytes"):O.check_axis(row,raw,l,2,"float16",store.__getitem__)
        l,raw,row,store=axis_fixture();store["after-scales"]=store["after-scales"][:-1]
        with self.assertRaisesRegex(ValueError,"complete plane"):O.check_axis(row,raw,l,2,"float16",store.__getitem__)
    def test07_bool_and_cross_rank_layout_rejected(self):
        for mutation in("bool","duplicate","empty"):
            v=layout()
            if mutation=="bool":v["permutation"][0]=True
            if mutation=="duplicate":v["permutation"][0]=v["permutation"][1]
            if mutation=="empty":v["starts"]=[0,64,64,128,256]
            with self.assertRaises(ValueError):C.layout(v)
    def test08_nondefault_clip_and_smooth_rejected(self):
        for key,value in(("clip",.91),("smooth",[.9]*256)):
            v=layout();v[key]=value
            with self.assertRaisesRegex(ValueError,"default smoothOFF"):C.layout(v)
    def test09_ref_bytes_bool_extra_sha_rejected(self):
        with tempfile.TemporaryDirectory(prefix="skvq-writer-ref-")as folder:
            path=Path(folder)/"actual.json";path.write_bytes(b'{"actual":true}\n');ref=C.ref(path)
            self.assertEqual(C.obj(ref),dict(actual=True))
            for edit in({"bytes":True},{"origin":"unknown"},{"sha256":"0"*64}):
                bad=dict(ref,**edit)
                with self.assertRaises(ValueError):C.checked(bad)
    def test10_unknown_cached_module_rejected(self):
        with tempfile.TemporaryDirectory(prefix="skvq-writer-module-")as folder:
            path=Path(folder)/"actual.py";path.write_bytes(b"value=3\n")
            row=C.ref(path);name="_skvq_unknown_cache_test";sys.modules[name]=types.ModuleType(name)
            try:
                with self.assertRaisesRegex(ValueError,"cached exact source"):C.module(name,row)
            finally:del sys.modules[name]
    def test11_failed_old_or_fixture_whole_never_reaches_modules(self):
        for status in("FAILED","SOURCE_MATERIALIZED_ONLY","OWNED_CPU_ALL128_CALIBRATION64_CONSUMED"):
            value=dict(schema="skvq.default-tp-local.whole/v1",status=status,source_ref=C.CAPTURE)
            with patch.object(C,"obj",return_value=value),patch.object(I,"calibration_modules")as load:
                with self.assertRaises(ValueError):I.verify_whole({})
                load.assert_not_called()
    def test12_raw_rank_selected64_without_relabelling_all_capture(self):
        data={};refs=[]
        for r in range(4):
            key="rank%d"%r;events=[]
            for sample in range(256):
                for layer in C.LAYERS:
                    e="%d-%d-%s"%(r,sample,layer);events.append(e)
                    data[e]=dict(rank=r,sample_id=sample,logical_layer=layer)
            data[key]=dict(rank=r,status="ALL_RANK_RAW_CAPTURED_NOT_CALIBRATED",events=events);refs.append(key)
        with patch.object(C,"obj",side_effect=data.__getitem__):
            actual=I.records(dict(rank_results=refs));self.assertEqual(len(actual),64)
            data["rank0"]["events"][-1]=data["rank0"]["events"][0]
            with self.assertRaisesRegex(ValueError,"unique complete"):I.records(dict(rank_results=refs))
    def test13_proof_foreign_map_bool_cid_rejected(self):
        source={"path":"source"};plan={"path":"plan"};ref={"path":"raw"}
        base=dict(schema="skvq.actual-writer.owned-device-proof/v1",source_ref=source,input_plan_ref=plan,
          image=C.IMAGE,physical_card=4,logical_device=0,cid="a"*64,host_owned_semantic_consumer_required=True,
          **{k:ref for k in("source_gate_ref","mapping_ref","resource_ref","clock_ref","owned_ref","fresh_canary_ref")})
        base["prior_numpy_ref"]=ref
        prior=dict(schema="skvq.actual-writer.numpy-preflight/v1",status="ACTUAL_NUMPY_SCALAR_BYTES_BITWISE_CHECKED",
          source_ref=source,input_plan_ref=plan,actual_configurations=24,configurations=[{}]*24,no_torch=True,Devices_empty=True,**C.scopes())
        with patch.object(C,"obj",return_value=prior):
            C.device_proof(base,source,plan)
            for edit in({"physical_card":0},{"physical_card":True},{"logical_device":False},{"cid":"a"*63},{"source_ref":plan}):
                with self.assertRaises(ValueError):C.device_proof(dict(base,**edit),source,plan)
    def test14_actual_geometry_and_scope_not_old176_or_fullmodel(self):
        self.assertEqual((C.START,C.STOP,C.STOP-C.START),(5,3968,3963))
        self.assertTrue(all(v is False for v in C.scopes().values()))
        self.assertEqual(C.extent([0,1,2,3,256],2),67)
        self.assertEqual(C.extent([0,1,2,3,256],4),130)
    def test15_complete_compile_ast_and_no_default_native_import(self):
        for file in HERE.glob("*.py"):
            raw=file.read_bytes();compile(raw,str(file),"exec");tree=ast.parse(raw)
            for node in tree.body:
                if isinstance(node,ast.Import):self.assertFalse(any(x.name in("torch","torch_npu","numpy")for x in node.names))
                if isinstance(node,ast.ImportFrom):self.assertNotIn(node.module,("torch","torch_npu","numpy"))
        self.assertNotIn("torch",sys.modules);self.assertNotIn("torch_npu",sys.modules)
    def test16_consumer_oracle_never_calls_candidate_critical_math(self):
        tree=ast.parse((HERE/"writer_byte_oracle.py").read_bytes())
        imports=[n for n in ast.walk(tree)if isinstance(n,(ast.Import,ast.ImportFrom))]
        names={x.name for n in imports if isinstance(n,ast.Import)for x in n.names}
        self.assertEqual(names,{"math","struct"})
        consumer=ast.parse((HERE/"writer_consume.py").read_bytes())
        self.assertFalse(any(isinstance(n,ast.Attribute)and n.attr in("seal_into","pack","quantize","reconstruct")for n in ast.walk(consumer)))
    def test17_actual_allocations_qualified_and_overlap_wrong_strides_rejected(self):
        l=layout(True);stride=C.extent(l["starts"],2);value={}
        for i,(name,shape,unit,dtype)in enumerate((("input",[4096,256],2,"torch.bfloat16"),
          ("payload",[4096,stride],1,"torch.uint8"),("scales",[4096,4],2,"torch.bfloat16"),
          ("zero_points",[4096,4],2,"torch.bfloat16"))):
            value[name]=dict(shape=shape,stride=[shape[1],1],dtype=dtype,device="npu:0",
              storage_offset=0,data_ptr=(i+1)*2**24,storage_nbytes=shape[0]*shape[1]*unit)
        R.check_allocations(value,l,2,"bfloat16")
        for key,edit in(("payload",{"data_ptr":value["input"]["data_ptr"]}),
          ("scales",{"stride":[1,4096]}),("input",{"dtype":"torch.float16"}),
          ("zero_points",{"storage_nbytes":1}),("payload",{"device":"npu:1"})):
            bad=copy.deepcopy(value);bad[key].update(edit)
            with self.assertRaises(ValueError):R.check_allocations(bad,l,2,"bfloat16")
def main():
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    return 0 if result.wasSuccessful()else 1
if __name__=="__main__":raise SystemExit(main())
