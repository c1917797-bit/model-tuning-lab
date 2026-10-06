# Native source gate stopped before math — 2026-10-06

MA0674 is actual terminal exit1, NOT live and NOT an accepted native feedback run.
It passed fresh nonprivileged NPU7 -> logical0 mul canary, observed actual
Ascend910B4/OPP9.1, pinned23 actual-image sources and three mapped selected/
decode/reference libraries. It stopped with zero numeric checks and zero native
cases at native_feedback.py's `inspect.getsourcefile(native)` hash assertion.
Original operation/report/failure and stop/release byte identities are in JSON.

The actual chunk.py uses `@torch.compiler.disable` at line263. Source inspection
of a decorated callable can point to the Torch wrapper, not the wrapped
algorithm file. Exact wrapper chain proof is still under review; do not bypass
the original decorated callable, swap in an arbitrary source SHA or waive
native source admission. Read-only MA0683 copied three exact Torch source files
from the STOPPED exact owned container; those copies are not loaded-callable
proof. No runtime/image/reference file was modified.

Exact owned418ab815... is stopped retained, Pid0/Runningfalse/OOMKilledfalse;
physical0–3 fingerprints and post-release were checked. MA0670's isolated
failure container also remains stopped retained. There is now no own NPU load.
Do not poll completed0670/0674 or launch another copy of their failed commands.

## Next finite action, without fabricated readiness

1. Prepare corrected realP2 noncontiguous indices fixture; assert exact-image
   semantics before numerical dispatch. Preserve all57 negatives and full
   packing/160-step feedback matrices; no kernel or threshold change is needed.
2. Prove actual native callable alias, wrapper/backlink chain and wrapped
   chunk source identities, still invoking the original decorated function.
3. Refresh only necessary source closures, software tests and target-image
   framework-semantic preflight; use fresh one-shot run IDs after MAIN review.
4. Prepare independent trueT/allP dispatchers in parallel, but admit each only
   with its own numerical/source proof and symmetric resource monitors.
5. Calibration OFF/ON remains failed, no final192/full service/E2E/task claim.

Auxiliary MAIN read-only probes also exposed absent hardcoded npu-smi and rg
executable paths. Preserve their actual failures; resolve executable paths/
safe read-only fallback before diagnostics. They did not cause either operator
gate failure and are not NPU numerical conclusions.

The user requirement is pre-card readiness and useful finite validation,
not artificial24h card occupancy or a guarantee that every unseen bug vanishes.
Fixed DAMP deadline remains 2026-10-07T08:48:03Z.
