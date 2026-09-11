from pathlib import Path


SOURCE = (
    Path(__file__).parents[1] / "tools" / "drrqr_recurrent_microbench.py"
).read_text()


def test_screen_uses_frozen_tp4_local_dk64_shape():
    for token in (
        "H_QK, H_V, D_V, D_K = 4, 12, 128, 64",
        "BATCHES = (1, 16)",
        '"state_dtype": "bfloat16"',
    ):
        assert token in SOURCE


def test_screen_has_warmup_repeated_device_timing_and_graph_replay():
    for token in (
        "WARMUP = 20",
        "BLOCKS = 7",
        "CALLS_PER_BLOCK = 100",
        "torch.npu.Event(enable_timing=True)",
        "graph.replay()",
        "median_device_ms",
    ):
        assert token in SOURCE


def test_screen_requires_exact_plugin_artifacts_and_fresh_output():
    for token in (
        "bridge.configure_exact_opapi",
        "configured_opapi_path",
        "output.exists()",
        "fresh directory",
        "ASCEND_RT_VISIBLE_DEVICES",
    ):
        assert token in SOURCE


def test_screen_explicitly_disclaims_endpoint_and_accuracy_evidence():
    for token in (
        "not endpoint throughput",
        "TTFT",
        "TPOT",
        "accuracy",
        "cross-host",
    ):
        assert token in SOURCE
