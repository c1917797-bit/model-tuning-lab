#!/usr/bin/env python3
"""Prototype train-only causal coordinate exchanges from an energy-Dk64 map.

This is a representative-layer CPU screening proxy.  It neither changes the
served plan nor establishes NPU, endpoint-performance, accuracy, or portability
acceptance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

import torch
import torch.nn.functional as F


LAYER_RE = re.compile(r"(?:^|\.)layers\.(\d+)(?:\.|$)")
DEFAULT_LAYERS = (0, 12, 25, 38, 50, 62)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sample_rows(tensor: torch.Tensor, maximum: int) -> torch.Tensor:
    if tensor.ndim != 2 or tensor.shape[0] < 1 or maximum < 1:
        raise ValueError("invalid token sampling input")
    if tensor.shape[0] <= maximum:
        return tensor
    rows = torch.linspace(0, tensor.shape[0] - 1, steps=maximum).round().long().unique()
    return tensor.index_select(0, rows)


def normalized_sequences(
    sequences: list[torch.Tensor], maximum: int
) -> list[torch.Tensor]:
    return [
        F.normalize(sample_rows(item.float(), maximum), p=2.0, dim=-1, eps=1e-6)
        for item in sequences
    ]


def causal_pairs(
    q_sequences: list[torch.Tensor],
    k_sequences: list[torch.Tensor],
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    if not q_sequences or len(q_sequences) != len(k_sequences):
        raise ValueError("Q/K sequence coverage mismatch")
    q_rows, k_rows, references = [], [], []
    width = q_sequences[0].shape[1]
    for q, k in zip(q_sequences, k_sequences, strict=True):
        if q.ndim != 2 or q.shape != k.shape or q.shape[1] != width:
            raise ValueError("Q/K sequence shape mismatch")
        pair = torch.tril_indices(q.shape[0], q.shape[0])
        q_pair, k_pair = q[pair[0]], k[pair[1]]
        q_rows.append(q_pair)
        k_rows.append(k_pair)
        references.append((q_pair * k_pair).sum(dim=-1))
    return torch.cat(q_rows), torch.cat(k_rows), torch.cat(references)


def retained_energy(
    q_sequences: list[torch.Tensor],
    k_sequences: list[torch.Tensor],
    selected: torch.Tensor,
) -> tuple[float, float]:
    q = torch.cat(q_sequences)
    k = torch.cat(k_sequences)
    return (
        float(q.index_select(1, selected).square().sum() / q.square().sum()),
        float(k.index_select(1, selected).square().sum() / k.square().sum()),
    )


def score_subset(
    q_pair: torch.Tensor,
    k_pair: torch.Tensor,
    reference: torch.Tensor,
    selected: torch.Tensor,
) -> tuple[float, int]:
    q = q_pair.index_select(1, selected)
    k = k_pair.index_select(1, selected)
    score = (q * k).sum(dim=1) / (
        q.square().sum(dim=1).clamp_min(1e-24).sqrt()
        * k.square().sum(dim=1).clamp_min(1e-24).sqrt()
    )
    return float((score - reference).square().sum()), score.numel()


def optimize_head(
    train_q: list[torch.Tensor],
    train_k: list[torch.Tensor],
    initial: torch.Tensor,
    *,
    energy_floor_ratio: float = 0.98,
    pool_size: int = 12,
    max_swaps: int = 4,
) -> dict:
    width = train_q[0].shape[1]
    if (
        initial.ndim != 1
        or initial.numel() >= width
        or initial.unique().numel() != initial.numel()
        or not 0 < energy_floor_ratio <= 1
        or pool_size < 1
        or max_swaps < 0
    ):
        raise ValueError("invalid causal exchange contract")
    q_pair, k_pair, reference = causal_pairs(train_q, train_k)
    selected = initial.clone().sort().values
    baseline_q, baseline_k = retained_energy(train_q, train_k, selected)
    q_floor, k_floor = baseline_q * energy_floor_ratio, baseline_k * energy_floor_ratio
    q_energy = torch.cat(train_q).square().sum(dim=0)
    k_energy = torch.cat(train_k).square().sum(dim=0)
    joint_energy = q_energy + k_energy
    contribution = q_pair * k_pair
    alignment = (contribution * reference[:, None]).mean(dim=0)
    current_square, pair_count = score_subset(q_pair, k_pair, reference, selected)
    swaps = []
    for _ in range(max_swaps):
        mask = torch.zeros(width, dtype=torch.bool)
        mask[selected] = True
        removals = selected[
            torch.argsort(joint_energy[selected], stable=True)[:pool_size]
        ]
        additions = torch.arange(width)[~mask]
        additions = additions[
            torch.argsort(alignment[additions], descending=True, stable=True)[:pool_size]
        ]
        remove = removals.repeat_interleave(additions.numel())
        add = additions.repeat(removals.numel())
        base_q = q_pair.index_select(1, selected)
        base_k = k_pair.index_select(1, selected)
        numerator = (base_q * base_k).sum(dim=1)
        q_norm = base_q.square().sum(dim=1)
        k_norm = base_k.square().sum(dim=1)
        candidate_numerator = (
            numerator[None, :]
            - (q_pair[:, remove] * k_pair[:, remove]).T
            + (q_pair[:, add] * k_pair[:, add]).T
        )
        candidate_q_norm = (
            q_norm[None, :] - q_pair[:, remove].square().T
            + q_pair[:, add].square().T
        )
        candidate_k_norm = (
            k_norm[None, :] - k_pair[:, remove].square().T
            + k_pair[:, add].square().T
        )
        scores = candidate_numerator / (
            candidate_q_norm.clamp_min(1e-24).sqrt()
            * candidate_k_norm.clamp_min(1e-24).sqrt()
        )
        square_errors = (scores - reference[None, :]).square().sum(dim=1)
        current_q, current_k = retained_energy(train_q, train_k, selected)
        candidate_q = current_q + (
            q_energy[add] - q_energy[remove]
        ).double().numpy() / float(torch.cat(train_q).square().sum())
        candidate_k = current_k + (
            k_energy[add] - k_energy[remove]
        ).double().numpy() / float(torch.cat(train_k).square().sum())
        allowed = torch.from_numpy(
            (candidate_q >= q_floor) & (candidate_k >= k_floor)
        )
        square_errors[~allowed] = float("inf")
        best = int(torch.argmin(square_errors))
        best_square = float(square_errors[best])
        if not math.isfinite(best_square) or best_square >= current_square - 1e-12:
            break
        removed, added = int(remove[best]), int(add[best])
        selected[selected == removed] = added
        selected = selected.sort().values
        swaps.append(
            {
                "removed": removed,
                "added": added,
                "train_rmse_before": math.sqrt(current_square / pair_count),
                "train_rmse_after": math.sqrt(best_square / pair_count),
            }
        )
        current_square = best_square
    final_q, final_k = retained_energy(train_q, train_k, selected)
    return {
        "selected": selected,
        "swaps": swaps,
        "pair_count": pair_count,
        "baseline_train_rmse": math.sqrt(
            score_subset(q_pair, k_pair, reference, initial.sort().values)[0]
            / pair_count
        ),
        "candidate_train_rmse": math.sqrt(current_square / pair_count),
        "baseline_q_energy": baseline_q,
        "baseline_k_energy": baseline_k,
        "candidate_q_energy": final_q,
        "candidate_k_energy": final_k,
        "q_energy_floor": q_floor,
        "k_energy_floor": k_floor,
    }


def parse_indices(value: str) -> tuple[int, ...]:
    try:
        result = tuple(int(item) for item in value.split(","))
    except ValueError as error:
        raise argparse.ArgumentTypeError("indices must be comma-separated integers") from error
    if not result or tuple(sorted(set(result))) != result or result[0] < 0:
        raise argparse.ArgumentTypeError("indices must be sorted unique non-negative integers")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-dir", type=Path, required=True)
    parser.add_argument("--baseline-plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--layers", type=parse_indices, default=DEFAULT_LAYERS)
    parser.add_argument("--train-indices", type=parse_indices, default=parse_indices("0,1,2,3,4,5,6,7,8,9,10,11"))
    parser.add_argument("--heldout-indices", type=parse_indices, default=parse_indices("12,13,14,15"))
    parser.add_argument("--train-tokens", type=int, default=16)
    parser.add_argument("--heldout-tokens", type=int, default=64)
    parser.add_argument("--energy-floor-ratio", type=float, default=0.98)
    parser.add_argument("--pool-size", type=int, default=12)
    parser.add_argument("--max-swaps", type=int, default=4)
    args = parser.parse_args()
    if args.output.exists() or set(args.train_indices) & set(args.heldout_indices):
        parser.error("output must not exist and train/heldout indices must be disjoint")
    plan = json.loads(args.baseline_plan.read_text())
    if (
        plan.get("schema") != "ascend-drrqr-plan/v1"
        or plan.get("selection_objective") != "energy-kernel"
        or plan.get("old_head_k_dim") != 128
        or plan.get("target_head_k_dim") != 64
        or plan.get("num_key_heads") != 16
    ):
        raise ValueError("expected frozen energy-Dk64 plan")
    groups: dict[tuple[int, int, int], dict] = {}
    wanted = set(args.train_indices) | set(args.heldout_indices)
    for path in sorted(args.capture_dir.glob("*.pt")):
        payload = torch.load(path, map_location="cpu", weights_only=True)
        index = int(payload.get("capture_index", -1))
        match = LAYER_RE.search(str(payload.get("prefix", "")))
        if index not in wanted or match is None or int(match.group(1)) not in args.layers:
            continue
        layer, rank = int(match.group(1)), int(payload.get("tp_rank", -1))
        key = (layer, rank, index)
        q, k = payload.get("q"), payload.get("k")
        required = {
            "schema": "drrqr-post-conv-qk/v2",
            "target_model_id": "Qwen/Qwen3.8-27B",
            "source_config_sha256": plan["source_config_sha256"],
            "source_index_sha256": plan["source_index_sha256"],
            "calibration_sha256": plan["provenance"]["calibration_sha256"],
            "stage": "post_conv_qk",
            "tp_size": 4,
            "old_head_k_dim": 128,
            "local_key_dim": 512,
        }
        if (
            key in groups
            or rank not in range(4)
            or any(payload.get(name) != value for name, value in required.items())
            or not isinstance(q, torch.Tensor)
            or not isinstance(k, torch.Tensor)
            or q.shape != k.shape
            or q.ndim != 2
            or q.shape[1] != 512
            or not torch.isfinite(q).all()
            or not torch.isfinite(k).all()
        ):
            raise ValueError(f"invalid or duplicate capture {path}")
        groups[key] = payload
    expected = {
        (layer, rank, index)
        for layer in args.layers
        for rank in range(4)
        for index in wanted
    }
    if set(groups) != expected:
        raise RuntimeError(f"capture coverage mismatch: {len(groups)} != {len(expected)}")

    records = []
    baseline_square = candidate_square = 0.0
    heldout_pairs = 0
    for layer in args.layers:
        global_keep = torch.tensor(plan["keep_indices"][str(layer)]).reshape(16, 64)
        for rank in range(4):
            payloads = {index: groups[layer, rank, index] for index in wanted}
            q_by_index = {
                index: payload["q"].float().view(-1, 4, 128)
                for index, payload in payloads.items()
            }
            k_by_index = {
                index: payload["k"].float().view(-1, 4, 128)
                for index, payload in payloads.items()
            }
            for head in range(4):
                global_head = rank * 4 + head
                initial = global_keep[global_head] - global_head * 128
                train_q = normalized_sequences(
                    [q_by_index[index][:, head] for index in args.train_indices],
                    args.train_tokens,
                )
                train_k = normalized_sequences(
                    [k_by_index[index][:, head] for index in args.train_indices],
                    args.train_tokens,
                )
                result = optimize_head(
                    train_q,
                    train_k,
                    initial,
                    energy_floor_ratio=args.energy_floor_ratio,
                    pool_size=args.pool_size,
                    max_swaps=args.max_swaps,
                )
                heldout_q = normalized_sequences(
                    [q_by_index[index][:, head] for index in args.heldout_indices],
                    args.heldout_tokens,
                )
                heldout_k = normalized_sequences(
                    [k_by_index[index][:, head] for index in args.heldout_indices],
                    args.heldout_tokens,
                )
                q_pair, k_pair, reference = causal_pairs(heldout_q, heldout_k)
                before, count = score_subset(q_pair, k_pair, reference, initial.sort().values)
                after, _ = score_subset(q_pair, k_pair, reference, result["selected"])
                baseline_square += before
                candidate_square += after
                heldout_pairs += count
                records.append(
                    {
                        "layer": layer,
                        "rank": rank,
                        "local_head": head,
                        "global_head": global_head,
                        **{key: value for key, value in result.items() if key != "selected"},
                        "selected": result["selected"].tolist(),
                        "heldout_pair_count": count,
                        "baseline_heldout_rmse": math.sqrt(before / count),
                        "candidate_heldout_rmse": math.sqrt(after / count),
                    }
                )
    baseline_rmse = math.sqrt(baseline_square / heldout_pairs)
    candidate_rmse = math.sqrt(candidate_square / heldout_pairs)
    energy_ok = all(
        row["candidate_q_energy"] >= row["q_energy_floor"]
        and row["candidate_k_energy"] >= row["k_energy_floor"]
        for row in records
    )
    report = {
        "schema": "drrqr-causal-exchange-prototype/v1",
        "status": "passed" if candidate_rmse <= 0.9 * baseline_rmse and energy_ok else "rejected",
        "claim_boundary": "Representative-layer CPU proxy only; not an NPU, endpoint, accuracy, or portability result.",
        "baseline_plan": {"path": str(args.baseline_plan.resolve()), "sha256": sha256(args.baseline_plan)},
        "capture_dir": str(args.capture_dir.resolve()),
        "layers": list(args.layers),
        "train_indices": list(args.train_indices),
        "heldout_indices": list(args.heldout_indices),
        "train_tokens": args.train_tokens,
        "heldout_tokens": args.heldout_tokens,
        "energy_floor_ratio": args.energy_floor_ratio,
        "pool_size": args.pool_size,
        "max_swaps": args.max_swaps,
        "head_count": len(records),
        "heldout_pair_count": heldout_pairs,
        "baseline_heldout_rmse": baseline_rmse,
        "candidate_heldout_rmse": candidate_rmse,
        "candidate_over_baseline": candidate_rmse / baseline_rmse,
        "energy_constraints_passed": energy_ok,
        "accepted_swap_count": sum(len(row["swaps"]) for row in records),
        "records": records,
        "script_sha256": sha256(Path(__file__)),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({key: report[key] for key in (
        "status", "head_count", "accepted_swap_count", "baseline_heldout_rmse",
        "candidate_heldout_rmse", "candidate_over_baseline",
        "energy_constraints_passed")}, indent=2))


if __name__ == "__main__":
    main()
