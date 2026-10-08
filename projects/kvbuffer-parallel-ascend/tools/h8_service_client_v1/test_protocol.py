"""Software-only contracts and real default-OFF CLI, not model or NPU evidence."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import protocol as p


def event(ids, prompt=None, finish=None):
    choice = {"index": 0, "token_ids": ids, "finish_reason": finish}
    if prompt is not None:
        choice["prompt_token_ids"] = prompt
    return p.canonical({"choices": [choice]})


class Tests(unittest.TestCase):
    def arm_fixture(self):
        # SOFTWARE-only input fixture, not an actual launched ARM receipt.
        return {"schema": "kvbp.h8-model-service-arm/v1", "arm": "candidate", "prepare_only": False,
                "image_id": p.IMAGE, "model_config_sha256": p.MODEL_CONFIG_SHA, "port": 8210,
                "served_model_name": "qwen36-h8", "protocol": copy.deepcopy(p.PROTOCOL),
                "client_sources": p.sources(), "measurement_scope": "same-eager-screen",
                "MAIN_launch_authority": {"software_only_fixture": True},
                "candidate_numeric_prerequisite_checked": True, "common_total_cache_budget_bytes": 1,
                "common": {"tensor_parallel_size": 4, "pipeline_parallel_size": 1,
                           "data_parallel_size": 1, "dtype": "bfloat16", "max_num_seqs": 16,
                           "max_model_len": 40960, "max_num_batched_tokens": 40960,
                           "enable_chunked_prefill": False,
                           "seed": 0, "enable_prefix_caching": True, "mamba_cache_mode": "align",
                           "speculative": False, "async_scheduling": False,
                           "profiling": False, "enforce_eager": True}}

    def test_new_arm_schema_positive_is_only_input_validation(self):
        arm = self.arm_fixture()
        self.assertIs(p.arm_contract(arm, 8210), arm)
        self.assertNotIn("torch", sys.modules)
        self.assertNotIn("torch_npu", sys.modules)

    def test_eager_arm_cannot_claim_formal_graph_pair(self):
        arm = self.arm_fixture()
        arm["measurement_scope"] = "formal-graph-pair"
        with self.assertRaises(ValueError):
            p.arm_contract(arm, 8210)

    def test_unrun_or_prepare_only_prerequisites_rejected(self):
        for key, value in (("prepare_only", True), ("candidate_numeric_prerequisite_checked", False),
                           ("MAIN_launch_authority", {}), ("common_total_cache_budget_bytes", 0)):
            arm = self.arm_fixture()
            arm[key] = value
            with self.assertRaises(ValueError):
                p.arm_contract(arm, 8210)

    def test_wrong_runtime_source_protocol_endpoint_rejected(self):
        for key, value in (("image_id", "other"), ("model_config_sha256", "0" * 64),
                           ("client_sources", {}), ("protocol", {}), ("port", 8211)):
            arm = self.arm_fixture()
            arm[key] = value
            with self.assertRaises(ValueError):
                p.arm_contract(arm, 8210)

    def test_old_prefix_off_or_unsupported_receiver_rejected(self):
        for key, value in (("enable_prefix_caching", False), ("mamba_cache_mode", "none"),
                           ("pipeline_parallel_size", 2), ("speculative", True),
                           ("async_scheduling", True), ("profiling", True), ("max_num_seqs", 32)):
            arm = self.arm_fixture()
            arm["common"][key] = value
            with self.assertRaises(ValueError):
                p.arm_contract(arm, 8210)

    def test_real_default_off_cli_without_torch_or_network(self):
        r = subprocess.run([sys.executable, "-I", "-B", str(Path(__file__).with_name("bench.py"))],
                           capture_output=True, text=True, timeout=5)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(json.loads(r.stdout)["NPU_executed"])
        self.assertNotIn("torch", sys.modules)
        self.assertNotIn("torch_npu", sys.modules)

    def test_exact_forty_distinct_prompts_shared_prefix(self):
        prompts = [p.prompt_ids(i) for i in range(40)]
        self.assertTrue(all(len(x) == 32768 for x in prompts))
        self.assertEqual(len({p.digest(x) for x in prompts}), 40)
        self.assertTrue(all(x[:16384] == prompts[0][:16384] for x in prompts))

    def test_stream_actual_delta_and_usage(self):
        s = p.StreamState([10, 11], 3)
        s.feed(event([1], [10, 11]), 5.0)
        s.feed(event([2, 3], finish="length"), 7.0)
        s.feed(p.canonical({"choices": [], "usage": {"prompt_tokens": 2, "completion_tokens": 3,
                                                  "total_tokens": 5}}), 8.0)
        s.feed(b"[DONE]", 8.0)
        s.finish_check()
        self.assertEqual(s.tokens, [1, 2, 3])
        self.assertEqual((s.first, s.last), (5.0, 7.0))

    def test_empty_first_prefill_echo_keeps_prompt_without_counting_ttft(self):
        s = p.StreamState([10], 1)
        s.feed(event([], [10]), 1.0)
        self.assertTrue(s.prompt_seen)
        self.assertIsNone(s.first)
        s.feed(event([2], finish="length"), 3.0)
        s.feed(p.canonical({"choices": [], "usage": {"prompt_tokens": 1,
                                                  "completion_tokens": 1, "total_tokens": 2}}), 4.0)
        s.feed(b"[DONE]", 4.0)
        s.finish_check()
        self.assertEqual(s.tokens, [2])
        self.assertEqual(s.first, 3.0)

    def test_reject_text_instead_of_token_ids(self):
        s = p.StreamState([10], 1)
        with self.assertRaises(ValueError):
            s.feed(p.canonical({"choices": [{"index": 0, "text": "not token evidence"}]}), 1.0)

    def test_reject_prompt_mutation(self):
        with self.assertRaises(ValueError):
            p.StreamState([10], 1).feed(event([1], [11]), 1.0)

    def test_reject_overlong_cumulative_delta(self):
        s = p.StreamState([10], 2)
        s.feed(event([1]), 1.0)
        with self.assertRaises(ValueError):
            s.feed(event([1, 2]), 2.0)

    def test_reject_nonmonotonic_or_nonfinite_token_receipts(self):
        for now in (0.5, float("nan")):
            s = p.StreamState([10], 2)
            s.feed(event([1]), 1.0)
            with self.assertRaises(ValueError):
                s.feed(event([2]), now)

    def test_reject_duplicate_done_and_usage(self):
        s = p.StreamState([10], 1)
        s.feed(b"[DONE]", 1.0)
        with self.assertRaises(ValueError):
            s.feed(b"[DONE]", 2.0)
        s = p.StreamState([10], 1)
        u = p.canonical({"choices": [], "usage": {"completion_tokens": 1}})
        s.feed(u, 1.0)
        with self.assertRaises(ValueError):
            s.feed(u, 2.0)

    def test_reject_legacy_p1_arm(self):
        with self.assertRaises(ValueError):
            p.arm_contract({"schema": "kvbp.service-arm/v1"}, 8210)

    def test_queue_is_not_ttft_and_wall_includes_complete_done(self):
        rows = [{"index": i, "ok": True, "completion_tokens": 1024, "prompt_tokens": 32768,
                 "finish_reason": "length", "done": True, "enqueued": 10., "submitted": 20.,
                 "first": 23., "last": 1026., "response_end": 1030.} for i in range(40)]
        r = p.summarize(rows)
        self.assertEqual(r["wall_seconds"], 1020.)
        self.assertEqual(r["mean_ttft_seconds"], 3.)
        self.assertEqual(r["mean_client_queue_seconds"], 10.)
        self.assertEqual(r["mean_ttft_including_client_queue_seconds"], 13.)
        self.assertEqual(r["total_output_tokens"], 40960)
        for bad in (rows[:-1], rows + [copy.deepcopy(rows[-1])]):
            with self.assertRaises(ValueError):
                p.summarize(bad)
        rows[0]["last"] = float("nan")
        with self.assertRaises(ValueError):
            p.summarize(rows)


if __name__ == "__main__":
    unittest.main()
