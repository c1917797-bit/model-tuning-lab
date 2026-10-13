import unittest
from types import SimpleNamespace,MappingProxyType
from independent_public_stage import CanonicalPublicStage
from independent_runner_context import CURRENT_PROMPT_TOKENS
from independent_request_map import freeze_request_slices
class PublicStageTests(unittest.TestCase):
    def test_exact_canonical_selector(self):
        stage=CanonicalPublicStage(model_identity='m',code_identity='c',
            public_tokens=list(range(16)),capacity_bytes=1024,boundary_tokens=3)
        req=freeze_request_slices(['a'],[0],[16],[0,16],rank=2,step=1)
        token=CURRENT_PROMPT_TOKENS.set(MappingProxyType({'a':tuple(range(16))}))
        try:
            selected=stage.select_public(SimpleNamespace(prefix='layer'),req)
            self.assertEqual((selected.layer,selected.rank,selected.length),('layer',2,16))
        finally:CURRENT_PROMPT_TOKENS.reset(token)
    def test_private_prompt_not_public_producer(self):
        stage=CanonicalPublicStage(model_identity='m',code_identity='c',
            public_tokens=list(range(16)),capacity_bytes=1024,boundary_tokens=3)
        req=freeze_request_slices(['a'],[0],[17],[0,17],rank=0,step=1)
        token=CURRENT_PROMPT_TOKENS.set({'a':(99,*range(16))})
        try:self.assertIsNone(stage.select_public(SimpleNamespace(prefix='layer'),req))
        finally:CURRENT_PROMPT_TOKENS.reset(token)
if __name__=='__main__':unittest.main()
