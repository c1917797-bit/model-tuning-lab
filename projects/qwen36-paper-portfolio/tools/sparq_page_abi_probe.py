#!/usr/bin/env python3
"""Check native Ascend paged-attention support for a SparQ page adapter.

This is a storage/ABI numerical gate, not a SparQ implementation or an
end-to-end performance benchmark. Run only in an audited container whose
logical NPU 0 maps to physical NPU 4.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import time


BLOCK_SIZE = 128
HEAD_DIM = 256
QUERY_HEADS = 6
PAGES_PER_REQUEST = 5
ORIGINAL_LENGTH = 4 * BLOCK_SIZE + 1
SELECTED_LENGTH = 2 * BLOCK_SIZE + 1
MAX_ABS_LIMIT = 0.04
RMS_LIMIT = 0.005


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    results_root = Path("/results").resolve()
    if results_root not in output.parents or output.exists():
        parser.error("output must be a new directory below /results")
    if os.environ.get("ASCEND_RT_VISIBLE_DEVICES") != "0":
        parser.error("expected one audited logical NPU 0 mapped to physical NPU 4")
    args.output_dir = output
    return args


def native_attention(torch_npu, query, key_cache, value_cache, block_table, lengths):
    return torch_npu.npu_fused_infer_attention_score(
        query=query,
        key=key_cache,
        value=value_cache,
        block_table=block_table,
        input_layout="TND",
        block_size=BLOCK_SIZE,
        actual_seq_lengths=list(range(1, query.shape[0] + 1)),
        actual_seq_lengths_kv=lengths,
        num_key_value_heads=1,
        num_heads=QUERY_HEADS,
        scale=1.0 / math.sqrt(HEAD_DIM),
        # Single-token decode sees only past KV entries in the selected table.
        # CANN 9.1 requires sparse_mode=0 when no attention mask is supplied.
        sparse_mode=0,
    )[0]


def reference(torch, query, key_cache, value_cache, chosen_pages):
    expected = []
    for request, pages in enumerate(chosen_pages):
        physical = [request * PAGES_PER_REQUEST + logical for logical in pages]
        indices = torch.tensor(physical, device=query.device, dtype=torch.long)
        keys = key_cache.index_select(0, indices).reshape(-1, HEAD_DIM)[:SELECTED_LENGTH].float()
        values = value_cache.index_select(0, indices).reshape(-1, HEAD_DIM)[:SELECTED_LENGTH].float()
        scores = query[request].float() @ keys.T / math.sqrt(HEAD_DIM)
        expected.append(torch.softmax(scores, dim=-1) @ values)
    return torch.stack(expected)


def table_for(torch, batch, middle_page):
    pages = [[0, middle_page, 4] for _ in range(batch)]
    table = torch.full((batch, PAGES_PER_REQUEST), -1, device="npu:0", dtype=torch.int32)
    for request, selected in enumerate(pages):
        table[request, : len(selected)] = torch.tensor(
            [request * PAGES_PER_REQUEST + page for page in selected],
            device="npu:0",
            dtype=torch.int32,
        )
    return table, pages


def numerical_result(torch, output, expected):
    actual = output.float().reshape_as(expected)
    if not bool(torch.isfinite(actual).all().item()):
        raise AssertionError("non-finite native attention output")
    delta = actual - expected
    max_abs = float(delta.abs().max().item())
    rms = float(torch.sqrt(torch.mean(delta.square())).item())
    if max_abs > MAX_ABS_LIMIT or rms > RMS_LIMIT:
        raise AssertionError(
            f"selected-support mismatch: max_abs={max_abs}, rms={rms}"
        )
    return {"max_abs": max_abs, "rms": rms}


def run_batch(torch, torch_npu, batch):
    torch.manual_seed(20260923 + batch)
    cache_shape = (batch * PAGES_PER_REQUEST, BLOCK_SIZE, HEAD_DIM)
    keys = torch.randn(cache_shape, device="npu:0", dtype=torch.bfloat16)
    values = torch.randn(cache_shape, device="npu:0", dtype=torch.bfloat16)
    base_query = torch.randn((batch, QUERY_HEADS, HEAD_DIM), device="npu:0", dtype=torch.bfloat16)
    lengths = [SELECTED_LENGTH] * batch
    eager = []
    for middle_page in (1, 2):
        query = base_query + middle_page / 16
        block_table, pages = table_for(torch, batch, middle_page)
        output = native_attention(torch_npu, query, keys, values, block_table, lengths)
        eager.append(
            {"middle_page": middle_page, **numerical_result(
                torch, output, reference(torch, query, keys, values, pages)
            )}
        )

    static_query = base_query.clone()
    static_table, _ = table_for(torch, batch, 1)
    native_attention(torch_npu, static_query, keys, values, static_table, lengths)
    torch.npu.synchronize()
    graph = torch.npu.NPUGraph()
    with torch.npu.graph(graph):
        graph_output = native_attention(
            torch_npu, static_query, keys, values, static_table, lengths
        )

    replays = []
    for middle_page in (1, 2):
        query = base_query + middle_page / 16
        table, pages = table_for(torch, batch, middle_page)
        static_query.copy_(query)
        static_table.copy_(table)
        graph.replay()
        first = graph_output.clone()
        graph.replay()
        second = graph_output.clone()
        if not bool(torch.equal(first, second)):
            raise AssertionError("identical graph replay was not bitwise stable")
        replays.append(
            {"middle_page": middle_page, **numerical_result(
                torch, first, reference(torch, query, keys, values, pages)
            )}
        )
    return {"batch": batch, "eager": eager, "graph_replay": replays}


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    record = {
        "schema": "sparq-page-abi-probe/v1",
        "claim": "native selected-page numerical/graph ABI only; no SparQ or E2E result",
        "physical_npu_contract": 4,
        "container_visible_npu": 0,
        "shape": {
            "query_heads": QUERY_HEADS,
            "kv_heads": 1,
            "head_dim": HEAD_DIM,
            "block_size": BLOCK_SIZE,
            "original_length": ORIGINAL_LENGTH,
            "selected_length": SELECTED_LENGTH,
        },
        "limits": {"max_abs": MAX_ABS_LIMIT, "rms": RMS_LIMIT},
        "started_epoch_s": time.time(),
        "status": "running",
    }
    output = args.output_dir / "result.json"
    try:
        import torch
        import torch_npu

        torch.npu.set_device(0)
        record["torch"] = torch.__version__
        record["torch_npu"] = torch_npu.__version__
        record["cases"] = [run_batch(torch, torch_npu, batch) for batch in (1, 16)]
        record["status"] = "pass"
    except BaseException as exc:
        record["status"] = "fail"
        record["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        record["finished_epoch_s"] = time.time()
        output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
