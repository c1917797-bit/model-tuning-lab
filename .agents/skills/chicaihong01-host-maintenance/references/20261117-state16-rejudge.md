# BOLE state16 evidence replay — 2026-11-17

Scope: host-maintenance lessons from the actual single-card BOLE state16 run and independent replay. This is not a whole-model, long160, performance, or task-accuracy acceptance.

- Preserve complete execution context when extracting an original metric helper. Its result.checks mapping is part of the contract. Matching the arithmetic AST alone did not prevent a list/string-index TypeError after metrics had passed.
- Inner metric success does not override an independent consumer failure. Retain the original FAIL; fix the proved reporting defect and replay immutable actual NPU outputs through the independent FP64 consumer. Do not rerun the producer just to regenerate the same evidence.
- Verify before/after RAW membership, sizes, and hashes. The accepted replay retained all 58 original files (129839520 bytes), obtained 128/128 checks, and used a bounded no-device container with read-only source/RAW mounts.
- An execution wrapper must use a validated Docker logging combination. local logging with max-file=1 needs compression disabled; the rejected container never started. Persist exact command stderr and container State.Error before attribution.
- Bind the actual current manifest, not a copied cardinality. The path-only successor expanded READSET from 148 to 157 entries with no removed paths. The old hardcoded count rejected it before any output directory or container existed; all current references still require byte/hash validation.
- Keep historical authority and current authority in their respective roles. An immutable old ledger keeps its original scope pin; current execution authorization must still be checked separately. No ledger rewrite or quota increase follows from a comparison repair.
- Namespace association alone is not compute utilization. Report fresh process/AICore/HBM observations separately, and retain the user's hold on physical1/3 and protection of4–7. Without continuous device samples, 30-minute utilization remains unmeasured.

Evidence: current workstream dual_resume_20261117T060217Z, MAIN_STATE16_INDEPENDENT_PASS_FRESH_RELEASE_20261117.json (26493 bytes, SHA256 6fca953e8464df51170c2acd1a6cb5c6b6c2ca03a88df9421bc4fa333f53f2a9). Original NPU operation exec-0000000000000184; successful replay operation exec-00000000000001b4. All source and RAW stay on chicaihong01.
