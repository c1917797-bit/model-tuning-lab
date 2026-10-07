"""SYNTHETIC stdlib protocol fixtures only; no runtime, NPU, or execution authority."""
import ast,contextlib,copy,io,json,sys,unittest
from datetime import datetime,timezone
from pathlib import Path
import entry

NOW=datetime(2026,10,7,12,0,tzinfo=timezone.utc)
BUILD=Path("/cache/cch/qwen36-kvbuffer-parallel-20261006/build-candidate-ub-trace-v2-SYNTHETIC-fixture")
SOURCE_REF={"path":str(entry.BASE/"SOURCE_MANIFEST.json"),"sha256":"f"*64}
def fixture():
    refs={
      "library":{"path":str(BUILD/"build/libqwen36_gdn_kvbuffer_native_order_trace_v2_ops.so"),"sha256":"a"*64},
      "build":{"path":str(BUILD/"build-receipt.json"),"sha256":"b"*64},
      "meta":{"path":str(BUILD/"meta-receipt.json"),"sha256":"c"*64}}
    ops={str(i):"d"*64 for i in range(7)}
    sources={str(i):"e"*64 for i in range(77)}
    commands=[
      {"command":["cmake","-S",str(entry.PROJECT/"operator/candidate_ub_trace_v2"),"-B",str(BUILD/"build"),
       "-DCMAKE_BUILD_TYPE=Release","-DPython3_EXECUTABLE=/usr/local/python3.12.13/bin/python3"],
       "exit_code":0,"stdout":"SYNTHETIC compile fixture","stderr":""},
      {"command":["cmake","--build",str(BUILD/"build"),"--parallel","1"],
       "exit_code":0,"stdout":"SYNTHETIC link fixture","stderr":""}]
    build={"schema":"kvbp.candidate-ub-trace-build/v2","status":"compiled_no_device","npu_executed":False,
      "image_id":entry.IMAGE,"namespace":entry.NAMESPACE,"npu_arch":"dav-2201","sources":ops,
      "sources_before":sources,"sources_after":sources,"library_sha256":refs["library"]["sha256"],
      "commands":commands,"exported_kernel":{"name":entry.SYMBOL,"defined":True,"type":"T"},
      "started_utc":"2026-10-07T11:40:00+00:00","completed_utc":"2026-10-07T11:41:00+00:00"}
    meta={"schema":"kvbp.candidate-ub-trace-meta/v2","status":"actual-load-schema-meta-only",
      "library":refs["library"],"schema_loaded":entry.SCHEMA,"positive_cases":2,
      "negative_cases":[{"argument":i,"shape":s,"dtype":d,"error":"SYNTHETIC rejection fixture"}
                        for i,s,d in entry.EXPECTED_NEGATIVES],
      "mapped_library_lines":["1-2 r-xp 0000 00:00 1 "+refs["library"]["path"]],
      "source_manifest_sha256":SOURCE_REF["sha256"],"npu_executed":False,
      "numeric_verified":False,"serving_ready":False}
    records={
      "command-0.json":commands[0],"command-1.json":commands[1],
      "exports.json":{"command":["nm","-D","--defined-only",refs["library"]["path"]],"exit_code":0,
                      "stdout":"000000001 T "+entry.SYMBOL+"\n","stderr":""},
      "original-meta-child.json":{"command":["/usr/local/python3.12.13/bin/python3","-B",str(entry.BASE/"meta_probe.py"),
       "--library",refs["library"]["path"],"--library-sha256",refs["library"]["sha256"],
       "--output",refs["meta"]["path"]],"exit_code":0,
       "stdout":json.dumps({"meta_receipt":refs["meta"]["path"],"meta_sha256":refs["meta"]["sha256"],
                            "negative_cases":12,"npu_executed":False})+"\n","stderr":""}}
    config={"build_root":str(BUILD),"source_manifest":SOURCE_REF,"namespace":entry.NAMESPACE,"schema":entry.SCHEMA}
    return refs,ops,sources,build,meta,records,config
def validate(f):
    refs,ops,sources,build,meta,records,config=f
    def reader(r):
        if r==refs["build"]:v=build
        elif r==refs["meta"]:v=meta
        elif r==refs["library"]:return b"SYNTHETIC SO identity fixture only"
        else:raise AssertionError("unexpected Ref")
        return json.dumps(v,allow_nan=False).encode()
    def record(path):return json.dumps(records[path.name],allow_nan=False).encode()
    return entry.trace_artifacts(refs,ops,sources,config,reader=reader,record_reader=record,now=NOW)
