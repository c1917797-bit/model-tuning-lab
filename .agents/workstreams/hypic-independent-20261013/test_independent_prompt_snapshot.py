import unittest
from types import SimpleNamespace
from independent_prompt_snapshot import freeze_prompt_tokens
class PromptSnapshotTests(unittest.TestCase):
    def test_runtime_mutation_isolated(self):
        s=SimpleNamespace(prompt_token_ids=[1,2,3],mm_features=[])
        out=freeze_prompt_tokens(['a'],{'a':s});s.prompt_token_ids[0]=8
        self.assertEqual(out['a'],(1,2,3))
        with self.assertRaises(TypeError):out['a']=()
    def test_multimodal_is_explicitly_unsupported(self):
        s=SimpleNamespace(prompt_token_ids=[1,2],mm_features=['image'])
        self.assertIsNone(freeze_prompt_tokens(['a'],{'a':s})['a'])
if __name__=='__main__':unittest.main()
