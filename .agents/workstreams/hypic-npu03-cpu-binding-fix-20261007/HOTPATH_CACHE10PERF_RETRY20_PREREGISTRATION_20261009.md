# HYPIC-only/repeat3 retry20 preregistration — 2026-10-09

## Scope and unchanged protocol

This is one new immutable root for the missing sixth matched performance phase.
The user authorized opportunistic monitoring and execution only while physical
NPU0–3 and port 8223 are not in use. Never stop or modify external work; NPU4–7
are forbidden. Any foreign PID or probe error in the continuous physical-NPU
guard invalidates this arm. Retry19 and retry20 must never be pooled or
overwritten.

Reuse the frozen retry19 contract exactly except for unique root/attempt
identity and retry selector: source `c12060cd47e7575ead059983d7a8bb4704165c98`,
image `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`,
Qwen3.6-27B, TP4, physical NPU0–3, 32768-token input, 1024-token output,
40 requests, concurrency 16, port 8223, frozen metrics and thresholds. The
serving command, cache, segment boundaries, environment, and workload are
unchanged.

## Pre-run and acceptance gates

Replay the retry19 verifier, prove the retry20 root absent, and run offline
admission. Immediately before launch, freshly resolve `chicaihong01/ma`, prove
direct routing, and verify physical NPU0–3 and port 8223 are idle. If external
work appears, preserve PID/time/container evidence, invalidate this root, and
remove only its exact service. Count the phase only with full same-root rows,
source identity, continuous isolation, exact cleanup, and independent
`audit_phase` success. This preregistration alone is not a run/result claim.
