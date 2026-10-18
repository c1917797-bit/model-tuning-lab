# BOLE retained-input probability quantization probe

## Bounded purpose

Test whether rounding saved-input softmax probabilities from independent FP64
to BF16 can explain three preregistered output blocks. This is a CPU diagnostic,
not a model repair, kernel implementation claim, numerical acceptance or
performance result. Original R6 failures are retained; all qualification flags stay false.

## Exact cases

All cases are original R6 rank 1, FA layer 43:

| Case | Original failed elements | Active KV tokens |
| --- | ---: | ---: |
| tree node 2 | 1 | 133 |
| native path 2, node 2 | 1 | 133 |
| tree node 0, passing control | 0 | 132 |

The two failing blocks both include head 2 / channel 61. Each block is compared
over all 6 x 256 = 1536 elements; case selection is not changed after execution.
Each arm uses its own original input frame. Tree/native frames are not assumed
to have equal Q/K/V. Original rank and previous rounding reports are fixed by
path, byte count and SHA256 in PLAN.json and plan.py.

## Single intervention

Both arms share the exact Python-FP64 QK products with math.fsum, scale 0.0625,
stable math.exp softmax, PV products with math.fsum, and nearest-even final BF16
rounding. The intervention alone rounds P64 to BF16 and widens it to FP64 before
PV. It does not renormalize probabilities or change any other precision stage.

BF16 conversion inspects neighbors around an FP32 seed to avoid double-rounding
midpoint errors. Signed zero is retained. Nonfinite or out-of-range conversions
fail instead of being silently clipped.

The diagnostic uses the same atol=0.001 and rtol=0.01 with its independently
computed compensated reference. The original CPU64 acceptance decision is not
replaced: the fixed prior report and the original 1/1/0 counts and failing element
identities must still match. All reports explicitly remain unqualified.

## Deployment and execution boundary

Remote source root:
`/cache/cch/qwen36-paper-preparation-20261007/lowbit/bole-fa-probability-quantization-renew24h-20261018-001`

Remote output leaf:
`/opt/host/vnf/austinov/run-bole-fa-probability-quantization-MAIN-RENEW24H_001/fa/consumer`

MAIN alone deploys the byte-exact source, reviews and hashes SOURCE_TEMPLATE.json,
binds it once with bind.py, audits the resulting SOURCE_BOUND.json, and admits
resources before owner.py --execute. SOURCE_BOUND.json is generated remotely;
it is deliberately absent from this proposal. Do not pass the cpu leaf or reuse
an existing output. Do not modify old sources, old outputs or the authority.

The owner derives from the previously inspected and executed rounding owner:
fixed existing authority, start 1792226600, cutoff 1792313000
(2026-10-18 08:43:20 UTC), whole 900 seconds including cleanup; guest 8 GiB,
1 CPU; host soft address-space limit 512 MiB; inherited hard limit unlimited;
no device nodes, no network, read-only root and inputs, one writable output leaf.
The inherited authority has not been extended. Execution must start with a full
900-second budget remaining after closure checking.

Fresh admission still requires 16.5 GiB MemAvailable, 13.5 GiB output-filesystem
free space, live reserve 8.5 GiB and output cap 5 GiB. The only raw input is the
fixed 776,474,709-byte rank-1 artifact. All labeled owned tasks must be absent;
the new task does not bypass no_overlap. Docker uses exact image digest, CID,
mount, command and resource inspection, normal stop, retained evidence and
post-stop source hashing. No detached process or NPU request is introduced.

## Outputs

- SOFTWARE.json: twelve arithmetic controls actually executed in the cold image.
- PROBE.json: three full-vector comparisons, input and probability hashes,
  bitwise match counts, unchanged-gate diagnostics, failed-point predictions.
- ATTRIBUTION.json: complete three-case result; qualified/kernel_path_proven=false.
- RESULT.json and FINAL_INSPECT.json: owner completion and exact resource release.

Passing arithmetic controls cannot prove the raw-data extraction path. This
local runtime has no torch, so raw tensor extraction was statically reviewed;
actual execution checks the source-bound tensor shapes, dtypes, mask, prefix and
ancestor joins before doing the diagnostic. The controls do not load old raw
data, start Docker, request NPU, download software or use network.

## Changes from the executed rounding package

- Reuse owner/bind resource and cleanup logic with new exact root, owner labels,
  source/result schemas and consumer-only output guard; remove dead preflight
  receiver and unused unrelated producer constant; correct diagnostic log labels.
- Replace four-rank rounding audit with one-rank, three-case preregistered plan.
- Add fixed references to the completed rounding diagnostic, preserving failures.
- Add probability quantization as the sole arithmetic intervention; no kernel,
  model, scheduler, tolerance, authority or ledger changes.
- Keep source references immutable and expose no numerical qualification switch.

## Interpretation

Matching saved output supports the explanatory precision model for these frames.
It does not prove the real kernel uses that path. Failure to match leaves the
hypothesis unsupported or incomplete. Do not tune a precision combination to
the answers, waive R6 FA failures, or label an exit-0 CPU diagnostic as model
acceptance or NPU performance evidence.
