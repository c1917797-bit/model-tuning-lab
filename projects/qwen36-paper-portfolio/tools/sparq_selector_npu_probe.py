#!/usr/bin/env python3
"""NPU correctness probe for paper-derived SparQ GQA and page adaptation.

Uses synthetic BF16 Q/K/V in the TP4 local geometry. It does not test a model,
vLLM dispatch, task accuracy, or end-to-end performance.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time

import torch
import torch_npu

from sparq_page_abi_probe import (
    BLOCK_SIZE,
    HEAD_DIM,
    ORIGINAL_LENGTH,
    PAGES_PER_REQUEST,
    QUERY_HEADS,
    SELECTED_LENGTH,
    native_attention,
    numerical_result,
    reference,
)
from sparq_page_selection import select_sparq_pages


def select_and_run(query, keys, values, dense_table):
    batch = query.shape[0]
    sparse_table = torch.full_like(dense_table, -1)
    retained = []
    for request in range(batch):
        indices = dense_table[request].long()
        logical_keys = keys.index_select(0, indices).reshape(-1, HEAD_DIM)[:ORIGINAL_LENGTH]
        selection = select_sparq_pages(
            query[request],
            logical_keys,
            dense_table[request],
            block_size=BLOCK_SIZE,
            rank=32,
            token_budget=128,
            page_budget=3,
            recent_tokens=1,
        )
        sparse_table[request, :3] = selection["selected_physical_pages"]
        retained.append(selection["retained_paper_top_k_tokens"])
    result = native_attention(
        torch_npu, query, keys, values, sparse_table, [SELECTED_LENGTH] * batch
    )
    return result, sparse_table, torch.stack(retained)


def check_result(query, keys, values, output, sparse_table, retained):
    batch = query.shape[0]
    logical_pages = [
        (sparse_table[request, :3].cpu().tolist())
        for request in range(batch)
    ]
    logical_pages = [
        [physical - request * PAGES_PER_REQUEST for physical in pages]
        for request, pages in enumerate(logical_pages)
    ]
    for pages in logical_pages:
        if pages != sorted(pages) or pages[-1] != PAGES_PER_REQUEST - 1:
            raise AssertionError(f"invalid or unsorted page support: {pages}")
    errors = numerical_result(
        torch, output, reference(torch, query, keys, values, logical_pages)
    )
    recall = retained.float() / 128
    return {
        **errors,
        "selected_logical_pages": logical_pages,
        "paper_topk_page_recall_mean": float(recall.mean().item()),
        "paper_topk_page_recall_min": float(recall.min().item()),
    }


def run_batch(batch):
    torch.manual_seed(20260923 + batch)
    keys = torch.randn(
        (batch * PAGES_PER_REQUEST, BLOCK_SIZE, HEAD_DIM),
        device="npu:0",
        dtype=torch.bfloat16,
    )
    values = torch.randn_like(keys)
    base_query = torch.randn(
        (batch, QUERY_HEADS, HEAD_DIM), device="npu:0", dtype=torch.bfloat16
    )
    dense_table = torch.arange(
        batch * PAGES_PER_REQUEST, device="npu:0", dtype=torch.int32
    ).reshape(batch, PAGES_PER_REQUEST)

    eager = []
    for offset in (0.0, 0.25):
        query = base_query + offset
        output, table, retained = select_and_run(query, keys, values, dense_table)
        eager.append({
            "query_offset": offset,
            **check_result(query, keys, values, output, table, retained),
        })

    static_query = base_query.clone()
    select_and_run(static_query, keys, values, dense_table)
    torch.npu.synchronize()
    graph = torch.npu.NPUGraph()
    with torch.npu.graph(graph):
        graph_output, graph_table, graph_retained = select_and_run(
            static_query, keys, values, dense_table
        )
    replays = []
    for offset in (0.0, 0.25):
        query = base_query + offset
        static_query.copy_(query)
        graph.replay()
        first = graph_output.clone()
        table = graph_table.clone()
        retained = graph_retained.clone()
        graph.replay()
        if not bool(torch.equal(first, graph_output)):
            raise AssertionError("identical selector graph replay is not bitwise stable")
        replays.append({
            "query_offset": offset,
            **check_result(query, keys, values, first, table, retained),
        })
    return {"batch": batch, "eager": eager, "graph_replay": replays}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if Path("/results").resolve() not in output.parents or output.exists():
        parser.error("output must be a new directory below /results")
    if os.environ.get("ASCEND_RT_VISIBLE_DEVICES") != "0":
        parser.error("expected audited logical NPU 0 mapped to physical NPU 4")
    output.mkdir(parents=True, exist_ok=False)
    record = {
        "schema": "sparq-selector-npu-probe/v1",
        "scope": "synthetic local GQA selector and page ABI, not model/E2E",
        "physical_npu_contract": 4,
        "torch": torch.__version__,
        "torch_npu": torch_npu.__version__,
        "started_epoch_s": time.time(),
        "status": "running",
    }
    try:
        torch.npu.set_device(0)
        record["cases"] = [run_batch(batch) for batch in (1, 16)]
        record["status"] = "pass"
    except BaseException as exc:
        record["status"] = "fail"
        record["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        record["finished_epoch_s"] = time.time()
        (output / "result.json").write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n"
        )


if __name__ == "__main__":
    main()
