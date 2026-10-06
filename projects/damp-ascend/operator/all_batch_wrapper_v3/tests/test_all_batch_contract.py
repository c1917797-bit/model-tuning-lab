"""Source/geometry only; stdlib, no Torch/build/load/NPU."""
import hashlib
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
OPERATOR = ROOT.parent
ARENA = OPERATOR / "arena_wrapper_v2"
OLD = OPERATOR / "production_integer_compaction_v1"
ORIGINAL_HEADER = OLD / "op_kernel/qwen36_gdn_damp_integer_compaction_v1_decode.h"
NEW_HEADER = ROOT / "op_kernel/qwen36_gdn_damp_all_batch_v3_decode.h"
FROZEN = {
 "production_integer_compaction_v1/op_kernel/qwen36_gdn_damp_integer_compaction_v1_decode.h":
  "15142a8360043e30cafbaebd19e2f528573819dcfdb519580867732e69340ff1",
 "production_integer_compaction_v1/op_kernel/qwen36_gdn_damp_integer_compaction_v1_decode_tiling.h":
  "ac40d62d8a37f8825ffb085beeb133a8b04f359e0e3a34bf4bca6ebf854224cc",
 "quantizer/exact_quantizer_bits.h":
  "f5d380534d34d6e4148d94fcfec35b294ca8ca38d09316d98b11e7f645ff6169",
 "quantizer/fast_integer_certificate/integer_certificate_ascendc.h":
  "e96cbd0565cdb879016e1970753342151936e3d45bafd375530d1d27cfd7b9cb",
 "arena_wrapper_v2/op_extension/qwen36_gdn_damp_arena_v2_decode_torch.cpp":
  "11f95e0caf5e68ca4cf7cbc2e2a03bb62828e8ea3af815f698c194ac31b615bf",
}


