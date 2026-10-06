"""Software regression plus opt-in real no-device runtime gate."""
import ast
import os
from pathlib import Path
import unittest


class TokenizerGateTests(unittest.TestCase):
    def test_no_device_platform_gate_reads_driver_dependent_source(self):
        source = Path(__file__).parents[1]/"damp_capture"/"platform_gate.py"
        tree = ast.parse(source.read_text())
        modules = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        direct = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        self.assertNotIn("vllm_ascend.ops.gdn", direct)
        self.assertNotIn("vllm_ascend.worker.model_runner_v1", direct)
        self.assertNotIn("vllm_ascend.utils", modules)
        calls = [n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Name)]
        self.assertNotIn("enable_custom_op", calls)

    def test_prepare_forces_native_list_not_batch_encoding_mapping(self):
        source=Path(__file__).parents[1]/"damp_capture"/"prepare.py"
        tree=ast.parse(source.read_text())
        calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and
               isinstance(n.func,ast.Attribute) and n.func.attr=="apply_chat_template"]
        self.assertEqual(len(calls),1)
        keywords={k.arg:k.value for k in calls[0].keywords}
        self.assertTrue(ast.literal_eval(keywords["tokenize"]))
        self.assertFalse(ast.literal_eval(keywords["return_dict"]))
        self.assertFalse(ast.literal_eval(keywords["enable_thinking"]))

    @unittest.skipUnless(os.environ.get("DAMP_NO_DEVICE_TOKENIZER_GATE")=="1",
                         "real tokenizer needs explicit same-image NO-NPU run")
    def test_real_same_image_no_device_tokenizer(self):
        from damp_capture.tokenizer_gate import inspect_tokenizer
        result=inspect_tokenizer("/cache/cch/qwen36-awq-w4a8-20260923/calibration_text_v1.jsonl")
        self.assertEqual(result["status"],"pass")
        self.assertEqual(len(result["rows"]),2)


if __name__=="__main__":
    unittest.main()
