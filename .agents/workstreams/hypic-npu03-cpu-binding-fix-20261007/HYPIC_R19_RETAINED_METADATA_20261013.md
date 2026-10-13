# r19 retained identity and retry evidence — 2026-10-13

This is a read-only supplement to QUALITY_CONTRACT_OBLIGATION_AUDIT_20261012.md,
not another quality wave, source change, or retrospective repair of the ruler.
Exact-main quality Skill303658f0a652ed392c875e58941c6b1d246552f7 and
referencea3d5ca9a98883ce651fc275f404a524b126f07c7 were re-read.
Existing full quality scores, rejection and immutable roots remain unchanged.

## Historical evidence recovered

Independent replay exec-00000000000001c3 passed in232ms. It reads the four
original service logs, start/stop receipts and NPU snapshots. It pins arm-result
and log hashes, verifies exact container identity, checks the log against the
retained stop hash and the NPU snapshot against the start hash. No current
runtime metadata is substituted for the October10 records.

| Arm | Logged framework | NPU display version | Retained HTTP200 POST records |
| --- | --- | --- | ---: |
| LongBench baseline | vLLM0.23.0 |25.2.0|638|
| LongBench HYPIC | vLLM0.23.0 |25.2.0|638|
| GSM8K baseline | vLLM0.23.0 |25.2.0|3957|
| GSM8K HYPIC | vLLM0.23.0 |25.2.0|3957|

All four logged engine configuration strings match after removing the
process/time prefix. They record model/tokenizer path Qwen3.6-27B, TP4,
BF16, max_seq_len41984, seed0 and tokenizer_revision=None.
This closes the narrow missing historical framework-version/display-version
observation, not a complete framework/CANN/driver binary manifest. A version
string or tokenizer path is not byte identity. Historical tokenizer bytes,
full driver identity and full loaded-runtime overlays remain unproved.

Original service-log SHA256s:
- LongBench baseline:6a4e6a1639665ff5c3413ef795b6642a6b4cd8cebc4916143612070e54fccee9
- LongBench HYPIC:f2f03e99cc06a751d229e750999221fdd569157628cee48ef95507ce224ed689
- GSM8K baseline:157ee6c04cc4f17dd0b1addcd543a1df94d628f26e8c31b5cb5ef6d531705fba
- GSM8K HYPIC:8f57043932005c9180316d6cab4b3abf187524fe3d5fdfb1f3534d958369b3eb

HTTP record counts are supplementary server observations, not per-sample
attempt ledgers. The log format has no request-ID join or client-side failures.
No missing/extra successful server record was observed against the retained
phase counts; this does not prove zero client retries.

## Concrete retry-accounting defect

The frozen evaluator SHA256
9c8cf4204964220acd31adc8a3f73332374f123e1b8681a522b33eff33504cc0
allows up to2 retries. request_one stores the most recent error in memory,
but on eventual success returns error=None without attempt history/count.
Its final row therefore cannot preserve protocol5 timeout/retry accounting.

The replay extracts the unchanged request_one function, substitutes only
synthetic transport/scoring/time dependencies, and exercises1,2,3 attempts.
A pre-server TimeoutError is injected in the latter cases; all successful
persisted rows are identical. No network, NPU, model or server is contacted.
This falsifies inference from final success/error=None (or matched server200
counts) to zero retries. It does not claim actual r19 timeouts occurred.

Do not patch the frozen evaluator in place: its digest binds completed
experiments. For the next genuinely required quality experiment, retain an
append-only per-attempt ledger with sample/run/request identity, attempt index,
start/end, exception/status, outcome and final-row linkage. This is a known
implementation evidence gap, not a reason to rerun r19 or change its scores.

## Exact-main acceptance and next action

The eight-protocol audit remains partial:
- declared pair, full repeats, canary, lifecycle, paired/category/length analysis
  and negative-result retention already have bounded evidence;
- historical identity is now better documented but not fully closed;
- actual client attempts/timeouts cannot be recovered from inspected final
  rows and successful access logs;
- quality-first ordering remains a recorded deviation from the main workflow;
- partial hot proof is separate from all-request quality; no new gate is added.

Do not repeatedly inspect these same logs to chase unavailable fields.
Do not require algorithm success/root-cause repair to validate a negative
quality-evaluation outcome, and do not promote full workflow conformance from
this metadata supplement. Counts remain9 bounded verified/20 partial.
Current4429e35 descriptive performance remains a separate unanswered user
choice; no device action is authorized by this supplement.
No main/remote sync, unchanged-auth retry or deadline extension.

Replay (CPU/read-only):
python3 -B verify_r19_retained_metadata.py
