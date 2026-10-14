import unittest
from types import SimpleNamespace
from independent_compact_stage import CompactCanonicalStage
class ChunkSelectorTests(unittest.TestCase):
    def test_default_native_fallback_and_optin_contiguous_capture(self):
        config=dict(model_identity="model",code_identity="code",public_tokens=tuple(range(16384)),
            capacity_bytes=1048576,allow_public_tail=True)
        req=SimpleNamespace(computed_tokens=0,scheduled_tokens=15360,rank=0)
        prompt=tuple(range(16384))+(1,)*256
        default=CompactCanonicalStage(**config)
        self.assertIsNone(default.public_identity_for_request("layer",req,prompt))
        stage=CompactCanonicalStage(**config,allow_public_chunks=True)
        self.assertIsNotNone(stage.public_identity_for_request("layer",req,prompt))
        req.computed_tokens=15360;req.scheduled_tokens=1280
        self.assertIsNotNone(stage.public_identity_for_request("layer",req,prompt))
        req.computed_tokens=16640;req.scheduled_tokens=1
        self.assertIsNone(stage.public_identity_for_request("layer",req,prompt))
if __name__=="__main__":unittest.main()
