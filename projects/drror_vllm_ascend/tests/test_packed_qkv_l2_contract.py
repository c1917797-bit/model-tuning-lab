from pathlib import Path


ROOT = Path(__file__).parents[1]
KERNEL = (ROOT / "drror_vllm_ascend/kernels/packed_qkv_l2.py").read_text()
PROBE = (ROOT / "tools/packed_qkv_l2_probe.py").read_text()


def test_kernel_is_fail_closed_to_admitted_tp4_dk64_layout():
    for token in (
        "(4, 12, 64, 128)",
        "rank-2 BF16",
        "width/stride contract",
        "is_contiguous()",
    ):
        assert token in KERNEL


def test_kernel_preserves_exact_normalization_boundary():
    for token in (
        "tl.float32",
        "tl.sum(values * values",
        "tl.rsqrt",
        "1e-6",
        "tl.bfloat16",
    ):
        assert token in KERNEL


def test_probe_uses_real_reference_and_graph_exactness():
    for token in (
        "from vllm.model_executor.layers.fla.ops.l2norm import l2norm_fwd",
        "torch.cat",
        "graph.replay()",
        "eager_exact",
        "graph_exact",
        "graph_pointers_stable",
    ):
        assert token in PROBE


def test_probe_disclaims_higher_level_claims():
    for token in (
        "not recurrent-state",
        "endpoint performance",
        "accuracy",
        "integration",
        "portability proof",
    ):
        assert token in PROBE
