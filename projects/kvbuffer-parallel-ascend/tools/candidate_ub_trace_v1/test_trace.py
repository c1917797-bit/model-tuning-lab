#!/usr/bin/env python3
"""Source/ABI contracts, not compiler/device synchronization or numeric evidence."""
import ast,contextlib,hashlib,io,json,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab")
HERE=ROOT/"projects/kvbuffer-parallel-ascend/tools/candidate_ub_trace_v1"
OP=ROOT/"projects/kvbuffer-parallel-ascend/operator/candidate_ub_trace_v1"
OLD=ROOT/"projects/kvbuffer-parallel-ascend/operator/native_order_v2"
def body(text,name):
    start=text.index(" "+name+"(");pos=text.index("{",start);depth=1;end=pos+1
    while depth:
        if text[end]=="{":depth+=1
        elif text[end]=="}":depth-=1
        end+=1
    return text[pos:end]
class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=types.ModuleType("_candidate_trace_protocol_test");cls.p.__file__=str(HERE/"protocol.py")
        exec(compile((HERE/"protocol.py").read_text(),cls.p.__file__,"exec"),cls.p.__dict__)
        cls.k=(OP/"op_kernel/qwen36_gdn_kvbuffer_native_order_trace_v1.h").read_text()
        cls.original=(OLD/"op_kernel/qwen36_gdn_kvbuffer_native_order_v2.h").read_text()
    def test_default_off(self):
        with patch.object(self.p,"source_admission",side_effect=AssertionError("OFF sources")),contextlib.redirect_stdout(io.StringIO()) as out:
            self.p.main([])
        self.assertFalse(json.loads(out.getvalue())["npu_executed"])
    def test_default_off_function(self):
        with self.assertRaisesRegex(ValueError,"default OFF"):
            self.p.diagnostic(None,None,None,None,None,None,Path("/uncreated"))
    def test_exact_trace_bytes(self):self.assertEqual(self.p.TRACE_BYTES,3*32*128*4+32*4+16*4)
    def test_arithmetic_functions_exact(self):
        for n in ("ExpScalar","LoadQK","LoadBeta","MatVecMul","ReduceRows","TreeFold","PrepareLogs",
                  "LoadUTile","ParallelFlush","StoreOutput","StoreBase","StoreULog","StoreKLog"):
            with self.subTest(name=n):self.assertEqual(body(self.k,n),body(self.original,n))
    def test_process_tile_arithmetic_exact(self):
        traced=body(self.k,"ProcessTile")
        for line in ("        if (TraceSelected(token, slot, head, vStart)) TraceState(0);\n",
                     "        if (TraceSelected(token, slot, head, vStart)) TraceState(1);\n",
                     "        if (TraceSelected(token, slot, head, vStart)) TraceState(2);\n",
                     "        if (TraceSelected(token, slot, head, vStart)) TraceReadout();\n"):
            self.assertEqual(traced.count(line),1);traced=traced.replace(line,"")
        self.assertEqual(traced,body(self.original,"ProcessTile"))
    def test_trace_is_copy_only(self):
        text=body(self.k,"TraceCopy");self.assertIn("DataCopy(local, src, elements);",text)
        self.assertIn("traceOutQueue_.EnQue<float>(local)",text)
        self.assertIn("DataCopyPad(dst[offset], local, params)",text)
        for n in ("Muls(","Mul(","Add(","Exp(","Cast("):self.assertNotIn(n,text)
        self.assertNotIn("traceStatesGm_.GetValue",self.k)
        self.assertNotIn("traceOutputGm_.GetValue",self.k)
        self.assertEqual(self.k.count("InitBuffer(traceOutQueue_"),1)
        self.assertEqual(self.k.count("InitBuffer(tmpBuff_, 128 * 1024)"),1)
    def test_actual_selected_flush_meta(self):
        self.assertEqual(self.p.EXPECTED_META,[6,5,4,15,0,1,1,1,1,1,1,16,19,0,0,0])
        self.assertIn("token == 6 && slot == 4 && head == 5 && vStart == 0",self.k)
        self.assertIn("traceMetaGm_.SetValue(10,merge ? 1 : 0);",self.k)
    def test_alias_ranges(self):
        self.p.check_ranges([(0,16),(16,16),(32,16)],[1,2])
        for ranges in ([(0,17),(16,16),(32,16)],[(0,16),(16,17),(32,16)]):
            with self.assertRaises(ValueError):self.p.check_ranges(ranges,[1,2])
    def test_schema_mutable_trace_alias(self):
        self.assertIn("Tensor(g!) trace_states, Tensor(h!) trace_output, Tensor(i!) trace_meta",self.p.SCHEMA)
        reg=(OP/"op_extension/register.cpp").read_text()
        self.assertIn('m.impl("decode_trace"',reg)
        self.assertIn("Meta, m)",reg)
        self.assertIn("PrivateUse1, m)",reg)
        self.assertNotIn("TORCH_LIBRARY_FRAGMENT(qwen36_kvbuffer_native_order_v2,",reg)
        meta=reg[reg.index("at::Tensor qwen36_gdn"):reg.index("void prepare_meta")]
        self.assertEqual(meta.count("const at::Tensor&"),16)
    def test_wrapper_exact_nd_alias_geometry(self):
        wrapper=(OP/"op_extension/qwen36_gdn_kvbuffer_native_order_trace_v1_torch.cpp").read_text()
        self.assertIn('get_npu_format(t)==ACL_FORMAT_ND',wrapper)
        self.assertIn("T==16 && S==19",wrapper)
        self.assertIn("{5,6,7,8,9,10,13,14,15}",wrapper)
        for n in ("traceStates,q,at::kFloat","traceOutput,q,at::kFloat","traceMeta,q,at::kInt"):
            self.assertIn(n,wrapper)
        self.assertIn("stream(false)",wrapper)
        self.assertNotIn(".cpu()",wrapper.replace("// Values and unique live slots are admitted from CPU scheduling mirrors;\n    // this wrapper never .cpu()/.item() or uploads tiling during graph replay.",""))
    def test_standalone_compile_target(self):
        cmake=(OP/"CMakeLists.txt").read_text()
        self.assertIn("--npu-arch=dav-2201",cmake)
        self.assertIn("qwen36_gdn_kvbuffer_native_order_trace_v1_ops SHARED",cmake)
        self.assertIn('project(qwen36_gdn_kvbuffer_native_order_trace_v1 LANGUAGES ASC CXX)',cmake)
    def test_full_anchor_not_padding_gold(self):
        source=(HERE/"protocol.py").read_text()
        self.assertIn('old.bitwise(torch,y,by)',source)
        self.assertIn('old.bitwise(torch,expected[:12],be[:12])',source)
        self.assertIn('old.bitwise(torch,native,bn)',source)
        self.assertIn('"native_precast_observed":False',source)
        self.assertIn('"cause_proved":False',source)
        self.assertNotIn("OUT_LIMIT =",source)
    def test_trace_raw_before_assert_math(self):
        f=next(x for x in ast.parse((HERE/"protocol.py").read_text()).body if isinstance(x,ast.FunctionDef) and x.name=="trace_step")
        source=ast.unparse(f)
        self.assertLess(source.index("torch.save(raw, p)"),source.index("not raw['copy_errors']"))
        self.assertLess(source.index("torch.save(raw, p)"),source.index("'trace_finite'"))
        self.assertIn("raise primary",source)
        self.assertNotIn("helper.logical",source)
    def test_source_hash_provenance_original_actual(self):
        m=json.loads((HERE/"SOURCE_MANIFEST.json").read_text())
        self.assertEqual(m["upstream_files"]["projects/kvbuffer-parallel-ascend/operator/native_order_v2/op_kernel/qwen36_gdn_kvbuffer_native_order_v2.h"]["sha256"],
                         "f04e12bb449cbe380e7454653fb29863604a68d6c8c9544042348fbc332941ce")
        self.assertFalse(m["npu_verified"]);self.assertFalse(m["default_enabled"])
        self.assertEqual(m["trace_bytes"],49344)
        for rel,r in m["upstream_files"].items():
            data=(ROOT/rel).read_bytes();self.assertEqual(hashlib.sha256(data).hexdigest(),r["sha256"])
        for rel,r in m["files"].items():
            if rel.endswith(".md"):continue # documentation byte hashes delivered separately
            data=(ROOT/rel).read_text().encode();self.assertEqual(hashlib.sha256(data).hexdigest(),r["sha256"])
if __name__=="__main__":unittest.main()
