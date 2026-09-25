#!/usr/bin/env python3
"""One-shot four-rank Ascend Ada-KV allocation ABI smoke, not service evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np
import torch
import torch.distributed as dist
import torch.nn.functional as functional
import torch_npu  # noqa: F401 - registers NPU backend

from qwen36_adakv_ascend.budget import allocate_global_head_budget


AUTHOR_COMMIT = "04497abac4c1a58426f3daf1014578990e225cc5"
WINDOW = 32
POOL = 7
TOKENS = 512
DIM = 256
BASE_CAPACITY = 256
FLOOR_RATIO = 0.5  # official README example, distinct from paper alpha notation


def author_style_scores(batch: int, rank: int, device: torch.device) -> torch.Tensor:
    """Synthetic Q/K with the official window-softmax/GQA-mean/maxpool order."""
    generator = torch.Generator(device="cpu").manual_seed(240711550 + batch * 10 + rank)
    query = torch.randn((batch, 6, WINDOW, DIM), generator=generator).to(device)
    key = torch.randn((batch, 1, TOKENS, DIM), generator=generator).to(device)
    logits = torch.matmul(query, key.transpose(-2, -1)) / math.sqrt(DIM)
    recent = logits[..., -WINDOW:]
    forbidden = torch.triu(torch.ones((WINDOW, WINDOW), dtype=torch.bool, device=device), diagonal=1)
    recent.masked_fill_(forbidden, torch.finfo(logits.dtype).min)
    weights = torch.softmax(logits.float(), dim=-1)
    old = weights[..., :-WINDOW].mean(dim=-2).mean(dim=1)
    return functional.max_pool1d(old.unsqueeze(1), kernel_size=POOL, stride=1, padding=POOL // 2).squeeze(1)


def cpu_reference(scores: np.ndarray) -> tuple[list[list[int]], list[list[int]]]:
    """Independent stable-sort implementation of global selection and safeguard."""
    batch, world, tokens = scores.shape
    budgets = []
    counts_all = []
    for request in range(batch):
        order = np.argsort(-scores[request].reshape(-1), kind="stable")[: world * BASE_CAPACITY]
        counts = np.bincount(order // tokens, minlength=world).astype(int).tolist()
        floor = int(BASE_CAPACITY * FLOOR_RATIO)
        guarded = [int(np.rint(count * (1 - FLOOR_RATIO) + floor)) for count in counts]
        counts_all.append(counts)
        budgets.append(guarded)
    return budgets, counts_all


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    rank = int(os.environ["RANK"])
    local_rank = int(os.environ["LOCAL_RANK"])
    world = int(os.environ["WORLD_SIZE"])
    if world != 4:
        raise SystemExit("This probe requires exactly four ranks")
    torch.npu.set_device(local_rank)
    device = torch.device(f"npu:{local_rank}")
    dist.init_process_group(backend="hccl")
    try:
        report = {"scope": "synthetic distributed allocation ABI only", "author_commit": AUTHOR_COMMIT,
                  "world": world, "physical_mapping_required": "host 4-7 -> container 0-3", "cases": []}
        for batch in (1, 16):
            local = author_style_scores(batch, rank, device)
            if not bool(torch.isfinite(local).all().item()):
                raise AssertionError("nonfinite observation scores")
            local_budget, budgets, counts = allocate_global_head_budget(local, BASE_CAPACITY, FLOOR_RATIO)
            gathered = torch.empty((world * batch, TOKENS - WINDOW), device=device, dtype=local.dtype)
            dist.all_gather_into_tensor(gathered, local.contiguous())
            reference, reference_counts = cpu_reference(
                gathered.view(world, batch, TOKENS - WINDOW).permute(1, 0, 2).cpu().numpy())
            actual = budgets.cpu().tolist()
            actual_counts = counts.cpu().tolist()
            if actual != reference or actual_counts != reference_counts:
                raise AssertionError(f"global allocation mismatch: {actual} vs {reference}")
            if any(sum(row) != world * BASE_CAPACITY for row in actual_counts):
                raise AssertionError("global selected count mismatch")
            if local_budget.cpu().tolist() != [row[rank] for row in actual]:
                raise AssertionError("local budget does not match this TP rank")
            report["cases"].append({"batch": batch, "budgets": actual, "raw_counts": actual_counts,
                                     "global_selected": world * BASE_CAPACITY,
                                     "nonuniform_requests": sum(len(set(row)) > 1 for row in actual)})
        dist.barrier()
        if rank == 0:
            out = Path(args.output_dir)
            out.mkdir(parents=True, exist_ok=False)
            report["torch"] = torch.__version__
            report["torch_npu"] = torch_npu.__version__
            report["script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
            (out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
            print(json.dumps({"status": "passed_abi_only", "report": str(out / 'report.json'),
                              "nonuniform": [case["nonuniform_requests"] for case in report["cases"]]}))
        dist.barrier()
    finally:
        dist.destroy_process_group()


if __name__ == "__main__":
    main()
