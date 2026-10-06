"""Offline deterministic builder tests: mock-tokenizer tests are not real runtime proof."""
import copy
import unittest
from damp_capture.contract import digest
from damp_capture.training_sources import PLAN, validate_plan
from damp_capture.build_full import (fixed_chat, build_rows, native_chat, character_probes,
                                     fit_context, NoExactBoundary)


class CharTokenizer:
    all_special_tokens=("[pad]",)
    def encode(self,text,add_special_tokens=False):
        return [ord(c) for c in text]
    def decode(self,ids,**kwargs):
        return "".join(chr(i) for i in ids)
    def apply_chat_template(self,messages,tokenize,return_dict,add_generation_prompt,enable_thinking):
        assert tokenize and return_dict is False and add_generation_prompt and not enable_thinking
        return self.encode("[user]"+messages[0]["content"]+"[/user][assistant]")


class GapTokenizer(CharTokenizer):
    """Deliberately skips exact1024 for one original context prefix, not real tokenizer."""
    def apply_chat_template(self, messages, **kwargs):
        ids = super().apply_chat_template(messages, **kwargs)
        content = messages[0]["content"]
        if content.startswith("Independent training-domain reference questions follow.\n\nReference question:\nBAD") and len(ids) == 1024:
            return ids + [12345]
        return ids


def context_record(name, good=False):
    return dict(domain="math", text=("GOOD" if good else "BAD") + " real TRAIN material " * 100,
                key=("MATH", name), source=dict(dataset="MATH", split="train", record_id=name,
                                                record_sha256=digest(name)))


class TrainingSourceTests(unittest.TestCase):
    def test_exact_pinned_train_source_budget(self):
        validate_plan()
        self.assertEqual(sum(a["size"] for a in PLAN["artifacts"]),110296287)
        self.assertEqual(len(PLAN["artifacts"]),9)
        self.assertLess(sum(a["size"] for a in PLAN["artifacts"]),128*1024*1024)
    def test_test_split_never_admitted(self):
        plan=copy.deepcopy(PLAN); plan["artifacts"][0]["split"]="test"
        with self.assertRaises(ValueError): validate_plan(plan)
    def test_test_path_never_admitted(self):
        plan=copy.deepcopy(PLAN); plan["artifacts"][0]["path"]="algebra/test.parquet"
        with self.assertRaises(ValueError): validate_plan(plan)
    def test_exact1024_keeps_full_target_and_native_template(self):
        tok=CharTokenizer()
        text,ids,meta=fixed_chat(tok,"Actual training context\n"*100,"What is two plus two?")
        self.assertEqual(len(ids),1024)
        self.assertEqual(ids,native_chat(tok,text))
        self.assertTrue(text.endswith("What is two plus two?\nSolve the target problem."))
        self.assertLess(meta["context_prefix_tokens"],meta["context_full_tokens"])
    def test_short_context_no_synthetic_padding(self):
        with self.assertRaises(ValueError): fixed_chat(CharTokenizer(),"short","target")
    def test_raw_character_diagnostic_is_exact_original_utf8_prefix(self):
        context = "Original TRAIN context 中文 😀\n" * 100
        target = "Complete target must survive."
        result = character_probes(CharTokenizer(), context, target)
        self.assertTrue(result["exact_codepoint_boundaries"])
        self.assertLessEqual(len(result["probes"]), 1045)
        for end in result["exact_codepoint_boundaries"]:
            prefix = context[:end]
            self.assertEqual(prefix.encode("utf-8").decode("utf-8"), prefix)
            text = prefix + "\nTarget problem:\n" + target + "\nSolve the target problem."
            self.assertEqual(len(native_chat(CharTokenizer(), text)), 1024)
    def test_raw_character_diagnostic_budget_is_finite(self):
        with self.assertRaises(ValueError): character_probes(CharTokenizer(), "x" * 65537, "target")
        with self.assertRaises(ValueError): character_probes(CharTokenizer(), "x" * 2000, "target", radius=513)
    def test_proven_gap_only_uses_next_real_train_reference(self):
        initial, extra = context_record("first"), context_record("next", good=True)
        text, ids, trim, selected = fit_context(GapTokenizer(), "Keep COMPLETE target", [initial], iter([extra]))
        self.assertEqual(len(ids), 1024)
        self.assertEqual(selected, [extra, initial])
        self.assertEqual(trim["boundary_candidate_attempt"], 1)
        self.assertEqual(len(trim["rejected_context_candidates"]), 1)
        rejected = trim["rejected_context_candidates"][0]
        self.assertEqual(rejected["context_records"], [initial["source"]])
        self.assertNotIn(1024, [p[1] for p in rejected["nearest_lengths"]])
        self.assertTrue(text.endswith("Keep COMPLETE target\nSolve the target problem."))
        self.assertEqual(ids, native_chat(GapTokenizer(), text))
    def test_gap_rule_consumes_no_more_than_three_new_records(self):
        extras = [context_record(str(i)) for i in range(4)]
        iterator = iter(extras)
        with self.assertRaisesRegex(ValueError, "all four bounded"):
            fit_context(GapTokenizer(), "Keep target", [context_record("initial")], iterator)
        self.assertEqual(next(iterator), extras[3])
    def test_gap_cannot_borrow_test_data_or_reuse_source(self):
        initial = context_record("initial")
        bad = context_record("next", good=True); bad["source"]["split"] = "test"
        for extra in (bad, copy.deepcopy(initial)):
            with self.subTest(extra=extra["source"]), self.assertRaises(ValueError):
                fit_context(GapTokenizer(), "Complete target", [initial], iter([extra]))
    def test_long_target_fail_closed(self):
        with self.assertRaises(ValueError): fixed_chat(CharTokenizer(),"context"*300,"x"*1100)
    def test_deterministic_balanced36_and_all_context_disjoint(self):
        pools={}
        for domain,dataset in (("math","MATH"),("code","APPS"),("general","ARC-Challenge")):
            pools[domain]=[dict(domain=domain,text=f"Question {i} "+("real " * 40),
                                key=(dataset,str(i)),
                                source=dict(dataset=dataset,split="train",record_id=str(i),
                                            record_sha256=digest([domain,i])))
                           for i in range(240)]
        first=build_rows(CharTokenizer(),pools)
        second=build_rows(CharTokenizer(),pools)
        self.assertEqual(first,second)
        self.assertEqual(len(first),36)
        keys=set()
        for row in first:
            self.assertEqual(len(row["input_ids"]),1024)
            for source in [row["source"]]+row["context_records"]:
                key=(source["dataset"],source["record_id"])
                self.assertNotIn(key,keys);keys.add(key)
        from collections import Counter
        self.assertEqual(Counter((r["domain"],r["split"]) for r in first),
                         Counter({(d,s):4 for d in pools for s in ("fit","tune","validation")}))
    def test_missing_domain_does_not_fallback_to_smoke(self):
        with self.assertRaises(ValueError): build_rows(CharTokenizer(),{"math":[],"code":[],"general":[]})


if __name__=="__main__":
    unittest.main()
