"""NO Torch import, no build/load/devices. Run with python -B."""
import hashlib
from pathlib import Path
import unittest

from interval_contract import View, MAXPTR, MAXI64, admit, data_span, disjoint

ROOT = Path(__file__).resolve().parents[1]
OPERATOR = ROOT.parent
OLD = OPERATOR / "production_integer_compaction_v1"
WRAPPER = ROOT / "op_extension/qwen36_gdn_damp_arena_v2_decode_torch.cpp"
FROZEN = {
    "production_integer_compaction_v1/op_kernel/qwen36_gdn_damp_integer_compaction_v1_decode.h":
        "15142a8360043e30cafbaebd19e2f528573819dcfdb519580867732e69340ff1",
    "production_integer_compaction_v1/op_kernel/qwen36_gdn_damp_integer_compaction_v1_decode_tiling.h":
        "ac40d62d8a37f8825ffb085beeb133a8b04f359e0e3a34bf4bca6ebf854224cc",
    "quantizer/exact_quantizer_bits.h":
        "f5d380534d34d6e4148d94fcfec35b294ca8ca38d09316d98b11e7f645ff6169",
    "quantizer/fast_integer_certificate/integer_certificate_ascendc.h":
        "e96cbd0565cdb879016e1970753342151936e3d45bafd375530d1d27cfd7b9cb",
}
BASE = 0x10000000