def round8(n):
    return ((n + 7) // 8) * 8


def admit_metadata(tokens, slots, lengths, indices):
    if not 1 <= tokens <= 16 or len(lengths) != tokens + 1 or len(indices) != tokens:
        return False
    if lengths != [0] + [1] * tokens or len(set(indices)) != tokens:
        return False
    return all(0 <= value < slots for value in indices)


class GeometryContract(unittest.TestCase):
    def test_metadata_capacity_all_sixteen(self):
        for tokens in range(1, 17):
            with self.subTest(tokens=tokens):
                self.assertLessEqual(round8(tokens), 16)
                self.assertLessEqual(16 + round8(tokens + 1), 40)
                self.assertLessEqual((8 - tokens % 8) % 8, 7)
                self.assertLessEqual((8 - (tokens + 1) % 8) % 8, 7)
                self.assertEqual(round8(tokens) * 4 % 32, 0)
                self.assertEqual(round8(tokens + 1) * 4 % 32, 0)
                self.assertTrue(admit_metadata(tokens, tokens + 3,
                                              [0] + [1] * tokens, list(range(tokens))))

    def test_active_reads_never_depend_on_padding(self):
        for tokens in range(1, 17):
            local = [None] * 40
            for i in range(round8(tokens)):
                local[i] = i if i < tokens else 0
            for i in range(round8(tokens + 1)):
                local[16 + i] = (0 if i == 0 else 1) if i <= tokens else 0
            self.assertEqual(local[16], 0)
            self.assertEqual([local[17 + t] for t in range(tokens)], [1] * tokens)
            self.assertEqual(local[:tokens], list(range(tokens)))

    def test_task_coverage_and_whole_head_ownership(self):
        for tokens in range(1, 17):
            tasks = tokens * 12
            for cores in (1, 8, 20, 32, 48):
                blocks = min(cores, tasks)
                actual = [task for block in range(blocks) for task in range(block, tasks, blocks)]
                self.assertEqual(sorted(actual), list(range(tasks)))
                owners = [(task // 12, task % 12) for task in actual]
                self.assertEqual(len(set(owners)), tasks)
            self.assertLessEqual(tasks, 192)

    def test_per_token_dma_source_bounds(self):
        for tokens in range(1, 17):
            for token in range(tokens):
                self.assertLessEqual(token * 4 * 128 * 2 + 4 * 128 * 2,
                                     tokens * 4 * 128 * 2)
                self.assertLessEqual(token * 12 * 128 * 2 + 12 * 128 * 2,
                                     tokens * 12 * 128 * 2)
                self.assertLessEqual(token * 12 * 4 + 48, tokens * 12 * 4)
                self.assertLessEqual(token * 12 * 2 + 24, tokens * 12 * 2)
            self.assertEqual(tokens * 12 * 128 * 2 % 32, 0)
        # Readonly rows are intentionally allowed to be below a 32B multiple.
        self.assertEqual(12 * 2, 24)
        self.assertEqual(12 * 4, 48)

    def test_invalid_tokens_and_padding(self):
        for tokens in (0, -1, 17, 32):
            self.assertFalse(admit_metadata(tokens, 32, [0] + [1] * max(tokens, 0),
                                            list(range(max(tokens, 0)))))
        for tokens in range(1, 17):
            good = [0] + [1] * tokens
            for index in range(len(good)):
                lengths = list(good); lengths[index] = 2 if index else 1
                self.assertFalse(admit_metadata(tokens, tokens + 3, lengths, list(range(tokens))))
                if index:
                    lengths[index] = 0
                    self.assertFalse(admit_metadata(tokens, tokens + 3, lengths, list(range(tokens))))

    def test_negative_duplicate_out_of_range_indices(self):
        for tokens in range(1, 17):
            for value in (-1, tokens + 3):
                indices = list(range(tokens)); indices[-1] = value
                self.assertFalse(admit_metadata(tokens, tokens + 3, [0] + [1] * tokens, indices))
            if tokens > 1:
                indices = list(range(tokens)); indices[-1] = 0
                self.assertFalse(admit_metadata(tokens, tokens + 3, [0] + [1] * tokens, indices))


class SourceContract(unittest.TestCase):
    def test_frozen_sources_unchanged(self):
        for relative, expected in FROZEN.items():
            with self.subTest(relative=relative):
                self.assertEqual(hashlib.sha256((OPERATOR / relative).read_bytes()).hexdigest(), expected)

    def test_exactly_one_device_admission_change(self):
        original = ORIGINAL_HEADER.read_text()
        self.assertEqual(original.count("(tokens_ != 1 && tokens_ != 16)"), 1)
        expected = original.replace(
            "QWEN36_GDN_DAMP_INTEGER_COMPACTION_V1_DECODE_KERNEL_H",
            "QWEN36_GDN_DAMP_ALL_BATCH_V3_DECODE_KERNEL_H").replace(
            '#include "qwen36_gdn_damp_integer_compaction_v1_decode_tiling.h"',
            '#include "../../production_integer_compaction_v1/op_kernel/qwen36_gdn_damp_integer_compaction_v1_decode_tiling.h"').replace(
            "(tokens_ != 1 && tokens_ != 16)", "(tokens_ < 1 || tokens_ > MAX_TOKENS)")
        self.assertEqual(NEW_HEADER.read_text().rstrip("\n"), expected.rstrip("\n"))

    def test_wrapper_only_named_batch_admission_differences(self):
        original = (ARENA / "op_extension/qwen36_gdn_damp_arena_v2_decode_torch.cpp").read_text()
        expected = original.replace("qwen36_gdn_damp_arena_v2", "qwen36_gdn_damp_all_batch_v3").replace(
            "Qwen36GdnDampArenaV2Decode", "Qwen36GdnDampAllBatchV3Decode").replace(
            "tokens == 1 || tokens == 16", "tokens >= 1 && tokens <= 16").replace(
            "DAMP arena v2 accepts exactly B1 or B16", "DAMP all-batch v3 accepts T1..16 only").replace(
            "unvalidated arena-wrapper v2", "unvalidated all-batch-wrapper v3")
        actual = (ROOT / "op_extension/qwen36_gdn_damp_all_batch_v3_decode_torch.cpp").read_text()
        self.assertEqual(actual.rstrip("\n"), expected.rstrip("\n"))

    def test_meta_only_named_batch_admission_differences(self):
        original = (ARENA / "op_extension/register.cpp").read_text()
        expected = original.replace("qwen36_damp_arena_v2", "qwen36_damp_all_batch_v3").replace(
            "qwen36_gdn_damp_arena_v2", "qwen36_gdn_damp_all_batch_v3").replace(
            "(query.size(0) == 1 || query.size(0) == 16)",
            "(query.size(0) >= 1 && query.size(0) <= 16)").replace(
            "query must be BF16 B1/B16 [T,4,128]", "query must be BF16 T1..16 [T,4,128]")
        self.assertEqual((ROOT / "op_extension/register.cpp").read_text().rstrip("\n"),
                         expected.rstrip("\n"))

    def test_default_off_host_visible_same_launcher_body(self):
        cmake = (ROOT / "CMakeLists.txt").read_text()
        self.assertIn("option(DAMP_BUILD_ALL_BATCH_WRAPPER_V3", cmake)
        self.assertIn(" OFF)", cmake)
        self.assertIn("PROPERTIES LANGUAGE ASC", cmake)
        kernel = (ROOT / "op_kernel/qwen36_gdn_damp_all_batch_v3_decode_kernel.asc").read_text()
        expected = (ARENA / "op_kernel/qwen36_gdn_damp_arena_v2_decode_kernel.asc").read_text().replace(
            "qwen36_gdn_damp_arena_v2_decode_kernel", "qwen36_gdn_damp_all_batch_v3_decode_kernel").replace(
            '#include "../../production_integer_compaction_v1/op_kernel/qwen36_gdn_damp_integer_compaction_v1_decode.h"',
            '#include "qwen36_gdn_damp_all_batch_v3_decode.h"')
        self.assertEqual(kernel.rstrip("\n"), expected.rstrip("\n"))
        definition = kernel.index('extern "C" __global__')
        self.assertGreater(kernel.index("#if defined(__NPU_ARCH__)", definition),
                           kernel.index("{", definition))


if __name__ == "__main__":
    unittest.main(verbosity=2)
