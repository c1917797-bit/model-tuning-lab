import unittest
from types import SimpleNamespace
import torch
from independent_public_stage import CanonicalPublicStage
from independent_runner_context import CURRENT_PROMPT_TOKENS
from independent_public_gdn_hook import prefix_material_inputs

class PublicTailTests(unittest.TestCase):
    def stage(self,enabled):
        return CanonicalPublicStage(model_identity="m",code_identity="c",
            public_tokens=range(16),capacity_bytes=4096,boundary_tokens=8,allow_public_tail=enabled)
    def test_optin_prefix_only_full_prefill(self):
        req=SimpleNamespace(request_id="r",computed_tokens=0,scheduled_tokens=20,rank=0)
        marker=CURRENT_PROMPT_TOKENS.set({"r":tuple(range(20))})
        try:
            self.assertIsNone(self.stage(False).select_public(SimpleNamespace(prefix="layer"),[req]))
            identity=self.stage(True).select_public(SimpleNamespace(prefix="layer"),[req])
            self.assertEqual(identity.length,16)
            req.computed_tokens=1
            self.assertIsNone(self.stage(True).select_public(SimpleNamespace(prefix="layer"),[req]))
        finally:CURRENT_PROMPT_TOKENS.reset(marker)
    def test_tail_never_enters_affine_or_conv_inputs(self):
        fields={n:torch.arange(20.).reshape(1,20,1) for n in ("k","v","g","beta")}
        projected=torch.arange(40.).reshape(20,2)
        a=prefix_material_inputs(16,projected,fields)
        for v in fields.values():v[:,16:]=999
        projected[16:]=999
        b=prefix_material_inputs(16,projected,fields)
        for x,y in zip(a,b):self.assertTrue(torch.equal(x,y))
        self.assertEqual(a[-1].shape,(16,2))
        with self.assertRaises(ValueError):prefix_material_inputs(21,projected,fields)
    def test_shifted_or_wrong_prefix_not_public(self):
        stage=self.stage(True)
        self.assertFalse(stage.is_public_prompt((99,)+tuple(range(16))))
        self.assertFalse(stage.is_public_prompt(tuple(range(15))))

if __name__=="__main__":unittest.main()
