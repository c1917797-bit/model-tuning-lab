from scripts.benchmark_qwen35_mmar_add_rmsnorm import geometric_mean, summarize


def cell(speedup: float, correct: bool = True) -> dict:
    return {
        "candidate_speedup_vs_control": speedup,
        "correctness": {"allclose_both": correct},
    }


def test_geometric_mean() -> None:
    assert geometric_mean([1.0, 4.0]) == 2.0


def test_promotes_only_when_every_cell_is_correct_and_non_regressing() -> None:
    result = summarize([cell(1.02), cell(1.04)], min_speedup=1.02)
    assert result["decision"] == "promote-fused-tail-to-e2e"
    assert result["correctness_pass"] is True


def test_rejects_one_regressing_cell() -> None:
    result = summarize([cell(1.20), cell(0.99)], min_speedup=1.02)
    assert result["decision"] == "reject-fused-tail-before-e2e"


def test_rejects_incorrect_result() -> None:
    result = summarize([cell(1.20), cell(1.20, correct=False)], min_speedup=1.02)
    assert result["decision"] == "reject-fused-tail-before-e2e"
    assert result["correctness_pass"] is False
