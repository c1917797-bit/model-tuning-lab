import json
from pathlib import Path
from types import SimpleNamespace

from drror_vllm_ascend.envs import DrrqrConfig
from drror_vllm_ascend.patches.gdn import install_decode_packed_qkv_l2


class Tensor:
    def __init__(self, shape):
        self.shape = shape


class Gdn:
    prefix = "layer"
    head_k_dim = 64
    head_v_dim = 128
    key_dim = 1024
    value_dim = 6144
    tp_size = 4

    def rearrange_mixed_qkv(self, mixed):
        return ("original", mixed)


def config(tmp_path):
    return DrrqrConfig(
        enable=True,
        plan_path="/plan.json",
        plan_sha256="a" * 64,
        evidence_file=str(tmp_path / "evidence.jsonl"),
        packed_qkv_l2=True,
    )


def test_pure_dk64_decode_uses_kernel_and_skips_exact_two_l2_calls(tmp_path):
    metadata = SimpleNamespace(
        spec_sequence_masks=None,
        num_prefills=0,
        num_decodes=2,
        num_decode_tokens=2,
    )
    module = SimpleNamespace(
        get_forward_context=lambda: SimpleNamespace(
            attn_metadata={"layer": metadata}
        ),
        l2norm_fwd=lambda value: ("normalized", value),
    )
    outputs = (object(), object(), object())
    calls = []

    def kernel(mixed, **kwargs):
        calls.append((mixed, kwargs))
        return outputs

    install_decode_packed_qkv_l2(Gdn, module, config(tmp_path), kernel=kernel)
    instance = Gdn()
    result = instance.rearrange_mixed_qkv(Tensor((2, 2048)))
    assert result is outputs
    assert calls[0][1] == {
        "h_qk": 4, "h_v": 12, "d_k": 64, "d_v": 128
    }
    assert module.l2norm_fwd(outputs[0]) is outputs[0]
    assert module.l2norm_fwd(outputs[1]) is outputs[1]
    assert module.l2norm_fwd(outputs[2]) == ("normalized", outputs[2])
    event = json.loads(Path(config(tmp_path).evidence_file).read_text().splitlines()[0])
    assert event["event"] == "packed_qkv_l2_patch_installed"


def test_prefill_keeps_original_rearrange_and_l2(tmp_path):
    class PrefillGdn:
        prefix = "layer"
        head_k_dim = 64
        head_v_dim = 128
        key_dim = 1024
        value_dim = 6144
        tp_size = 4

        def rearrange_mixed_qkv(self, mixed):
            return ("original", mixed)

    metadata = SimpleNamespace(
        spec_sequence_masks=None,
        num_prefills=1,
        num_decodes=0,
        num_decode_tokens=0,
    )
    module = SimpleNamespace(
        get_forward_context=lambda: SimpleNamespace(attn_metadata=metadata),
        l2norm_fwd=lambda value: ("normalized", value),
    )
    install_decode_packed_qkv_l2(
        PrefillGdn,
        module,
        config(tmp_path),
        kernel=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("kernel must not run")
        ),
    )
    mixed = Tensor((8, 2048))
    assert PrefillGdn().rearrange_mixed_qkv(mixed) == ("original", mixed)
    assert module.l2norm_fwd(mixed) == ("normalized", mixed)
