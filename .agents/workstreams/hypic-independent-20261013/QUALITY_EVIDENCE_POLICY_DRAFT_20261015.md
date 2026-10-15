# Quality evidence policy draft — not activated

Current full40 controller062d and its101 source bindings remain unchanged.
This draft is not imported by either worker loader or scheduler.

## Tested component
Operation0643: six CPU controls pass. Default profile full preserves event bytes
as dictionaries. Explicit quality-hot may omit only mixed_native_gdn_completed,
mixed_native_c2_completed and native_decode_batch_completed outside sampled
shadow groups. Every retained record carries cumulative omission counts.
All private C1/C2 hot, public publication/eviction, request progress, shadow
(including failures), errors and client quality records are retained.
Every sampled shadow group's batch and matching native commits are retained.

This is a deliberate, preregistered evidence profile, not silent log truncation.
It does not raise the existing100000events/128MiB bounds or drop scored samples.
The policy alone does not prove real-run event/byte consumption stays in bounds.

## Remaining quality critical path
- Wire the already-tested catalog scheduler factory instead of public_tokens-only
  construction, and pass max_requests1024 for all381 plus bounded producers.
- Remove an explicit evidence-profile configuration before stage construction;
  emit profile descriptor before activation and filter only the worker sink.
- Keep all frozen R7 C1/C2/backend math unchanged; identify workload adapters and
  package/source bindings separately from the shared inference core.
- Freeze original repetition-major127x3 order, naturalEOS/nonthinking1024,
  baseline/candidate same inputs/ruler/batch8. No hidden retry or changed scorer.
- Validate proposed linear768MiB/KV2560MiB perrank with fresh ordinary memory and
  actual retained material/generation receipts. Meta accounting05b9 is not this proof.
- Bounded integrated catalog admission/pool/evidence-budget canary before full381.
- Full paired381, every intended request's actual fourworker hot proof and
  independent source/isolation/release/quality audit remain required.

Do not edit current runtime while062d is live or terminal unclear. Do not turn
this CPU draft into a quality or full Paper-to-Ascend completion claim.
