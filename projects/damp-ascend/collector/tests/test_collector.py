"""CPU-only contract/lifecycle tests; these do not prove Ascend correctness."""
import copy
import math
from pathlib import Path
import unittest
from damp_capture.contract import (DOMAINS, INPUT_ROOT, LAYERS, base_manifest, digest,
                                   token_digest, validate_manifest)
from damp_capture.session import Session, layer_index
from damp_capture.timeline import Timeline, decay_weights


def row(i, domain="project-smoke", split="smoke"):
    ids = [10, i + 100, 20]
    return dict(id=f"r{i}", input_ids=ids, input_ids_sha256=token_digest(ids),
                prompt_text_sha256=digest("text" + str(i)), domain=domain, split=split)


def smoke():
    m = base_manifest("smoke")
    m["rows"] = [row(0), row(1)]
    m["prompt_builder_sha256"] = digest("test-builder")
    return m


def full():
    m = base_manifest("full")
    m["rows"], m["prompt_builder_sha256"] = [], digest("test-builder")
    for split in ("fit", "tune", "validation"):
        for domain, dataset in DOMAINS.items():
            for _ in range(4):
                i = len(m["rows"])
                r = row(i, domain, split)
                r["input_ids"] = [10] * 1023 + [100 + i]
                r["input_ids_sha256"] = token_digest(r["input_ids"])
                r["source"] = dict(dataset=dataset, split="train", revision="a"*40,
                                   record_id=i, record_sha256=digest(i), artifact_sha256=digest("source"),
                                   artifact_path=str(INPUT_ROOT / (domain + ".jsonl")),
                                   license="test-only", url="https://example.invalid/source")
                m["rows"].append(r)
    return m


class FakeWriter:
    def __init__(self):
        self.events = []
    def event(self, kind, **fields):
        self.events.append((kind, fields))


class ContractTests(unittest.TestCase):
    def test_nonchunked_launch_budget_covers_model_len(self):
        import ast
        from types import SimpleNamespace
        source = Path(__file__).parents[1] / "damp_capture" / "run.py"
        tree = ast.parse(source.read_text())
        call = next(n for n in ast.walk(tree) if isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Name) and n.func.id == "LLM")
        keywords = {k.arg: k.value for k in call.keywords}
        model_len = ast.literal_eval(keywords["max_model_len"])
        self.assertFalse(ast.literal_eval(keywords["enable_chunked_prefill"]))
        budget = compile(ast.Expression(keywords["max_num_batched_tokens"]), "<budget>", "eval")
        for count in range(1, 5):
            value = eval(budget, {"__builtins__": {}, "max": max},
                         {"args": SimpleNamespace(batch_size=count)})
            self.assertGreaterEqual(value, model_len)

    def test_smoke_scope(self):
        validate_manifest(smoke(), verify_files=False)
    def test_full_balanced_training_and_zero_record_id(self):
        validate_manifest(full(), verify_files=False)
    def test_missing_training_corpus_is_not_smoke_fallback(self):
        m = full(); m["rows"] = []
        with self.assertRaises(ValueError): validate_manifest(m, verify_files=False)
    def test_full_rejects_evaluation_source(self):
        m = full(); m["rows"][0]["source"]["split"] = "test"
        with self.assertRaises(ValueError): validate_manifest(m, verify_files=False)
    def test_full_rejects_unpinned_revision(self):
        m = full(); m["rows"][0]["source"]["revision"] = "main"
        with self.assertRaises(ValueError): validate_manifest(m, verify_files=False)
    def test_full_rejects_duplicate_source_between_splits(self):
        m = full(); m["rows"][9]["source"]["record_id"] = m["rows"][0]["source"]["record_id"]
        m["rows"][9]["source"]["dataset"] = m["rows"][0]["source"]["dataset"]
        m["rows"][9]["domain"] = "math"
        with self.assertRaises(ValueError): validate_manifest(m, verify_files=False)
    def test_wrong_hash_and_duplicate_prompt(self):
        for m in (smoke(), smoke()):
            m["rows"][1] = copy.deepcopy(m["rows"][0]); m["rows"][1]["id"] = "other"
            with self.assertRaises(ValueError): validate_manifest(m, verify_files=False)
    def test_last_future_must_fit_output_minus_prefill_token(self):
        m = smoke(); m["generation"]["min_tokens"] = m["generation"]["max_tokens"] = 6
        with self.assertRaises(ValueError): validate_manifest(m, verify_files=False)
    def test_wrong_state_axis_geometry(self):
        m = smoke(); m["native_state_shape"] = [4, 128, 128]
        with self.assertRaises(ValueError): validate_manifest(m, verify_files=False)
    def test_tensor_parallel_partial_coverage_forbidden(self):
        m = smoke(); m["tp_size"] = 1
        with self.assertRaises(ValueError): validate_manifest(m, verify_files=False)
    def test_token_ids_must_be_strict_int(self):
        with self.assertRaises(ValueError): token_digest([True])
    def test_train_artifact_missing_fail_closed(self):
        with self.assertRaises(ValueError): validate_manifest(full(), verify_files=True)


