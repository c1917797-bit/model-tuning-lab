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
            rows = [
                json.loads(line)
                for line in evidence.read_text(encoding="utf-8").splitlines()
            ]
            row = next(row for row in rows if row["event"] == "prefill_finite_trace")
            assert row["event"] == "prefill_finite_trace"
            assert row["first_nonfinite_stage"] == "chunk.output"
            assert row["stats"]["raw.q"]["nonfinite_count"] == 0
            assert row["stats"]["normalized.q"]["nonfinite_count"] == 0
            assert row["stats"]["chunk.output"]["nan_count"] == 1
            assert row["arithmetic_changed"] is False
            json.dumps(row, allow_nan=False)
        finally:
            Gdn._forward_core = original_core


def test_mixed_state_trace_binds_cache_identity_and_first_nonfinite_stage():
    tokens = 4
    metadata = NS(
        num_prefills=1,
        num_decodes=0,
        num_decode_tokens=0,
        num_actual_tokens=tokens,
        prefill_state_indices=torch.tensor([2]),
        non_spec_state_indices_tensor=torch.tensor([], dtype=torch.long),
        spec_sequence_masks=None,
    )
    chunk_module = NS(
        chunk_gated_delta_rule_fwd=lambda *args, **kwargs: (
            args[3], args[2], torch.ones(1), args[6].clone(), None, None, None
        )
    )

    def public(q, k, v, g, beta, scale=None, initial_state=None,
               output_final_state=False, cu_seqlens=None, prebuilt_meta=None,
               head_first=False, use_qk_l2norm_in_kernel=False):
        del scale, output_final_state, cu_seqlens, prebuilt_meta, head_first
        del use_qk_l2norm_in_kernel
        result = chunk_module.chunk_gated_delta_rule_fwd(
            q, k, v, g, beta, None, initial_state, True, None, None
        )
        return result[1], result[3]

    gdn_module = NS(
        chunk_gated_delta_rule=public,
        get_forward_context=lambda: NS(attn_metadata={"layer.0": metadata}),
    )

    class Gdn:
        def __init__(self):
            self.prefix = "layer.0"
            self.kv_cache = [
                torch.zeros((8, 1, 2)),
                torch.zeros((8, 1, 2, 3), dtype=torch.float32),
            ]

        def _forward_core(self, mixed_qkv, b, a, core_attn_out):
            del mixed_qkv, b, a
            core_attn_out.fill_(1)
            if metadata.num_decodes:
                self.kv_cache[1][3, 0, 0, 0] = float("nan")
            return "unchanged-return"

    original_core = Gdn._forward_core
    with tempfile.TemporaryDirectory() as directory:
        evidence = Path(directory) / "evidence.jsonl"
        config = DrrqrConfig(
            enable=True,
            plan_path="/plan.json",
            plan_sha256="b" * 64,
            evidence_file=str(evidence),
            prefill_diagnostic=True,
            prefill_diagnostic_tokens=tokens,
        )
        install_prefill_diagnostic(Gdn, gdn_module, chunk_module, config)
        try:
            instance = Gdn()
            output = torch.empty((tokens, 1, 3))
            inputs = torch.ones((tokens, 2))
            instance._forward_core(inputs, inputs, inputs, output)
            metadata.num_prefills = 0
            metadata.num_decodes = 1
            metadata.num_decode_tokens = 1
            metadata.num_actual_tokens = 1
            metadata.prefill_state_indices = torch.tensor([], dtype=torch.long)
            metadata.non_spec_state_indices_tensor = torch.tensor([3])
            instance._forward_core(inputs[:1], inputs[:1], inputs[:1], output[:1])
            rows = [
                json.loads(line)
                for line in evidence.read_text(encoding="utf-8").splitlines()
            ]
            mixed = [row for row in rows if row["event"] == "mixed_state_finite_trace"]
            assert len(mixed) == 2
            decode = mixed[-1]
            assert decode["phase"] == "decode"
            assert decode["decode_state_indices"] == [3]
            assert decode["invalid_state_indices"] == []
            assert decode["first_nonfinite_stage"] == "state.ssm.after"
            assert decode["stats"]["state.ssm.before"]["nonfinite_count"] == 0
            assert decode["stats"]["state.ssm.after"]["nan_count"] == 1
            assert decode["ssm_storage"]["data_ptr"] == (
                instance.kv_cache[1].untyped_storage().data_ptr()
            )
            assert decode["arithmetic_changed"] is False
        finally:
            Gdn._forward_core = original_core
