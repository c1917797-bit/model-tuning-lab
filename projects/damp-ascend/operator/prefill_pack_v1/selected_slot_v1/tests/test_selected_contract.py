"""NEW selected-pack preparation: stdlib source checks, not compilation/NPU."""
import ast
import pathlib
import re
import struct
import unittest
BASE=pathlib.Path(__file__).resolve().parents[1]
OPERATOR=BASE.parents[1]
def body(text,name):
    m=re.search(r"    __aicore__ inline [^{]+?\b"+name+r"\([^{]*\{",text)
    if m is None:raise AssertionError(name)
    i=m.end();depth=1
    while depth:
        if text[i]=="{":depth+=1
        if text[i]=="}":depth-=1
        i+=1
    return text[m.start():i]
class SelectedPreparation(unittest.TestCase):
    def test_packing_four_methods_byte_exact(self):
        original=(OPERATOR/"production_integer_compaction_v1/op_kernel/qwen36_gdn_damp_integer_compaction_v1_decode.h").read_text()
        candidate=(BASE/"op_kernel/selected_prefill.h").read_text()
        for name in ("PackStore","QuantizeChunk","VectorToScalar","LoadQuantizerTables"):
            self.assertEqual(body(candidate,name),body(original,name))
    def test_disjoint_explicit_UB(self):
        shapes=[(0,160),(256,512),(768,512),(1280,512),(1792,512),(2304,512),
                (2816,512),(3328,16384),(19712,2048),(21760,512),(22272,512),
                (22784,256),(23040,14336),(37376,14336),(51712,8192)]
        self.assertTrue(all(a%32==0 and n%32==0 for a,n in shapes))
        self.assertTrue(all(a+n<=b for (a,n),(b,m) in zip(shapes,shapes[1:])))
        self.assertEqual(shapes[-1][0]+shapes[-1][1],59904)
        self.assertEqual(59904+42496+160+2048+512+10240+32,115392)
    def test_fp16_overflow_threshold_independently(self):
        x=lambda b:struct.unpack("<f",struct.pack("<I",b))[0]
        self.assertEqual(struct.unpack("<e",struct.pack("<e",x(0x477fefff)))[0],65504.0)
        for bits in (0x477ff000,0x477ff001):
            with self.assertRaises(OverflowError):struct.pack("<e",x(bits))
    def test_metadata_before_any_writer_and_true_P(self):
        h=(BASE/"op_kernel/selected_prefill.h").read_text()
        self.assertLess(h.index("const bool metadataValid=LoadValidateMetadata();"),
                        h.index("if(!PackStore(headSlot,group))"))
        self.assertIn("meta_.GetValue(j)==slot",h)
        self.assertIn("prefills_<1 || prefills_>16",h)
        self.assertNotIn("tokens_ != 1",h)
    def test_exact_general_SR_no_fp32_sidecar(self):
        h=(BASE/"op_kernel/selected_prefill.h").read_text()
        self.assertIn("Qwen36DampPrefill::ExactFloatDiv(raw,c)",h)
        self.assertIn("Qwen36DampPrefill::CertifiesFloat(raw,c,proposal)",h)
        self.assertIn("if(c==0x3f800000U)",h)
        self.assertIn("if(!valid) return false",h)
        self.assertNotIn("denseGm_.SetValue",h)
        self.assertNotIn("DataCopy(denseGm_",h)
    def test_wrapper_real_arena_bounds_and_queue(self):
        w=(BASE/"op_extension/selected_prefill_torch.cpp").read_text()
        self.assertIn("begin == base + offsetBytes",w)
        self.assertIn("bytes <= storageEnd - begin",w)
        self.assertIn("custom_ops::get_npu_format",w)
        self.assertIn("stream(false)",w);self.assertIn("OpCommand::RunOpApi",w)
        self.assertIn("status.mutable_data_ptr())+32",w)
        self.assertNotIn("indices.to(at::kCPU)",w)
    def test_host_definition_visible_meta_three_mutations_defaultoff(self):
        k=(BASE/"op_kernel/selected_prefill_kernel.asc").read_text()
        self.assertIn('#endif\nextern "C" __global__ __vector__ void',k)
        m=(BASE/"op_extension/register.cpp").read_text()
        for value in ("Tensor(a!) hi","Tensor(b!) lo","Tensor(c!) scales",
                      "bool use_float_candidate=False"):self.assertIn(value,m)
        c=(BASE/"CMakeLists.txt").read_text()
        self.assertIn('option(DAMP_BUILD_SELECTED_PREFILL_V1',c);self.assertIn(' OFF)',c)
if __name__=="__main__":unittest.main()