class TimelineTests(unittest.TestCase):
    def test_next_decay_not_anchor_decay(self):
        t = Timeline([2, 4], 2, 1)
        self.assertEqual(t.advance([-1]), (False, []))
        self.assertEqual(t.advance([-2]), (True, []))
        self.assertEqual(t.advance([-3]), (False, []))
        self.assertEqual(t.advance([-4]), (True, [2]))
        self.assertEqual(t.finished[2], ((-3,), (-4,)))
        self.assertEqual(t.advance([-5]), (False, []))
        self.assertEqual(t.advance([-6]), (False, [4]))
        self.assertTrue(t.complete)
    def test_full_six_anchors_and_futures(self):
        t = Timeline([256, 512, 768, 2304, 2560, 2816], 256, 12)
        for i in range(1, 3073):
            t.advance([-0.01 * i] * 12)
        self.assertTrue(t.complete)
        self.assertEqual(len(t.finished), 6)
        self.assertAlmostEqual(t.finished[256][0][0], -2.57)
        self.assertAlmostEqual(t.finished[2816][-1][0], -30.72)
    def test_nonfinite_and_expanding_decay_rejected(self):
        for v in (float("nan"), float("inf"), 0.1):
            with self.assertRaises(ValueError): Timeline([2], 2, 1).advance([v])
    def test_future_equation_includes_identity_anchor_term(self):
        weights = decay_weights([[-1.0], [-2.0]])
        self.assertAlmostEqual(weights[0], 1 + math.exp(-2) + math.exp(-6))
    def test_per_value_head_not_shared_qk_head(self):
        t = Timeline([1], 1, 12); t.advance([-1]*12); t.advance([-x for x in range(12)])
        self.assertEqual(len(t.finished[1][0]), 12)
        self.assertNotEqual(decay_weights(t.finished[1])[0], decay_weights(t.finished[1])[11])


class SessionTests(unittest.TestCase):
    def setup_session(self):
        m = smoke(); s = Session(m, FakeWriter())
        prompts = {"a": m["rows"][0]["input_ids"], "b": m["rows"][1]["input_ids"]}
        return m, s, prompts
    def prefill(self, s, prompts, ids=("a",), slots=(0,), active=("a", "b")):
        s.begin(ids, prompts, active, tuple(range(3)) * len(ids))
        for layer in LAYERS: s.plan(layer, [], list(slots), [3]*len(ids), [False]*len(ids))
        s.finish()
    def test_full_layer_coverage(self):
        m, s, p = self.setup_session(); s.begin(("a",), p, ("a",), (0,1,2))
        s.plan(0, [], [0], [3], [False])
        with self.assertRaises(ValueError): s.finish()
    def test_slot_alias_rejected_before_native_call(self):
        m, s, p = self.setup_session(); s.begin(("a","b"), p, ("a","b"), (0,1,2,0,1,2))
        with self.assertRaises(ValueError): s.plan(0, [], [0,0], [3,3], [False,False])
    def test_decode_without_prefill_rejected(self):
        m, s, p = self.setup_session(); s.begin(("a",), p, ("a",), (3,))
        with self.assertRaises(ValueError): s.plan(0, [0], [], [], [])
    def test_prefix_hit_and_continuation_rejected(self):
        m, s, p = self.setup_session(); s.begin(("a",), p, ("a",), (0,1,2))
        with self.assertRaises(ValueError): s.plan(0, [], [0], [3], [True])
    def test_exact_decode_position_and_stable_slot(self):
        m, s, p = self.setup_session(); self.prefill(s, p)
        s.begin(("a",), p, ("a","b"), (3,))
        for layer in LAYERS:
            plan = s.plan(layer, [0], [], [], [])
            plan[0][2].advance([-1]*12)
        s.finish()
        s.begin(("a",), p, ("a","b"), (4,))
        with self.assertRaises(ValueError): s.plan(0, [1], [], [], [])
    def test_unscheduled_active_request_is_not_retired(self):
        m, s, p = self.setup_session(); self.prefill(s,p)
        s.begin(("b",),p,("a","b"),(0,1,2))
        with self.assertRaises(ValueError): s.plan(0, [], [0], [3], [False])
    def test_incomplete_retirement_rejected(self):
        m,s,p=self.setup_session(); self.prefill(s,p)
        with self.assertRaises(ValueError): s.begin(("b",),p,("b",),(0,1,2))
    def test_complete_slot_reuse_is_fresh_request(self):
        m,s,p=self.setup_session(); self.prefill(s,p)
        for layer in LAYERS:
            for _ in range(6): s.timelines[("a",layer)].advance([-1]*12)
        self.prefill(s,p,ids=("b",),slots=(0,),active=("b",))
        self.assertEqual(s.timelines[("b",0)].step,0)
        self.assertEqual(s.slots[(0,0)],"b")
    def test_logical_prompt_cannot_replay_under_new_runtime_id(self):
        m,s,p=self.setup_session(); self.prefill(s,p)
        p["c"]=p["a"]
        with self.assertRaises(ValueError): s.begin(("c",),p,("a","c"),(0,1,2))
    def test_cross_model_layer_prefix(self):
        self.assertEqual(layer_index("language_model.model.layers.62.linear_attn"),62)
        with self.assertRaises(ValueError): layer_index("language_model.model.layers.63.self_attn")
    def test_mixed_decode_then_new_prefill_proven_by_positions(self):
        m,s,p=self.setup_session(); self.prefill(s,p)
        s.begin(("a","b"),p,("a","b"),(3,0,1,2))
        for layer in LAYERS:
            plan=s.plan(layer,[0],[1],[3],[False])
            plan[0][2].advance([-1]*12)
        s.finish()
        self.assertEqual(s.timelines[("a",0)].step,1)
        self.assertEqual(s.timelines[("b",0)].step,0)


if __name__ == "__main__":
    unittest.main()
