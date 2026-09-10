import torch

from tools.analyze_gdn_tail_dot_compensation import (
    SKETCH_WIDTH,
    TAIL_WIDTH,
    advance_record,
    coordinate_sets,
    qk_coefficients,
    sketch_matrix,
)


def test_sketch_is_deterministic_scaled_orthoprojector():
    first = sketch_matrix("layer0.rank0.head0")
    second = sketch_matrix("layer0.rank0.head0")
    other = sketch_matrix("layer0.rank0.head1")
    assert torch.equal(first, second)
    assert not torch.equal(first, other)
    assert first.shape == (TAIL_WIDTH, SKETCH_WIDTH)
    gram = first.T @ first
    assert torch.allclose(
        gram,
        torch.eye(SKETCH_WIDTH) * (TAIL_WIDTH / SKETCH_WIDTH),
        atol=0,
        rtol=0,
    )


def test_coordinate_sets_partition_local_width():
    selected = torch.arange(0, 128, 2)
    kept, discarded = coordinate_sets(selected)
    assert kept.shape == discarded.shape == (64,)
    assert set(kept.tolist()).isdisjoint(discarded.tolist())
    assert sorted(kept.tolist() + discarded.tolist()) == list(range(128))


def test_qk_coefficients_shapes_and_zero_tail_exactness():
    selected = torch.arange(64)
    raw_q = torch.randn(3, 128)
    raw_k = torch.randn(3, 128)
    raw_q[:, 64:] = 0
    raw_k[:, 64:] = 0
    q, k, coefficient64, estimated = qk_coefficients(
        raw_q, raw_k, selected, sketch_matrix("zero-tail")
    )
    assert q.shape == k.shape == (3, 64)
    assert coefficient64.shape == estimated.shape == (3,)
    expected = (raw_q[:, :64] * raw_k[:, :64]).sum(dim=-1)
    expected = expected / (
        raw_q[:, :64].norm(dim=-1) * raw_k[:, :64].norm(dim=-1)
    )
    expected = expected * (128 ** -0.5)
    assert torch.allclose(estimated, expected, atol=1e-6, rtol=1e-6)


def test_correction_does_not_change_recurrent_state():
    torch.manual_seed(7)
    selected = torch.arange(64)
    item = {
        "q": torch.randn(2, 128),
        "k": torch.randn(2, 128),
        "v": torch.randn(2, 3, 128),
        "g": torch.randn(2, 3).clamp(max=0),
        "beta": torch.sigmoid(torch.randn(2, 3)),
    }
    state = torch.randn(3, 128, 64)
    baseline_state, baseline_output = advance_record(
        state.clone(), item, selected
    )
    candidate_state, candidate_output = advance_record(
        state.clone(), item, selected, sketch_matrix("state-identity")
    )
    assert torch.equal(baseline_state, candidate_state)
    assert baseline_output.shape == candidate_output.shape == (2, 3, 128)
    assert torch.isfinite(candidate_output).all()
