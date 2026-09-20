# EPD-Serve: Qwen3.6 Ascend Piercing Report

## Decision

**Rejected for the current acceptance workload and physical NPU4-7 resource
envelope.** No end-to-end candidate was launched because the paper mechanism is
not reachable from the fixed text-only workload and a faithful deployment does
not fit on the four permitted cards.

This is not a rejection of EPD-Serve for a production multimodal fleet. It is a
scope decision for Qwen3.6-27B, plugin delivery, fixed 1024-token generation,
LongBench-v2, GSM8K, and one TP4 Ascend instance.

## Paper contract

EPD-Serve is a system-level architecture for high-concurrency multimodal
serving. It independently schedules Encode, Prefill, and Decode instances,
adds asynchronous multimodal-feature prefetch, hierarchically groups P-to-D KV
transfers, routes text and multimodal requests on different paths, and balances
load across instances.

The paper evaluates openPangu-7B-VL and Qwen3-VL-8B on an Atlas 800I A2 using
mixed image/text datasets, 64 output tokens, and 1-12 requests/s. Its headline
57.37-69.48% throughput gain is relative to a PD-disaggregated multimodal
baseline under SLO constraints. This is not the current Qwen3.6 TP4 text-only
baseline.

No paper-specific official implementation repository was identified. The
public `vbdi/epdserve` repository found by name implements the earlier
arXiv:2501.05460/ICML 2025 work and must not be treated as the official code for
arXiv:2601.11590.

## Workload reachability gate

The paper explicitly routes multimodal requests through E-P-D and text-only
requests through P-D. The fixed performance and accuracy protocols in this
workstream contain no image, audio, or video inputs. Therefore:

- asynchronous E-to-P feature prefetch is never invoked;
- MM Store reuse is never invoked;
- Encode isolation cannot improve the measured throughput, TTFT, or TPOT; and
- the headline multimodal throughput result cannot be compared with the fixed
  1024-output-token text workload.

The P-to-D grouped transfer idea remains conceptually relevant to a separate PD
deployment, but it requires independent Prefill and Decode instances and a
different resource topology and baseline. It is not a monkeypatch inside one
TP4 process.

## Current stack audit

The exact vLLM-Ascend v0.23 reference at commit
`5cb98caaadeff42b5b62b996e34bb2aaa29d20fd` already contains related EPD
infrastructure:

- a disaggregated encoder guide and load-balancing proxy example;
- an `ECExampleConnector` reference path;
- a `MooncakeLayerwiseConnector` P-to-D path that overlaps layer-wise KV
  transfer with prefill computation; and
- separate 1E1PD and 1E1P1D deployment examples.

This means a future fleet experiment should use the upstream connector seams,
not recreate a competing transport inside a plugin. The reference guide also
states that production E-to-P Mooncake/SHM transports were future work; plugin
discovery alone would not reproduce the paper's asynchronous MM Store.

Source identities:

- EPD deployment guide SHA256:
  `baac30aed4e60c132d3f1110a875ee85919ea7d91aa95527e161f015f4e8a65d`
- EPD feature guide SHA256:
  `ce5b3babf8edecbcbcc8055505473a50ca3ddb39691187f56c8e66229e597933`

## Live NPU resource gate

Fresh `npu-smi` evidence on 2026-09-20 showed physical NPU4-7 idle and healthy,
with about 32 GiB HBM per card. A same-day Qwen3.6-27B TP4 service on those
physical cards recorded:

- four HCCL ranks;
- 12.8735 GiB model weights per rank;
- about 1.2 GiB peak activation and 0.48 GiB non-torch memory per rank; and
- about 29.49 GiB usable HBM per card.

A faithful P/D split needs at least two complete language-model instances. With
only four cards, each instance cannot retain TP4. Co-locating two TP4 instances
would duplicate roughly 25.747 GiB of weights per card before activation, cache,
and runtime memory, so it cannot fit the observed per-card envelope. Reducing to
TP2 would place roughly 25.747 GiB of weights on each card before the same
runtime overhead and KV/state cache, also outside the demonstrated safe
configuration.

Starting containers under this topology would therefore test OOM behavior, not
the paper hypothesis. The run was correctly stopped at the resource gate.

## Re-entry conditions

Re-open EPD-Serve only for a separately authorized multimodal/fleet objective
with all of the following:

- a mixed text/image workload and its own accuracy contract;
- enough cards or nodes for independent E and P/D, preferably P and D,
  instances without oversubscription;
- matched monolithic, PD, and EPD baselines normalized per NPU;
- a production E-to-P transport and MM Store identity; and
- explicit permission for multi-instance proxy and connector deployment beyond
  the current single-plugin boundary.
