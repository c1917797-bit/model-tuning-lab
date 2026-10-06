"""Source-only contracts: no Torch, build, dlopen or device."""
import ast
import importlib.util
from pathlib import Path
import sys
import unittest
BASE=Path(__file__).resolve().parent
def load(name):
    spec=importlib.util.spec_from_file_location(name,BASE/(name+".py"))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
cases=load("cases")
runner=load("run_float_gate")
class ProbeContracts(unittest.TestCase):
    def test_default_optin_false(self):
        args=runner.parse(["--mode","meta","--source-manifest","a","--source-manifest-sha256","b",
            "--runtime-manifest","a","--runtime-manifest-sha256","b","--library","a","--library-sha256","b",
            "--build-receipt","a","--build-receipt-sha256","b","--output-dir","c"])
        self.assertFalse(args.execute)
        self.assertNotIn("torch",sys.modules)
    def test_sentinel_and_sign_bits(self):
        self.assertEqual(cases.signed(0x80000000),-2147483648)
        self.assertEqual(cases.signed(0xffffffff),-1)
        self.assertEqual(len(set(cases.GUARDS)),4)
    def test_deterministic_extreme_boundary_random_fixture(self):
        rows=cases.rows()
        self.assertGreater(len(rows),6000)
        self.assertIn("invalid",{r["label"] for r in rows})
        self.assertIn("midpoint-preimage-neighbor",{r["label"] for r in rows})
        for row in rows[::53]:
            v,f,b=cases.gold.oracle(row["x"],row["c"],)
            self.assertEqual((row["valid"],row["finite"],row["bits"]),(int(v),int(f),b))
    def test_actual_counts_and_changed_inputs(self):
        first=cases.changing_rows(64,0);second=cases.changing_rows(64,1)
        self.assertEqual(len(first),64);self.assertNotEqual(first,second)
        self.assertEqual(len(cases.changing_rows(896,0)),896)
    def test_host_visible_definition_and_device_guard(self):
        kernel=(BASE/"op_kernel/float_div_probe_kernel.asc").read_text()
        self.assertIn('#endif\nextern "C" __global__ __vector__ void',kernel)
        body=(BASE/"op_kernel/float_div_probe.h").read_text()
        self.assertIn("__NPU_ARCH__ != 2201",body)
        self.assertNotIn("std::array",body)
        self.assertIn("HardEvent::MTE2_S",body);self.assertIn("HardEvent::S_V",body)
        self.assertIn("DataCopy(outputGm_[i][GUARD_INTS],out_[i],count_)",body)
    def test_real_queued_ASC_wrapper(self):
        wrapper=(BASE/"op_extension/float_div_torch.cpp").read_text()
        self.assertIn("stream(false)",wrapper);self.assertIn("OpCommand::RunOpApi(",wrapper)
        self.assertIn("<<<1,nullptr,stream>>>",wrapper)
        self.assertIn("custom_ops::get_npu_format",wrapper)
        self.assertIn("custom_ops::npu_format_cast",wrapper)
        self.assertNotIn("n.to(at::kCPU)",wrapper)
    def test_saved_before_H2D_and_raw_before_assert(self):
        source=(BASE/"run_float_gate.py").read_text()
        self.assertLess(source.index('torch.save(artifact,out/(name+".before.pt"))'),
                        source.index('roots=[torch_npu.npu_format_cast'))
        self.assertLess(source.index('torch.save(artifact,out/(name+".pt"))'),
                        source.index('require(artifact["dispatch_error"] is None'))
        self.assertIn('artifact["copy_errors"]+=errors',source)
        self.assertIn('identical_repeats=8',source)
        self.assertIn('for replay in range(8):',source)
    def test_python_AST_and_scope(self):
        for file in BASE.glob("*.py"):ast.parse(file.read_text())
        self.assertNotIn("torch",sys.modules)
if __name__=="__main__":unittest.main()
