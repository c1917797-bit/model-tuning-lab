# Retry17 terminal audit — 2026-10-09

## Decision

`hypic-only/repeat3` retry17 is an **environmental pre-health failure**, not a
HYPIC performance result. The sixth matched phase remains unmeasured.

## Evidence

- The controller ran 26 continuous physical-lane guard samples with zero probe
  errors. At 2026-10-09 13:28:42.922 UTC it captured foreign container
  `87ab8b2137c62e965c4ed88ce241b306794316cc04625770648a1d3cbd1caaa` using
  physical NPU0 (PID 1198578). The external work was not stopped or modified.
- The service never reached a proven healthy state. No benchmark command,
  `performance.json`, or scored request was produced; performance metrics and
  performance SHA are null.
- Only retry17's exact owned service container
  `9aea36d4c555c1dc62377f2eb0fca783a255c0e2bd8324f1d9798fb69b9d9ec6` was
  removed. The controller correctly does not claim worker-release proof.
- An immediate post-cleanup physical snapshot showed no running process on
  NPU0–3 and TCP 8223 free. This is a point-in-time observation, not a lease.

## Immutable receipts

| Receipt | SHA256 |
|---|---|
| `contract.json` | `78065f257df89c1eb032b22f4372d5a21793b97084657b8ea56324cca7cc7d22` |
| `arm-result.json` | `04c59278c0720e531e88dc0936a4b4a04f991ed178bf9e06472045dd14b49e46` |
| `hypic-only/lane-guard.json` | `f0276d28026a9b7da0218db46093521aa70be4077d2c77c9f0654f7011b168b6` |
| `hypic-only/pre-health-release.json` | `bb665f2c1afa4db4f3eb5acd143c79fdf0cb44e16e646ccfdce6f6feeaf63898` |
| `hypic-only/hypic-evidence.jsonl` | `4105a55809328e22620da7e8f1a68a1bf96ea1326039e7c335e00e90f0570251` |

Independent replay: `python3 -B verify_retry17_environmental_failure.py`.
The checker verifies these hashes, the foreign physical device/PID/container,
the 26 clean-probe samples, the zero-measurement boundary, and exact owned
container removal. This event does not pass or fail HYPIC.
