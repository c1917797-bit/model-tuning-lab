# Fixed-admission diagnostic: actual same-image preflight

Stage: attempted/source-verified, not NPU-verified, measured or accepted.
The ready-before-resource rule was exercised while the existing independent
allT matrix still owned physical4–7. No new model or NPU operation was launched.

## Actual evidence

Canonical root /opt/host/vnf/austinov/model-tuning-lab, branch
work/qwen36-damp-ascend-20261006. Source manifest
projects/damp-ascend/tools/fixed_admission_capture_v1/SOURCE_MANIFEST.json:
SHA256 a685970e567b629016470f9a821e97ceb9007404f9a3065615715ce1c0f51aae.

MAIN direct MA exec-00000000000006d1 completed exit0, no cancellation/timeout.
Original tool JSON, not a synthetic terminal projection:
- /cache/cch/qwen36-damp-20261006/fixed-admission-no-device-v1-terminal-original.json
- SHA256 5be667ac33269604bfeaae93e5dd7197cd6dc68445f3aeb1b26abbaae906edb4.

MAIN MA06d5 independently read results and fresh exact stopped identity:
- RESULT.json SHA256 7e496840f25292e03c26ceb914fc0df978534a6f845bc8ae347bd705da12b464.
- preflight.json SHA256 2fc079ea6124059918154fe0ea13fdba5afebf4b40a84783077fdb00a0c37de9.
Both are under /cache/cch/qwen36-damp-20261006/fixed-admission-no-device-v1.
Target image660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1,
actual CPython3.12 public profile API, 48/48 stdlib tests, unique damp_capture
entrypoint -> damp_admission_diagnostic:register, source imports and five actual
image source hashes passed. No Torch/model/NPU or native worker hook was loaded.

Fresh quota admission observed Docker NCPU7 and MemAvailable57,631,059,968B.
Known allT caps4CPU/32GiB + preflight1CPU/2GiB + reserve1CPU/8GiB were jointly
checked; required ordinary RAM42GiB. This does not admit a full model run.

Only newly nonce-owned no-device container
344b2ed169cfeb7b93c00fe6750bbf4e1aa64878fdda1f43b398c9aa4abaec89
was stopped and retained: PID0, Running:false, OOMKilled:false, no devices,
nonprivileged, 1CPU/2GiB. Its sleep process exit137 after stop is not a numerical
or test failure; the original docker-exec/preflight exit was0.

MAIN MA06d6 additionally verified all13 own source hashes and all28 external
repository bindings, and found all28 external files tracked. The original
collector run.py was already bound; a suspected missing-pin visual reading was
corrected before any patch. No redundant repair or historical rewrite occurred.

## Success/failure learning and next action

Read-only MAIN MA06c6 reproduced the former resource-policy ValueError that
classified the exact protected0–3 baseline's26.76GiB resident memory as an
unknown >2GiB task. Original tool bytes:
 /cache/cch/qwen36-damp-20261006/fixed-admission-external-policy-v1-original.json,
 SHA256 65b6d10d2e83e4b27cdd479d4e65380ba7048b5def78e75a30c70c23234cf390.
The reviewed new policy binds that exact identity/map/process set and records
initial resident usage (already reflected in MemAvailable), requiring unchanged
PID/name set, CPU<=50%, growth<=4GiB and live8GiB reserve. UNKNOWN limits remain
unchanged. It stops only its own diagnostic, never protected0–3.

The separate allT run is still a restricted SR1/power2 correctness attempt,
not DAMP full-model acceptance. Source/progress auditing identified excessive
whole-state transfers and repeated growing JSON writes; do not relabel a budget
timeout as a numerical or paper-wide no-go. Preserve live sources and its original
matrix; only evidence-backed new harness preparation may follow actual terminal.

Next model diagnostic remains OFF-A/OFF-B/ON C1 x1024/33, eagerly checked and
defaultOFF. It requires original MAIN MA06a0 terminal, four exact stopped/PID0
proofs, fresh authorized4–7 idle and the unchanged72GiB model admission. This
preflight proves none of native frame coverage, bitwise output/state parity,
full36x4096 noninterference, SOURCE_LOCK, final192 plans, mixed/graph lifecycle,
paired E2E throughput or task accuracy. No accepted migration is claimed.
DAMP cutoff2026-10-07T08:48:03Z and portfolio cutoff2026-10-09T11:17:31Z remain.
