import types,unittest
from unittest.mock import patch
from independent_prompt_snapshot import freeze_prompt_tokens
from independent_prefill_prompt_snapshot import freeze_prefill_prompt_tokens as candidate

class NoIteration:
    def __len__(self):return 32768
    def __iter__(self):raise AssertionError("decode prompt must not be copied")

def state(tokens,mm=()):return types.SimpleNamespace(prompt_token_ids=tokens,mm_features=mm)

class PrefillSnapshotTest(unittest.TestCase):
    def test_default_is_exact_original(self):
        states={"a":state([1,2]),"b":state([3])}
        self.assertEqual(candidate(states,states),freeze_prompt_tokens(states,states))
    def test_disabled_delegates_without_metadata(self):
        with patch("independent_prefill_prompt_snapshot.freeze_prompt_tokens",return_value="original") as f:
            self.assertEqual(candidate(["a"],{},enabled=False),"original")
            f.assert_called_once_with(("a",),{})
    def test_pure_decode_never_iterates_long_prompt(self):
        self.assertEqual(candidate(["a"],{"a":state(NoIteration())},
            computed_tokens=[32768],scheduled_tokens=[1],enabled=True),{"a":None})
    def test_decode_after_generated_tokens(self):
        self.assertEqual(candidate(["a"],{"a":state(NoIteration())},
            computed_tokens=[33000],scheduled_tokens=[1],enabled=True),{"a":None})
    def test_mixed_exact_prefill(self):
        states={"a":state(NoIteration()),"b":state([1,2,3])}
        self.assertEqual(candidate(["a","b"],states,computed_tokens=[32768,1],
            scheduled_tokens=[1,2],enabled=True),{"a":None,"b":(1,2,3)})
    def test_last_prompt_token_is_not_decode(self):
        self.assertEqual(candidate(["a"],{"a":state([1,2,3])},computed_tokens=[2],
            scheduled_tokens=[1],enabled=True),{"a":(1,2,3)})
    def test_producer_chunk_unchanged(self):
        self.assertEqual(candidate(["a"],{"a":state([1,2,3])},computed_tokens=[0],
            scheduled_tokens=[3],enabled=True),{"a":(1,2,3)})
    def test_multitoken_completed_prompt_not_fastpath(self):
        with patch("independent_prefill_prompt_snapshot.freeze_prompt_tokens",return_value={"a":(1,2)}) as f:
            out=candidate(["a"],{"a":state([1,2])},computed_tokens=[2],
                          scheduled_tokens=[2],enabled=True)
            self.assertEqual(out,{"a":(1,2)});f.assert_called_once()
    def test_multimodal_and_embeddings_stay_native(self):
        self.assertEqual(candidate(["a","b"],{"a":state(None),"b":state([1],["image"])},
            computed_tokens=[0,0],scheduled_tokens=[1,1],enabled=True),{"a":None,"b":None})
    def test_invalid_prefill_tokens_still_rejected(self):
        with self.assertRaises(ValueError):
            candidate(["a"],{"a":state([1,-2])},computed_tokens=[0],scheduled_tokens=[2],enabled=True)
    def test_empty_prompt_still_rejected(self):
        with self.assertRaises(ValueError):
            candidate(["a"],{"a":state([])},computed_tokens=[0],scheduled_tokens=[1],enabled=True)
    def test_bad_metadata(self):
        for done,count in [([-1],[1]),([True],[1]),([0],[False]),([0],[0]),([],[1]),([0,1],[1])]:
            with self.subTest(done=done,count=count),self.assertRaises(ValueError):
                candidate(["a"],{"a":state([1])},computed_tokens=done,scheduled_tokens=count,enabled=True)
    def test_duplicate_identity_rejected(self):
        with self.assertRaises(ValueError):
            candidate(["a","a"],{"a":state([1])},computed_tokens=[0,0],scheduled_tokens=[1,1],enabled=True)
    def test_mapping_and_tokens_are_private_immutable(self):
        tokens=[1,2];out=candidate(["a"],{"a":state(tokens)},computed_tokens=[0],
                                 scheduled_tokens=[2],enabled=True)
        tokens[0]=99;self.assertEqual(out["a"],(1,2))
        with self.assertRaises(TypeError):out["a"]=None
    def test_request_id_reuse_does_not_reuse_stale_snapshot(self):
        states={"a":state([1,2])}
        self.assertEqual(candidate(["a"],states,computed_tokens=[2],scheduled_tokens=[1],enabled=True),{"a":None})
        states["a"]=state([3,4,5])
        self.assertEqual(candidate(["a"],states,computed_tokens=[0],scheduled_tokens=[3],enabled=True),{"a":(3,4,5)})
    def test_nonboolean_switch_rejected(self):
        with self.assertRaises(ValueError):candidate([],{},enabled=1)
    def test_empty_batch_preserved(self):
        self.assertEqual(candidate([],{},enabled=True),{})
if __name__=="__main__":unittest.main()
