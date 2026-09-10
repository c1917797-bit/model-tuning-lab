import json
import tempfile
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

import torch

from drror_vllm_ascend.envs import DrrqrConfig, get_config
from drror_vllm_ascend.patches.prefill_diagnostic import (
    install_prefill_diagnostic,
    tensor_stats,
)


def test_tensor_stats_are_full_and_json_safe():
    value = torch.tensor([1.0, -2.0, float("nan"), float("inf")])
    stats = tensor_stats(value)
    assert stats["finite_count"] == 2
    assert stats["nonfinite_count"] == 2
    assert stats["nan_count"] == 1
    assert stats["inf_count"] == 1
    json.dumps(stats, allow_nan=False)


def test_diagnostic_is_explicit_treatment_only():
    with patch.dict("os.environ", {"VLLM_ASCEND_DRRQR_PREFILL_DIAGNOSTIC": "1"}, clear=True):
        try:
            get_config()
        except ValueError as error:
            assert "require VLLM_ASCEND_DRRQR_ENABLE" in str(error)
        else:
            raise AssertionError("diagnostic unexpectedly enabled without treatment")


def test_first_nonfinite_chunk_stage_is_bound_to_exact_request():
    tokens = 4
    metadata = NS(
        num_prefills=1,
        num_decodes=0,
        num_actual_tokens=tokens,
        spec_sequence_masks=None,
    )

    def inner(q, k, v, g, beta, scale, initial_state, output_final_state,
              cu_seqlens=None, prebuilt_meta=None):
        output = v.clone()
        output[0, 0, 0, 0] = float("nan")
        return g, output, torch.ones(1), initial_state.clone(), None, None, None

    chunk_module = NS(chunk_gated_delta_rule_fwd=inner)

    def public(q, k, v, g, beta, scale=None, initial_state=None,
               output_final_state=False, cu_seqlens=None, prebuilt_meta=None,
               head_first=False, use_qk_l2norm_in_kernel=False):
        qn = torch.nn.functional.normalize(q.float(), dim=-1).to(q.dtype)
        kn = torch.nn.functional.normalize(k.float(), dim=-1).to(k.dtype)
        result = chunk_module.chunk_gated_delta_rule_fwd(
            qn, kn, v, g, beta, scale, initial_state, output_final_state,
            cu_seqlens, prebuilt_meta,
        )
        return result[1], result[3]

    gdn_module = NS(
        chunk_gated_delta_rule=public,
        get_forward_context=lambda: NS(attn_metadata={"layer.0": metadata}),
    )

    class Gdn:
        def __init__(self):
            self.prefix = "layer.0"

        def _forward_core(self, mixed_qkv, b, a, core_attn_out):
            del mixed_qkv, b, a
            q = torch.ones((1, tokens, 1, 2), dtype=torch.bfloat16)
            v = torch.ones((1, tokens, 1, 3), dtype=torch.bfloat16)
            state = torch.zeros((1, 1, 2, 3), dtype=torch.float32)
            output, _ = gdn_module.chunk_gated_delta_rule(
                q, q, v, torch.zeros((1, tokens, 1)),
                torch.ones((1, tokens, 1)), scale=1.0,
                initial_state=state, output_final_state=True,
                use_qk_l2norm_in_kernel=True,
            )
            core_attn_out.copy_(output.squeeze(0))
            return "unchanged-return"

    original_core = Gdn._forward_core
    with tempfile.TemporaryDirectory() as directory:
        evidence = Path(directory) / "evidence.jsonl"
        config = DrrqrConfig(
            enable=True,
            plan_path="/plan.json",
            plan_sha256="a" * 64,
            evidence_file=str(evidence),
            prefill_diagnostic=True,
            prefill_diagnostic_tokens=tokens,
        )
        install_prefill_diagnostic(Gdn, gdn_module, chunk_module, config)
        try:
            output = torch.empty((tokens, 1, 3), dtype=torch.bfloat16)
            assert Gdn()._forward_core(None, None, None, output) == "unchanged-return"
            row = json.loads(evidence.read_text(encoding="utf-8"))
            assert row["event"] == "prefill_finite_trace"
            assert row["first_nonfinite_stage"] == "chunk.output"
            assert row["stats"]["raw.q"]["nonfinite_count"] == 0
            assert row["stats"]["normalized.q"]["nonfinite_count"] == 0
            assert row["stats"]["chunk.output"]["nan_count"] == 1
            assert row["arithmetic_changed"] is False
            json.dumps(row, allow_nan=False)
        finally:
            Gdn._forward_core = original_core
