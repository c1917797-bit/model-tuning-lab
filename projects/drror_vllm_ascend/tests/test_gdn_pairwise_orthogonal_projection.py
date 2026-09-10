import torch

from tools.analyze_gdn_pairwise_orthogonal_projection import (
    TARGET,
    WIDTH,
    _normalized_psd,
    one_hot_transform,
    pairwise_transform,
    project_and_normalize,
    static_decode_operation_count,
)
from tools.analyze_gdn_recurrent_transition_selector import normalize


def test_normalized_psd_is_symmetric_unit_trace():
    source = torch.arange(WIDTH * 7, dtype=torch.float64).reshape(WIDTH, 7)
    gram = source @ source.T
    result = _normalized_psd(gram)
    assert torch.equal(result, result.T)
    assert torch.isclose(torch.trace(result), torch.tensor(1.0, dtype=torch.float64))
    assert float(torch.linalg.eigvalsh(result)[0]) >= -1e-10


def test_pairwise_transform_is_deterministic_orthonormal_and_disjoint():
    generator = torch.Generator().manual_seed(19)
    source = torch.randn((WIDTH, 48), generator=generator, dtype=torch.float64)
    gram = source @ source.T
    baseline = torch.arange(TARGET)

    first, first_metadata = pairwise_transform(gram, baseline)
    second, second_metadata = pairwise_transform(gram, baseline)

    assert torch.equal(first, second)
    assert first_metadata == second_metadata
    assert torch.allclose(
        first.T @ first, torch.eye(TARGET, dtype=torch.float64), atol=1e-12, rtol=0
    )
    assert int((first != 0).sum(dim=0).max()) <= 2
    assert int((first != 0).sum(dim=0).min()) >= 1
    assert sorted(item["anchor"] for item in first_metadata["pairs"]) == list(range(64))
    assert sorted(item["partner"] for item in first_metadata["pairs"]) == list(range(64, 128))


def test_one_hot_projection_exactly_matches_frozen_coordinate_semantics():
    generator = torch.Generator().manual_seed(23)
    raw = torch.randn((9, WIDTH), generator=generator)
    selected = torch.randperm(WIDTH, generator=generator)[:TARGET].sort().values
    transform = one_hot_transform(selected)
    projected = project_and_normalize(raw, transform)
    expected = normalize(raw.index_select(-1, selected))
    assert torch.equal(projected, expected)


def test_static_projection_cost_is_bounded_and_not_a_speed_claim():
    result = static_decode_operation_count()
    assert result["projection_scalar_ops"] == 1536
    assert result["estimated_recurrent_scalar_ops_removed"] == 786432
    assert result["projection_over_removed_ratio"] < 0.10
    assert "not latency" in result["claim"]