def view(offset, size, item=1, total=1 << 28):
    assert offset % item == 0 and size % item == 0
    return View(BASE, total, BASE + offset, offset // item, size // item, item)


class IntervalContract(unittest.TestCase):
    def test_shared_arena_regions(self):
        for slots in (4, 19):
            conv = view(0, slots * 15360)
            start = slots * 15360
            hi = view(start, slots * 49152, 2)
            start += slots * 49152
            lo = view(start, slots * 172032)
            start += slots * 172032
            scales = view(start, slots * 21504, 4)
            self.assertTrue(admit([hi, lo, scales], [conv]))
            self.assertEqual(data_span(hi)[1], data_span(lo)[0])
            self.assertEqual(data_span(lo)[1], data_span(scales)[0])

    def test_guarded_arena_regions(self):
        writers = [view(64, 49152, 2), view(64 + 49152 + 64, 172032),
                   view(64 + 49152 + 64 + 172032 + 64, 21504, 4)]
        self.assertTrue(admit(writers, [view(0, 32)]))

    def test_short_readonly_metadata(self):
        self.assertEqual(data_span(view(0, 4, 4))[1] - BASE, 4)
        self.assertEqual(data_span(view(32, 8, 4))[1] - BASE, 40)
        self.assertTrue(admit([view(64, 32)], [view(0, 4, 4), view(32, 8, 4)]))
        with self.assertRaises(ValueError):
            data_span(view(0, 4, 4), writer=True)

    def test_exact_backing_end(self):
        self.assertEqual(data_span(view(32, 32, 4, 64)), (BASE + 32, BASE + 64))

    def test_overlap_and_touch(self):
        self.assertTrue(disjoint((0, 32), (32, 64)))
        self.assertFalse(disjoint((0, 33), (32, 64)))
        with self.assertRaises(ValueError):
            admit([view(0, 64), view(32, 64)], [])

    def test_writer_vs_tiling_every_input(self):
        for reader in (view(32, 4, 4), view(32, 1056), view(32, 6144, 4)):
            with self.assertRaises(ValueError):
                admit([view(0, 64)], [reader])

    def test_readonly_overlap_allowed(self):
        self.assertTrue(admit([view(128, 32)], [view(0, 64), view(32, 64)]))

    def test_pointer_offset_width(self):
        self.assertEqual(data_span(view(32, 32, 4)), (BASE + 32, BASE + 64))
        wrong = View(BASE, 128, BASE + 32, 32, 8, 4)
        with self.assertRaises(ValueError):
            data_span(wrong)
        wrong = View(BASE, 128, BASE + 32, 7, 8, 4)
        with self.assertRaises(ValueError):
            data_span(wrong)

    def test_negative_empty_bounds(self):
        cases = [
            View(BASE, 128, BASE, -1, 8, 4),
            View(BASE, 128, BASE, 0, 0, 4),
            View(BASE, 128, BASE, 0, -1, 4),
            View(BASE, 128, BASE, 0, 1, 0),
            View(BASE, 128, BASE + 128, 32, 1, 4),
            View(BASE, 128, BASE + 96, 24, 9, 4),
            View(BASE, 0, BASE, 0, 8, 4),
        ]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(ValueError):
                data_span(case)

    def test_overflow(self):
        cases = [
            View(MAXPTR - 31, 64, MAXPTR - 31, 0, 32, 1),
            View(BASE, 128, BASE, 0, MAXI64, 8),
            View(BASE, 128, BASE, MAXI64, 1, 8),
        ]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(ValueError):
                data_span(case)

    def test_physical_layout_device_alignment(self):
        for changed in ({"nd": False}, {"contiguous": False}, {"device": "cpu"},
                        {"data": BASE + 1, "element_offset": 1}):
            values = dict(base=BASE, backing_bytes=128, data=BASE, element_offset=0,
                          count=32, item_bytes=1)
            values.update(changed)
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                data_span(View(**values))


class SourceContract(unittest.TestCase):
    def test_delegated_sources_exact(self):
        for relative, expected in FROZEN.items():
            with self.subTest(path=relative):
                self.assertEqual(hashlib.sha256((OPERATOR / relative).read_bytes()).hexdigest(), expected)

    def test_no_new_numerical_header(self):
        self.assertFalse((ROOT / "op_kernel/qwen36_gdn_damp_arena_v2_decode.h").exists())
        kernel = (ROOT / "op_kernel/qwen36_gdn_damp_arena_v2_decode_kernel.asc").read_text()
        old = (OLD / "op_kernel/qwen36_gdn_damp_integer_compaction_v1_decode_kernel.asc").read_text()
        normalized = kernel.replace("qwen36_gdn_damp_arena_v2_decode_kernel",
                                    "qwen36_gdn_damp_integer_compaction_v1_decode_kernel")
        normalized = normalized.replace("../../production_integer_compaction_v1/op_kernel/", "")
        # New-file patch normalizes only redundant EOF blank lines. Mathematical
        # launcher body and normalized declarations remain byte-for-byte equal.
        self.assertEqual(normalized.rstrip("\n"), old.rstrip("\n"))
        definition = normalized.index('extern "C" __global__')
        body_guard = normalized.index("#if defined(__NPU_ARCH__)", definition)
        self.assertGreater(body_guard, normalized.index("{", definition))

    def test_default_off_distinct_namespace_schema(self):
        cmake = (ROOT / "CMakeLists.txt").read_text()
        self.assertIn('option(DAMP_BUILD_ARENA_WRAPPER_V2', cmake)
        self.assertIn(' OFF)', cmake)
        register = (ROOT / "op_extension/register.cpp").read_text()
        old = (OLD / "op_extension/register.cpp").read_text()
        normalized = register.replace("qwen36_damp_arena_v2", "qwen36_damp_integer_compaction_v1")
        normalized = normalized.replace("qwen36_gdn_damp_arena_v2", "qwen36_gdn_damp_integer_compaction_v1")
        self.assertEqual(normalized.rstrip("\n"), old.rstrip("\n"))
        for alias in ("Tensor(a!) high_state", "Tensor(b!) low_state", "Tensor(c!) low_scale"):
            self.assertIn(alias, register)

    def test_offset_bound_and_dma_scope(self):
        wrapper = WRAPPER.read_text()
        for fragment in ("tensor.storage_offset()", "begin == base + offsetBytes",
                         "bytes <= storageEnd - begin", "(void)tensor_span(tensor)",
                         "maximum / static_cast<uint64_t>(itemBytes)",
                         "backingBytes <= maximum - base"):
            self.assertIn(fragment, wrapper)
        self.assertNotIn("storage_span", wrapper)
        for name in ("highState", "lowState", "lowScale", "out"):
            self.assertIn("check_writer_dma_span(" + name + ",", wrapper)
        for name in ("query", "key", "value", "g", "beta", "actualSeqLengths", "stateIndices"):
            self.assertNotIn("check_writer_dma_span(" + name + ",", wrapper)

    def test_every_mutable_vs_tiling(self):
        wrapper = WRAPPER.read_text()
        for name in ("highState", "lowState", "lowScale"):
            self.assertIn("check_disjoint(" + name + ", tilingTensor);", wrapper)
        self.assertIn('check_tensor(tilingTensor, query, at::kByte, "tiling");', wrapper)
        self.assertIn("&actualSeqLengths, &stateIndices, &tilingTensor", wrapper)

    def test_stream_kernel_gates_unchanged(self):
        wrapper = WRAPPER.read_text()
        self.assertIn("tokens == 1 || tokens == 16", wrapper)
        self.assertIn('std::string(soc) == "Ascend910B4"', wrapper)
        self.assertIn("getCurrentNPUStream().stream(false)", wrapper)
        self.assertIn('OpCommand::RunOpApi("Qwen36GdnDampArenaV2Decode", aclCall)', wrapper)
        self.assertIn("get_npu_format(tensor) == ACL_FORMAT_ND", wrapper)
        self.assertIn("prepareStream = c10_npu::getCurrentNPUStream().stream(true)", wrapper)


if __name__ == "__main__":
    unittest.main(verbosity=2)