class EntryContract(unittest.TestCase):
    def test_synthetic_contract_only(self):
        r=validate(fixture())
        self.assertFalse(r["npu_verified"]);self.assertFalse(r["serving_ready"])
        self.assertEqual(len(r["producer_evidence"]),4)
    def test_default_off_imports_no_torch_and_no_source_read(self):
        before=set(sys.modules)
        with contextlib.redirect_stdout(io.StringIO()) as out:entry.main([])
        r=json.loads(out.getvalue());self.assertFalse(r["default_enabled"])
        self.assertFalse(r["npu_executed"]);self.assertNotIn("torch",set(sys.modules)-before)
    def test_incomplete_execute_fails_before_device_import(self):
        before=set(sys.modules)
        with self.assertRaisesRegex(ValueError,"complete MAIN explicit"):entry.main(["--execute"])
        self.assertNotIn("torch",set(sys.modules)-before)
    def test_wrong_schema_or_unexecuted_build_status(self):
        for key,value in [("schema","other"),("status","pending"),("npu_executed",True),
                          ("npu_arch","arch35"),("image_id","other"),("namespace","other")]:
            f=fixture();f[3][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate(f)
    def test_source77_full_identity_and_before_after(self):
        for kind in range(3):
            f=fixture()
            if kind==0:f[2].pop("0")
            elif kind==1:f[3]["sources_after"]=dict(f[2],extra="e"*64)
            else:f[3]["sources"]=dict(f[1],extra="d"*64)
            with self.subTest(kind=kind),self.assertRaises(ValueError):validate(f)
    def test_commands_and_original_command_bytes(self):
        f=fixture();f[3]["commands"][0]["exit_code"]=False
        with self.assertRaises(ValueError):validate(f)
        f=fixture();f[5]["command-1.json"]=dict(f[5]["command-1.json"],stdout="changed")
        with self.assertRaises(ValueError):validate(f)
    def test_defined_export_only(self):
        for change in ("receipt","raw","duplicate"):
            f=fixture()
            if change=="receipt":f[3]["exported_kernel"]["defined"]=False
            elif change=="raw":f[5]["exports.json"]["stdout"]=" U "+entry.SYMBOL+"\n"
            else:f[5]["exports.json"]["stdout"]*=2
            with self.subTest(change=change),self.assertRaises(ValueError):validate(f)
    def test_actual_meta_scope_flags(self):
        for key,value in [("status","pass"),("npu_executed",True),("numeric_verified",True),
                          ("serving_ready",True),("positive_cases",2.0),("schema_loaded","other")]:
            f=fixture();f[4][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate(f)
    def test_all_twelve_meta_negative_shapes(self):
        f=fixture();f[4]["negative_cases"].pop()
        with self.assertRaises(ValueError):validate(f)
        f=fixture();f[4]["negative_cases"][0]["shape"]=[16,4,128]
        with self.assertRaises(ValueError):validate(f)
    def test_maps_exact_not_substring_or_deleted(self):
        for suffix in (" (deleted)","-other"):
            f=fixture();f[4]["mapped_library_lines"][0]+=suffix
            with self.subTest(suffix=suffix),self.assertRaises(ValueError):validate(f)
    def test_meta_actual_child_unique_ref_and_exit(self):
        for kind in range(4):
            f=fixture();c=f[5]["original-meta-child.json"]
            if kind==0:c["exit_code"]=1
            elif kind==1:c["stdout"]*=2
            elif kind==2:c["command"][2]="/other/meta.py"
            else:c["stdout"]=c["stdout"].replace("c"*64,"f"*64)
            with self.subTest(kind=kind),self.assertRaises(ValueError):validate(f)
    def test_exact_build_locations(self):
        f=fixture();f[0]["library"]["path"]="/other/trace.so"
        with self.assertRaises(ValueError):validate(f)
    def test_completed_times_not_future(self):
        f=fixture();f[3]["completed_utc"]="2026-10-08T00:00:00+00:00"
        with self.assertRaises(ValueError):validate(f)
    def test_strict_json_nonfinite_and_duplicate(self):
        for s in ('{"x":1,"x":2}','{"x":NaN}','{"x":Infinity}'):
            with self.subTest(text=s),self.assertRaises(ValueError):entry.strict_json(s)
    def test_actual_source_order_and_frozen_entry(self):
        source=Path(entry.__file__).read_text() if Path(entry.__file__).exists() else entry._TEST_SOURCE
        tree=ast.parse(source)
        main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="main")
        nodes=list(ast.walk(main))
        torch_import=min(n.lineno for n in nodes if isinstance(n,ast.Import) and any(a.name=="torch" for a in n.names))
        artifact=max(n.lineno for n in nodes if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)
                     and n.func.id=="trace_artifacts" and n.lineno<torch_import)
        self.assertLess(artifact,torch_import)
        self.assertIn("c.validate_identity(ident,16,6",source)
        self.assertIn('protocol.diagnostic(torch,helper,old,fixture,production,trace,out,enabled=True',source)
        self.assertNotIn("torch.ops."+entry.NAMESPACE+" =",source)
        self.assertIn("time.sleep(12)",source)
        self.assertIn("if primary is None:raise",source)
if __name__=="__main__":unittest.main()
