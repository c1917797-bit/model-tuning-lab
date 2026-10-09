# Retry18 terminal audit — 2026-10-09

## Decision

`hypic-only/repeat3` retry18 is an **environmental pre-health failure**, not
a HYPIC performance result. The sixth matched phase remains unmeasured.

## Evidence

- The controller sampled the physical-lane guard 80 times with zero probe
  errors. At 2026-10-09 13:50:39 UTC it captured external container
  `efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6`
  using physical NPU1 (PID 1420898). The external workload was not stopped
  or modified.
- The exact retry18 service did not reach a proven healthy state. No
  benchmark command, `performance.json`, or scored request was produced;
  metrics and performance SHA are null.
- Only retry18's exact owned service container
  `71ace370461d0090de57c1239f26015231e6252b0000ab3dc104ef27710b4f83`
  was removed. The controller does not claim worker-release proof.
- An immediate independent post-cleanup snapshot found no physical NPU0–3
  process and no listener on TCP 8223. This is point-in-time evidence, not a
  resource lease.

## Immutable receipts

| Receipt | SHA256 |
|---|---|
| `contract.json` | `c03c8fdf79ffe02ed42ee2e80558479e372b2be0959128795e83c6dbe7dd322a` |
| `arm-result.json` | `c0bd15e0a0a6340e338bcbf05a5f4791139d747589ad63b1351cb67f198bd4bc` |
| `hypic-only/lane-guard.json` | `6ae72bebd66aba903dd9f8bfebf90561374bd2699363428268b97d4f498f553b` |
| `hypic-only/pre-health-release.json` | `413c9d8d3b2af629b5c6732c0eeba857299ea28794d9245d8ae2b2a365a5048c` |
| `hypic-only/hypic-evidence.jsonl` | `26eaf6cda31342ba6742045a15ca34039c0d3598dad61a2508cbcdb8400e568c` |

Independent replay:
`python3 -B verify_retry18_environmental_failure.py`. It checks all five
hashes, the foreign physical NPU/PID/container identity, 80 clean probe
samples, the zero-measurement boundary, and exact owned-container removal.
This event does not pass or fail HYPIC.
