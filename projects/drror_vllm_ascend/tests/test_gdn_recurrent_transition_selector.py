import torch

from tools.analyze_gdn_recurrent_transition_selector import (
    CONFIGURATIONS,
    WIDTH,
    choose_indices,
    lock_fit_configuration,
    select_for_configuration,
)


def _terms():
    energy = torch.zeros(WIDTH)
    q_energy = torch.ones(WIDTH)
    k_energy = torch.ones(WIDTH)
    return {
        "energy": energy,
        "q_energy": q_energy,
        "k_energy": k_energy,
        "read": torch.zeros(WIDTH),
        "write": torch.zeros(WIDTH),
        "feedback": torch.zeros(WIDTH),
    }


def test_choose_indices_removes_lowest_scored_baseline_coordinate():
    terms = _terms()
    baseline = torch.arange(64)
    terms["energy"][baseline] = 1.0
    terms["energy"][10] = -5.0
    terms["energy"][127] = 8.0

    selected, metadata = choose_indices(
        terms, baseline, ("test", 0.0, 0.0, 0.0),
        max_swaps=1, floor_ratio=0.98,
    )

    assert selected.numel() == 64
    assert selected.unique().numel() == 64
    assert 10 not in selected.tolist()
    assert 127 in selected.tolist()
    assert metadata["removed"] == [10]
    assert metadata["added"] == [127]


def test_energy_configuration_is_the_frozen_plan_not_a_new_exchange():
    terms = _terms()
    baseline = torch.arange(64)
    terms["energy"][baseline] = 1.0
    terms["energy"][10] = -5.0
    terms["energy"][127] = 8.0

    selected, metadata = select_for_configuration(
        terms, baseline, ("energy", 0.0, 0.0, 0.0)
    )

    assert torch.equal(selected, baseline)
    assert metadata == {
        "swaps": 0,
        "q_energy_ratio": 1.0,
        "k_energy_ratio": 1.0,
        "removed": [],
        "added": [],
    }


def _train(changed_heads=1, state=1.0, post=1.0, operator=1.0):
    result = {}
    for name, *_ in CONFIGURATIONS:
        result[name] = {
            "changed_heads": changed_heads if name != "energy" else 0,
            "metrics": {
                "state_relative_l2": state,
                "post_rms_relative_l2": post,
                "operator_relative_l2": operator,
            },
        }
    result["energy"]["metrics"]["state_relative_l2"] = 1.0
    return result


def test_lock_fit_configuration_fails_closed_without_eligible_candidate():
    train = _train(state=1.01)
    assert lock_fit_configuration(train) is None


def test_lock_fit_configuration_uses_predeclared_metric_order():
    train = _train()
    train["read"]["metrics"]["post_rms_relative_l2"] = 0.8
    train["write"]["metrics"]["post_rms_relative_l2"] = 0.7
    assert lock_fit_configuration(train) == "write"
