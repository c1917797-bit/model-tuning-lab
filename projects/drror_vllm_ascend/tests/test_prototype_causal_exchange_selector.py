import torch

from tools.prototype_causal_exchange_selector import (
    causal_pairs,
    normalized_sequences,
    optimize_head,
    retained_energy,
    score_subset,
)


def test_causal_pairs_exclude_future_keys():
    q = torch.eye(3)
    k = torch.eye(3)
    q_pair, k_pair, reference = causal_pairs([q], [k])
    assert q_pair.shape == k_pair.shape == (6, 3)
    assert reference.tolist() == [1.0, 0.0, 1.0, 0.0, 0.0, 1.0]


def test_exchange_is_deterministic_nonworsening_and_energy_bounded():
    generator = torch.Generator().manual_seed(23)
    q = normalized_sequences(
        [torch.randn(18, 8, generator=generator) for _ in range(3)], 12
    )
    k = normalized_sequences(
        [torch.randn(18, 8, generator=generator) for _ in range(3)], 12
    )
    initial = torch.tensor([0, 1, 2, 3])
    first = optimize_head(
        q, k, initial, energy_floor_ratio=0.9, pool_size=4, max_swaps=3
    )
    second = optimize_head(
        q, k, initial, energy_floor_ratio=0.9, pool_size=4, max_swaps=3
    )
    assert torch.equal(first["selected"], second["selected"])
    assert first["candidate_train_rmse"] <= first["baseline_train_rmse"]
    assert first["candidate_q_energy"] >= first["q_energy_floor"]
    assert first["candidate_k_energy"] >= first["k_energy_floor"]
    assert first["selected"].unique().numel() == initial.numel()

    q_pair, k_pair, reference = causal_pairs(q, k)
    before, count = score_subset(q_pair, k_pair, reference, initial)
    after, _ = score_subset(q_pair, k_pair, reference, first["selected"])
    assert after <= before + 1e-9
    assert count == 3 * (12 * 13 // 2)
    q_energy, k_energy = retained_energy(q, k, first["selected"])
    assert q_energy == first["candidate_q_energy"]
    assert k_energy == first["candidate_k_energy"]
