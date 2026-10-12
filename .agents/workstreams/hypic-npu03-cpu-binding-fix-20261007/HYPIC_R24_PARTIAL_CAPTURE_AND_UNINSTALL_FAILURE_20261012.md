# r24 partial numerical capture and uninstall failure — 2026-10-12

## Decision

Frozen r24 remains **FAILED_POST_UNINSTALL**, not accepted. Controller
exec-0000000000000d16 ended exit1 after 598.259 seconds. Source/image,
four-worker installation, three completed requests and selected captures are
valid partial evidence. The fourth, post-uninstall request failed HTTP500.
No quality/performance claim or r19/r22 reclassification follows.

Raw root:
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r24-state-enabled`

Separate post-terminal partial auditor: `r24_partial_capture_audit.py`,
exec-0000000000000d2a exit0. It does not replace or weaken the frozen r24 auditor.
External audit:
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/r24-state-enabled-partial-capture-audit.json`
SHA256 `aaf7f910e93eabb74222fad7aa27431a880cb697178c4c007627b28c8a986518`.

## Observed device evidence

- Unchanged HYPIC source4429e35177979c874bf053ab29789e4773f39b22 in pinned
  image660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1.
- Known-hot serial sample59: two one-token warmups, target20414 input /
  1496 output tokens, natural stop. The post-uninstall request failed.
- Four workers, namespace PIDs268-271 / host PIDs283779-283782, all captured
  the exact internal request chatcmpl-hypic-state-r24-s059-bb17110c at step8.
- Per rank: selected KV keys/values (three rows, head0), convolution slots,
  positions and destination-cast GDN state all had max_abs0 and zero differing
  coordinates. FP64 GDN residual maxima by rank:
  1.4594260377975843e-07, 9.328871364289171e-07,
  5.622073295796781e-08, 0.
- 110 continuous physical0-3 isolation samples clean; exact own container,
  port and physical processes released. No NPU4-7 workload or foreign task altered.

The nested CPU comparator deliberately reports physical_device_proven=false:
physical provenance is checked by the outer independent auditor, not inferred
from tensor JSON. Selected layers/head/rows are NOT all-layer equivalence.
Material inputs/producer generations were not independently regenerated.
This narrows sampled destination/replay corruption for this one request only;
it neither explains nor overturns r19 full quality regression.

## Failure mechanism and prospective fix

Full service log SHA256:
`46299b8dbd26d500b3c217c67c4a8282a05d2e050a7738cc09be2e751513c67c`.

After uninstall, a retained instrumented GDN function referenced the deleted
global `_hypic_diagnostic_state_observer`, raising NameError. Restoring the module
attribute does not invalidate already-retained function aliases. The CPU
regression reproduces this exact mechanism; compiler retention is a possible
carrier, not independently isolated as the only retention source.

New, unconnected `numerical_state_observer_v2.py` uses generation-specific
dispatchers. Uninstall restores owned function attributes and clears callback
references but retains inert globals so aliases remain callable. Reinstall gets
a new generation; old aliases cannot reactivate. This is active-hook removal,
not zero-residue namespace restoration; process restart removes tombstones.

52 CPU numerical tests passed exec-0000000000000d30, including old-failure
reproduction, retained-alias safety, reinstall isolation and disabled no-access.
This is NOT NPU post-uninstall validation. Frozen r24 controller, package,
support files and raw root are unchanged.

## Resume and skill lesson

Use runtime-monkeypatch-delivery: unload tests must call retained aliases and
a real post-uninstall request, not merely inspect restored module attributes.
Classify observer integration failure separately from algorithm quality.
Use ascend-benchmark-evidence: retain failed whole-experiment status even when
independently audited partial captures are informative; don't discard or promote
them wholesale.

Next package this single lifecycle correction prospectively, verify exact-image
integration, freeze a fresh bounded successor and recheck physical0-3/8223 before
device admission. Do not repeat r24 or another unchanged c32/full-quality wave.
29 cases remain provenance coverage (7 bounded verified,22 partial), not all
Skills accepted. Authentication unchanged: no push attempted or remote/main sync.
