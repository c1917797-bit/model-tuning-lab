# R15 exact ACL evidence repair; R14 failure retained

R14 passed110 actual Linux CPU controls, then parser plugin failed BEFORE model.
This is not a native enum-value difference: source line175 is exactly
`ACL_FORMAT_ND = 2,`. Its embedded header is13721B/SHA827d3a579902e1e81a85e0d7c5e1f0f541a5f65ab00662bac40d0e509376085a,
whereas the unchanged plugin expects the reviewed actual13720B/SHA4055d6b9d3a96face0efb5d68aafb68900a1d9c78c6a877ae21381688dd8b529.
The exact difference is one trailing LF. The local original snapshot already has
the extra LF, so the corruption precedes LAYOUT/base64 generation; its original
creation step remains UNKNOWN. MAIN independently re-opened stopped actual R14
candidate2104eadab7fcb0fe56a71296ffc942c5766436aa2cf554b4b33dcbb573cb220c
via read-only docker-cp TAR operation107e (exit0, exactly one regular member):
`/usr/local/Ascend/ascend-toolkit/latest/include/acl/acl_base_rt.h`, exactly
13720B/SHA4055d6b9d3a96face0efb5d68aafb68900a1d9c78c6a877ae21381688dd8b529.
This confirms the old pin; no installed image file is changed. The operation
Ref itself is not supplied here and is not fabricated as a local actual report.

Only the new LAYOUT header snapshot is corrected by the explicit one-byte inverse
whose result must equal that already fixed reviewed SHA. No runtime stripping,
alternate SHA allowlist, relaxed ND predicate or enum parser is introduced.
The collector, plugin (including actual strict guard), independent consumer,
client, native math, safety host/observers, budgets and thresholds are EXACT R14.
All four embedded source entries have byte/SHA/base64 self-consistency controls;
this does not pretend to independently re-read actual installed package sources.

New four stdlib controls execute the actual plugin guard expression against the
actual repaired embedded header; old extraLF, wrongSHA, ND-value change (even with
updated self-consistent embedded SHA), and malformed embedded records are refused.
These are added to the existing mandatory110, now114. Existing native/geometry/
short-prior/source tests remain mandatory. Actual sameimage114 and real parser
still must run under MAIN admission. No new actual resource/format/model PASS is
supplied. Preserve R14 failed owner and all original sources/output.

Use only COMMANDS_FINAL.json after complete byte deployment and actual bind.
The source-bound COMMANDS.json keeps its seal placeholder, not final execution.
New root/output/run/owner are R15; old authority/cutoff2700whole270cleanup,
RAM48+.5+8, Docker8.5GiB and opt40.5GiB are unchanged. Native observation still
unconditionally stops before decoder; it cannot grant numerical/model/perf/task
qualification, normal EOS or real reuse. Actual4rank reports remain pending.
